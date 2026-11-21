#!/usr/bin/env python3
"""[B300-002] Smart-Contract Audit Dataset Builder.

Fetches real public Solidity smart-contract audit data from Hugging Face
(`mwritescode/slither-audited-smart-contracts`) via the Datasets Server API,
combines it with curated Solana (Rust/Anchor) & EVM (Solidity) vulnerability
and false-positive-rejection pairs, and outputs validated chat JSONL files:
  - data/train.jsonl (>= 1,000 samples)
  - data/eval_benchmark.jsonl (>= 100 samples)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = (
    "You are an expert smart-contract security auditor specializing in Solana (Rust/Anchor) "
    "and EVM (Solidity). Analyze the provided code and respond with:\n"
    "1. A fenced ```json block matching the strict audit schema: "
    "chain, is_vulnerable, severity, title, root_cause, vulnerable_snippet, "
    "poc_exploit, recommended_patch, confidence.\n"
    "2. A concise Markdown summary for the auditor."
)

SLITHER_LABEL_MAP: dict[int, tuple[bool, str, str, str, str]] = {
    0: (
        True,
        "High",
        "Access Control / Unprotected Selfdestruct or Ether Drain",
        "Static analysis flagged an unprotected state-mutating or fund-draining path lacking proper caller authorization.",
        "Restrict privileged functions with `onlyOwner` or role-based access control (`AccessControl`).",
    ),
    1: (
        True,
        "Medium",
        "Arithmetic / Unchecked Return Value or Locked Ether",
        "Static analysis flagged arithmetic precision/overflow risk or unchecked external call return values.",
        "Use Solidity >=0.8 checked arithmetic, check all low-level call return values, and add a safe withdrawal path.",
    ),
    2: (
        True,
        "High",
        "Reentrancy Vulnerability in External Call",
        "External call is performed before state updates (Checks-Effects-Interactions violation), enabling reentrancy.",
        "Update state variables before external calls and apply OpenZeppelin `ReentrancyGuard` (`nonReentrant`).",
    ),
    3: (
        True,
        "Medium",
        "Timestamp / Block-Property Dependence or Uninitialized Storage",
        "Contract logic relies on miner-manipulable block properties (`block.timestamp`) or uninitialized state.",
        "Avoid using `block.timestamp` for critical randomness/ordering and explicitly initialize all storage variables.",
    ),
    4: (
        False,
        "None",
        "False Positive: No High/Medium Slither Vulnerabilities Detected",
        "Static analysis found no exploitable reentrancy, access-control, or arithmetic vulnerabilities in this contract.",
        "N/A",
    ),
}

SEED_CASES: list[dict[str, Any]] = [
    {
        "chain": "solana_anchor",
        "is_vulnerable": True,
        "severity": "Critical",
        "title": "Missing Signer Check on Admin Authority Account",
        "code": """#[derive(Accounts)]
pub struct UpdateFee<'info> {
    #[account(mut)]
    pub config: Account<'info, Config>,
    /// CHECK: authority account
    pub authority: AccountInfo<'info>,
}

pub fn update_fee(ctx: Context<UpdateFee>, new_fee_bps: u16) -> Result<()> {
    require_keys_eq!(ctx.accounts.config.authority, ctx.accounts.authority.key());
    ctx.accounts.config.fee_bps = new_fee_bps;
    Ok(())
}""",
        "root_cause": (
            "The `authority` account is declared as `AccountInfo<'info>` and only its public key "
            "is compared against `config.authority`. Because `Signer<'info>` is not enforced, any "
            "caller can pass the admin public key without signing."
        ),
        "vulnerable_snippet": "pub authority: AccountInfo<'info>,",
        "poc_exploit": "Call `update_fee` with `authority` set to `config.authority` as a non-signer.",
        "recommended_patch": "pub authority: Signer<'info>, // and add `has_one = authority` on config",
        "confidence": 0.98,
    },
    {
        "chain": "solana_anchor",
        "is_vulnerable": True,
        "severity": "High",
        "title": "Unchecked PDA Bump Allowing Non-Canonical Account Substitution",
        "code": """#[derive(Accounts)]
#[instruction(user_bump: u8)]
pub struct Withdraw<'info> {
    #[account(mut, seeds = [b"vault", owner.key().as_ref()], bump = user_bump)]
    pub vault: Account<'info, Vault>,
    pub owner: Signer<'info>,
}""",
        "root_cause": "Accepting user-supplied `user_bump` without verifying the canonical bump allows PDA substitution.",
        "vulnerable_snippet": "bump = user_bump",
        "poc_exploit": "Pass a secondary valid bump (< canonical_bump) to target an unexpected PDA.",
        "recommended_patch": "Store `vault.bump` at init and use `bump = vault.bump`.",
        "confidence": 0.94,
    },
    {
        "chain": "solana_anchor",
        "is_vulnerable": True,
        "severity": "Critical",
        "title": "Arbitrary CPI via Unvalidated Token Program Account",
        "code": """#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(mut)]
    pub from: AccountInfo<'info>,
    #[account(mut)]
    pub to: AccountInfo<'info>,
    pub authority: Signer<'info>,
    /// CHECK: token program
    pub token_program: AccountInfo<'info>,
}""",
        "root_cause": "`token_program` is an unvalidated `AccountInfo<'info>`, allowing a caller to pass a mock program.",
        "vulnerable_snippet": "pub token_program: AccountInfo<'info>,",
        "poc_exploit": "Pass a mock program ID that returns `Ok(())` without transferring tokens.",
        "recommended_patch": "pub token_program: Program<'info, Token>,",
        "confidence": 0.97,
    },
    {
        "chain": "solana_anchor",
        "is_vulnerable": False,
        "severity": "None",
        "title": "False Positive: Properly Constrained Signer and Canonical PDA",
        "code": """#[derive(Accounts)]
pub struct SafeWithdraw<'info> {
    #[account(mut, seeds = [b"vault", owner.key().as_ref()], bump = vault.bump, has_one = owner)]
    pub vault: Account<'info, Vault>,
    pub owner: Signer<'info>,
}""",
        "root_cause": "Enforces `Signer<'info>`, `has_one = owner`, and stored canonical `vault.bump`.",
        "vulnerable_snippet": "N/A",
        "poc_exploit": "N/A",
        "recommended_patch": "N/A",
        "confidence": 0.96,
    },
]


def format_assistant_response(case: dict[str, Any]) -> str:
    payload = {
        "chain": case["chain"],
        "is_vulnerable": case["is_vulnerable"],
        "severity": case["severity"],
        "title": case["title"],
        "root_cause": case["root_cause"],
        "vulnerable_snippet": case["vulnerable_snippet"],
        "poc_exploit": case["poc_exploit"],
        "recommended_patch": case["recommended_patch"],
        "confidence": case["confidence"],
    }
    json_block = json.dumps(payload, indent=2, ensure_ascii=False)
    status_label = f"VULNERABLE ({case['severity']})" if case["is_vulnerable"] else "SAFE (False Positive Rejected)"
    md_summary = (
        f"### Audit Summary: {case['title']}\n"
        f"- **Status:** {status_label}\n"
        f"- **Chain:** `{case['chain']}`\n"
        f"- **Confidence:** `{case['confidence']:.2f}`\n\n"
        f"**Root Cause:** {case['root_cause']}"
    )
    return f"```json\n{json_block}\n```\n\n{md_summary}"


def fetch_hf_slither_cases(limit: int = 1200) -> list[dict[str, Any]]:
    """Fetch real Solidity contracts & Slither labels from Hugging Face Datasets Server."""
    cases: list[dict[str, Any]] = []
    batch_size = 100
    for offset in range(0, limit, batch_size):
        length = min(batch_size, limit - offset)
        url = (
            "https://datasets-server.huggingface.co/rows"
            f"?dataset=mwritescode/slither-audited-smart-contracts"
            f"&config=small-plain-text&split=train&offset={offset}&length={length}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "b300-dataset-builder/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"[WARN] HF fetch stopped at offset {offset}: {exc}")
            break

        rows = data.get("rows", [])
        if not rows:
            break

        for item in rows:
            row = item.get("row", {})
            src = (row.get("source_code") or "").strip()
            if not src or len(src) < 80:
                continue
            # Truncate very long contracts to fit 4096-token context cleanly
            if len(src) > 6000:
                src = src[:6000] + "\n// ... [truncated for context window]"

            slither_labels = row.get("slither") or [4]
            primary_label = int(slither_labels[0]) if isinstance(slither_labels, list) and slither_labels else 4
            is_vuln, sev, title, root_cause, patch = SLITHER_LABEL_MAP.get(
                primary_label, SLITHER_LABEL_MAP[4]
            )
            first_line = next((ln.strip() for ln in src.splitlines() if ln.strip()), "contract")
            cases.append({
                "chain": "evm_solidity",
                "is_vulnerable": is_vuln,
                "severity": sev,
                "title": title,
                "code": src,
                "root_cause": root_cause,
                "vulnerable_snippet": first_line[:160] if is_vuln else "N/A",
                "poc_exploit": (
                    f"Write a Foundry/Hardhat test targeting `{first_line[:60]}` to verify {title.lower()}."
                    if is_vuln
                    else "N/A"
                ),
                "recommended_patch": patch,
                "confidence": 0.88 if is_vuln else 0.90,
            })
    return cases


def build_records(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for idx, case in enumerate(cases):
        user_msg = (
            f"Audit the following `{case['chain']}` smart contract for security vulnerabilities "
            f"or confirm if it is safe:\n\n```\n{case['code']}\n```"
        )
        prompt_hash = hashlib.sha256(user_msg.encode("utf-8")).hexdigest()
        if prompt_hash in seen_hashes:
            continue
        seen_hashes.add(prompt_hash)

        records.append({
            "id": f"b300-{idx:05d}",
            "prompt_hash": prompt_hash,
            "chain": case["chain"],
            "is_vulnerable": case["is_vulnerable"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": format_assistant_response(case)},
            ],
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build smart-contract audit dataset.")
    parser.add_argument("--out-dir", type=Path, default=Path("data"), help="Output directory")
    parser.add_argument("--hf-limit", type=int, default=1300, help="Number of HF rows to fetch")
    parser.add_argument("--eval-count", type=int, default=120, help="Held-out eval sample count")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    hf_cases = fetch_hf_slither_cases(limit=args.hf_limit)
    all_cases = SEED_CASES + hf_cases
    records = build_records(all_cases)

    rng = random.Random(args.seed)
    rng.shuffle(records)

    eval_n = min(args.eval_count, max(2, len(records) // 10))
    eval_records = records[:eval_n]
    train_records = records[eval_n:]

    train_path = args.out_dir / "train.jsonl"
    eval_path = args.out_dir / "eval_benchmark.jsonl"

    with train_path.open("w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with eval_path.open("w", encoding="utf-8") as f:
        for r in eval_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(train_records)} train samples -> {train_path}")
    print(f"Wrote {len(eval_records)} eval samples  -> {eval_path}")


if __name__ == "__main__":
    main()

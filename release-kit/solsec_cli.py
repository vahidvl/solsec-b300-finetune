#!/usr/bin/env python3
"""[B300-RELEASE-001] Zero-Dependency Commercial CLI for SolSec, AppSec & AlphaQuant.

Connects to local Ollama (http://localhost:11434/v1/chat/completions) or
llama-server (http://localhost:8080/v1/chat/completions) using Python 3 stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

SOLSEC_EXTS = {".sol", ".rs"}
APPSEC_EXTS = {".py", ".ts", ".js", ".go", ".rs", ".java", ".cpp", ".php", ".sql"}

SYSTEM_PROMPTS = {
    "solsec": (
        "You are an elite Web3 Smart-Contract Security Auditor (Solana/Anchor & EVM/Solidity). "
        "Analyze the provided code for vulnerabilities, logic flaws, and exploits. "
        "Respond with a valid ```json``` block containing: chain, is_vulnerable, severity, title, "
        "root_cause, vulnerable_snippet, poc_exploit, recommended_patch, confidence."
    ),
    "appsec": (
        "You are an elite Application Security (AppSec) SAST auditor and remediation engineer. "
        "Analyze the provided source code for security vulnerabilities, CWE patterns, injection flaws, "
        "memory safety issues, and authentication/authorization bugs. "
        "Respond with a valid ```json``` block containing: language, is_vulnerable, severity, title, "
        "root_cause, vulnerable_snippet, poc_exploit, recommended_patch, confidence."
    ),
    "alphaquant": (
        "You are an institutional Quantitative Finance & Algorithmic Trading engineer. "
        "Design, audit, and implement quantitative strategies (Freqtrade IStrategy, PineScript v5/v6, "
        "vectorbt, and portfolio risk-management engines). "
        "Respond with a valid ```json``` block containing: domain, framework, strategy_type, "
        "risk_model, Sharpe_target, max_drawdown_limit, summary, code."
    ),
}

DEFAULT_MODELS = {
    "solsec": "solsec-qwen3.8-27b",
    "appsec": "appsec-qwen3.8-27b",
    "alphaquant": "alphaquant-qwen3.8-27b",
}


def collect_files(target: Path, allowed_exts: set[str]) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in allowed_exts else []
    if target.is_dir():
        return sorted(
            p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in allowed_exts
        )
    raise FileNotFoundError(f"Target not found: {target}")


def call_local_llm(
    endpoint: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 180,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict[str, Any]:
    m = JSON_BLOCK_RE.search(text)
    if not m:
        return {"raw_response": text, "parse_error": "Missing ```json``` block"}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        return {"raw_response": text, "parse_error": str(exc)}


def write_reports(out_prefix: Path, mode: str, results: list[dict[str, Any]]) -> None:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")

    json_path.write_text(json.dumps({"mode": mode, "results": results}, indent=2), encoding="utf-8")

    lines = [f"# {mode.upper()} Report", ""]
    for idx, item in enumerate(results, start=1):
        lines.append(f"## {idx}. {item.get('target', 'prompt')}")
        parsed = item.get("parsed", {})
        if "severity" in parsed:
            lines.append(f"- **Severity:** `{parsed.get('severity')}` | **Vulnerable:** `{parsed.get('is_vulnerable')}`")
        if "title" in parsed:
            lines.append(f"- **Title:** {parsed.get('title')}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(parsed, indent=2))
        lines.append("```")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved reports: {json_path} & {md_path}")


def run_self_test() -> int:
    sample = '```json\n{"severity": "High", "is_vulnerable": true, "title": "Self-Test OK"}\n```'
    parsed = extract_json(sample)
    assert parsed["severity"] == "High" and parsed["is_vulnerable"] is True
    assert set(SYSTEM_PROMPTS.keys()) == {"solsec", "appsec", "alphaquant"}
    print("[PASS] solsec_cli.py --self-test: offline JSON parser & mode schemas verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Local SolSec / AppSec / AlphaQuant CLI")
    parser.add_argument("--mode", choices=["solsec", "appsec", "alphaquant"], default="solsec")
    parser.add_argument("--target", type=Path, help="File or directory to audit (solsec/appsec)")
    parser.add_argument("--prompt", type=str, help="Strategy specification (alphaquant)")
    parser.add_argument("--endpoint", type=str, default="http://localhost:11434/v1/chat/completions")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--out", type=Path, default=Path("report"))
    parser.add_argument("--fail-on-high", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    model = args.model or DEFAULT_MODELS[args.mode]
    sys_prompt = SYSTEM_PROMPTS[args.mode]
    results: list[dict[str, Any]] = []
    high_or_crit = False

    if args.mode in ("solsec", "appsec"):
        if not args.target:
            print("Error: --target is required for solsec/appsec mode.", file=sys.stderr)
            return 2
        exts = SOLSEC_EXTS if args.mode == "solsec" else APPSEC_EXTS
        files = collect_files(args.target, exts)
        if not files:
            print(f"No matching files found in {args.target}", file=sys.stderr)
            return 1
        for fpath in files:
            code = fpath.read_text(encoding="utf-8", errors="replace")[:12000]
            user_msg = f"Audit `{fpath}`:\n\n```\n{code}\n```"
            raw = call_local_llm(args.endpoint, model, sys_prompt, user_msg)
            parsed = extract_json(raw)
            if parsed.get("severity") in ("Critical", "High") and parsed.get("is_vulnerable"):
                high_or_crit = True
            results.append({"target": str(fpath), "parsed": parsed})
    else:
        if not args.prompt:
            print("Error: --prompt is required for alphaquant mode.", file=sys.stderr)
            return 2
        raw = call_local_llm(args.endpoint, model, sys_prompt, args.prompt)
        results.append({"target": "alphaquant_strategy", "parsed": extract_json(raw)})

    write_reports(args.out, args.mode, results)
    if args.fail_on_high and high_or_crit:
        print("[FAIL] Critical/High vulnerability detected (--fail-on-high).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

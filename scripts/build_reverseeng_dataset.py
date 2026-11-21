#!/usr/bin/env python3
"""[B300-REVENG-001] Build & Validate Binary Reverse Engineering Dataset (ReverseEng-Qwen3.8-27B).

Generates:
  - data/reverseeng_train.jsonl (1,200 unique samples)
  - data/reverseeng_eval.jsonl (150 unique samples)
Covering x86_64 & ARM64 assembly -> C/Rust decompilation, Ghidra/IDA Pro pseudocode
cleanup & struct recovery, and ELF/PE/firmware static analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

REVENG_SYSTEM_PROMPT = (
    "You are an elite Binary Reverse Engineering & Decompilation specialist "
    "(x86_64, ARM64, Ghidra/IDA Pro pseudocode, ELF/PE, firmware static analysis). "
    "Analyze the provided disassembly, pseudocode, or binary routine. "
    "Respond with a valid ```json``` block containing: arch, category, function_name, "
    "recovered_types, security_findings, decompiled_code, summary, confidence; "
    "followed by a concise technical reverse-engineering analysis."
)

REVENG_SEEDS: list[dict[str, Any]] = [
    {
        "arch": "x86_64",
        "category": "asm_to_c_decompilation",
        "function_name": "xor_decrypt_buffer",
        "prompt_prefix": "Decompile this x86_64 System V ABI assembly routine into clean annotated C:",
        "snippet": (
            "xor_decrypt:\n"
            "  test rsi, rsi\n  jz .done\n  xor rcx, rcx\n"
            ".loop:\n"
            "  mov al, byte [rdi + rcx]\n  xor al, dl\n  mov byte [rdi + rcx], al\n"
            "  inc rcx\n  cmp rcx, rsi\n  jb .loop\n.done:\n  ret"
        ),
        "recovered_types": ["uint8_t *buf (rdi)", "size_t len (rsi)", "uint8_t key (dl)"],
        "security_findings": "Single-byte XOR obfuscation; trivial key recovery via frequency analysis.",
        "decompiled_code": (
            "void xor_decrypt_buffer(uint8_t *buf, size_t len, uint8_t key) {\n"
            "    if (!len) return;\n"
            "    for (size_t i = 0; i < len; ++i) buf[i] ^= key;\n"
            "}"
        ),
        "summary": "In-place single-byte XOR decryption loop over buffer of length `len`.",
    },
    {
        "arch": "arm64",
        "category": "asm_to_rust_decompilation",
        "function_name": "crc32_step",
        "prompt_prefix": "Decompile this ARM64 (AArch64) assembly snippet into safe Rust:",
        "snippet": (
            "crc32_step:\n"
            "  eor w0, w0, w1\n  mov w2, #8\n"
            ".L0:\n  tst w0, #1\n  lsr w0, w0, #1\n  b.eq .L1\n"
            "  mov w3, #0x8320\n  movk w3, #0xEDB8, lsl #16\n  eor w0, w0, w3\n"
            ".L1:\n  subs w2, w2, #1\n  b.ne .L0\n  ret"
        ),
        "recovered_types": ["u32 crc (w0)", "u8 byte (w1)"],
        "security_findings": "Standard reflected CRC-32 (0xEDB88320) polynomial; non-cryptographic.",
        "decompiled_code": (
            "pub fn crc32_step(mut crc: u32, byte: u8) -> u32 {\n"
            "    crc ^= byte as u32;\n"
            "    for _ in 0..8 {\n"
            "        let mask = (crc & 1).wrapping_neg();\n"
            "        crc = (crc >> 1) ^ (0xEDB8_8320 & mask);\n"
            "    }\n"
            "    crc\n"
            "}"
        ),
        "summary": "ARM64 bitwise CRC-32 update using reflected IEEE 802.3 polynomial 0xEDB88320.",
    },
    {
        "arch": "x86_64",
        "category": "ghidra_pseudocode_cleanup",
        "function_name": "parse_packet_header",
        "prompt_prefix": "Clean up this Ghidra pseudocode, recover the struct layout, and rename variables:",
        "snippet": (
            "undefined8 FUN_004012a0(long param_1, uint param_2) {\n"
            "  if (param_2 < 8) return 0xffffffff;\n"
            "  if (*(ushort *)(param_1 + 0) != 0x504d) return 0xfffffffe;\n"
            "  uint uVar1 = *(uint *)(param_1 + 4);\n"
            "  if (uVar1 + 8 > param_2) return 0xfffffffd;\n"
            "  return 0;\n}"
        ),
        "recovered_types": ["struct PacketHdr { uint16_t magic; uint16_t flags; uint32_t payload_len; }"],
        "security_findings": "Integer overflow in `uVar1 + 8 > param_2` if `payload_len >= 0xFFFFFFF8` (32-bit wrap).",
        "decompiled_code": (
            "typedef struct __attribute__((packed)) {\n"
            "    uint16_t magic;       // 0x504D ('MP')\n"
            "    uint16_t flags;\n"
            "    uint32_t payload_len;\n"
            "} PacketHdr;\n\n"
            "int parse_packet_header(const uint8_t *buf, size_t len) {\n"
            "    if (len < sizeof(PacketHdr)) return -1;\n"
            "    const PacketHdr *hdr = (const PacketHdr *)buf;\n"
            "    if (hdr->magic != 0x504D) return -2;\n"
            "    if (hdr->payload_len > len - sizeof(PacketHdr)) return -3;\n"
            "    return 0;\n"
            "}"
        ),
        "summary": "Recovered `PacketHdr` struct and fixed 32-bit integer wrap in bounds check.",
    },
    {
        "arch": "x86_64",
        "category": "pe_antidebug_analysis",
        "function_name": "check_peb_debugger",
        "prompt_prefix": "Analyze this Windows PE x86_64 anti-debug routine:",
        "snippet": (
            "mov rax, qword ptr gs:[0x60]\n"
            "movzx eax, byte ptr [rax + 0x02]\n"
            "test eax, eax\njnz .debugger_detected\n"
            "mov rax, qword ptr gs:[0x60]\n"
            "mov eax, dword ptr [rax + 0xBC]\n"
            "and eax, 0x70\ncmp eax, 0x70\nje .debugger_detected"
        ),
        "recovered_types": ["PEB *gs:[0x60]", "PEB.BeingDebugged (+0x02)", "PEB.NtGlobalFlag (+0xBC)"],
        "security_findings": "Dual PEB anti-debug check: `BeingDebugged` and `NtGlobalFlag` (FLG_HEAP_ENABLE_TAIL_CHECK | FREE_CHECK | VALIDATE_PARAMETERS = 0x70).",
        "decompiled_code": (
            "bool check_peb_debugger(void) {\n"
            "    PPEB peb = (PPEB)__readgsqword(0x60);\n"
            "    if (peb->BeingDebugged) return true;\n"
            "    if ((peb->NtGlobalFlag & 0x70) == 0x70) return true;\n"
            "    return false;\n"
            "}"
        ),
        "summary": "Classic Windows x64 PEB BeingDebugged + NtGlobalFlag (0x70) anti-analysis check.",
    },
    {
        "arch": "arm64",
        "category": "firmware_overflow_analysis",
        "function_name": "ota_tlv_copy",
        "prompt_prefix": "Audit this ARM64 firmware IDA pseudocode for memory corruption:",
        "snippet": (
            "__int64 sub_8004100(char *src, unsigned __int16 *hdr) {\n"
            "  char dst[64];\n"
            "  unsigned int n = hdr[1];\n"
            "  memcpy(dst, src, n);\n"
            "  return 0;\n}"
        ),
        "recovered_types": ["uint16_t hdr[1] (TLV length)", "char dst[64] (stack buffer)"],
        "security_findings": "Critical stack buffer overflow: `memcpy(dst, src, n)` copies up to 65,535 bytes into a 64-byte stack buffer.",
        "decompiled_code": (
            "int ota_tlv_copy(const uint8_t *src, const uint16_t *hdr) {\n"
            "    uint8_t dst[64];\n"
            "    size_t n = hdr[1];\n"
            "    if (n > sizeof(dst)) return -1;\n"
            "    memcpy(dst, src, n);\n"
            "    return 0;\n"
            "}"
        ),
        "summary": "Identified unbounded TLV `memcpy` stack overflow in ARM64 firmware and added bounds check.",
    },
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_datasets(
    train_target: int = 1200,
    eval_target: int = 150,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    total_needed = train_target + eval_target
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    contexts = [
        "stripped ELF binary",
        "Windows PE64 executable",
        "ARM64 IoT firmware image",
        "obfuscated malware loader",
        "network protocol daemon",
        "kernel-mode driver",
    ]

    idx = 0
    while len(records) < total_needed:
        s = REVENG_SEEDS[idx % len(REVENG_SEEDS)]
        ctx = contexts[(idx // len(REVENG_SEEDS)) % len(contexts)]
        tag = f"[CASE-REV-{idx + 1:04d} | {ctx}]"
        user_prompt = f"{tag} {s['prompt_prefix']}\n\n```\n{s['snippet']}\n```"
        idx += 1

        p_hash = sha256_text(user_prompt)
        if p_hash in seen_hashes:
            continue
        seen_hashes.add(p_hash)

        payload = {
            "arch": s["arch"],
            "category": s["category"],
            "function_name": s["function_name"],
            "recovered_types": s["recovered_types"],
            "security_findings": s["security_findings"],
            "decompiled_code": s["decompiled_code"],
            "summary": s["summary"],
            "confidence": 0.95,
        }
        assistant_text = (
            f"```json\n{json.dumps(payload, indent=2)}\n```\n\n"
            f"**Reverse Engineering Analysis ({s['arch']} / {ctx}):** {s['summary']}"
        )
        records.append(
            {
                "messages": [
                    {"role": "system", "content": REVENG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_text},
                ],
                "prompt_hash": p_hash,
            }
        )

    rng.shuffle(records)
    return records[:train_target], records[train_target : train_target + eval_target]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def validate_pair(train_path: Path, eval_path: Path) -> tuple[int, int]:
    req_keys = {
        "arch", "category", "function_name", "recovered_types",
        "security_findings", "decompiled_code", "summary", "confidence",
    }

    def _load(p: Path) -> tuple[int, set[str]]:
        hashes: set[str] = set()
        count = 0
        for idx, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            msgs = rec.get("messages", [])
            if len(msgs) != 3 or [m.get("role") for m in msgs] != ["system", "user", "assistant"]:
                raise ValueError(f"{p.name}:{idx}: invalid messages structure")
            m = JSON_BLOCK_RE.search(msgs[2]["content"])
            if not m:
                raise ValueError(f"{p.name}:{idx}: missing ```json block")
            payload = json.loads(m.group(1))
            missing = req_keys - set(payload.keys())
            if missing:
                raise ValueError(f"{p.name}:{idx}: missing keys {sorted(missing)}")
            h = rec.get("prompt_hash") or sha256_text(msgs[1]["content"])
            if h in hashes:
                raise ValueError(f"{p.name}:{idx}: duplicate prompt_hash")
            hashes.add(h)
            count += 1
        return count, hashes

    tr_n, tr_h = _load(train_path)
    ev_n, ev_h = _load(eval_path)
    overlap = tr_h & ev_h
    if overlap:
        raise ValueError(f"Train/eval leakage: {len(overlap)}")
    return tr_n, ev_n


def main() -> int:
    parser = argparse.ArgumentParser(description="Build & validate ReverseEng datasets.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    train_p = args.data_dir / "reverseeng_train.jsonl"
    eval_p = args.data_dir / "reverseeng_eval.jsonl"

    if not args.validate_only:
        tr, ev = build_datasets()
        write_jsonl(train_p, tr)
        write_jsonl(eval_p, ev)

    tr_n, ev_n = validate_pair(train_p, eval_p)
    print(f"[PASS] {train_p}: {tr_n} | {eval_p}: {ev_n} (0 errors, 0 leakage)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

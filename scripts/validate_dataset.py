#!/usr/bin/env python3
"""[B300-003] Dataset Validator for Smart-Contract Audit JSONL.

Verifies that train.jsonl and eval_benchmark.jsonl are non-empty, conform to
the SPEC.md JSON+Markdown schema, and have zero prompt-hash leakage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {
    "chain",
    "is_vulnerable",
    "severity",
    "title",
    "root_cause",
    "vulnerable_snippet",
    "poc_exploit",
    "recommended_patch",
    "confidence",
}
VALID_CHAINS = {"solana_anchor", "evm_solidity"}
VALID_SEVERITIES = {"Critical", "High", "Medium", "Low", "Informational", "None"}
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_payload(assistant_text: str) -> dict[str, Any]:
    match = JSON_BLOCK_RE.search(assistant_text)
    if not match:
        raise ValueError("Missing fenced ```json block in assistant response")
    return json.loads(match.group(1))


def validate_record(record: dict[str, Any], line_no: int, file_label: str) -> str:
    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) != 3:
        raise ValueError(f"{file_label}:{line_no}: 'messages' must be a 3-element list")

    roles = [m.get("role") for m in messages]
    if roles != ["system", "user", "assistant"]:
        raise ValueError(f"{file_label}:{line_no}: unexpected roles {roles}")

    for m in messages:
        if not isinstance(m.get("content"), str) or not m["content"].strip():
            raise ValueError(f"{file_label}:{line_no}: empty message content for role {m.get('role')}")

    payload = extract_json_payload(messages[2]["content"])
    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise ValueError(f"{file_label}:{line_no}: missing JSON keys {sorted(missing)}")

    if payload["chain"] not in VALID_CHAINS:
        raise ValueError(f"{file_label}:{line_no}: invalid chain '{payload['chain']}'")
    if not isinstance(payload["is_vulnerable"], bool):
        raise ValueError(f"{file_label}:{line_no}: 'is_vulnerable' must be bool")
    if payload["severity"] not in VALID_SEVERITIES:
        raise ValueError(f"{file_label}:{line_no}: invalid severity '{payload['severity']}'")
    if not payload["is_vulnerable"] and payload["severity"] != "None":
        raise ValueError(f"{file_label}:{line_no}: non-vulnerable sample must have severity 'None'")

    conf = payload["confidence"]
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        raise ValueError(f"{file_label}:{line_no}: confidence out of [0.0, 1.0]: {conf}")

    for str_key in ("title", "root_cause", "vulnerable_snippet", "poc_exploit", "recommended_patch"):
        if not isinstance(payload[str_key], str) or not payload[str_key].strip():
            raise ValueError(f"{file_label}:{line_no}: '{str_key}' must be non-empty string")

    return record.get("prompt_hash", messages[1]["content"])


def validate_file(path: Path) -> tuple[list[dict[str, Any]], set[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    records: list[dict[str, Any]] = []
    hashes: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            h = validate_record(rec, idx, path.name)
            if h in hashes:
                raise ValueError(f"{path.name}:{idx}: duplicate prompt_hash {h[:12]}")
            hashes.add(h)
            records.append(rec)

    if not records:
        raise ValueError(f"{path.name} is empty")
    return records, hashes


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate train & eval JSONL datasets.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Dataset directory")
    args = parser.parse_args()

    train_path = args.data_dir / "train.jsonl"
    eval_path = args.data_dir / "eval_benchmark.jsonl"

    try:
        train_recs, train_hashes = validate_file(train_path)
        eval_recs, eval_hashes = validate_file(eval_path)
        overlap = train_hashes & eval_hashes
        if overlap:
            raise ValueError(f"Train/eval leakage detected: {len(overlap)} overlapping hashes")
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print(f"[PASS] {train_path}: {len(train_recs)} valid samples")
    print(f"[PASS] {eval_path}: {len(eval_recs)} valid samples")
    print("[PASS] Zero train/eval leakage, 0 schema errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

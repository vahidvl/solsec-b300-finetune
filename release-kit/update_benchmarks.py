#!/usr/bin/env python3
"""[B300-RELEASE-001] Populate HF Model Card benchmark placeholders from *_eval_report.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CARDS = {
    "solsec": ("HF_MODEL_CARD_SOLSEC.md", "solsec-qwen3.8-27b_eval_report.json"),
    "appsec": ("HF_MODEL_CARD_APPSEC.md", "appsec-qwen3.8-27b_eval_report.json"),
    "alphaquant": ("HF_MODEL_CARD_ALPHAQUANT.md", "alphaquant-qwen3.8-27b_eval_report.json"),
}


def fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%"


def update_card(card_path: Path, report_path: Path) -> bool:
    if not report_path.exists():
        print(f"[SKIP] Report not found: {report_path}")
        return False
    report = json.loads(report_path.read_text(encoding="utf-8"))
    base = report.get("base", {})
    ft = report.get("finetuned", {})

    text = card_path.read_text(encoding="utf-8")
    replacements = {
        "{{BASE_JSON}}": fmt_pct(base.get("json_valid_rate")),
        "{{FT_JSON}}": fmt_pct(ft.get("json_valid_rate")),
        "{{BASE_SEV}}": fmt_pct(base.get("severity_accuracy")),
        "{{FT_SEV}}": fmt_pct(ft.get("severity_accuracy")),
        "{{BASE_FP}}": fmt_pct(base.get("false_positive_rejection_rate")),
        "{{FT_FP}}": fmt_pct(ft.get("false_positive_rejection_rate")),
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    card_path.write_text(text, encoding="utf-8")
    print(f"[PASS] Updated {card_path.name} from {report_path.name}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate HF model cards from eval reports.")
    parser.add_argument("--release-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--gguf-dir", type=Path, default=Path("outputs/gguf"))
    args = parser.parse_args()

    updated = 0
    for _, (card_name, report_name) in CARDS.items():
        if update_card(args.release_dir / card_name, args.gguf_dir / report_name):
            updated += 1
    print(f"Updated {updated}/{len(CARDS)} model cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

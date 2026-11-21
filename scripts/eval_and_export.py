#!/usr/bin/env python3
"""[B300-004] Evaluate Base vs Fine-Tuned Model, Merge LoRA, and Export GGUF (Q4_K_M, Q8_0)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def evaluate_model(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    eval_records: list[dict[str, Any]],
    max_new_tokens: int = 768,
) -> dict[str, Any]:
    model.eval()
    json_valid = 0
    severity_match = 0
    fp_total = 0
    fp_correct = 0

    for rec in eval_records:
        messages = rec["messages"]
        prompt_msgs = messages[:2]
        expected_match = JSON_BLOCK_RE.search(messages[2]["content"])
        expected_json = json.loads(expected_match.group(1)) if expected_match else {}

        text = tokenizer.apply_chat_template(prompt_msgs, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        gen_text = tokenizer.decode(out_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        m = JSON_BLOCK_RE.search(gen_text)
        if m:
            try:
                pred = json.loads(m.group(1))
                json_valid += 1
                if pred.get("severity") == expected_json.get("severity"):
                    severity_match += 1
                if expected_json.get("is_vulnerable") is False:
                    fp_total += 1
                    if pred.get("is_vulnerable") is False:
                        fp_correct += 1
            except json.JSONDecodeError:
                pass

    n = max(1, len(eval_records))
    return {
        "total": len(eval_records),
        "json_valid_rate": round(json_valid / n, 4),
        "severity_accuracy": round(severity_match / n, 4),
        "false_positive_rejection_rate": round(fp_correct / max(1, fp_total), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate, merge LoRA, and export GGUF.")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-Coder-14B-Instruct")
    parser.add_argument("--lora-dir", type=Path, default=Path("outputs/b300-lora"))
    parser.add_argument("--eval-file", type=Path, default=Path("data/eval_benchmark.jsonl"))
    parser.add_argument("--merged-dir", type=Path, default=Path("outputs/merged-safetensors"))
    parser.add_argument("--gguf-dir", type=Path, default=Path("outputs/gguf"))
    parser.add_argument("--llama-cpp-dir", type=Path, default=Path("/opt/llama.cpp"))
    parser.add_argument("--skip-base-eval", action="store_true")
    args = parser.parse_args()

    eval_records = [json.loads(line) for line in args.eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)

    report: dict[str, Any] = {}
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    if not args.skip_base_eval:
        report["base"] = evaluate_model(base_model, tokenizer, eval_records)

    peft_model = PeftModel.from_pretrained(base_model, str(args.lora_dir))
    merged_model = peft_model.merge_and_unload()
    report["finetuned"] = evaluate_model(merged_model, tokenizer, eval_records)

    args.merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(args.merged_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(args.merged_dir))

    report_path = args.merged_dir / "eval_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved eval report -> {report_path}")
    print(json.dumps(report, indent=2))

    args.gguf_dir.mkdir(parents=True, exist_ok=True)
    f16_gguf = args.gguf_dir / "auditor-14b-f16.gguf"
    convert_script = args.llama_cpp_dir / "convert_hf_to_gguf.py"
    quantize_bin = args.llama_cpp_dir / "build" / "bin" / "llama-quantize"

    subprocess.run(
        ["python3", str(convert_script), str(args.merged_dir), "--outfile", str(f16_gguf), "--outtype", "bf16"],
        check=True,
    )
    for quant in ("Q4_K_M", "Q8_0"):
        out_gguf = args.gguf_dir / f"auditor-14b-{quant}.gguf"
        subprocess.run([str(quantize_bin), str(f16_gguf), str(out_gguf), quant], check=True)
        print(f"Exported GGUF -> {out_gguf}")


if __name__ == "__main__":
    main()

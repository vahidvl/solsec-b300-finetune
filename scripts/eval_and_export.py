#!/usr/bin/env python3
"""[B300-004 / B300-HARDEN-001] Export GGUF First, Then Evaluate Base vs Fine-Tuned."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
    AutoTokenizer,
)

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def load_model_dynamic(model_id: str):
    cfg = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
    archs = cfg.architectures or []
    model_type = getattr(cfg, "model_type", "") or ""
    is_vlm = any("ConditionalGeneration" in a for a in archs) or model_type.startswith(
        ("qwen3_5", "qwen3_vl", "qwen2_vl")
    )
    loader = AutoModelForImageTextToText if is_vlm else AutoModelForCausalLM
    return loader.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )


def format_prompt(tokenizer: AutoTokenizer, prompt_msgs: list[dict[str, str]]) -> str:
    try:
        return tokenizer.apply_chat_template(
            prompt_msgs,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            prompt_msgs,
            tokenize=False,
            add_generation_prompt=True,
        )


def evaluate_model(
    model: Any,
    tokenizer: AutoTokenizer,
    eval_records: list[dict[str, Any]],
    max_new_tokens: int = 512,
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

        text = format_prompt(tokenizer, prompt_msgs)
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
    parser = argparse.ArgumentParser(description="Merge LoRA, export GGUF, then evaluate.")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen3.8-27B")
    parser.add_argument("--lora-dir", type=Path, default=Path("outputs/b300-lora"))
    parser.add_argument("--eval-file", type=Path, default=Path("data/eval_benchmark.jsonl"))
    parser.add_argument("--merged-dir", type=Path, default=Path("outputs/merged-safetensors"))
    parser.add_argument("--gguf-dir", type=Path, default=Path("outputs/gguf"))
    parser.add_argument("--llama-cpp-dir", type=Path, default=Path.home() / "llama.cpp")
    parser.add_argument("--eval-limit", type=int, default=25)
    parser.add_argument("--skip-base-eval", action="store_true")
    parser.add_argument("--model-prefix", type=str, default="solsec-qwen3.8-27b")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    base_model = load_model_dynamic(args.base_model)

    # 1. EXPORT FIRST: Merge LoRA -> safetensors -> GGUF (Q4_K_M, Q8_0)
    peft_model = PeftModel.from_pretrained(base_model, str(args.lora_dir))
    merged_model = peft_model.merge_and_unload()

    args.merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(args.merged_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(args.merged_dir))
    print(f"Saved merged safetensors -> {args.merged_dir}")

    args.gguf_dir.mkdir(parents=True, exist_ok=True)
    bf16_gguf = args.gguf_dir / f"{args.model_prefix}-bf16.gguf"
    convert_script = args.llama_cpp_dir / "convert_hf_to_gguf.py"
    quantize_bin = args.llama_cpp_dir / "build" / "bin" / "llama-quantize"

    subprocess.run(
        ["python3", str(convert_script), str(args.merged_dir), "--outfile", str(bf16_gguf), "--outtype", "bf16"],
        check=True,
    )
    for quant in ("Q4_K_M", "Q8_0"):
        out_gguf = args.gguf_dir / f"{args.model_prefix}-{quant}.gguf"
        subprocess.run([str(quantize_bin), str(bf16_gguf), str(out_gguf), quant], check=True)
        print(f"Exported GGUF -> {out_gguf}")

    if bf16_gguf.exists():
        bf16_gguf.unlink()
        print(f"Deleted intermediate {bf16_gguf.name} to free ~54GB disk.")

    # 2. EVAL SECOND: Fast eval on held-out subset
    eval_records = [
        json.loads(line)
        for line in args.eval_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ][: args.eval_limit]

    report: dict[str, Any] = {"finetuned": evaluate_model(merged_model, tokenizer, eval_records)}
    if not args.skip_base_eval:
        del merged_model, peft_model
        torch.cuda.empty_cache()
        fresh_base = load_model_dynamic(args.base_model)
        report["base"] = evaluate_model(fresh_base, tokenizer, eval_records)

    report_path = args.gguf_dir / f"{args.model_prefix}_eval_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved eval report -> {report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

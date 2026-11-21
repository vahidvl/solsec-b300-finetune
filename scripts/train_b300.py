#!/usr/bin/env python3
"""[B300-004 / B300-HARDEN-001] Multi-GPU BF16 LoRA Fine-Tuning on 8x NVIDIA B300.

Launch with:
    accelerate launch --num_processes=8 --mixed_precision=bf16 scripts/train_b300.py
"""

from __future__ import annotations

import argparse
import inspect
from pathlib import Path

import torch
import torch.nn as nn
from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
    AutoTokenizer,
)
from trl import SFTConfig, SFTTrainer

CANDIDATE_LORA_MODULES = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
    "in_proj_qkv",
    "in_proj_z",
    "out_proj",
)


def load_model_dynamic(model_id: str) -> nn.Module:
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
        attn_implementation="sdpa",
        trust_remote_code=True,
    )


def find_language_lora_targets(model: nn.Module) -> list[str]:
    found: set[str] = set()
    for name, module in model.named_modules():
        if "visual" in name or "vision" in name:
            continue
        if isinstance(module, nn.Linear):
            leaf = name.rsplit(".", 1)[-1]
            if leaf in CANDIDATE_LORA_MODULES:
                found.add(leaf)
    return sorted(found) if found else ["q_proj", "k_proj", "v_proj", "o_proj"]


def format_chat_text(tokenizer: AutoTokenizer, messages: list[dict[str, str]]) -> str:
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Qwen3.8-27B on 8x B300.")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen3.8-27B")
    parser.add_argument("--train-file", type=Path, default=Path("data/train.jsonl"))
    parser.add_argument("--eval-file", type=Path, default=Path("data/eval_benchmark.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/b300-lora"))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1.5e-4)
    parser.add_argument("--max-seq-len", type=int, default=3072)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = load_model_dynamic(args.model_id)
    model.config.use_cache = False
    if hasattr(model.config, "text_config"):
        model.config.text_config.use_cache = False

    for name, param in model.named_parameters():
        if "visual" in name or "vision" in name:
            param.requires_grad = False

    target_modules = find_language_lora_targets(model)
    lora_kwargs: dict[str, object] = {
        "task_type": TaskType.CAUSAL_LM,
        "r": 64,
        "lora_alpha": 128,
        "lora_dropout": 0.05,
        "target_modules": target_modules,
    }
    if "exclude_modules" in inspect.signature(LoraConfig.__init__).parameters:
        lora_kwargs["exclude_modules"] = ["visual", "vision"]
    lora_config = LoraConfig(**lora_kwargs)

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train_file), "eval": str(args.eval_file)},
    )
    dataset = dataset.map(
        lambda ex: {"text": format_chat_text(tokenizer, ex["messages"])},
        remove_columns=dataset["train"].column_names,
    )

    sft_params = inspect.signature(SFTConfig.__init__).parameters
    sft_kwargs: dict[str, object] = {
        "output_dir": str(args.output_dir),
        "num_train_epochs": args.epochs,
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "learning_rate": args.lr,
        "lr_scheduler_type": "cosine",
        "bf16": True,
        "logging_steps": 5,
        "eval_strategy": "epoch",
        "save_strategy": "epoch",
        "gradient_checkpointing": True,
        "gradient_checkpointing_kwargs": {"use_reentrant": False},
        "ddp_find_unused_parameters": False,
        "report_to": "none",
    }
    if "dataset_text_field" in sft_params:
        sft_kwargs["dataset_text_field"] = "text"
    if "max_length" in sft_params:
        sft_kwargs["max_length"] = args.max_seq_len
    elif "max_seq_length" in sft_params:
        sft_kwargs["max_seq_length"] = args.max_seq_len
    if "warmup_ratio" in sft_params:
        sft_kwargs["warmup_ratio"] = 0.05

    sft_config = SFTConfig(**sft_kwargs)

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        processing_class=tokenizer,
        peft_config=lora_config,
    )

    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    print(f"Saved LoRA adapter & tokenizer to {args.output_dir}")


if __name__ == "__main__":
    main()

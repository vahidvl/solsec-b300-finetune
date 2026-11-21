#!/usr/bin/env python3
"""[B300-004] Multi-GPU BF16 LoRA Fine-Tuning on 8x NVIDIA B300 (288GB).

Launch with:
    accelerate launch --num_processes=8 scripts/train_b300.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Qwen2.5-Coder-14B-Instruct on 8x B300.")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen2.5-Coder-14B-Instruct")
    parser.add_argument("--train-file", type=Path, default=Path("data/train.jsonl"))
    parser.add_argument("--eval-file", type=Path, default=Path("data/eval_benchmark.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/b300-lora"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1.5e-4)
    parser.add_argument("--max-seq-len", type=int, default=4096)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=64,
        lora_alpha=128,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train_file), "eval": str(args.eval_file)},
    )

    sft_config = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=True,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        gradient_checkpointing=True,
        max_seq_length=args.max_seq_len,
        report_to="none",
    )

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

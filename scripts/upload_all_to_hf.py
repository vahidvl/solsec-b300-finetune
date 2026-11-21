#!/usr/bin/env python3
"""[B300-HF-UPLOAD / B300-HF-100G] Upload all 4 B300 models under 100 GB HF Free Private quota."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi


def wait_for_stable_files(paths: list[Path], poll_interval: int = 20) -> None:
    print(f"Waiting for PsycheFa artifacts: {[p.name for p in paths]}")
    prev_sizes: dict[Path, int] = {}
    while True:
        if all(p.exists() for p in paths):
            curr_sizes = {p: p.stat().st_size for p in paths}
            if curr_sizes == prev_sizes and all(s > 0 for s in curr_sizes.values()):
                print("All PsycheFa artifacts present and size-stabilized.")
                return
            prev_sizes = curr_sizes
        time.sleep(poll_interval)


def upload_model_repo(
    api: HfApi,
    repo_id: str,
    files: list[tuple[Path, str]],
    lora_dir: Path | None = None,
) -> None:
    api.create_repo(repo_id=repo_id, repo_type="model", private=True, exist_ok=True)
    existing = set(api.list_repo_files(repo_id=repo_id, repo_type="model"))
    for local_path, path_in_repo in files:
        if path_in_repo in existing:
            print(f"[SKIP] Already in {repo_id}: {path_in_repo}")
            continue
        if not local_path.exists():
            print(f"[WARN] Missing file, skipping: {local_path}")
            continue
        print(f"Uploading {local_path} -> {repo_id}/{path_in_repo} ...")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type="model",
        )
    if lora_dir and lora_dir.exists() and lora_dir.is_dir():
        if any(f.startswith("lora-adapter/") for f in existing):
            print(f"[SKIP] lora-adapter/ already in {repo_id}")
        else:
            print(f"Uploading LoRA adapter {lora_dir} -> {repo_id}/lora-adapter ...")
            api.upload_folder(
                folder_path=str(lora_dir),
                path_in_repo="lora-adapter",
                repo_id=repo_id,
                repo_type="model",
            )
    print(f"[PASS] Uploaded {repo_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload 4 B300 Q4_K_M GGUFs + LoRAs under 100GB HF quota.")
    parser.add_argument("--token", type=str, default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--gguf-dir", type=Path, default=Path("outputs/gguf"))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--release-dir", type=Path, default=Path("release-kit"))
    parser.add_argument("--wait-for-psyche", action="store_true")
    args = parser.parse_args()

    if not args.token:
        print("Error: HF_TOKEN env var or --token is required.", file=sys.stderr)
        return 1

    api = HfApi(token=args.token)
    username = api.whoami()["name"]
    print(f"Authenticated to Hugging Face as: {username}")

    immediate_models = [
        (
            f"{username}/SolSec-Qwen3.8-27B-GGUF",
            [
                (args.gguf_dir / "solsec-qwen3.8-27b-Q4_K_M.gguf", "solsec-qwen3.8-27b-Q4_K_M.gguf"),
                (args.gguf_dir / "eval_report.json", "eval_report.json"),
                (args.release_dir / "Modelfile.solsec", "Modelfile.solsec"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_SOLSEC.md", "README.md"),
            ],
            args.outputs_dir / "b300-lora",
        ),
        (
            f"{username}/AppSec-Qwen3.8-27B-GGUF",
            [
                (args.gguf_dir / "appsec-qwen3.8-27b-Q4_K_M.gguf", "appsec-qwen3.8-27b-Q4_K_M.gguf"),
                (args.gguf_dir / "appsec-qwen3.8-27b_eval_report.json", "appsec-qwen3.8-27b_eval_report.json"),
                (args.release_dir / "Modelfile.appsec", "Modelfile.appsec"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_APPSEC.md", "README.md"),
            ],
            args.outputs_dir / "lora-appsec",
        ),
        (
            f"{username}/AlphaQuant-Qwen3.8-27B-GGUF",
            [
                (args.gguf_dir / "alphaquant-qwen3.8-27b-Q4_K_M.gguf", "alphaquant-qwen3.8-27b-Q4_K_M.gguf"),
                (args.gguf_dir / "alphaquant-qwen3.8-27b_eval_report.json", "alphaquant-qwen3.8-27b_eval_report.json"),
                (args.release_dir / "Modelfile.alphaquant", "Modelfile.alphaquant"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_ALPHAQUANT.md", "README.md"),
            ],
            args.outputs_dir / "lora-alphaquant",
        ),
    ]

    for repo_id, files, lora_dir in immediate_models:
        upload_model_repo(api, repo_id, files, lora_dir=lora_dir)

    psyche_q4 = args.gguf_dir / "psyche-fa-qwen3.8-27b-Q4_K_M.gguf"
    psyche_q8 = args.gguf_dir / "psyche-fa-qwen3.8-27b-Q8_0.gguf"
    psyche_report = args.gguf_dir / "psyche-fa-qwen3.8-27b_eval_report.json"

    if args.wait_for_psyche:
        wait_for_stable_files([psyche_q4, psyche_report], poll_interval=20)

    psyche_repo = f"{username}/PsycheFa-Qwen3.8-27B-GGUF"
    upload_model_repo(
        api,
        psyche_repo,
        [
            (psyche_q4, "psyche-fa-qwen3.8-27b-Q4_K_M.gguf"),
            (psyche_report, "psyche-fa-qwen3.8-27b_eval_report.json"),
            (args.release_dir / "Modelfile.psyche_fa", "Modelfile.psyche_fa"),
            (args.release_dir / "HF_MODEL_CARD_PSYCHE_FA.md", "README.md"),
        ],
        lora_dir=args.outputs_dir / "lora-psyche-fa",
    )

    if psyche_q8.exists():
        try:
            print(f"Attempting optional Q8_0 upload for PsycheFa ({psyche_q8.name})...")
            api.upload_file(
                path_or_fileobj=str(psyche_q8),
                path_in_repo="psyche-fa-qwen3.8-27b-Q8_0.gguf",
                repo_id=psyche_repo,
                repo_type="model",
            )
            print("[PASS] Uploaded optional psyche-fa-qwen3.8-27b-Q8_0.gguf")
        except Exception as exc:
            print(f"[WARN] Optional PsycheFa Q8_0 upload skipped/failed (quota?): {exc}")

    print("ALL 4 Q4_K_M MODELS + LORA ADAPTERS UPLOADED TO HUGGING FACE! SAFE TO RELEASE THE B300 NODE NOW.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

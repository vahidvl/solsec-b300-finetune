#!/usr/bin/env python3
"""[B300-HF-UPLOAD] Upload all 4 B300-trained GGUF models to private Hugging Face repos."""

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
) -> None:
    api.create_repo(repo_id=repo_id, repo_type="model", private=True, exist_ok=True)
    for local_path, path_in_repo in files:
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
    print(f"[PASS] Uploaded {repo_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload 4 B300 GGUF models to private HF repos.")
    parser.add_argument("--token", type=str, default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--gguf-dir", type=Path, default=Path("outputs/gguf"))
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
                (args.gguf_dir / "solsec-qwen3.8-27b-Q8_0.gguf", "solsec-qwen3.8-27b-Q8_0.gguf"),
                (args.gguf_dir / "eval_report.json", "eval_report.json"),
                (args.release_dir / "Modelfile.solsec", "Modelfile.solsec"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_SOLSEC.md", "README.md"),
            ],
        ),
        (
            f"{username}/AppSec-Qwen3.8-27B-GGUF",
            [
                (args.gguf_dir / "appsec-qwen3.8-27b-Q4_K_M.gguf", "appsec-qwen3.8-27b-Q4_K_M.gguf"),
                (args.gguf_dir / "appsec-qwen3.8-27b-Q8_0.gguf", "appsec-qwen3.8-27b-Q8_0.gguf"),
                (args.gguf_dir / "appsec-qwen3.8-27b_eval_report.json", "appsec-qwen3.8-27b_eval_report.json"),
                (args.release_dir / "Modelfile.appsec", "Modelfile.appsec"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_APPSEC.md", "README.md"),
            ],
        ),
        (
            f"{username}/AlphaQuant-Qwen3.8-27B-GGUF",
            [
                (args.gguf_dir / "alphaquant-qwen3.8-27b-Q4_K_M.gguf", "alphaquant-qwen3.8-27b-Q4_K_M.gguf"),
                (args.gguf_dir / "alphaquant-qwen3.8-27b-Q8_0.gguf", "alphaquant-qwen3.8-27b-Q8_0.gguf"),
                (args.gguf_dir / "alphaquant-qwen3.8-27b_eval_report.json", "alphaquant-qwen3.8-27b_eval_report.json"),
                (args.release_dir / "Modelfile.alphaquant", "Modelfile.alphaquant"),
                (args.release_dir / "solsec_cli.py", "solsec_cli.py"),
                (args.release_dir / "HF_MODEL_CARD_ALPHAQUANT.md", "README.md"),
            ],
        ),
    ]

    for repo_id, files in immediate_models:
        upload_model_repo(api, repo_id, files)

    psyche_files_required = [
        args.gguf_dir / "psyche-fa-qwen3.8-27b-Q4_K_M.gguf",
        args.gguf_dir / "psyche-fa-qwen3.8-27b-Q8_0.gguf",
        args.gguf_dir / "psyche-fa-qwen3.8-27b_eval_report.json",
    ]
    if args.wait_for_psyche:
        wait_for_stable_files(psyche_files_required, poll_interval=20)

    upload_model_repo(
        api,
        f"{username}/PsycheFa-Qwen3.8-27B-GGUF",
        [
            (args.gguf_dir / "psyche-fa-qwen3.8-27b-Q4_K_M.gguf", "psyche-fa-qwen3.8-27b-Q4_K_M.gguf"),
            (args.gguf_dir / "psyche-fa-qwen3.8-27b-Q8_0.gguf", "psyche-fa-qwen3.8-27b-Q8_0.gguf"),
            (args.gguf_dir / "psyche-fa-qwen3.8-27b_eval_report.json", "psyche-fa-qwen3.8-27b_eval_report.json"),
            (args.release_dir / "Modelfile.psyche_fa", "Modelfile.psyche_fa"),
            (args.release_dir / "HF_MODEL_CARD_PSYCHE_FA.md", "README.md"),
        ],
    )

    print("ALL 4 MODELS (8 GGUFs) UPLOADED TO HUGGING FACE! SAFE TO RELEASE THE B300 NODE NOW.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

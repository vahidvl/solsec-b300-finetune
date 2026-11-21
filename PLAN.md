# Project 02: 8× NVIDIA B300 Fine-Tuned Model Asset — Global USD/USDC Edition (`[B300-001..010]`)

> **Master Schedule:** Synchronized with Project 01 in [MASTER_TIMELINE.md](file:///F:/Develop/NationalCompute-Monetization/MASTER_TIMELINE.md) (`Nov 21–24` prep → `Nov 25` `8× B300` run → `Nov 26–28` SolSec launch & Project 01 audit).

> **Goal:** Convert the expiring **`$100.00` National Compute Promo Credits** (expires **2026-11-28**) + **`$25/week` Marshall inference** into a high-ticket, global USD/USDC-sellable AI model asset before the credits vanish.
> **Target Product:** **Local Smart-Contract Security & Vulnerability Auditor (`14B` or `32B`)** — specialized in **Solana (Rust / Anchor)** & **EVM (Solidity)** audits, PoC exploit-test generation, and patch synthesis; fine-tuned on `8× NVIDIA B300 (2.3 TB VRAM)` and exported to `GGUF (Q4_K_M / Q8_0)` + merged `safetensors` for Ollama / LM Studio / vLLM.

---

## 1. Why This Niche Has Maximum Global USD Demand (and Zero Crypto/KYC Friction)
1. **Strict Privacy Requirement (Why Local GGUF Beats Cloud APIs):** Pre-launch DeFi protocols, Web3 audit firms, and bug bounty hunters **cannot upload unreleased smart-contract code** to OpenAI/Anthropic cloud APIs due to IP/exploit-leakage risk. They actively pay for **offline, local** auditing models.
2. **Highest Willingness to Pay in USD:** A single missed vulnerability costs protocols `$100k–$10M+`, and bug bounty hunters earn `$1k–$100k+` per finding. Charging `$49–$199` for a commercial GGUF/vLLM model pack (or `$500+` for team/API access) is trivial for this audience.
3. **Native Crypto Payments (`USDC / USDT / ETH / SOL`):** Web3 auditors, bounty hunters, and DeFi teams natively pay in **USDC/USDT**—meaning **zero Stripe/PayPal/Western bank or KYC friction**.
4. **Synergy with Project 01:** You can immediately use this same model to audit your own Solana code in Project 01 (`01-Superteam-Solana-Bounty`) and future Web3 bounties.

---

## 2. Compute Budget & Safety Rules
| Resource | Available | Rate | Usage Plan |
| :--- | :--- | :--- | :--- |
| **Marshall Inference (Pro)** | `$25.00 / week` | Included | Synthesize & structure `10k–20k` vulnerability → root-cause → PoC-test → patched-code training pairs from public audit reports (`$0` from GPU pool). |
| **National Compute Promo Credits** | `$100.00` (Expires **2026-11-28**) | **8× NVIDIA B300:** `$32.00/hr` (`$4/GPU-hr`)<br>**8× AMD MI355X:** `$24.00/hr` (`$3/GPU-hr`) | **~3.1 hours** on `8× B300` (or **~4.1 hours** on `8× MI355X`). Reserve **2h** for training + **45m** for eval & GGUF export. |

### Strict Operating Invariants
- **Zero Idle GPU Burn:** Write and syntax-test **100% of training, eval, and export scripts locally** before requesting the `public_research` node in Marshall (`$0.53/minute` on `8× B300`).
- **Immediate `scp` & Release:** Node NVMe is wiped on release. Copy final merged weights, `GGUF` files, and eval logs to your Marshall workspace / local machine **before** releasing the node.
- **Tier 2 Data Sharing:** Because `.edu` Public Research accounts use Tier 2 artifact sharing, train **only on open-source base models and public audit datasets** (e.g., public Code4rena / Sherlock / Solodit-style reports and synthetic variations—never private client code).

---

## 3. Task Breakdown (`[B300-001]` – `[B300-010]`)

| Task UID | Title | Owner | Target Date | Compute Cost | Done Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[B300-001]` | **Lock Base Model & Audit Output Schema** | Agent + Human | Day 1 (`Nov 21`) | `$0` | Base model (`Qwen2.5-Coder-14B/32B-Instruct` or `Qwen3-Coder`) + structured audit report/PoC JSON+Markdown schema locked. |
| `[B300-002]` | **Public Audit Corpus & Synthetic CoT Generation** | Agent | Days 1–2 (`Nov 21–22`) | Marshall (`$25/wk` free) | `10,000–20,000` high-signal Solidity + Rust/Anchor vulnerability, false-positive rejection, PoC test, and fix pairs generated. |
| `[B300-003]` | **Dataset Validation, Deduplication & Eval Benchmark** | Agent | Day 3 (`Nov 23`) | `$0` | Compiler/syntax-checked samples; `300–500` held-out real historical vulnerability benchmark created. |
| `[B300-004]` | **Training & GGUF Export Scripts** | Agent | Day 4 (`Nov 24`) | `$0` | `TRL`/`Axolotl` multi-GPU (`8× B300`) script + `llama.cpp` GGUF quantization script tested locally. |
| `[B300-005]` | **Marshall Workspace Staging & Pre-Flight** | Human + Agent | Day 5 (`Nov 25`) | `$0` | Dataset + scripts uploaded to Marshall workspace; base model Hugging Face pull command verified. |
| `[B300-006]` | **Lease `8× B300` & Run Fine-Tuning** | Human (Marshall) + Agent | Day 5 (`Nov 25`) | `~$55–$65` (~1.8–2.0h) | Fine-tuning completes on `8× NVIDIA B300`; loss curve & checkpoints verified. |
| `[B300-007]` | **Automated Eval + Merge + GGUF Quantization** | Human (Marshall) + Agent | Day 5 (`Nov 25`) | `~$20–$25` (~40m) | Fine-tuned model beats base model on vulnerability detection & PoC precision; `Q4_K_M` & `Q8_0` GGUFs built. |
| `[B300-008]` | **Artifact Extraction (`scp`) & Node Release** | Human | Day 5 (`Nov 25`) | `$0` | All GGUFs, merged weights/LoRA, and benchmark report copied off node; node **released immediately**. |
| `[B300-009]` | **Packaging, Benchmark Report & Ollama/vLLM Kit** | Agent | Day 6 (`Nov 26`) | `$0` (or remaining `~$10` if extra eval needed) | `Modelfile`, `vLLM` launch script, before/after vulnerability detection benchmark chart, and commercial license ready. |
| `[B300-010]` | **Global Crypto-Native Launch** | Human + Agent | Day 7 (`Nov 27`) | `$0` | Free `7B/quantized` teaser on Hugging Face + paid `14B/32B` Pro GGUF + CLI audit runner sold globally for **USDC/USDT** (e.g., via crypto checkout / direct wallet). |

---

## 4. Strict 7-Day Timeline (`2026-11-21` → `2026-11-27`, 24h Buffer Before Nov 28 Expiry)

```text
Nov 21 (Day 1): [B300-001] Spec lock + start [B300-002] public audit & synthetic CoT dataset (Marshall)
Nov 22 (Day 2): Finish [B300-002] dataset generation
Nov 23 (Day 3): [B300-003] Dedup, syntax validation & held-out vulnerability benchmark
Nov 24 (Day 4): [B300-004] Write & locally dry-run training + GGUF export scripts
Nov 25 (Day 5): [B300-005] Stage in Marshall → [B300-006] 8× B300 train → [B300-007] eval & GGUF → [B300-008] scp & RELEASE
Nov 26 (Day 6): [B300-009] Package Ollama/vLLM kit + publishable benchmark comparison
Nov 27 (Day 7): [B300-010] Launch Hugging Face teaser + USDC/USDT commercial release (1 full day before Nov 28 expiry)
```

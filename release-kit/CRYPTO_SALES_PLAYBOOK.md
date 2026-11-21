# Zero-KYC Crypto Sales Playbook (SolSec / AppSec / AlphaQuant 27B)

## 1. Zero-KYC Crypto Checkout Setup

- **Helio Pay (Solana USDC/SOL):** Create a Helio Pay link ($149 Single-Model / $349 3-Model Bundle) with webhook -> automated Hugging Face private repo invite or S3 presigned URL. Zero KYC, instant settlement.
- **NOWPayments (BTC/ETH/USDT/XMR):** Enable non-custodial payout to your cold wallet; zero KYC for crypto-to-crypto.
- **Direct USDC Wallet:** Accept USDC on Solana/Base/Arbitrum; verify tx signature via RPC and issue download token.

## 2. Launch Copy

### `r/LocalLLaMA`
> **Released: 3x Specialized Qwen3.8-27B GGUFs (SolSec, AppSec, AlphaQuant) — 100% Local, Zero-Cloud**
> Fine-tuned on 8x B300s in BF16 LoRA, quantized to `Q4_K_M` & `Q8_0`. Includes zero-dependency Python CLI (`solsec_cli.py`) + Ollama `Modelfile`s with structured JSON output and `--fail-on-high` CI gating.

### `r/solana` & `r/ethdev`
> **Air-Gapped Smart-Contract Auditor (`SolSec-Qwen3.8-27B`)**
> Audit Anchor/Rust and Solidity contracts locally before paying $50k+ for an external audit. Outputs structured JSON + PoC + recommended patch.

### `r/algotrading`
> **Local Quant Strategy & Risk Engine (`AlphaQuant-Qwen3.8-27B`)**
> Generates Freqtrade `IStrategy`, PineScript v5/v6, `vectorbt` backtests, and VaR/CVaR + Kelly sizing modules locally on your own GPU.

### `r/bugbounty`
> **Local Multi-Language SAST Auditor (`AppSec-Qwen3.8-27B`)**
> Scan Python, TS/JS, Go, Rust, C++, Java, PHP, and SQL offline with structured CWE/severity JSON reports.

### X (Twitter)
> Shipped 3x local 27B GGUFs (`SolSec`, `AppSec`, `AlphaQuant`) trained on 8x B300s. Zero cloud, zero telemetry, Ollama-ready + CI `--fail-on-high` CLI. Pay with USDC/SOL.

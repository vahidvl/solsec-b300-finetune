---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
language:
  - en
tags:
  - quantitative-finance
  - algorithmic-trading
  - freqtrade
  - pinescript
  - risk-management
  - gguf
  - local-llm
---

![AlphaQuant-Qwen3.8-27B Enterprise Banner](./assets/banner-alphaquant.png)

# AlphaQuant-Qwen3.8-27B-GGUF

> **Institutional Quantitative Strategy & Risk Engineering Model** — Fine-tuned on **8x NVIDIA B300** GPUs from `Qwen/Qwen3.8-27B` for **Freqtrade (`IStrategy`)**, **PineScript v5/v6**, **`vectorbt`**, statistical arbitrage, and tail-risk sizing.

| Channel | Link | Purpose |
| :--- | :--- | :--- |
| **24/7 Automated Store** | [**@backerv_bot**](https://t.me/backerv_bot) | Instant Zero-KYC Purchase & Signed GGUF Delivery |
| **Direct Engineering Support** | [**t.me/Vahvldi**](https://t.me/Vahvldi) | Enterprise Licensing, Custom Fine-Tuning & BEP-20 / TRC-20 Unlock |
| **GitHub Repository** | [**vahidvl/solsec-b300-finetune**](https://github.com/vahidvl/solsec-b300-finetune) | `solsec_cli.py`, Modelfiles, Eval Harness & Benchmarks |
| **Model Hub** | [**huggingface.co/backerv**](https://huggingface.co/backerv) | Full 27B Specialist Suite |

---

## Core Quantitative Capabilities

- **Strategy Synthesis:** Production-ready `Freqtrade` `IStrategy` classes, `PineScript v5/v6` indicators, and vectorized `vectorbt` backtest pipelines.
- **Market Microstructure:** Order-book imbalance, slippage modeling, funding-rate arbitrage, and cointegration pairs trading.
- **Institutional Risk Engines:** Fractional Kelly sizing, Historical/Parametric VaR & CVaR, drawdown circuit breakers, and lookahead-bias auditing.
- **Private Local Execution:** Keep proprietary alpha 100% air-gapped on your own hardware (`Q4_K_M`, `16.7 GB`).

---

## 8x B300 Fine-Tuning Pipeline Benchmark (`SolSec` Sibling Eval)

Trained with the same `8x NVIDIA B300` deterministic structured-output pipeline:

![8x B300 Pipeline Benchmark](./assets/chart-solsec-benchmark.png)

| Specification | Value |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen3.8-27B` (Dense 27B) |
| **Training Hardware** | `8x NVIDIA B300` (Blackwell) |
| **Dataset Corpus** | `1,200` train / `150` eval quantitative strategy & risk specs |
| **Quantization** | `Q4_K_M` (`16.7 GB` GGUF) |

---

## Quant Research & Risk Pipeline

```mermaid
flowchart LR
    A["Market Hypothesis & Constraints"] --> B["AlphaQuant-Qwen3.8-27B (Air-Gapped)"]
    B --> C["Freqtrade / PineScript / vectorbt Code"]
    C --> D["Lookahead & Leakage Audit"]
    D --> E["Kelly / VaR Risk Parameters"]
```

---

## Quickstart (Ollama & `llama.cpp`)

```bash
ollama create alphaquant-qwen3.8-27b -f Modelfile.alphaquant
python solsec_cli.py --mode alphaquant --prompt "Build a 15m EMA+RSI Freqtrade IStrategy with ATR trailing stop"
```

```bash
./llama-server -m alphaquant-qwen3.8-27b-Q4_K_M.gguf -c 32768 -ngl 99 --port 8080
```

---

## Instant Purchase & Visual Checkout Guide (Zero KYC)

![4-Step Visual Checkout Guide](./assets/guide-checkout-flow.png)

| Model / Package | Coverage | Price | Checkout |
| :--- | :--- | :---: | :--- |
| **AlphaQuant-Qwen3.8-27B** | Quant Strategy & Risk Engine + `solsec_cli.py` | **$49** | [**Buy via @backerv_bot**](https://t.me/backerv_bot) |
| **Full Enterprise Bundle** | All 4 Private Pro Models (`SolSec` + `AppSec` + `AlphaQuant` + `PsycheFa`) | **$119** | [**Buy Bundle via @backerv_bot**](https://t.me/backerv_bot) |

### Supported Non-Custodial Payment Networks
- **Solana USDC (Instant Auto-Verify in ~5s):** `9JQ8EBuPk4qDN92dy6WCtrivemjw8w9FHTp6jubwPHuK`
- **BNB Smart Chain (BEP-20):** `0xf74BfB2234150CdCf7eAa35AEF1b6a2e95E650b0`
- **Tron (TRC-20):** `TURHs9J1eXHzCRm7zGUvMyehT7G7GppD87`

For BEP-20 / TRC-20 verification or custom quant fine-tuning, message [**https://t.me/Vahvldi**](https://t.me/Vahvldi) directly.

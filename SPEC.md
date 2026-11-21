# [B300-001] Model & Audit Output Specification

**Project:** Local Smart-Contract Security & Vulnerability Auditor (`02-B300-Finetune-Asset`)  
**Status:** Locked (`2026-11-21`)

---

## 1. Base Model & Target Artifacts

| Parameter | Locked Value |
| :--- | :--- |
| **Base Model** | `Qwen/Qwen2.5-Coder-14B-Instruct` |
| **Fine-Tuning Method** | Multi-GPU BF16 LoRA (`r=64`, `lora_alpha=128`, `lora_dropout=0.05`) via TRL `SFTTrainer` + Accelerate |
| **Compute Target** | `8× NVIDIA B300` (288 GB VRAM/GPU, 2.3 TB total VRAM) |
| **Merged Weights** | `safetensors` (BF16, sharded) |
| **Target GGUF Quantizations** | `Q4_K_M` (primary local/Ollama distribution) & `Q8_0` (high-precision audit tier) |
| **Supported Runtimes** | Ollama, LM Studio, llama.cpp, vLLM |

---

## 2. Strict JSON + Markdown Audit Output Schema

Every assistant response in training, evaluation, and inference MUST follow a two-part structure:
1. A fenced `json` code block containing the machine-parseable audit finding.
2. A concise Markdown summary (for human auditors).

### JSON Schema

```json
{
  "chain": "solana_anchor | evm_solidity",
  "is_vulnerable": true,
  "severity": "Critical | High | Medium | Low | Informational | None",
  "title": "Short descriptive title of the finding or safe pattern",
  "root_cause": "Technical explanation of why the code is vulnerable or why a flagged pattern is a false positive",
  "vulnerable_snippet": "Exact minimal code snippet exhibiting the issue (or 'N/A' for safe code)",
  "poc_exploit": "Deterministic PoC test outline / verification steps (or 'N/A' for safe code)",
  "recommended_patch": "Minimal unified diff or patched code snippet (or 'N/A' for safe code)",
  "confidence": 0.95
}
```

### Field Constraints
- `severity`: Must be one of `Critical`, `High`, `Medium`, `Low`, `Informational`, `None`.
  - When `is_vulnerable` is `false` (false-positive rejection), `severity` MUST be `"None"`.
- `title`: Non-empty string (max 140 chars).
- `root_cause`: Non-empty technical explanation.
- `vulnerable_snippet`: Non-empty string (`"N/A"` if `is_vulnerable` is `false`).
- `poc_exploit`: Non-empty string (`"N/A"` if `is_vulnerable` is `false`).
- `recommended_patch`: Non-empty string (`"N/A"` if `is_vulnerable` is `false`).
- `confidence`: Float in `[0.0, 1.0]`.

---

## 3. Target Vulnerability & False-Positive Coverage

### Solana (Rust / Anchor)
1. **Missing Signer Check:** Account passed as `AccountInfo` without `Signer<'info>` or `is_signer` verification.
2. **PDA Seed Collision / Missing Canonical Bump:** Unchecked bump or non-unique seeds allowing account substitution.
3. **Integer Overflow / Underflow:** Unchecked arithmetic (`+`, `-`, `*`) instead of `checked_add` / `checked_sub` / `checked_mul`.
4. **Arbitrary CPI / Unvalidated Program ID:** `invoke` / `CpiContext` using an unvalidated `AccountInfo` program account.
5. **False-Positive Rejection:** Properly constrained `Signer<'info>`, `has_one`, `seeds = [...], bump`, and `checked_*` math.

### EVM (Solidity)
1. **Reentrancy (CEI Violation):** External `.call{value: ...}` before state update.
2. **Missing Access Control:** Privileged state-mutating function missing `onlyOwner` / role check or using `tx.origin`.
3. **Oracle Manipulation:** Using spot AMM reserves (`getReserves()`) instead of TWAP / Chainlink with staleness checks.
4. **Precision / Rounding Loss:** Division before multiplication causing truncation to zero.
5. **False-Positive Rejection:** Proper `ReentrancyGuard` (`nonReentrant`) + CEI ordering, `onlyOwner`, and `mulDiv` / safe math.

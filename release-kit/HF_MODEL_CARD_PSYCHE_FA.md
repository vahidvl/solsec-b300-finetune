---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
language:
  - fa
  - en
tags:
  - psychology
  - psychiatry
  - persian
  - dsm-5-tr
  - icd-11
  - hitop
  - gguf
---

# PsycheFa-Qwen3.8-27B-GGUF

Persian Clinical Psychology, Psychiatry, Psychotherapy & Psychometric Supervisor fine-tuned on `Qwen/Qwen3.8-27B` with 2024–2026 peer-reviewed EuropePMC evidence.

## Coverage

- **Nosology:** DSM-III / DSM-IV-TR / DSM-5 / DSM-5-TR (AMPD), ICD-11, HiTOP & RDoC.
- **Psychotherapy Protocols:** CBT, Schema Therapy (18 schemas, 3 coping styles, modes), ACT (Hexaflex), DBT (TIPP, DEAR MAN), ISTDP (Davanloo triangles & anxiety discharge pathways), Process-Based Therapy (PBT).
- **Psychometrics:** MMPI-3 / MMPI-2-RF / MMPI-2, MCMI-IV/III, WAIS-IV / WISC-V, YSQ-S3 / SMI, NEO-PI-R, Rorschach (R-PAS / Exner).
- **2026 Psychopharmacology:** Xanomeline-Trospium (Cobenfy M1/M4), Esketamine, Auvelity, Zuranolone, DORAs (Daridorexant, Lemborexant), GLP-1 metabolic psychiatry, CPIC 2025–2026 (`CYP2D6`, `CYP2C19`, `HLA-B*15:02`).

## Quickstart (Ollama)

```bash
ollama create psyche-fa-qwen3.8-27b -f Modelfile.psyche_fa
ollama run psyche-fa-qwen3.8-27b
```

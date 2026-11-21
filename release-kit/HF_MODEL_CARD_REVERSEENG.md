---
license: apache-2.0
base_model: Qwen/Qwen3.8-27B
tags:
  - reverse-engineering
  - decompilation
  - ghidra
  - ida-pro
  - x86_64
  - arm64
  - gguf
---

# ReverseEng-Qwen3.8-27B-GGUF

Local Binary Reverse Engineering & Decompilation specialist fine-tuned on `Qwen/Qwen3.8-27B`.

## Capabilities

- `x86_64` and `ARM64` assembly -> clean annotated C / Rust decompilation
- Ghidra / IDA Pro pseudocode cleanup, struct/type recovery, and variable/function renaming
- ELF/PE binary & firmware static analysis (crypto routines, anti-debug/anti-VM, buffer/integer overflows, custom protocol parsers)

## Quickstart (Ollama)

```bash
ollama create reverseeng-qwen3.8-27b -f Modelfile.reverseeng
ollama run reverseeng-qwen3.8-27b
```

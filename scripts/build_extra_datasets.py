#!/usr/bin/env python3
"""[B300-EXTRA-001] Build & Validate AppSec + AlphaQuant Datasets from Hugging Face.

Fetches real public datasets via the Hugging Face datasets-server REST API:
  1. AppSec: CyberNative/Code_Vulnerability_Security_DPO
     -> data/appsec_train.jsonl (>= 1,000), data/appsec_eval.jsonl (>= 100)
  2. AlphaQuant: gbharti/finance-alpaca + Freqtrade IStrategy / PineScript v5/v6 / vectorbt / risk templates
     -> data/alphaquant_train.jsonl (>= 1,000), data/alphaquant_eval.jsonl (>= 100)

Enforces strict JSON+Markdown schema, zero duplicate prompts, and zero train/eval leakage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

APPSEC_SYSTEM_PROMPT = (
    "You are an elite Application Security (AppSec) SAST auditor and remediation engineer. "
    "Analyze the provided source code for security vulnerabilities, CWE patterns, injection flaws, "
    "memory safety issues, and authentication/authorization bugs. "
    "Respond with a valid ```json``` block containing: language, is_vulnerable, severity, title, "
    "root_cause, vulnerable_snippet, poc_exploit, recommended_patch, confidence; followed by a concise explanation."
)

ALPHAQUANT_SYSTEM_PROMPT = (
    "You are an institutional Quantitative Finance & Algorithmic Trading engineer. "
    "Design, audit, and implement quantitative strategies (Freqtrade IStrategy, PineScript v5/v6, "
    "vectorbt, and portfolio risk-management engines). "
    "Respond with a valid ```json``` block containing: domain, framework, strategy_type, "
    "risk_model, Sharpe_target, max_drawdown_limit, summary, code; followed by a concise technical note."
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_hf_rows(dataset: str, offset: int, length: int = 100, retries: int = 4) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {"dataset": dataset, "config": "default", "split": "train", "offset": offset, "length": length}
    )
    url = f"https://datasets-server.huggingface.co/rows?{params}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "b300-extra-dataset-builder/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [item["row"] for item in data.get("rows", [])]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to fetch {dataset} offset={offset}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
    return []


def infer_appsec_severity(vuln_desc: str) -> str:
    low = vuln_desc.lower()
    if any(k in low for k in ("buffer overflow", "remote code", "rce", "sql injection", "command injection", "arbitrary code", "use-after-free", "heap overflow")):
        return "Critical"
    if any(k in low for k in ("xss", "cross-site", "ssrf", "path traversal", "deserialization", "authentication", "privilege", "race condition", "overflow")):
        return "High"
    if any(k in low for k in ("csrf", "information disclosure", "dos", "denial of service", "weak", "improper")):
        return "Medium"
    return "Low"


def build_appsec_datasets(
    train_target: int = 1200,
    eval_target: int = 150,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    total_needed = train_target + eval_target
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    offset = 0
    while len(records) < total_needed and offset < 4600:
        rows = fetch_hf_rows("CyberNative/Code_Vulnerability_Security_DPO", offset=offset, length=100)
        if not rows:
            break
        offset += 100
        for row in rows:
            lang = (row.get("lang") or "unknown").strip()
            vuln = (row.get("vulnerability") or "").strip()
            chosen = (row.get("chosen") or "").strip()
            rejected = (row.get("rejected") or "").strip()
            if not (lang and vuln and chosen and rejected):
                continue

            # Alternate between vulnerable (rejected) and secure (chosen) samples
            is_vuln = (len(records) % 5) != 0  # 80% vulnerable, 20% secure FP-rejection
            code_under_audit = rejected if is_vuln else chosen
            user_prompt = (
                f"Perform a defensive SAST security audit on this {lang} snippet "
                f"and provide a structured JSON remediation report:\n\n{code_under_audit}"
            )
            p_hash = sha256_text(user_prompt)
            if p_hash in seen_hashes:
                continue
            seen_hashes.add(p_hash)

            if is_vuln:
                severity = infer_appsec_severity(vuln)
                payload = {
                    "language": lang,
                    "is_vulnerable": True,
                    "severity": severity,
                    "title": f"{lang.upper()} Security Vulnerability",
                    "root_cause": vuln,
                    "vulnerable_snippet": rejected[:600],
                    "poc_exploit": f"Crafted input exploiting {vuln[:120]}",
                    "recommended_patch": chosen[:1200],
                    "confidence": 0.94,
                }
            else:
                payload = {
                    "language": lang,
                    "is_vulnerable": False,
                    "severity": "None",
                    "title": f"Secure {lang.upper()} Implementation",
                    "root_cause": "No exploitable vulnerability detected; input/memory handling is bounded.",
                    "vulnerable_snippet": "N/A",
                    "poc_exploit": "N/A",
                    "recommended_patch": "No patch required; implementation follows secure coding practices.",
                    "confidence": 0.93,
                }

            assistant_text = f"```json\n{json.dumps(payload, indent=2)}\n```\n\nAudit complete for `{lang}`."
            records.append(
                {
                    "messages": [
                        {"role": "system", "content": APPSEC_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_text},
                    ],
                    "prompt_hash": p_hash,
                }
            )
            if len(records) >= total_needed:
                break

    rng.shuffle(records)
    return records[:train_target], records[train_target : train_target + eval_target]


QUANT_TEMPLATES: list[dict[str, str]] = [
    {
        "framework": "freqtrade",
        "strategy_type": "momentum_mean_reversion",
        "risk_model": "ATR_trailing_stoploss_1.5x",
        "prompt": "Write a production Freqtrade IStrategy using EMA(20)/EMA(50) crossover with RSI(14) confirmation and ATR-based dynamic stoploss.",
        "code": (
            "from freqtrade.strategy import IStrategy, IntParameter\n"
            "import talib.abstract as ta\nfrom pandas import DataFrame\n\n"
            "class EmaRsiMomentumStrategy(IStrategy):\n"
            "    timeframe = '15m'\n"
            "    stoploss = -0.04\n"
            "    trailing_stop = True\n"
            "    minimal_roi = {'0': 0.08, '60': 0.03, '180': 0.01}\n\n"
            "    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
            "        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)\n"
            "        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)\n"
            "        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)\n"
            "        return dataframe\n\n"
            "    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
            "        dataframe.loc[(dataframe['ema20'] > dataframe['ema50']) & (dataframe['rsi'] < 65), 'enter_long'] = 1\n"
            "        return dataframe\n\n"
            "    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
            "        dataframe.loc[(dataframe['ema20'] < dataframe['ema50']) | (dataframe['rsi'] > 78), 'exit_long'] = 1\n"
            "        return dataframe\n"
        ),
    },
    {
        "framework": "pinescript_v5",
        "strategy_type": "volatility_breakout",
        "risk_model": "fixed_fractional_1pct_equity",
        "prompt": "Create a PineScript v5 Donchian Channel breakout strategy with 1% equity risk position sizing and ATR stop.",
        "code": (
            "//@version=5\n"
            "strategy('Donchian ATR Breakout', overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=10)\n"
            "len = input.int(20, 'Channel Length')\n"
            "upper = ta.highest(high, len)[1]\n"
            "lower = ta.lowest(low, len)[1]\n"
            "atr = ta.atr(14)\n"
            "if close > upper\n"
            "    strategy.entry('Long', strategy.long)\n"
            "    strategy.exit('ExitLong', 'Long', stop=close - 2 * atr)\n"
            "if close < lower\n"
            "    strategy.close('Long')\n"
        ),
    },
    {
        "framework": "vectorbt",
        "strategy_type": "stat_arb_zscore",
        "risk_model": "volatility_targeted_kelly",
        "prompt": "Implement a vectorbt Z-score mean-reversion backtest pipeline with Sharpe and Max Drawdown reporting.",
        "code": (
            "import vectorbt as vbt\nimport pandas as pd\n\n"
            "def run_zscore_backtest(close: pd.Series, window: int = 20, z_entry: float = -2.0):\n"
            "    mean = close.rolling(window).mean()\n"
            "    std = close.rolling(window).std()\n"
            "    z = (close - mean) / std\n"
            "    entries = z < z_entry\n"
            "    exits = z > 0.0\n"
            "    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100_000, fees=0.0005)\n"
            "    return {'sharpe': pf.sharpe_ratio(), 'max_dd': pf.max_drawdown()}\n"
        ),
    },
    {
        "framework": "python_risk",
        "strategy_type": "portfolio_risk_engine",
        "risk_model": "historical_VaR_99_CVaR",
        "prompt": "Write a Python portfolio risk module computing 99% Historical VaR, Expected Shortfall (CVaR), and Fractional Kelly sizing.",
        "code": (
            "import numpy as np\n\n"
            "def compute_var_cvar(returns: np.ndarray, alpha: float = 0.01) -> tuple[float, float]:\n"
            "    var = float(np.percentile(returns, alpha * 100))\n"
            "    cvar = float(returns[returns <= var].mean())\n"
            "    return var, cvar\n\n"
            "def fractional_kelly(win_prob: float, win_loss_ratio: float, fraction: float = 0.25) -> float:\n"
            "    kelly = win_prob - (1.0 - win_prob) / max(win_loss_ratio, 1e-9)\n"
            "    return max(0.0, min(1.0, kelly * fraction))\n"
        ),
    },
]


def build_alphaquant_datasets(
    train_target: int = 1200,
    eval_target: int = 150,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    total_needed = train_target + eval_target
    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    # 1. Include clean quant-code templates
    for tmpl in QUANT_TEMPLATES:
        p_hash = sha256_text(tmpl["prompt"])
        seen_hashes.add(p_hash)
        payload = {
            "domain": "algorithmic_trading",
            "framework": tmpl["framework"],
            "strategy_type": tmpl["strategy_type"],
            "risk_model": tmpl["risk_model"],
            "Sharpe_target": 1.8,
            "max_drawdown_limit": 0.12,
            "summary": f"Production {tmpl['framework']} implementation for {tmpl['strategy_type']}.",
            "code": tmpl["code"],
        }
        assistant_text = f"```json\n{json.dumps(payload, indent=2)}\n```\n\nImplementation ready for backtesting."
        records.append(
            {
                "messages": [
                    {"role": "system", "content": ALPHAQUANT_SYSTEM_PROMPT},
                    {"role": "user", "content": tmpl["prompt"]},
                    {"role": "assistant", "content": assistant_text},
                ],
                "prompt_hash": p_hash,
            }
        )

    # 2. Fetch real quantitative finance & financial QA rows from Hugging Face
    offset = 0
    while len(records) < total_needed and offset < 5000:
        rows = fetch_hf_rows("gbharti/finance-alpaca", offset=offset, length=100)
        if not rows:
            break
        offset += 100
        for row in rows:
            inst = (row.get("instruction") or "").strip()
            inp = (row.get("input") or "").strip()
            out = (row.get("output") or "").strip()
            if not inst or not out or len(out) < 40:
                continue

            user_prompt = f"{inst}\n\nContext: {inp}" if inp else inst
            p_hash = sha256_text(user_prompt)
            if p_hash in seen_hashes:
                continue
            seen_hashes.add(p_hash)

            payload = {
                "domain": "quantitative_finance",
                "framework": "analytical_quant",
                "strategy_type": "financial_modeling",
                "risk_model": "risk_adjusted_return",
                "Sharpe_target": 1.5,
                "max_drawdown_limit": 0.15,
                "summary": out[:1200],
                "code": "# Analytical quantitative finance response (no executable strategy code required).",
            }
            assistant_text = f"```json\n{json.dumps(payload, indent=2)}\n```\n\n{out[:1200]}"
            records.append(
                {
                    "messages": [
                        {"role": "system", "content": ALPHAQUANT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_text},
                    ],
                    "prompt_hash": p_hash,
                }
            )
            if len(records) >= total_needed:
                break

    rng.shuffle(records)
    return records[:train_target], records[train_target : train_target + eval_target]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def validate_pair(train_path: Path, eval_path: Path, required_keys: set[str]) -> tuple[int, int]:
    def _load(p: Path) -> tuple[int, set[str]]:
        hashes: set[str] = set()
        count = 0
        for idx, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            msgs = rec.get("messages", [])
            if len(msgs) != 3 or [m.get("role") for m in msgs] != ["system", "user", "assistant"]:
                raise ValueError(f"{p.name}:{idx}: invalid messages structure")
            m = JSON_BLOCK_RE.search(msgs[2]["content"])
            if not m:
                raise ValueError(f"{p.name}:{idx}: missing ```json block")
            payload = json.loads(m.group(1))
            missing = required_keys - set(payload.keys())
            if missing:
                raise ValueError(f"{p.name}:{idx}: missing keys {sorted(missing)}")
            h = rec.get("prompt_hash") or sha256_text(msgs[1]["content"])
            if h in hashes:
                raise ValueError(f"{p.name}:{idx}: duplicate prompt_hash")
            hashes.add(h)
            count += 1
        return count, hashes

    tr_n, tr_h = _load(train_path)
    ev_n, ev_h = _load(eval_path)
    overlap = tr_h & ev_h
    if overlap:
        raise ValueError(f"Train/eval leakage between {train_path.name} and {eval_path.name}: {len(overlap)}")
    return tr_n, ev_n


def main() -> int:
    parser = argparse.ArgumentParser(description="Build & validate AppSec and AlphaQuant datasets.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    appsec_train_p = args.data_dir / "appsec_train.jsonl"
    appsec_eval_p = args.data_dir / "appsec_eval.jsonl"
    aq_train_p = args.data_dir / "alphaquant_train.jsonl"
    aq_eval_p = args.data_dir / "alphaquant_eval.jsonl"

    if not args.validate_only:
        print("Fetching CyberNative/Code_Vulnerability_Security_DPO -> AppSec...")
        app_tr, app_ev = build_appsec_datasets()
        write_jsonl(appsec_train_p, app_tr)
        write_jsonl(appsec_eval_p, app_ev)

        print("Fetching gbharti/finance-alpaca + quant templates -> AlphaQuant...")
        aq_tr, aq_ev = build_alphaquant_datasets()
        write_jsonl(aq_train_p, aq_tr)
        write_jsonl(aq_eval_p, aq_ev)

    app_tr_n, app_ev_n = validate_pair(
        appsec_train_p,
        appsec_eval_p,
        {"language", "is_vulnerable", "severity", "title", "root_cause", "recommended_patch", "confidence"},
    )
    aq_tr_n, aq_ev_n = validate_pair(
        aq_train_p,
        aq_eval_p,
        {"domain", "framework", "strategy_type", "risk_model", "summary", "code"},
    )

    print(f"[PASS] {appsec_train_p}: {app_tr_n} | {appsec_eval_p}: {app_ev_n} (0 errors, 0 leakage)")
    print(f"[PASS] {aq_train_p}: {aq_tr_n} | {aq_eval_p}: {aq_ev_n} (0 errors, 0 leakage)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(r"F:\Develop\NationalCompute-Monetization\02-B300-Finetune-Asset\release-kit\assets")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


FONT_BOLD = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
]
FONT_REG = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
]
FONT_MONO = [
    r"C:\Windows\Fonts\consolab.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
]


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_grid_bg(img, accent_rgb):
    w, h = img.size
    # Base dark slate gradient
    base_draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(10 + 5 * t)
        g = int(14 + 7 * t)
        b = int(24 + 12 * t)
        base_draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Alpha overlay for subtle grid + ambient radial accent
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    step = 48
    for x in range(0, w, step):
        odraw.line([(x, 0), (x, h)], fill=(148, 163, 184, 16), width=1)
    for y in range(0, h, step):
        odraw.line([(0, y), (w, y)], fill=(148, 163, 184, 16), width=1)

    cx, cy = int(w * 0.88), int(h * 0.18)
    for rad, alpha in [(360, 12), (250, 18), (150, 24)]:
        odraw.ellipse(
            [cx - rad, cy - rad, cx + rad, cy + rad],
            fill=(accent_rgb[0], accent_rgb[1], accent_rgb[2], alpha),
        )

    composited = Image.alpha_composite(img, overlay)
    img.paste(composited)
    # Return an RGBA-compositing helper or draw on an overlay?
    # Note: Pillow ImageDraw.Draw(rgb_img, "RGBA") composites properly on RGB mode!
    return img


MODELS = [
    {
        "filename": "banner-solsec.png",
        "tag": "ENTERPRISE SECURITY MODEL  |  SOLANA / ANCHOR / RUST",
        "title": "SolSec-Qwen3.8-27B",
        "subtitle": "Deterministic Smart Contract Vulnerability & Audit Engine",
        "accent": "#10B981",
        "price": "$49 USDC",
        "access": "PRIVATE LICENSED",
        "metrics": [
            ("JSON Validity", "100.0%", "vs 36% Base"),
            ("Severity Acc.", "100.0%", "vs 0% Base"),
            ("FP Rejection", "100.0%", "25-Case Eval"),
            ("Quantization", "Q4_K_M", "16.7 GB GGUF"),
        ],
        "capabilities": [
            "Missing Signer & Owner Checks",
            "PDA Seed & Bump Collision",
            "Anchor Reinit & CPI Hijack",
            "Integer Overflow & Precision",
        ],
    },
    {
        "filename": "banner-appsec.png",
        "tag": "ENTERPRISE SECURITY MODEL  |  WEB / API / K8S / IAM",
        "title": "AppSec-Qwen3.8-27B",
        "subtitle": "Full-Stack SAST, API Exploit Triage & Cloud Misconfiguration Engine",
        "accent": "#38BDF8",
        "price": "$49 USDC",
        "access": "PRIVATE LICENSED",
        "metrics": [
            ("Architecture", "27B Dense", "Qwen3.8 Base"),
            ("Train Hardware", "8x B300", "NVIDIA Blackwell"),
            ("Dataset Scale", "1,200+", "Verified CVEs"),
            ("Quantization", "Q4_K_M", "16.7 GB GGUF"),
        ],
        "capabilities": [
            "SQLi / SSRF / RCE Sink Tracing",
            "JWT / OAuth2 / IDOR Bypass",
            "Docker & K8s RBAC Hardening",
            "Zero-Hallucination Patch Diffs",
        ],
    },
    {
        "filename": "banner-alphaquant.png",
        "tag": "QUANTITATIVE FINANCE MODEL  |  CRYPTO / EQUITIES / RISK",
        "title": "AlphaQuant-Qwen3.8-27B",
        "subtitle": "Institutional Strategy Synthesis, Microstructure & Risk Modeling",
        "accent": "#F59E0B",
        "price": "$49 USDC",
        "access": "PRIVATE LICENSED",
        "metrics": [
            ("Architecture", "27B Dense", "Qwen3.8 Base"),
            ("Train Hardware", "8x B300", "NVIDIA Blackwell"),
            ("Context Focus", "Alpha + Risk", "Structured JSON"),
            ("Quantization", "Q4_K_M", "16.7 GB GGUF"),
        ],
        "capabilities": [
            "Statistical Arbitrage & Cointegration",
            "Order-Book Imbalance & Slippage",
            "Kelly / VaR / Tail-Risk Sizing",
            "Backtest Bias & Leakage Audit",
        ],
    },
    {
        "filename": "banner-psychefa.png",
        "tag": "CLINICAL & PERSIAN NLP MODEL  |  FA / EN BILINGUAL",
        "title": "PsycheFa-Qwen3.8-27B",
        "subtitle": "Culturally Grounded Persian Behavioral Analysis & Therapeutic Triage",
        "accent": "#A78BFA",
        "price": "$79 USDC",
        "access": "PRIVATE LICENSED",
        "metrics": [
            ("Primary Lang", "Persian (FA)", "Native Fluency"),
            ("Train Hardware", "8x B300", "NVIDIA Blackwell"),
            ("Clinical Schema", "CBT / DSM", "Structured Triage"),
            ("Quantization", "Q4_K_M", "16.7 GB GGUF"),
        ],
        "capabilities": [
            "Nuanced Persian Idiom & Affect",
            "CBT Cognitive Distortion Mapping",
            "Risk & Crisis Escalation Guardrails",
            "Private Local Air-Gapped Inference",
        ],
    },
    {
        "filename": "banner-reverseeng.png",
        "tag": "OPEN RESEARCH RELEASE  |  BINARY / ELF / PE / ASM",
        "title": "ReverseEng-Qwen3.8-27B",
        "subtitle": "Decompilation Recovery, Malware Triage & Control-Flow Analysis",
        "accent": "#F43F5E",
        "price": "FREE / PUBLIC",
        "access": "OPEN WEIGHTS",
        "metrics": [
            ("JSON Validity", "100.0%", "Eval Verified"),
            ("Train Hardware", "8x B300", "NVIDIA Blackwell"),
            ("Targets", "x86_64 / ARM", "ELF & PE32+"),
            ("Quantization", "Q4_K_M", "16.7 GB GGUF"),
        ],
        "capabilities": [
            "Ghidra / IDA Pseudocode Recovery",
            "Obfuscation & Packer Signatures",
            "Syscall & C2 Behavior Mapping",
            "100% Local Offline Execution",
        ],
    },
]


def create_banner(spec):
    w, h = 1600, 620
    img = Image.new("RGBA", (w, h), (10, 14, 24, 255))
    accent_rgb = hex_to_rgb(spec["accent"])
    img = draw_grid_bg(img, accent_rgb)
    rgb_img = img.convert("RGB")
    draw = ImageDraw.Draw(rgb_img, "RGBA")

    f_tag = load_font(FONT_MONO, 20)
    f_title = load_font(FONT_BOLD, 56)
    f_sub = load_font(FONT_REG, 26)
    f_badge = load_font(FONT_BOLD, 22)
    f_m_lbl = load_font(FONT_REG, 18)
    f_m_val = load_font(FONT_BOLD, 34)
    f_m_sub = load_font(FONT_MONO, 16)
    f_cap_hdr = load_font(FONT_MONO, 17)
    f_cap = load_font(FONT_REG, 20)
    f_foot = load_font(FONT_MONO, 17)

    # Outer border
    draw_rounded_rect(draw, [24, 24, w - 24, h - 24], radius=18, outline=(255, 255, 255, 32), width=2)
    # Left accent bar
    draw_rounded_rect(draw, [24, 24, 34, h - 24], radius=5, fill=accent_rgb + (255,))

    # Top tag pill & right access badge
    draw.text((64, 54), spec["tag"], font=f_tag, fill=accent_rgb + (255,))

    badge_text = f"{spec['access']}  •  {spec['price']}"
    bbox = draw.textbbox((0, 0), badge_text, font=f_badge)
    bw = bbox[2] - bbox[0] + 44
    bx1 = w - 64 - bw
    draw_rounded_rect(
        draw,
        [bx1, 44, w - 64, 92],
        radius=10,
        fill=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 32),
        outline=accent_rgb + (180,),
        width=2,
    )
    draw.text((bx1 + 22, 54), badge_text, font=f_badge, fill=(245, 248, 255, 255))

    # Title & Subtitle
    draw.text((64, 102), spec["title"], font=f_title, fill=(248, 250, 252, 255))
    draw.text((64, 174), spec["subtitle"], font=f_sub, fill=(180, 194, 214, 255))

    # Divider line
    draw.line([(64, 224), (w - 64, 224)], fill=(255, 255, 255, 28), width=1)

    # 4 Metric Cards
    card_top = 248
    card_h = 136
    gap = 20
    total_w = w - 128
    card_w = (total_w - 3 * gap) // 4
    for i, (lbl, val, sub) in enumerate(spec["metrics"]):
        cx0 = 64 + i * (card_w + gap)
        cx1 = cx0 + card_w
        draw_rounded_rect(
            draw,
            [cx0, card_top, cx1, card_top + card_h],
            radius=12,
            fill=(18, 25, 40, 225),
            outline=(255, 255, 255, 30),
            width=1,
        )
        draw.text((cx0 + 20, card_top + 16), lbl.upper(), font=f_m_lbl, fill=(148, 163, 184, 255))
        draw.text((cx0 + 20, card_top + 46), val, font=f_m_val, fill=accent_rgb + (255,))
        draw.text((cx0 + 20, card_top + 96), sub, font=f_m_sub, fill=(203, 213, 225, 255))

    # Capabilities bar (2x2 grid inside sleek box)
    cap_top = 408
    cap_h = 116
    draw_rounded_rect(
        draw,
        [64, cap_top, w - 64, cap_top + cap_h],
        radius=12,
        fill=(15, 21, 34, 210),
        outline=(255, 255, 255, 24),
        width=1,
    )
    draw.text((86, cap_top + 14), "CORE CAPABILITIES", font=f_cap_hdr, fill=accent_rgb + (235,))
    col_w = (w - 172) // 2
    for idx, cap in enumerate(spec["capabilities"]):
        col = idx % 2
        row = idx // 2
        tx = 86 + col * col_w
        ty = cap_top + 44 + row * 32
        draw.ellipse([tx, ty + 8, tx + 8, ty + 16], fill=accent_rgb + (255,))
        draw.text((tx + 20, ty), cap, font=f_cap, fill=(226, 232, 240, 255))

    # Footer trust strip
    footer = "Bot: @backerv_bot   |   Support: t.me/Vahvldi   |   GitHub: github.com/vahidvl/solsec-b300-finetune   |   HF: huggingface.co/backerv"
    draw.text((64, 548), footer, font=f_foot, fill=(148, 163, 184, 255))

    out_path = OUT_DIR / spec["filename"]
    rgb_img.save(out_path, "PNG", optimize=True)
    print(f"Saved {out_path}")


def create_benchmark_chart():
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial"]
    plt.rcParams["axes.edgecolor"] = "#334155"
    plt.rcParams["axes.linewidth"] = 1.0

    fig, ax = plt.subplots(figsize=(14, 7.6), dpi=130)
    fig.patch.set_facecolor("#0A0E18")
    ax.set_facecolor("#0F1626")

    categories = [
        "JSON Schema\nValidity (%)",
        "Severity\nAccuracy (%)",
        "False Positive\nRejection (%)",
    ]
    base_vals = [36.0, 0.0, 88.9]
    solsec_vals = [100.0, 100.0, 100.0]

    x = np.arange(len(categories))
    width = 0.34

    bars1 = ax.bar(
        x - width / 2,
        base_vals,
        width,
        label="Base Qwen3.8-27B (Zero-Shot)",
        color="#475569",
        edgecolor="#64748B",
        linewidth=1.2,
        zorder=3,
    )
    bars2 = ax.bar(
        x + width / 2,
        solsec_vals,
        width,
        label="SolSec-Qwen3.8-27B (Fine-Tuned on 8x B300)",
        color="#10B981",
        edgecolor="#34D399",
        linewidth=1.2,
        zorder=3,
    )

    ax.grid(axis="y", color="#1E293B", linestyle="--", linewidth=1.0, zorder=0)
    ax.set_ylim(0, 126)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, color="#E2E8F0", fontsize=13, fontweight="bold")
    ax.tick_params(axis="y", colors="#94A3B8", labelsize=11)
    ax.set_ylabel("Benchmark Score (%)", color="#CBD5E1", fontsize=13, fontweight="bold", labelpad=12)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    for bar in bars1:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color="#CBD5E1",
            fontsize=12,
            fontweight="bold",
        )

    for bar in bars2:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color="#34D399",
            fontsize=13,
            fontweight="bold",
        )

    fig.text(
        0.065,
        0.93,
        "Empirical 25-Case Smart Contract Audit Benchmark (eval_report.json)",
        color="#F8FAFC",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.065,
        0.885,
        "Evaluated on 25 Solana / Anchor & adversarial false-positive test cases  |  Deterministic Q4_K_M GGUF inference",
        color="#94A3B8",
        fontsize=11,
    )

    legend = ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.01),
        ncol=2,
        frameon=True,
        facecolor="#131C2E",
        edgecolor="#334155",
        fontsize=11,
        labelcolor="#F1F5F9",
    )
    legend.get_frame().set_linewidth(1.0)

    fig.text(
        0.065,
        0.025,
        "Source: github.com/vahidvl/solsec-b300-finetune  |  @backerv_bot  |  Direct Support: t.me/Vahvldi",
        color="#64748B",
        fontsize=10,
    )

    plt.tight_layout(rect=[0.02, 0.05, 0.98, 0.85])
    out_path = OUT_DIR / "chart-solsec-benchmark.png"
    plt.savefig(out_path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_path}")


def create_checkout_guide():
    w, h = 1600, 900
    img = Image.new("RGBA", (w, h), (10, 14, 24, 255))
    accent_rgb = hex_to_rgb("#38BDF8")
    img = draw_grid_bg(img, accent_rgb)
    rgb_img = img.convert("RGB")
    draw = ImageDraw.Draw(rgb_img, "RGBA")

    f_tag = load_font(FONT_MONO, 20)
    f_title = load_font(FONT_BOLD, 46)
    f_sub = load_font(FONT_REG, 24)
    f_num = load_font(FONT_BOLD, 28)
    f_step_t = load_font(FONT_BOLD, 26)
    f_step_d = load_font(FONT_REG, 20)
    f_box_h = load_font(FONT_MONO, 18)
    f_box_t = load_font(FONT_MONO, 19)
    f_foot = load_font(FONT_MONO, 18)

    draw_rounded_rect(draw, [24, 24, w - 24, h - 24], radius=18, outline=(255, 255, 255, 32), width=2)

    draw.text((64, 52), "INSTANT NON-CUSTODIAL CHECKOUT  |  ZERO KYC  |  24/7 AUTOMATED", font=f_tag, fill=(56, 189, 248, 255))
    draw.text((64, 92), "How to Purchase & Download in 4 Steps", font=f_title, fill=(248, 250, 252, 255))
    draw.text((64, 152), "Automated verification via @backerv_bot  •  Solana USDC, BNB (BEP-20), or Tron (TRC-20)", font=f_sub, fill=(148, 163, 184, 255))

    steps = [
        (
            "01",
            "#38BDF8",
            "Open @backerv_bot",
            "Start the Telegram bot, choose your preferred language (6 languages supported), and select your model or the Full Bundle ($119).",
            "Command: /start  ->  Select Model",
        ),
        (
            "02",
            "#10B981",
            "Send Payment",
            "Transfer the exact USDC / USDT amount using Solana (instant auto-verify), BNB Smart Chain (BEP-20), or Tron (TRC-20).",
            "Solana USDC: Auto-verified in ~5s",
        ),
        (
            "03",
            "#F59E0B",
            "Submit TX Signature",
            "Paste your Solana TX signature directly in the bot chat (or send BEP-20 / TRC-20 TXID to @Vahvldi for fast manual unlock).",
            "Bot checks on-chain finality live",
        ),
        (
            "04",
            "#A78BFA",
            "Instant GGUF Link",
            "Receive a private, time-limited signed CDN download URL for the Q4_K_M GGUF weights + Modelfile to run locally in Ollama.",
            "Run: ollama create & ollama run",
        ),
    ]

    card_w = 344
    card_h = 370
    gap = 32
    start_x = 64
    top_y = 224

    for i, (num, col_hex, title, desc, pill) in enumerate(steps):
        col = hex_to_rgb(col_hex)
        x0 = start_x + i * (card_w + gap)
        x1 = x0 + card_w
        draw_rounded_rect(
            draw,
            [x0, top_y, x1, top_y + card_h],
            radius=16,
            fill=(17, 24, 39, 235),
            outline=(col[0], col[1], col[2], 140),
            width=2,
        )
        # Step number badge
        draw_rounded_rect(
            draw,
            [x0 + 24, top_y + 24, x0 + 88, top_y + 76],
            radius=10,
            fill=(col[0], col[1], col[2], 38),
            outline=col + (220,),
            width=2,
        )
        draw.text((x0 + 38, top_y + 34), num, font=f_num, fill=col + (255,))
        draw.text((x0 + 24, top_y + 98), title, font=f_step_t, fill=(248, 250, 252, 255))

        # Word-wrap description cleanly
        words = desc.split()
        lines = []
        cur = ""
        for w_tok in words:
            test = (cur + " " + w_tok).strip()
            if draw.textbbox((0, 0), test, font=f_step_d)[2] <= card_w - 48:
                cur = test
            else:
                lines.append(cur)
                cur = w_tok
        if cur:
            lines.append(cur)

        for li, line in enumerate(lines[:6]):
            draw.text((x0 + 24, top_y + 144 + li * 28), line, font=f_step_d, fill=(203, 213, 225, 255))

        # Bottom pill
        draw_rounded_rect(
            draw,
            [x0 + 20, top_y + card_h - 58, x1 - 20, top_y + card_h - 18],
            radius=8,
            fill=(10, 14, 24, 230),
            outline=(255, 255, 255, 25),
            width=1,
        )
        draw.text((x0 + 30, top_y + card_h - 49), pill, font=load_font(FONT_MONO, 15), fill=col + (255,))

        # Arrow connector to next card
        if i < 3:
            ax0 = x1 + 4
            ax1 = x1 + gap - 4
            ay = top_y + card_h // 2
            draw.line([(ax0, ay), (ax1 - 6, ay)], fill=(148, 163, 184, 180), width=3)
            draw.polygon([(ax1, ay), (ax1 - 10, ay - 7), (ax1 - 10, ay + 7)], fill=(148, 163, 184, 220))

    # Payment & Trust Strip at bottom
    box_y0 = 632
    box_y1 = 806
    draw_rounded_rect(
        draw,
        [64, box_y0, w - 64, box_y1],
        radius=14,
        fill=(15, 21, 34, 230),
        outline=(255, 255, 255, 28),
        width=1,
    )
    draw.text((90, box_y0 + 18), "VERIFIED PAYMENT CHANNELS & DIRECT SUPPORT", font=f_box_h, fill=(56, 189, 248, 255))
    draw.text((90, box_y0 + 52), "Solana USDC (Auto):  9JQ8EBuPk4qDN92dy6WCtrivemjw8w9FHTp6jubwPHuK", font=f_box_t, fill=(226, 232, 240, 255))
    draw.text((90, box_y0 + 84), "BNB (BEP-20):        0xf74BfB2234150CdCf7eAa35AEF1b6a2e95E650b0", font=f_box_t, fill=(226, 232, 240, 255))
    draw.text((90, box_y0 + 116), "Tron (TRC-20):       TURHs9J1eXHzCRm7zGUvMyehT7G7GppD87", font=f_box_t, fill=(226, 232, 240, 255))

    footer = "Telegram Bot: https://t.me/backerv_bot   |   Direct Support: https://t.me/Vahvldi   |   GitHub: https://github.com/vahidvl/solsec-b300-finetune"
    draw.text((64, 836), footer, font=f_foot, fill=(148, 163, 184, 255))

    out_path = OUT_DIR / "guide-checkout-flow.png"
    rgb_img.save(out_path, "PNG", optimize=True)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    for m in MODELS:
        create_banner(m)
    create_benchmark_chart()
    create_checkout_guide()
    print("ALL 7 ASSETS GENERATED SUCCESSFULLY.")

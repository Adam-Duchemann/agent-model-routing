#!/usr/bin/env python3
"""Generate the cost-comparison hero charts (light + dark SVG) for the README.
Two variants:
  - absolute : mean $ per pass (real billed)            -> cost-comparison-{light,dark}.svg
  - relative : cost vs all-Fable baseline (=100)        -> cost-comparison-relative-{light,dark}.svg
Regenerate after re-running the benchmark: python3 make_chart.py
Palette + accessibility per the dataviz method (validated blue/orange categorical pair)."""
import os

# --- source numbers (from benchmark/score.py, n=3): (label1, label2, routed$, baseline$, savings) ---
RAW = [
    ("Exploration", "Haiku",  0.093, 1.056, "91%"),
    ("Interpretive", "Sonnet", 0.839, 1.235, "32%"),
    ("Full mix", "6 tasks",   0.931, 2.291, "59%"),
]

def rel_groups():
    # baseline normalised to 100 per group; routed = its share of the baseline
    out = []
    for g1, g2, rv, bv, pct in RAW:
        out.append((g1, g2, round(rv / bv * 100, 1), 100.0, pct))
    return out

VARIANTS = {
    "absolute": dict(
        groups=RAW, ymax=2.4, ystep=0.6, valfmt=lambda v: f"${v:.2f}",
        ytitle="mean $ (billed)", label_routed=True,
        subtitle="6-task mix · n=3 trials · real billed cost · lower is better ↓",
        footer="Quality identical both arms: 18/18 tasks passed. Fixture: a ~270-file Rust+TS repo.",
        suffix=""),
    "relative": dict(
        groups=rel_groups(), ymax=100.0, ystep=25.0, valfmt=lambda v: f"{v:.0f}",
        ytitle="relative cost", label_routed=False,
        subtitle="6-task mix · n=3 trials · cost vs all-Fable (=100) · lower is better ↓",
        footer="Quality identical both arms: 18/18 tasks passed. Absolute $ omitted — short tasks; the ratio is what generalizes.",
        suffix="-relative"),
}

# --- geometry (shared) ---
W, H = 780, 440
PL, PR, PT, PB = 76, 756, 100, 360
PW = PR - PL
BARW, GAP = 64, 4
ANNOT_Y = 168

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", sec="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", routed="#2a78d6", base="#eb6834",
                  good="#006300"),
    "dark":  dict(surface="#1a1a19", ink="#ffffff", sec="#c3c2b7", muted="#898781",
                  grid="#2c2c2a", axis="#383835", routed="#3987e5", base="#d95926",
                  good="#0ca30c"),
}
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

def svg(mode, cfg):
    c = THEMES[mode]
    ymax, ystep = cfg["ymax"], cfg["ystep"]
    ppu = (PB - PT) / ymax
    valfmt = cfg["valfmt"]
    def y(v): return PB - v * ppu
    def bar(x, val, fill):
        top = y(val); h = PB - top; r = min(3, h / 2)
        return (f'<path d="M{x},{PB} L{x},{top+r} Q{x},{top} {x+r},{top} '
                f'L{x+BARW-r},{top} Q{x+BARW},{top} {x+BARW},{top+r} L{x+BARW},{PB} Z" fill="{fill}"/>')
    e = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" '
         f'aria-label="Cost per session pass, routed model mix versus all-Fable baseline. '
         f'Exploration 91% cheaper, interpretive 32%, full mix 59%, at 100% quality parity.">']
    e.append(f'<rect width="{W}" height="{H}" rx="10" fill="{c["surface"]}"/>')
    e.append(f'<text x="40" y="36" font-size="19" font-weight="600" fill="{c["ink"]}">Cost per session pass — routed mix vs all-Fable</text>')
    e.append(f'<text x="40" y="57" font-size="13" fill="{c["muted"]}">{cfg["subtitle"]}</text>')
    e.append(f'<rect x="40" y="70" width="12" height="12" rx="2" fill="{c["routed"]}"/>')
    e.append(f'<text x="58" y="80" font-size="13" fill="{c["sec"]}">Routed (policy tiers)</text>')
    e.append(f'<rect x="210" y="70" width="12" height="12" rx="2" fill="{c["base"]}"/>')
    e.append(f'<text x="228" y="80" font-size="13" fill="{c["sec"]}">All-Fable (baseline)</text>')
    v = 0.0
    while v <= ymax + 1e-9:
        yy = y(v)
        if v > 0:
            e.append(f'<line x1="{PL}" y1="{yy:.1f}" x2="{PR}" y2="{yy:.1f}" stroke="{c["grid"]}" stroke-width="1"/>')
        e.append(f'<text x="66" y="{yy+4:.1f}" font-size="11" text-anchor="end" fill="{c["muted"]}" '
                 f'font-variant-numeric="tabular-nums">{valfmt(v)}</text>')
        v += ystep
    e.append(f'<line x1="{PL}" y1="{PB}" x2="{PR}" y2="{PB}" stroke="{c["axis"]}" stroke-width="1.5"/>')
    e.append(f'<text x="22" y="{(PT+PB)//2}" font-size="12" fill="{c["muted"]}" text-anchor="middle" '
             f'transform="rotate(-90 22 {(PT+PB)//2})">{cfg["ytitle"]}</text>')
    slot = PW / len(cfg["groups"])
    for i, (g1, g2, rv, bv, pct) in enumerate(cfg["groups"]):
        center = PL + slot/2 + i*slot
        rx = center - (BARW + GAP/2); bx = center + GAP/2
        e.append(bar(rx, rv, c["routed"]))
        e.append(bar(bx, bv, c["base"]))
        if cfg["label_routed"]:
            e.append(f'<text x="{rx+BARW/2:.0f}" y="{y(rv)-6:.0f}" font-size="12" text-anchor="middle" '
                     f'fill="{c["sec"]}" font-variant-numeric="tabular-nums">{valfmt(rv)}</text>')
        e.append(f'<text x="{bx+BARW/2:.0f}" y="{y(bv)-6:.0f}" font-size="12" text-anchor="middle" '
                 f'fill="{c["sec"]}" font-variant-numeric="tabular-nums">{valfmt(bv)}</text>')
        annot = min(ANNOT_Y, y(rv) - 34)   # float above the routed bar when it's tall
        e.append(f'<text x="{rx+BARW/2:.0f}" y="{annot:.0f}" font-size="16" font-weight="700" '
                 f'text-anchor="middle" fill="{c["good"]}">↓ {pct}</text>')
        e.append(f'<text x="{rx+BARW/2:.0f}" y="{annot+16:.0f}" font-size="11" text-anchor="middle" fill="{c["good"]}">cheaper</text>')
        e.append(f'<text x="{center:.0f}" y="382" font-size="13" font-weight="600" text-anchor="middle" fill="{c["ink"]}">{g1}</text>')
        e.append(f'<text x="{center:.0f}" y="398" font-size="11" text-anchor="middle" fill="{c["muted"]}">{g2}</text>')
    e.append(f'<text x="40" y="428" font-size="11" fill="{c["muted"]}">{cfg["footer"]}</text>')
    e.append('</svg>')
    return "\n".join(e)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for vname, cfg in VARIANTS.items():
        for mode in ("light", "dark"):
            p = os.path.join(here, f"cost-comparison{cfg['suffix']}-{mode}.svg")
            open(p, "w").write(svg(mode, cfg) + "\n")
            print("wrote", os.path.basename(p))

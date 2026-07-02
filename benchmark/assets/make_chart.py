#!/usr/bin/env python3
"""Generate the cost-comparison hero chart (light + dark SVG) for the README.
Regenerate after re-running the benchmark: python3 make_chart.py
Palette + accessibility per the dataviz method (validated blue/orange categorical pair)."""
import os

# --- data (from benchmark/score.py, n=3) ---
GROUPS = [
    ("Exploration", "Haiku",  0.093, 1.056, "91%"),
    ("Interpretive", "Sonnet", 0.839, 1.235, "32%"),
    ("Full mix", "6 tasks",   0.931, 2.291, "59%"),
]
YMAX = 2.4
YSTEP = 0.6

# --- geometry ---
W, H = 780, 440
PL, PR, PT, PB = 76, 756, 100, 360         # plot box
PW = PR - PL
PPU = (PB - PT) / YMAX                      # pixels per $
BARW, GAP = 64, 4
ANNOT_Y = 168                              # common line for the "% cheaper" callouts

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", sec="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", routed="#2a78d6", base="#eb6834",
                  good="#006300"),
    "dark":  dict(surface="#1a1a19", ink="#ffffff", sec="#c3c2b7", muted="#898781",
                  grid="#2c2c2a", axis="#383835", routed="#3987e5", base="#d95926",
                  good="#0ca30c"),
}
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

def y(v): return PB - v * PPU

def bar(x, val, fill):
    top = y(val); h = PB - top
    r = min(3, h / 2)
    # rounded top corners only, anchored to baseline
    return (f'<path d="M{x},{PB} L{x},{top+r} Q{x},{top} {x+r},{top} '
            f'L{x+BARW-r},{top} Q{x+BARW},{top} {x+BARW},{top+r} L{x+BARW},{PB} Z" '
            f'fill="{fill}"/>')

def svg(mode):
    c = THEMES[mode]
    e = []
    e.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'font-family="{FONT}" role="img" '
             f'aria-label="Cost per full benchmark pass: routed model mix versus all-Fable baseline. '
             f'Exploration 91% cheaper, interpretive 32%, full mix 59%, at 100% quality parity.">')
    e.append(f'<rect width="{W}" height="{H}" rx="10" fill="{c["surface"]}"/>')
    # title + subtitle
    e.append(f'<text x="40" y="36" font-size="19" font-weight="600" fill="{c["ink"]}">'
             f'Cost per session pass — routed mix vs all-Fable</text>')
    e.append(f'<text x="40" y="57" font-size="13" fill="{c["muted"]}">'
             f'6-task mix · n=3 trials · real billed cost · lower is better ↓</text>')
    # legend (own row, below subtitle)
    e.append(f'<rect x="40" y="70" width="12" height="12" rx="2" fill="{c["routed"]}"/>')
    e.append(f'<text x="58" y="80" font-size="13" fill="{c["sec"]}">Routed (policy tiers)</text>')
    e.append(f'<rect x="210" y="70" width="12" height="12" rx="2" fill="{c["base"]}"/>')
    e.append(f'<text x="228" y="80" font-size="13" fill="{c["sec"]}">All-Fable (baseline)</text>')
    # gridlines + y ticks
    v = 0.0
    while v <= YMAX + 1e-9:
        yy = y(v)
        if v > 0:
            e.append(f'<line x1="{PL}" y1="{yy:.1f}" x2="{PR}" y2="{yy:.1f}" stroke="{c["grid"]}" stroke-width="1"/>')
        e.append(f'<text x="66" y="{yy+4:.1f}" font-size="11" text-anchor="end" fill="{c["muted"]}" '
                 f'font-variant-numeric="tabular-nums">${v:.2f}</text>')
        v += YSTEP
    # baseline axis
    e.append(f'<line x1="{PL}" y1="{PB}" x2="{PR}" y2="{PB}" stroke="{c["axis"]}" stroke-width="1.5"/>')
    # y-axis title
    e.append(f'<text x="22" y="{(PT+PB)/2:.0f}" font-size="12" fill="{c["muted"]}" '
             f'text-anchor="middle" transform="rotate(-90 22 {(PT+PB)/2:.0f})">mean $ (billed)</text>')
    # groups
    slot = PW / len(GROUPS)
    for i, (g1, g2, rv, bv, pct) in enumerate(GROUPS):
        center = PL + slot/2 + i*slot
        rx = center - (BARW + GAP/2); bx = center + GAP/2
        e.append(bar(rx, rv, c["routed"]))
        e.append(bar(bx, bv, c["base"]))
        # value labels
        e.append(f'<text x="{rx+BARW/2:.0f}" y="{y(rv)-6:.0f}" font-size="12" text-anchor="middle" '
                 f'fill="{c["sec"]}" font-variant-numeric="tabular-nums">${rv:.2f}</text>')
        e.append(f'<text x="{bx+BARW/2:.0f}" y="{y(bv)-6:.0f}" font-size="12" text-anchor="middle" '
                 f'fill="{c["sec"]}" font-variant-numeric="tabular-nums">${bv:.2f}</text>')
        # "% cheaper" callout over the routed bar, common line
        e.append(f'<text x="{rx+BARW/2:.0f}" y="{ANNOT_Y}" font-size="16" font-weight="700" '
                 f'text-anchor="middle" fill="{c["good"]}">↓ {pct}</text>')
        e.append(f'<text x="{rx+BARW/2:.0f}" y="{ANNOT_Y+16}" font-size="11" '
                 f'text-anchor="middle" fill="{c["good"]}">cheaper</text>')
        # x labels
        e.append(f'<text x="{center:.0f}" y="382" font-size="13" font-weight="600" text-anchor="middle" fill="{c["ink"]}">{g1}</text>')
        e.append(f'<text x="{center:.0f}" y="398" font-size="11" text-anchor="middle" fill="{c["muted"]}">{g2}</text>')
    # footer note
    e.append(f'<text x="40" y="428" font-size="11" fill="{c["muted"]}">'
             f'Quality identical both arms: 18/18 tasks passed. Fixture: a ~270-file Rust+TS repo.</text>')
    e.append('</svg>')
    return "\n".join(e)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for mode in ("light", "dark"):
        p = os.path.join(here, f"cost-comparison-{mode}.svg")
        open(p, "w").write(svg(mode) + "\n")
        print("wrote", p)

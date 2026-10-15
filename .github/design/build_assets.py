"""Builds the profile's SVGs (all type outlined to paths, no web fonts needed).

    npm i @fontsource/noto-serif-display @fontsource/onest @fontsource/jetbrains-mono
    FONTS=node_modules/@fontsource python3 .github/design/build_assets.py
"""
import json, os
from html import escape
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets")
FONTS = os.environ.get("FONTS", "node_modules/@fontsource")
os.makedirs(OUT, exist_ok=True)


def load(pkg, f):
    return TTFont(os.path.join(FONTS, pkg, "files", f))


SERIF = load("noto-serif-display", "noto-serif-display-latin-400-normal.woff2")
SERIF_I = load("noto-serif-display", "noto-serif-display-latin-400-italic.woff2")
MONO = load("jetbrains-mono", "jetbrains-mono-latin-400-normal.woff2")
SANS = load("onest", "onest-latin-400-normal.woff2")
SANS_M = load("onest", "onest-latin-500-normal.woff2")

FALLBACK = {"—": "-", "·": "·", "↗": ">", "↔": "-", "×": "x"}


def _g(font, ch):
    cm = font.getBestCmap()
    if ord(ch) in cm:
        return cm[ord(ch)]
    return cm.get(ord(FALLBACK.get(ch, "?")), cm[ord("?")])


def width(font, text, size, ls=0.0):
    s = size / font["head"].unitsPerEm
    return sum(font["hmtx"][_g(font, c)][0] * s for c in text) + ls * max(len(text) - 1, 0)


def path(font, text, x, base, size, ls=0.0, anchor="start"):
    w = width(font, text, size, ls)
    x = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
    s = size / font["head"].unitsPerEm
    gs = font.getGlyphSet()
    out = []
    for c in text:
        g = _g(font, c)
        pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, base)))
        if pen.getCommands():
            out.append(pen.getCommands())
        x += font["hmtx"][g][0] * s + ls
    return " ".join(out)


def cap(font, size):
    return font["OS/2"].sCapHeight * size / font["head"].unitsPerEm


def wrap(font, text, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if width(font, t, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


P = {
    "light": dict(bg="#ECEBE6", tile="#F7F6F2", ink="#0F0F0F", soft="#3B3A37", muted="#5E5C57", acc="#D4380D",
                  on_acc="#FFFFFF", inv="#0F0F0F", inv_ink="#ECEBE6", inv_muted="#A8A69F", hair="#0F0F0F", chip="#0F0F0F"),
    "dark": dict(bg="#FFFFFF0A", tile="#FFFFFF0D", ink="#ECEBE6", soft="#CFCCC4", muted="#A8A69F", acc="#F2531F",
                 on_acc="#151515", inv="#ECEBE6", inv_ink="#0F0F0F", inv_muted="#5E5C57", hair="#ECEBE6", chip="#ECEBE6"),
}


def svg(w, h, label, body):
    label = escape(label, quote=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">\n'
            f"<title>{label}</title>\n{body}</svg>\n")


def write(name, theme, content):
    open(os.path.join(OUT, f"{name}-{theme}.svg"), "w").write(content)


def monogram_group(p, tx, ty, k):
    size = 168
    ls = -0.05 * size
    wd = width(SERIF, "D", size, ls)
    wg = width(SERIF_I, "G", size, ls)
    x0 = 230 - (wd + wg + ls) / 2
    base = 206.5 + cap(SERIF, size) / 2
    d = path(SERIF, "D", x0, base, size, ls)
    g = path(SERIF_I, "G", x0 + wd + ls, base, size, ls)
    m = path(MONO, "FRONTEND", 230, 392 + cap(MONO, 14) / 2, 14, 0.42 * 14, "middle")
    return f'''<g transform="translate({tx} {ty}) scale({k})">
<g fill="none" stroke="{p['acc']}" stroke-width="5" stroke-linejoin="miter">
<path d="M96 100 L112 84 H212 L230 66 L248 84 H348 L364 100"/><path d="M96 314 L112 330 H212 L230 348 L248 330 H348 L364 314"/></g>
<path fill="{p['ink']}" d="{d}"/><path fill="{p['acc']}" d="{g}"/><path fill="{p['muted']}" d="{m}"/></g>
'''


def brace(p, x, y0, y1, left=True):
    m = (y0 + y1) / 2
    s = 1 if left else -1
    pts = [(x + 18 * s, y0), (x, y0 + 18), (x, m - 22), (x - 20 * s, m), (x, m + 22), (x, y1 - 18), (x + 18 * s, y1)]
    d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
    return f'<path fill="none" stroke="{p["acc"]}" stroke-width="5" stroke-linejoin="miter" d="{d}"/>\n'


def banner(p):
    W, H = 1280, 300
    size = 118
    ls = -0.04 * size
    a, b = "Daniil ", "Grebnev"
    wa, wb = width(SERIF, a, size, ls), width(SERIF_I, b, size, ls)
    x0 = W / 2 - (wa + wb + ls) / 2
    body = f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="28" fill="{p["bg"]}" stroke="{p["hair"]}" stroke-opacity=".14"/>\n'
    body += brace(p, 150, 52, 248, True) + brace(p, W - 150, 52, 248, False)
    body += f'<path fill="{p["ink"]}" d="{path(SERIF, a, x0, 168, size, ls)}"/>\n'
    body += f'<path fill="{p["acc"]}" d="{path(SERIF_I, b, x0 + wa + ls, 168, size, ls)}"/>\n'
    body += f'<path fill="{p["muted"]}" d="{path(MONO, "FRONTEND DEVELOPER — REACT · NEXT.JS · TYPESCRIPT", W/2, 216, 16, 0.14*16, "middle")}"/>\n'
    return svg(W, H, "Daniil Grebnev, frontend developer", body)


def head(p, plain, accent, n):
    W, H = 1280, 96
    size = 56
    ls = -0.04 * size
    x = 4
    b = ""
    if plain:
        b += f'<path fill="{p["ink"]}" d="{path(SERIF, plain + " ", x, 64, size, ls)}"/>\n'
        x += width(SERIF, plain + " ", size, ls) + ls
    b += f'<path fill="{p["acc"]}" d="{path(SERIF_I, accent, x, 64, size, ls)}"/>\n'
    b += f'<path fill="{p["muted"]}" d="{path(MONO, n, W - 4, 60, 16, 0.12*16, "end")}"/>\n'
    b += f'<path stroke="{p["hair"]}" stroke-opacity=".18" d="M0 88.5 H{W}"/>\n'
    return svg(W, H, f"{plain} {accent}".strip(), b)


ACH = [
    ("14.82", "ms", "Real-time map rendering for 10,000+ data points"),
    ("30", "x", "Faster CI/CD release pipeline: from 1 hour to 2 minutes"),
    ("2,600", "+", "Lazy-loaded UI components with zero degradation"),
    ("13", "", "Sales-team members freed from manual approvals by CRM modules and a document editor"),
]


def achievements(p):
    W, H, gap = 1280, 292, 16
    w = (W - 3 * gap) / 4
    b = ""
    for i, (val, unit, text) in enumerate(ACH):
        x = i * (w + gap)
        kind = "acc" if i == 1 else "inv" if i == 3 else "tile"
        bg = {"acc": p["acc"], "inv": p["inv"], "tile": p["tile"]}[kind]
        ink = {"acc": p["on_acc"], "inv": p["inv_ink"], "tile": p["ink"]}[kind]
        soft = {"acc": p["on_acc"], "inv": p["inv_ink"], "tile": p["soft"]}[kind]
        mut = {"acc": p["on_acc"], "inv": p["inv_muted"], "tile": p["muted"]}[kind]
        b += f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{H}" rx="26" fill="{bg}"' + (f' stroke="{p["hair"]}" stroke-opacity=".1"' if kind == "tile" else "") + "/>\n"
        b += f'<path fill="{mut}" d="{path(MONO, f"0{i+1}", x+28, 52, 15, 0.12*15)}"/>\n'
        size = 84
        ls = -0.05 * size
        b += f'<path fill="{ink}" d="{path(SERIF, val, x+28, 142, size, ls)}"/>\n'
        vw = width(SERIF, val, size, ls)
        if unit in ("+", "x"):
            b += f'<path fill="{ink if kind != "tile" else p["acc"]}" d="{path(SERIF_I, "+" if unit == "+" else "×", x+28+vw+ls, 142, size, ls)}"/>\n'
        elif unit:
            b += f'<path fill="{ink}" d="{path(SERIF, unit, x+28+vw+8, 142, 34, -0.02*34)}"/>\n'
        for j, line in enumerate(wrap(SANS, text, 17, w - 56)[:4]):
            b += f'<path fill="{soft}" fill-opacity="{1 if kind=="tile" else .92}" d="{path(SANS, line, x+28, 190+j*24, 17)}"/>\n'
    return svg(W, H, "Key achievements: 14.82 ms map rendering, 30× faster releases, 2,600+ lazy-loaded components, 13 people freed from manual approvals", b)


ICONS = json.load(open(os.path.join(HERE, "icons.json")))
TOOLS = [("react", "React"), ("nextjs", "Next.js"), ("typescript", "TypeScript"), ("javascript", "JavaScript"), ("redux", "Redux"),
         ("tailwind", "Tailwind"), ("nestjs", "NestJS"), ("nodejs", "Node.js"), ("docker", "Docker"), ("nginx", "Nginx"),
         ("git", "Git"), ("flutter", "Flutter"), ("leaflet", "Leaflet"), ("vitest", "Vitest")]


def stack(p):
    per, gap, th = 7, 14, 132
    W = 1280
    tw = (W - gap * (per - 1)) / per
    H = th * 2 + gap
    b = ""
    for i, (slug, label) in enumerate(TOOLS):
        x, y = (i % per) * (tw + gap), (i // per) * (th + gap)
        core = i < 3
        bg = p["inv"] if core else p["tile"]
        ink = p["inv_ink"] if core else p["ink"]
        b += f'<rect x="{x+.5:.1f}" y="{y+.5}" width="{tw-1:.1f}" height="{th-1}" rx="22" fill="{bg}"' + ('' if core else f' stroke="{p["hair"]}" stroke-opacity=".1"') + "/>\n"
        k = 46 / 24
        b += f'<path transform="translate({x + tw/2 - 12*k:.1f} {y+24}) scale({k:.3f})" fill="{ink}" d="{ICONS[slug]["path"]}"/>\n'
        b += f'<path fill="{ink}" d="{path(MONO, label, x + tw/2, y+th-26, 15, 0.04*15, "middle")}"/>\n'
    return svg(W, H, "Stack: " + ", ".join(l for _, l in TOOLS), b)


def contact(p, label, value, primary, alt):
    W, H = 620, 104
    bg = p["acc"] if primary else p["tile"]
    ink = p["on_acc"] if primary else p["ink"]
    mut = p["on_acc"] if primary else p["muted"]
    b = f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="26" fill="{bg}"' + ('' if primary else f' stroke="{p["hair"]}" stroke-opacity=".1"') + "/>\n"
    b += f'<path fill="{mut}" d="{path(MONO, label.upper(), 32, 38, 15, 0.12*15)}"/>\n'
    b += f'<path fill="{ink}" d="{path(SERIF, value, 32, 78, 30, -0.02*30)}"/>\n'
    ax, ay = W - 52, 36
    b += f'<g fill="none" stroke="{ink}" stroke-width="2.4" stroke-linecap="square"><path d="M{ax} {ay+22} L{ax+22} {ay}"/><path d="M{ax+4} {ay} H{ax+22} V{ay+18}"/></g>\n'
    return svg(W, H, f"{label}: {value}", b)


if __name__ == "__main__":
    for theme, p in P.items():
        write("banner", theme, banner(p))
        write("achievements", theme, achievements(p))
        write("stack", theme, stack(p))
        for key, label, value, primary in [("c-email", "Email", "danilgrebneff@gmail.com", True), ("c-telegram", "Telegram", "t.me/daniilgral", False),
                                           ("c-github", "GitHub", "github.com/daniilgrebnev", False), ("c-linkedin", "LinkedIn", "linkedin.com/in/daniilgrebnev", False)]:
            write(key, theme, contact(p, label, value, primary, ""))
    print("built", len(os.listdir(OUT)), "files")

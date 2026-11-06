#!/usr/bin/env python3
"""把 Action 生成的卡片改成黑白漫画风，并各出浅色、深色两版，由 PersonalStatus.yml 调用。

原始卡片（stats.svg 等）保持不动，每次都从它生成 *-light.svg / *-dark.svg：
- 字体换成内嵌的 Playfair Display；整张去色，深色版再反相到 me 站点的夜间配色
- 加双线框、网点角、扫光、闪光、泡沫、樱花、小水母和红色印章标签（这些装饰在深色版里直接换成夜间配色）
- 奖杯摆上展示架、各自浮动；活动图折线反复描出；贪吃蛇包进一格漫画，底下走胶片
"""
import math
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (BASE_CSS, DEFS, EASE_OUT, INK, MINCHO, MINCHO_STACK, NIGHT_RED, PAPER, RED, SERIF, SERIF_STACK,  # noqa: E402
                   chime, film_strip, foam, jellyfish, letters, load_font, petals, sheen_grad, sparkles, stamp, title_fx, to_night)

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "profile"
SANS_CSS = re.compile(r"""(['"])Segoe UI\1,\s*Ubuntu,(\s*"Helvetica Neue",)?\s*Sans-Serif""")
SANS_ATTR = re.compile(r'font-family="[^"]*Segoe UI[^"]*"')
LABELS = "能力値言語推し活動記録連載中草を食べる蛇・365日"
JP = load_font(MINCHO, 800, LABELS)


def size(svg):
    w = float(re.search(r'<svg[^>]*?\bwidth="([\d.]+)', svg).group(1))
    h = float(re.search(r'<svg[^>]*?\bheight="([\d.]+)', svg).group(1))
    return w, h


def split(svg):
    """拆成根标签和内容。"""
    i = svg.index(">", svg.index("<svg")) + 1
    return svg[:i], svg[i:svg.rfind("</svg>")]


def serif(svg):
    text = "".join(re.findall(r">([^<>]+)<", svg))
    faces = [f for f in (load_font(SERIF, 400, text), load_font(SERIF, 700, text)) if f]
    svg = SANS_CSS.sub(SERIF_STACK, svg)
    svg = SANS_ATTR.sub('font-family="Playfair Display, Georgia, serif"', svg)
    return svg, faces


def fit_stats(svg, faces):
    """统计卡片的标签到数值的距离固定，衬线字更宽，按最长标签缩小字号。"""
    bold = faces[-1] if faces else None
    labels = re.findall(r'class="stat\s+bold"[^>]*>([^<]+)<', svg)
    if bold and labels:
        widest = max(bold.width(t.strip(), 14) for t in labels)
        if widest > 190:
            svg = svg.replace("font: 600 14px", f"font: 600 {max(11.5, 14 * 190 / widest):.1f}px", 1)
    return svg


KIRA_CSS = f"""
  .kira {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: kira 2.4s {EASE_OUT} infinite; }}
  @keyframes kira {{ 0% {{ opacity: 0; transform: scale(0.2) rotate(0deg); }} 12% {{ opacity: 1; }} 65% {{ opacity: 0; transform: scale(1) rotate(12deg); }} 100% {{ opacity: 0; transform: scale(1) rotate(12deg); }} }}
  .sweep {{ animation: sweep 6.4s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(0); }} 45%, 100% {{ transform: translateX(var(--len)); }} }}
"""
BAND = ('<linearGradient id="band" x1="0" x2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0" />'
        '<stop offset="0.5" stop-color="#ffffff" stop-opacity="__BAND__" /><stop offset="1" stop-color="#ffffff" stop-opacity="0" /></linearGradient>')


def kira(x, y, r, delay, dur=2.4):
    """闪光：八道细光往外弹开、淡掉，中心一颗四角星。"""
    rays = "".join(f"M{x + math.cos(a) * r * 0.35:.1f} {y + math.sin(a) * r * 0.35:.1f}L{x + math.cos(a) * r * (1 if k % 2 else 0.65):.1f} {y + math.sin(a) * r * (1 if k % 2 else 0.65):.1f}"
                   for k, a in enumerate(i * math.pi / 4 for i in range(8)))
    return (f'<g class="kira" style="animation-duration:{dur}s;animation-delay:{-delay:.2f}s"><path d="{rays}" stroke="{INK}" stroke-width="1" stroke-linecap="round" />'
            f'<path d="M{x} {y - r * 0.3:.1f}L{x + r * 0.07:.1f} {y - r * 0.07:.1f}L{x + r * 0.3:.1f} {y}L{x + r * 0.07:.1f} {y + r * 0.07:.1f}L{x} {y + r * 0.3:.1f}L{x - r * 0.07:.1f} {y + r * 0.07:.1f}L{x - r * 0.3:.1f} {y}L{x - r * 0.07:.1f} {y - r * 0.07:.1f}Z" fill="{INK}" /></g>')


def sweep(w, h, delay=0.0, width=90):
    """一道斜向的光从左扫到右，扫完停一会儿。"""
    return (f'<g class="sweep" style="--len:{w + width * 3:.0f}px;animation-delay:{-delay:.2f}s"><rect x="{-width * 2:.0f}" y="{-h * 0.2:.0f}" width="{width}" height="{h * 1.4:.0f}" '
            f'fill="url(#band)" transform="skewX(-18)" /></g>')


def manga_overlay(w, h, seed, jelly=None, foam_bottom=True):
    """墨层上的装饰：内框细线、右上角网点、扫光、闪光、底边泡沫、樱花，可选一只小水母。"""
    rng = random.Random(seed)
    corner = f'<path d="M{w - 90:.0f} 1L{w - 1:.0f} 1L{w - 1:.0f} {min(90, h * 0.6):.0f}Z" fill="url(#toneFine)" opacity="0.45" />'
    jf = jellyfish(f"c{seed}", *jelly, seed) if jelly else ""
    bursts = "".join(kira(x, y, r, d) for x, y, r, d in [(w - 30, h - 26, 12, 0.3), (24, 22, 10, 1.5), (w * 0.62, 12, 8, 0.9)])
    return (f'<g pointer-events="none">'
            f'<rect x="5" y="5" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.8" />'
            f'{corner}{sweep(w, h, seed * 0.7)}{jf}{bursts}'
            f'{foam(rng, 10, 12, w - 12, h - 8, h + 4, 1.6, 3.6, (14, 34), 0.25) if foam_bottom else ""}'
            f'{petals(rng, 4, w * 0.05, w * 0.95, -10, h + 20)}'
            f'{sparkles([(w - 26, 24, 5, 0), (w - 48, 40, 3.5, 1.2), (14, h - 16, 4, 2.2)])}</g>')


def write_pair(name, root, body, overlay, accent, extra_css="", faces=(), under=""):
    """外部生成的卡片本体套滤镜（浅色去色，深色去色后反相）；自己画的底层、装饰和红章直接按模式换色，不进滤镜。"""
    own_css = BASE_CSS + KIRA_CSS + (JP.css() if JP else "") + extra_css
    font_css = "".join(f.css() for f in faces)
    for mode, flt in (("light", "mono"), ("dark", "night")):
        conv = (lambda t: t) if mode == "light" else to_night
        defs = conv(DEFS + BAND.replace("__BAND__", "0.8" if mode == "light" else "0.13"))
        acc = accent if mode == "light" else accent.replace(RED, NIGHT_RED)
        out = (f"{root}<style>{font_css}{conv(own_css)}</style><defs>{defs}</defs>{conv(under)}"
               f"<g filter=\"url(#{flt})\">{body}</g>{conv(overlay)}{acc}</svg>\n")
        (PROFILE / f"{name}-{mode}.svg").write_text(out, encoding="utf-8")
    print("wrote", name, "light/dark")


def card(name, label, jelly=None):
    path = PROFILE / f"{name}.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    if name == "stats":
        svg = fit_stats(svg, faces)
    w, h = size(svg)
    root, body = split(svg)
    lw = 17 * len(label) + 18
    write_pair(name, root, body, manga_overlay(w, h, len(name), jelly), stamp(w - lw - 14, 14, lw, 24, label, 14), faces=faces)


def trophy():
    path = PROFILE / "trophy.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    tw, th = size(svg)
    _, body = split(svg)
    spans, depth, start = [], 0, None
    for m in re.finditer(r"<svg\b|</svg>", body):
        if m.group() == "<svg":
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, m.end()))
    xs = []
    for k, (a, b) in reversed(list(enumerate(spans))):
        x = float(re.search(r'\bx="([\d.]+)"', body[a:a + 200]).group(1))
        xs.append(x)
        body = body[:a] + f'<g class="tb" style="animation-delay:{-k * 0.4:.2f}s;transform-origin:{x + 55:.0f}px 100px">' + body[a:b] + "</g>" + body[b:]
    xs.sort()
    L, T = 54, 46
    w, h = tw + L * 2, th + T + 40
    rng = random.Random(3)
    root = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="GitHub Trophies">'
    shelf_y = T + th + 4
    under = (f'<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="{PAPER}" /><rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" filter="url(#grain)" />'
             f'<rect x="2" y="2" width="{w - 4:.0f}" height="{T - 8}" fill="url(#toneFine)" opacity="0.2" />'
             f'<text x="{L}" y="27" class="tmeta">TROPHY CABINET  ·  SUMMER 2026</text>'
             f'<text x="{w - L:.0f}" y="27" class="tmeta" text-anchor="end">全 6 種  ·  COLLECT THEM ALL</text>'
             f'<rect x="{L - 16}" y="{shelf_y}" width="{tw + 32:.0f}" height="7" rx="1.5" fill="{PAPER}" stroke="{INK}" stroke-width="1.4" />'
             f'<rect x="{L - 12}" y="{shelf_y + 7}" width="{tw + 24:.0f}" height="12" fill="url(#hatch)" opacity="0.6" />'
             + "".join(f'<path d="M{x + L + 55:.0f} {shelf_y + 7}l-6 14h12z" fill="{INK}" opacity="0.7" />' for x in xs[::2]))
    body = f'<svg x="{L}" y="{T}" width="{tw:.0f}" height="{th:.0f}" viewBox="0 0 {tw:.0f} {th:.0f}">{body}</svg>'
    bursts = "".join(kira(L + x + 55 + rng.uniform(-38, 38), T + rng.uniform(4, 40), rng.uniform(9, 14), k * 0.4 + rng.uniform(0, 0.3)) for k, x in enumerate(xs))
    overlay = (f'<g pointer-events="none">{sweep(w, h, 0.0, 70)}{bursts}'
               f'{chime("tl", 26, 2, 0.62)}{chime("tr", round(w - 26), 2, 0.62, "風")}'
               f'{foam(rng, 18, L, w - L, shelf_y + 6, h - 6, 1.8, 4.5, (30, 90), 0.3)}'
               f'{petals(rng, 7, 40, w - 60, -10, h + 20)}'
               f'{sparkles([(L + x + 55 + 46, T + 70, 4, k * 0.5) for k, x in enumerate(xs)])}'
               f'<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="none" stroke="{INK}" stroke-width="3" />'
               f'<rect x="8" y="8" width="{w - 16:.0f}" height="{h - 16:.0f}" rx="3" fill="none" stroke="{INK}" stroke-width="0.7" /></g>')
    css = f"""
  .tb {{ animation: tbFloat 3.2s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }}
  @keyframes tbFloat {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 35% {{ transform: translateY(-4px) rotate(-1.5deg); }} 70% {{ transform: translateY(-1px) rotate(1deg); }} }}
  .tmeta {{ font: 400 10.5px {SERIF_STACK}, {MINCHO_STACK}; fill: {INK}; letter-spacing: 3px; }}
"""
    meta_font = load_font(SERIF, 400, "TROPHY CABINET · SUMMER 2026 COLLECT THEM ALL")
    write_pair("trophy", root, body, overlay, stamp(w / 2 - 34, 12, 68, 22, "実績", 13), css, list(faces) + ([meta_font] if meta_font else []), under)


def activity():
    path = PROFILE / "activity.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    w, h = size(svg)
    svg, n = re.subn(r'<path([^>]*class="ct-line")', r'<path id="zzLine" pathLength="1000"\1', svg, count=1)
    root, body = split(svg)
    css = ""
    if n:
        motion = '<animateMotion dur="9s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.45;1" calcMode="linear"><mpath href="#zzLine" /></animateMotion>'
        css = """
  .ct-line { stroke-dasharray: 1000; animation: zzDraw 9s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }
  .ct-area { animation: zzArea 9s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }
  @keyframes zzDraw { 0% { stroke-dashoffset: 1000; } 45%, 85% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: -1000; } }
  @keyframes zzArea { 0%, 10% { opacity: 0; } 45%, 85% { opacity: 1; } 100% { opacity: 0; } }
"""
        body += (f'<g><circle r="11" fill="none" stroke="{INK}" stroke-width="1"><animate attributeName="r" values="7;15;7" dur="1.2s" repeatCount="indefinite" />{motion}</circle>'
                 f'<circle r="5" fill="{PAPER}" stroke="{INK}" stroke-width="2">{motion}</circle></g>')
    write_pair("activity", root, body, manga_overlay(w, h, 7, (w - 70, 54, 0.55, 0.8, 0.6)), stamp(40, 22, 86, 26, "活動記録", 14), css, faces)


def snake():
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    svg = raw.read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', svg).group(1)
    sw, sh = size(svg)
    inner = svg[svg.index(">", svg.index("<svg")) + 1: svg.rfind("</svg>")]
    pad, top, foot = 26, 92, 40
    w, h = sw + pad * 2, sh + top + foot
    rng = random.Random(5)
    title_font = load_font(SERIF, 700, "Contribution Snake")
    film_font = load_font(SERIF, 400, "0123456789A▸ · GITHUB FILM 365")
    title, tl, tw = letters(title_font, "Contribution Snake", 28, pad + 96, 58, "zt float", step=0.06, anchor="start") if title_font else ("", 0, 0)
    jp_w = JP.width("草を食べる蛇・365日", 14, 4) if JP else 0
    jp = letters(JP, "草を食べる蛇・365日", 14, w - pad - jp_w - 110, 58, "zj", spacing=4, step=0, anchor="start")[0] if JP else ""
    root = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Contribution snake">'
    under = f"""<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="{PAPER}" />
<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" filter="url(#grain)" />
<rect x="2" y="2" width="{w - 4:.0f}" height="74" fill="url(#toneFine)" opacity="0.18" />
<line x1="2" y1="76" x2="{w - 2:.0f}" y2="76" stroke="{INK}" stroke-width="1.6" />
<line x1="2" y1="80" x2="{w - 2:.0f}" y2="80" stroke="{INK}" stroke-width="0.6" />"""
    body = f'<svg x="{pad}" y="{top}" width="{sw:.0f}" height="{sh:.0f}" viewBox="{view}">{inner}</svg>'
    bursts = "".join(kira(rng.uniform(pad + 20, w - pad - 20), rng.uniform(top + 10, top + sh - 10), rng.uniform(8, 12), k * 0.6) for k in range(5))
    overlay = (f'<g pointer-events="none">{sweep(w, 80, 1.0, 80)}'
               f'{title_fx(title, 2.5, 0.8)}{jp}'
               f'{chime("zs", round(w - 60), 2, 0.68)}{jellyfish("zj1", w - 150, 30, 0.3, 0.6, 0.45, 4)}'
               f'{bursts}'
               f'{foam(rng, 14, pad, w - pad, h - foot - 10, h - foot, 1.8, 4.5, (30, 120), 0.3)}'
               f'{petals(rng, 9, 20, w - 80, 70, h)}'
               f'{sparkles([(pad + 14, 30, 5, 0.2), (w * 0.55, 24, 4, 1.4), (w - 24, h - foot - 14, 5, 2.4)])}'
               f'<g clip-path="url(#zclip)">{film_strip(h - foot + 4, w, foot - 8, "GITHUB FILM 365")}</g>'
               f'<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="none" stroke="{INK}" stroke-width="3.2" /></g>')
    css = f"""
  .zt {{ font: 700 28px {SERIF_STACK}; fill: url(#zsheen); stroke: {PAPER}; stroke-width: 2.5px; paint-order: stroke; }}
  .zj {{ font: 800 14px {MINCHO_STACK}; fill: {INK}; }}
  .filmtxt {{ font: 400 9px {SERIF_STACK}; fill: {PAPER}; letter-spacing: 2.5px; }}
"""
    extra_defs = sheen_grad("zsheen", tl, tl + tw, 6.4, 2.0, 40) + f'<clipPath id="zclip"><rect x="3" y="3" width="{w - 6:.0f}" height="{h - 6:.0f}" rx="5" /></clipPath>'
    write_pair("snake", root, body, f"<defs>{extra_defs}</defs>" + overlay, stamp(pad, 38, 76, 28, "連載中", 15), css,
               [f for f in (title_font, film_font) if f], under)


if __name__ == "__main__":
    card("stats", "能力値")
    card("top-langs", "言語")
    card("pin-typewriter-nocturne", "推し", (356, 92, 0.32, 0.5, 0.4))
    card("pin-yohaku", "推し", (356, 92, 0.32, 1.6, 0.4))
    trophy()
    activity()
    snake()

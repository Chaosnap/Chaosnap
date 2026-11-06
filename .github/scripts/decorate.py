#!/usr/bin/env python3
"""把 Action 生成的卡片改成黑白漫画风，并各出浅色、深色两版，由 PersonalStatus.yml 调用。

原始卡片（stats.svg 等）保持不动，每次都从它生成 *-light.svg / *-dark.svg：
- 字体换成内嵌的 Playfair Display；整张去色，深色版再反相到 me 站点的夜间配色
- 加双线框、网点角、泡沫、樱花、小水母和红色印章标签
- 奖杯各自浮动；活动图折线反复描出；贪吃蛇包进一格漫画
"""
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (BASE_CSS, DEFS, INK, MINCHO, MINCHO_STACK, PAPER, SERIF, SERIF_STACK, bubbles, jellyfish,  # noqa: E402
                   letters, load_font, petals, sparkles, stamp, star)

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


def manga_overlay(w, h, seed, jelly=None, left_bubbles=True):
    """墨层上的装饰：内框细线、右上角网点、泡沫、樱花、星光，可选一只小水母。"""
    rng = random.Random(seed)
    corner = f'<path d="M{w - 90:.0f} 1L{w - 1:.0f} 1L{w - 1:.0f} {min(90, h * 0.6):.0f}Z" fill="url(#toneFine)" opacity="0.45" />'
    jf = jellyfish(f"c{seed}", *jelly, seed) if jelly else ""
    return (f'<g pointer-events="none">'
            f'<rect x="5" y="5" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.8" />'
            f'{corner}{jf}'
            f'{bubbles(rng, 6, 10, w * 0.22, h * 0.7, h, 2.2, 5, (h * 0.35, h * 0.75)) if left_bubbles else ""}'
            f'{bubbles(rng, 5, w * 0.8, w - 10, h * 0.7, h, 2.2, 5, (h * 0.35, h * 0.75))}'
            f'{petals(rng, 3, w * 0.1, w * 0.9, -10, h + 20)}'
            f'{sparkles([(w - 26, 24, 5, 0), (w - 48, 40, 3.5, 1.2)])}</g>')


def write_pair(name, root, body, overlay, accent, extra_css="", faces=()):
    """浅色版去色，深色版去色后反相。印章等彩色层在滤镜外面。"""
    css = BASE_CSS + "".join(f.css() for f in faces) + (JP.css() if JP else "") + extra_css
    for mode, flt in (("light", "mono"), ("dark", "night")):
        out = f"{root}<style>{css}</style><defs>{DEFS}</defs><g filter=\"url(#{flt})\">{body}{overlay}</g>{accent}</svg>\n"
        (PROFILE / f"{name}-{mode}.svg").write_text(out, encoding="utf-8")
    print("wrote", name, "light/dark")


def card(name, label, jelly=None, left_bubbles=True):
    path = PROFILE / f"{name}.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    if name == "stats":
        svg = fit_stats(svg, faces)
    w, h = size(svg)
    root, body = split(svg)
    lw = 17 * len(label) + 18
    write_pair(name, root, body, manga_overlay(w, h, len(name), jelly, left_bubbles), stamp(w - lw - 14, 14, lw, 24, label, 14), faces=faces)


def trophy():
    path = PROFILE / "trophy.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    root, body = split(svg)
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
    for k, (a, b) in reversed(list(enumerate(spans))):
        x = float(re.search(r'\bx="([\d.]+)"', body[a:a + 200]).group(1))
        body = body[:a] + f'<g class="tb" style="animation-delay:{-k * 0.35:.2f}s;transform-origin:{x + 55:.0f}px 55px">' + body[a:b] + "</g>" + body[b:]
    w, _ = size(svg)
    css = """
  .tb { animation: tbFloat 3s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }
  @keyframes tbFloat { 0%, 100% { transform: translateY(0) rotate(0deg); } 35% { transform: translateY(-4px) rotate(-1.5deg); } 70% { transform: translateY(-1px) rotate(1deg); } }
"""
    overlay = sparkles([(a + 100, 12, 4.5, i * 0.45) for i, a in enumerate(range(0, int(w), 120))])
    write_pair("trophy", root, body, overlay, "", css, faces)


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
    pad, top, foot = 26, 92, 30
    w, h = sw + pad * 2, sh + top + foot
    rng = random.Random(5)
    title_font = load_font(SERIF, 700, "Contribution Snake")
    title = letters(title_font, "Contribution Snake", 28, pad + 96, 58, "zt float", step=0.06, anchor="start")[0] if title_font else ""
    jp_w = JP.width("草を食べる蛇・365日", 14, 4) if JP else 0
    jp = letters(JP, "草を食べる蛇・365日", 14, w - pad - jp_w - 110, 58, "zj", spacing=4, step=0, anchor="start")[0] if JP else ""
    root = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Contribution snake">'
    body = f"""<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="{PAPER}" />
<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" filter="url(#grain)" />
<rect x="2" y="2" width="{w - 4:.0f}" height="74" fill="url(#toneFine)" opacity="0.18" />
<line x1="2" y1="76" x2="{w - 2:.0f}" y2="76" stroke="{INK}" stroke-width="1.6" />
<line x1="2" y1="80" x2="{w - 2:.0f}" y2="80" stroke="{INK}" stroke-width="0.6" />
{title}
{jp}
<svg x="{pad}" y="{top}" width="{sw:.0f}" height="{sh:.0f}" viewBox="{view}">{inner}</svg>
<rect x="2" y="2" width="{w - 4:.0f}" height="{h - 4:.0f}" rx="6" fill="none" stroke="{INK}" stroke-width="3.2" />"""
    overlay = (manga_overlay(w, h, 11, (w - 70, 30, 0.5, 0.45, 0.4))
               + f'<g>{bubbles(rng, 8, w * 0.3, w * 0.7, h - 40, h - 10, 2, 4.5, (40, 80))}</g>')
    css = f"""
  .zt {{ font: 700 28px {SERIF_STACK}; fill: {INK}; }}
  .zj {{ font: 800 14px {MINCHO_STACK}; fill: {INK}; }}
"""
    write_pair("snake", root, body, overlay, stamp(pad, 38, 76, 28, "連載中", 15), css, [title_font] if title_font else [])


if __name__ == "__main__":
    card("stats", "能力値")
    card("top-langs", "言語")
    card("pin-typewriter-nocturne", "推し", (356, 92, 0.32, 0.5, 0.4), False)
    card("pin-yohaku", "推し", (356, 92, 0.32, 1.6, 0.4), False)
    trophy()
    activity()
    snake()

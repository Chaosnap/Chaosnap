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
from manga import (BASE_CSS, DEFS, EASE, EASE_OUT, INK, MINCHO, MINCHO_STACK, NIGHT_RED, PAPER, RED, SERIF, SERIF_STACK,  # noqa: E402
                   chime, film_strip, foam, jellyfish, letters, load_font, petals, sheen_grad, sparkles, stamp, title_fx, to_night)

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "profile"
SANS_CSS = re.compile(r"""(['"])Segoe UI\1,\s*Ubuntu,(\s*"Helvetica Neue",)?\s*Sans-Serif""")
SANS_ATTR = re.compile(r'font-family="[^"]*Segoe UI[^"]*"')
LABELS = "能力値言語推し活動記録連載中草を食べる蛇・365日実績一年分の草を食べる白蛇、草はまた生える"
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
  .comet {{ animation: comet linear infinite; }}
  .comet.head {{ stroke-dasharray: 70 930; }}
  .comet.tail {{ stroke-dasharray: 160 840; opacity: 0.22; }}
  @keyframes comet {{ from {{ stroke-dashoffset: 1000; }} to {{ stroke-dashoffset: 0; }} }}
  .rip {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: rip 2.4s {EASE_OUT} infinite; }}
  @keyframes rip {{ 0% {{ opacity: 0; transform: scale(1); }} 10% {{ opacity: 0.8; }} 100% {{ opacity: 0; transform: scale(var(--s, 2.4)); }} }}
  .orbit {{ animation: spin 19.2s linear infinite; }}
  .orbit2 {{ animation: spin 4.8s linear infinite; }}
  .barglint {{ animation: barglint 3.2s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }}
  @keyframes barglint {{ 0% {{ transform: translateX(0); }} 60%, 100% {{ transform: translateX(var(--len)); }} }}
  @keyframes sweep {{ 0% {{ transform: translateX(0); }} 45%, 100% {{ transform: translateX(var(--len)); }} }}
"""
BAND = ('<linearGradient id="band" x1="0" x2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0" />'
        '<stop offset="0.5" stop-color="#ffffff" stop-opacity="__BAND__" /><stop offset="1" stop-color="#ffffff" stop-opacity="0" /></linearGradient>'
        '<linearGradient id="band2" x1="0" x2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0" />'
        '<stop offset="0.5" stop-color="#ffffff" stop-opacity="0.85" /><stop offset="1" stop-color="#ffffff" stop-opacity="0" /></linearGradient>')



def walk(svg):
    """遍历卡片 SVG，累加 translate 和内嵌 <svg> 的 x/y，返回 [(标签, 元素, 绝对 x, 绝对 y)]。"""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg)
    out = []

    def rec(el, ox, oy):
        m = re.match(r"translate\(\s*([-\d.]+)[\s,]+([-\d.]+)\s*\)", el.get("transform") or "")
        if m:
            ox, oy = ox + float(m.group(1)), oy + float(m.group(2))
        tag = el.tag.split("}")[-1]
        if tag == "svg" and el is not root:
            ox, oy = ox + float(el.get("x", 0)), oy + float(el.get("y", 0))
        out.append((tag, el, ox, oy))
        for c in el:
            rec(c, ox, oy)
    rec(root, 0.0, 0.0)
    return out


def comet(w, h, dur=9.6, delay=0.0, inset=5):
    """跑马灯：两道红光沿着内框一圈圈地跑，后面拖着淡淡的墨色尾巴。"""
    box = f'x="{inset}" y="{inset}" width="{w - 2 * inset:.0f}" height="{h - 2 * inset:.0f}" rx="3" pathLength="1000" fill="none" stroke-linecap="round"'
    out = []
    for k in (0, 0.5):
        d = delay + k * dur
        out.append(f'<rect {box} class="comet tail" stroke="{INK}" stroke-width="1.6" style="animation-duration:{dur}s;animation-delay:{-d:.2f}s" />'
                   f'<rect {box} class="comet head" stroke="{RED}" stroke-width="2.4" style="animation-duration:{dur}s;animation-delay:{-(d + dur * 0.09):.2f}s" />')
    return "".join(out)


def ripples(x, y, r, n=3, dur=2.4, delay=0.0, scale=2.4):
    return "".join(f'<circle class="rip" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{INK}" stroke-width="1" vector-effect="non-scaling-stroke" '
                   f'style="--s:{scale};animation-duration:{dur}s;animation-delay:{-(delay + dur * i / n):.2f}s" />' for i in range(n))


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


def card_motion(name, svg, w, h):
    """每张卡的专属动画：统计卡的段位圈有轨道和波纹，语言卡的色点脉动、进度条走光，置顶卡的语言点和星星。"""
    out = []
    nodes = walk(svg)
    for tag, el, ox, oy in nodes:
        cls = el.get("class") or ""
        tid = el.get("data-testid") or ""
        if tag == "circle" and cls == "rank-circle-rim":
            cx, cy = ox + float(el.get("cx", 0)), oy + float(el.get("cy", 0))
            out.append(f'<g transform="translate({cx:.1f} {cy:.1f})">'
                       f'<g class="orbit"><circle r="50" fill="none" stroke="{INK}" stroke-width="0.9" stroke-dasharray="1.5 5.5" /></g>'
                       f'<g class="orbit2"><circle cx="50" cy="0" r="3.2" fill="{RED}" /><circle cx="50" cy="0" r="6" fill="none" stroke="{RED}" stroke-width="0.8" opacity="0.6" /></g>'
                       f'<g class="orbit" style="animation-direction:reverse"><circle r="58" fill="none" stroke="{INK}" stroke-width="0.6" stroke-dasharray="26 18 4 18" opacity="0.6" /></g>'
                       f'</g>{ripples(cx, cy, 41, 3, 3.2, 0, 1.45)}')
        elif tag == "circle" and (el.get("r") in ("5", "6")) and (tid == "lang-color" or el.get("cx") == "5"):
            cx, cy = ox + float(el.get("cx", 0)), oy + float(el.get("cy", 0))
            out.append(ripples(cx, cy, float(el.get("r")), 2, 2.4, len(out) * 0.4, 2.6))
        elif tag == "rect" and tid == "lang-progress" and not any("barclip" in o for o in out):
            bx, by = ox, oy
            out.append(f'<clipPath id="barclip"><rect x="{bx:.1f}" y="{by:.1f}" width="250" height="8" rx="5" /></clipPath>'
                       f'<g clip-path="url(#barclip)"><g class="barglint" style="--len:320px"><rect x="{bx - 60:.1f}" y="{by - 2:.1f}" width="50" height="12" fill="url(#band2)" /></g></g>')
        elif tag == "svg" and "icon" in cls and any(t == "text" and (e.get("data-testid") == "stargazers") for t, e, _, _ in nodes):
            if el.find("{http://www.w3.org/2000/svg}path") is not None and "M8 .25" in (el.find("{http://www.w3.org/2000/svg}path").get("d") or ""):
                out.append(kira(ox + float(el.get("x", 0) or 0) + 8, oy + 8, 13, 0.6, 3.2))
    return "".join(out)


def manga_overlay(w, h, seed, jelly=None, foam_bottom=True, extra=""):
    """墨层上的装饰：内框细线、右上角网点、扫光、闪光、底边泡沫、樱花，可选一只小水母。"""
    rng = random.Random(seed)
    corner = f'<path d="M{w - 90:.0f} 1L{w - 1:.0f} 1L{w - 1:.0f} {min(90, h * 0.6):.0f}Z" fill="url(#toneFine)" opacity="0.45" />'
    jf = jellyfish(f"c{seed}", *jelly, seed) if jelly else ""
    bursts = "".join(kira(x, y, r, d) for x, y, r, d in [(w - 30, h - 26, 12, 0.3), (24, 22, 10, 1.5), (w * 0.62, 12, 8, 0.9)])
    return (f'<g pointer-events="none">'
            f'<rect x="5" y="5" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.8" />'
            f'{corner}{sweep(w, h, seed * 0.7)}{comet(w, h, 9.6, seed * 1.3)}{extra}{jf}{bursts}'
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
               f"<g filter=\"url(#{flt})\">{body}</g>{conv(overlay) if mode == 'light' else to_night(overlay).replace(RED, NIGHT_RED)}{acc}</svg>\n")
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
    write_pair(name, root, body, manga_overlay(w, h, len(name), jelly, extra=card_motion(name, svg, w, h)), stamp(w - lw - 14, 14, lw, 24, label, 14), faces=faces)


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
    overlay = (f'<g pointer-events="none">{sweep(w, h, 0.0, 70)}{comet(w, h, 12.8, 0, 8)}{bursts}'
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


def path_points(d):
    """chartist 折线只用 M 和 C：返回每段终点（数据点）处的累计弧长、总长。"""
    nums = [float(v) for v in re.findall(r"-?[\d.]+", d)]
    x, y = nums[0], nums[1]
    acc, marks, i = 0.0, [(x, y, 0.0)], 2
    while i + 5 < len(nums) + 1 and i + 6 <= len(nums):
        x1, y1, x2, y2, x3, y3 = nums[i:i + 6]
        px, py = x, y
        for t in (k / 24 for k in range(1, 25)):
            u = 1 - t
            qx = u ** 3 * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3
            qy = u ** 3 * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3
            acc += math.hypot(qx - px, qy - py)
            px, py = qx, qy
        x, y = x3, y3
        marks.append((x, y, acc))
        i += 6
    return marks, acc


def activity():
    path = PROFILE / "activity.svg"
    if not path.exists():
        return
    svg, faces = serif(path.read_text(encoding="utf-8"))
    w, h = size(svg)
    root, body = split(svg)
    m = re.search(r'<path d="([^"]+)"[^>]*class="ct-line"', svg)
    extra = ""
    if m:
        d = m.group(1)
        marks, total = path_points(d)
        dur = 9.6
        base_y = max(y for _, y, _ in marks)
        area = f'{d}L{marks[-1][0]:.1f} {base_y:.1f}L{marks[0][0]:.1f} {base_y:.1f}Z'
        rings = []
        top = sorted(range(len(marks)), key=lambda i: marks[i][1])[:3]
        for i, (x, y, a) in enumerate(marks):
            arrive = dur * a / total
            rings.append(f'<circle class="rip" cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{INK}" stroke-width="1.2" vector-effect="non-scaling-stroke" '
                         f'style="--s:2.8;animation-duration:{dur}s;animation-name:ripOnce;animation-delay:{arrive - dur:.2f}s" />')
            if i in top:
                rings.append(kira(x, y - 18, 16, dur - arrive, dur).replace('class="kira" style="animation-duration', 'class="kira kira1" style="animation-duration'))
        motion = f'<animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="paced" path="{d}" />'
        extra = (f'<path d="{area}" fill="url(#tone)" opacity="0.32" class="areaflow" />'
                 f'<path d="{d}" pathLength="1000" class="acomet halo" fill="none" stroke="{PAPER}" stroke-width="9" stroke-linecap="round" style="animation-duration:{dur}s" />'
                 f'<path d="{d}" pathLength="1000" class="acomet" fill="none" stroke="{RED}" stroke-width="3.4" stroke-linecap="round" style="animation-duration:{dur}s" />'
                 f'{"".join(rings)}'
                 f'<g><circle r="9" fill="none" stroke="{RED}" stroke-width="1" opacity="0.5">{motion}</circle><circle r="5" fill="{PAPER}" stroke="{RED}" stroke-width="2.2">{motion}</circle></g>')
    css = f"""
  .acomet {{ stroke-dasharray: 90 910; animation: acomet linear infinite; }}
  .acomet.halo {{ opacity: 0.9; }}
  @keyframes acomet {{ from {{ stroke-dashoffset: 90; }} to {{ stroke-dashoffset: -910; }} }}
  @keyframes ripOnce {{ 0% {{ opacity: 0; transform: scale(1); }} 1% {{ opacity: 0.9; }} 14%, 100% {{ opacity: 0; transform: scale(var(--s, 2.4)); }} }}
  .kira1 {{ animation-name: kiraOnce !important; }}
  @keyframes kiraOnce {{ 0% {{ opacity: 0; transform: scale(0.2); }} 2% {{ opacity: 1; }} 16%, 100% {{ opacity: 0; transform: scale(1) rotate(12deg); }} }}
"""
    write_pair("activity", root, body, manga_overlay(w, h, 7, (w - 70, 54, 0.55, 0.8, 0.6), extra=extra), stamp(40, 22, 86, 26, "活動記録", 14), css, faces)


# ---------------------------------------------------------------- 贪吃蛇：白蛇吃网点草，草过一会儿又长回来
LEVEL_R = [0, 2.3, 3.4, 4.5, 5.7]


def snake_data(svg):
    """从 snk 的 SVG 里取：周期、每格位置/等级/被吃的时刻、蛇头的路径关键帧。"""
    cycle = float(re.search(r"animation:none (?:linear )?(\d+)ms", svg).group(1)) / 1000
    level = {m.group(1): int(m.group(2)) for m in re.finditer(r"\.c\.(c\w+)\{fill:var\(--c(\d)\)", svg)}
    eaten = {m.group(1): float(m.group(2)) / 100 for m in re.finditer(r"@keyframes (c\w+)\{[^{]*\{[^}]*\}([\d.]+)%,100%", svg)}
    cells = []
    for m in re.finditer(r'<rect class="c(?: (c\w+))?" x="([\d.]+)" y="([\d.]+)"', svg):
        k = m.group(1)
        cells.append((float(m.group(2)) + 6, float(m.group(3)) + 6, level.get(k, 0), eaten.get(k)))
    body = svg[svg.index("@keyframes s0{"):]
    body = body[:body.index("}}") + 2]
    pts = []
    for keys, x, y in re.findall(r"([\d.,%]+)\{transform:translate\(([-\d.]+)px,([-\d.]+)px\)\}", body):
        for k in keys.split(","):
            pts.append((float(k.rstrip("%")), float(x) + 8, float(y) + 8))
    pts.sort()
    if pts[-1][0] < 100:
        pts.append((100.0, pts[0][1], pts[0][2]))
    return cycle, cells, pts


def snake_keyframes(pts):
    """蛇头：位置 + 朝向（转角处在 0.12% 内转过去，角度展开避免绕远路）；蛇身只要位置。"""
    pos = " ".join(f"{p:.2f}% {{ transform: translate({x:.1f}px, {y:.1f}px); }}" for p, x, y in pts)
    frames, prev = [], None
    for i, (p, x, y) in enumerate(pts):
        nxt = pts[i + 1] if i + 1 < len(pts) else pts[1]
        ang = math.degrees(math.atan2(nxt[2] - y, nxt[1] - x)) if (nxt[1], nxt[2]) != (x, y) else (prev if prev is not None else 0)
        if prev is not None:
            while ang - prev > 180:
                ang -= 360
            while ang - prev < -180:
                ang += 360
        before = prev if prev is not None else ang
        frames.append(f"{p:.2f}% {{ transform: translate({x:.1f}px, {y:.1f}px) rotate({before:.0f}deg); }}")
        if i + 1 < len(pts) and pts[i + 1][0] - p > 0.25:
            q = p + 0.12
            f = 0.12 / (pts[i + 1][0] - p)
            frames.append(f"{q:.2f}% {{ transform: translate({x + (nxt[1] - x) * f:.1f}px, {y + (nxt[2] - y) * f:.1f}px) rotate({ang:.0f}deg); }}")
        prev = ang
    return pos, " ".join(frames)


def snake():
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    svg = raw.read_text(encoding="utf-8")
    C, cells, pts = snake_data(svg)
    pad, top = 26, 92
    w, h = 932, 300
    gx, gy = 42, 118
    rng = random.Random(5)
    title_font = load_font(SERIF, 700, "Contribution Snake")
    small = load_font(SERIF, 400, "0123456789A▸ · GITHUB FILM 365 JanFebMarAprMayJunJulAugSepOctNovDec MonWedFri Less More")
    title, tl, tw = letters(title_font, "Contribution Snake", 28, pad + 96, 58, "zt float", step=0.06, anchor="start") if title_font else ("", 0, 0)
    jp_w = JP.width("草を食べる蛇・365日", 14, 4) if JP else 0
    jp = letters(JP, "草を食べる蛇・365日", 14, w - pad - jp_w - 110, 58, "zj", spacing=4, step=0, anchor="start")[0] if JP else ""
    root = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Contribution snake">'

    # 月份与星期
    import datetime
    today = datetime.date.today()
    cols = int(max(c[0] for c in cells) // 16) + 1
    months, last = [], None
    for k in range(cols):
        day = today - datetime.timedelta(weeks=cols - 1 - k)
        if day.month != last and k < cols - 2:
            months.append(f'<text class="zm" x="{gx + k * 16 + 2}" y="{gy - 12}">{day.strftime("%b")}</text>')
        last = day.month
    days = "".join(f'<text class="zm" x="{gx - 8}" y="{gy + r * 16 + 11}" text-anchor="end">{n}</text>' for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    grid = "".join(f"M{gx + x - 0.9:.1f} {gy + y:.1f}a0.9 0.9 0 1 0 1.8 0a0.9 0.9 0 1 0 -1.8 0" for x, y, _, _ in cells)
    grass, rings = [], []
    for x, y, lv, e in cells:
        if not lv:
            continue
        delay = (e if e is not None else 0) * C - C
        grass.append(f'<circle class="gd" cx="{gx + x:.1f}" cy="{gy + y:.1f}" r="{LEVEL_R[lv]}" style="animation-delay:{delay:.2f}s" />')
        rings.append(f'<circle class="gr" cx="{gx + x:.1f}" cy="{gy + y:.1f}" r="5" style="animation-delay:{delay:.2f}s" />')
    legend = "".join(f'<circle cx="{w - 150 + i * 16}" cy="{gy + 132}" r="{max(LEVEL_R[i], 1)}" fill="{INK}" opacity="{0.3 if i == 0 else 1}" />' for i in range(5))
    pos, head_kf = snake_keyframes(pts)
    beads = []
    n = 12
    for k in range(n, 0, -1):
        r = 6.3 - 3.6 * (k - 1) / (n - 1)
        beads.append(f'<g class="zb" style="animation-delay:{0.055 * k * 1.15 - C:.3f}s"><circle r="{r:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" />'
                     f'<circle r="{r * 0.5:.1f}" cx="{r * 0.18:.1f}" cy="{r * 0.18:.1f}" fill="url(#toneFine)" /></g>')
    head = (f'<g class="zh" style="animation-delay:{-C:.2f}s"><g class="tongue"><path d="M8 0H15.5M15.5 0l3.2 -2.6M15.5 0l3.2 2.6" fill="none" stroke="{RED}" stroke-width="1.3" stroke-linecap="round" /></g>'
            f'<path d="M-8.5 -6C-2 -8.6 6.5 -6.6 9.6 0C6.5 6.6 -2 8.6 -8.5 6C-10.4 2.4 -10.4 -2.4 -8.5 -6Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round" />'
            f'<path d="M-6 -3.4Q-3.6 0 -6 3.4" fill="none" stroke="{INK}" stroke-width="0.7" />'
            f'<circle cx="3.2" cy="-3.3" r="1.6" fill="{INK}" /><circle cx="3.2" cy="3.3" r="1.6" fill="{INK}" />'
            f'<circle cx="3.7" cy="-3.8" r="0.5" fill="{PAPER}" /><circle cx="3.7" cy="2.8" r="0.5" fill="{PAPER}" />'
            f'<ellipse cx="0.5" cy="-5.2" rx="1.6" ry="0.8" fill="{RED}" opacity="0.55" /><ellipse cx="0.5" cy="5.2" rx="1.6" ry="0.8" fill="{RED}" opacity="0.55" /></g>')
    under = f"""<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="6" fill="{PAPER}" />
<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="6" filter="url(#grain)" />
<rect x="2" y="2" width="{w - 4}" height="74" fill="url(#toneFine)" opacity="0.18" />
<line x1="2" y1="76" x2="{w - 2}" y2="76" stroke="{INK}" stroke-width="1.6" />
<line x1="2" y1="80" x2="{w - 2}" y2="80" stroke="{INK}" stroke-width="0.6" />
{"".join(months)}{days}
<path d="{grid}" fill="{INK}" opacity="0.28" />
<text class="zm" x="{w - 162}" y="{gy + 136}" text-anchor="end">Less</text>{legend}<text class="zm" x="{w - 72}" y="{gy + 136}">More</text>
<text class="zm" x="{gx}" y="{gy + 136}">SHIROHEBI  ·  一年分の草を食べる白蛇、草はまた生える</text>"""
    overlay = (f'<g pointer-events="none">{sweep(w, 80, 1.0, 80)}'
               f'{title_fx(title, 2.5, 0.8)}{jp}'
               f'{chime("zs", round(w - 60), 2, 0.68)}{jellyfish("zj1", w - 150, 30, 0.3, 0.6, 0.45, 4)}'
               f'<g>{"".join(grass)}</g><g>{"".join(rings)}</g>'
               f'<g transform="translate({gx} {gy})">{"".join(beads)}{head}</g>'
               f'{petals(rng, 6, 20, w - 80, 70, h - 40)}'
               f'{sparkles([(pad + 14, 30, 5, 0.2), (w * 0.55, 24, 4, 1.4), (w - 24, h - 50, 5, 2.4)])}'
               f'<g clip-path="url(#zclip)">{film_strip(h - 34, w, 30, "GITHUB FILM 365")}</g>'
               f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="6" fill="none" stroke="{INK}" stroke-width="3.2" /></g>')
    css = f"""
  .zt {{ font: 700 28px {SERIF_STACK}; fill: url(#zsheen); stroke: {PAPER}; stroke-width: 2.5px; paint-order: stroke; }}
  .zj {{ font: 800 14px {MINCHO_STACK}; fill: {INK}; }}
  .zm {{ font: 400 9.5px {SERIF_STACK}, {MINCHO_STACK}; fill: {INK}; opacity: 0.7; letter-spacing: 1px; }}
  .filmtxt {{ font: 400 9px {SERIF_STACK}; fill: {PAPER}; letter-spacing: 2.5px; }}
  .gd {{ fill: {INK}; transform-box: fill-box; transform-origin: center; animation: gd {C}s linear infinite; }}
  @keyframes gd {{ 0% {{ transform: scale(1); opacity: 1; animation-timing-function: {EASE_OUT}; }} 1.4% {{ transform: scale(1.9); opacity: 0; }}
    28% {{ transform: scale(0); opacity: 0; animation-timing-function: {EASE_OUT}; }} 31% {{ transform: scale(1.18); opacity: 1; }} 33%, 100% {{ transform: scale(1); opacity: 1; }} }}
  .gr {{ fill: none; stroke: {INK}; stroke-width: 1; transform-box: fill-box; transform-origin: center; opacity: 0; animation: gr {C}s linear infinite; }}
  @keyframes gr {{ 0% {{ opacity: 0; transform: scale(0.4); animation-timing-function: {EASE_OUT}; }} 0.3% {{ opacity: 0.9; }} 3.5% {{ opacity: 0; transform: scale(2.8); }} 100% {{ opacity: 0; }} }}
  .zb {{ animation: zb {C}s linear infinite; }}
  @keyframes zb {{ {pos} }}
  .zh {{ animation: zh {C}s linear infinite; }}
  @keyframes zh {{ {head_kf} }}
  .tongue {{ transform-origin: 8px 0; animation: tongue 1.6s {EASE} infinite; }}
  @keyframes tongue {{ 0%, 55% {{ transform: scaleX(0); }} 65% {{ transform: scaleX(1); }} 72% {{ transform: scaleX(0.35); }} 80% {{ transform: scaleX(1); }} 92%, 100% {{ transform: scaleX(0); }} }}
"""
    extra_defs = sheen_grad("zsheen", tl, tl + tw, 6.4, 2.0, 40) + f'<clipPath id="zclip"><rect x="3" y="3" width="{w - 6}" height="{h - 6}" rx="5" /></clipPath>'
    write_pair("snake", root, "", f"<defs>{extra_defs}</defs>" + overlay, stamp(pad, 38, 76, 28, "連載中", 15), css,
               [f for f in (title_font, small) if f], under)


if __name__ == "__main__":
    card("stats", "能力値")
    card("top-langs", "言語")
    card("pin-typewriter-nocturne", "推し", (352, 84, 0.4, 0.5, 0.45))
    card("pin-yohaku", "推し", (352, 84, 0.4, 1.6, 0.45))
    trophy()
    activity()
    snake()

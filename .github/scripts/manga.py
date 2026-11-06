"""漫画风（週刊ユキ）共用部件：字体子集嵌入、配色、浅色/深色两版输出，以及水母、风铃、泡沫、樱花、雨伞等线稿。

所有图都先按浅色（纸白墨黑）画；深色版把“墨”层套上 night 滤镜反相成白线墨底，
红色印章和青、品红的印刷错版层不反相。make_art.py 和 decorate.py 都用这里的东西。
"""
import base64
import math
import random
import re
import struct
import urllib.parse
import urllib.request
from html import escape

# 与 me 站点（週刊ユキ）同一套色：纸、墨、红、错版青/品红
PAPER, INK, GRAY, TONE_GRAY, RED, CYAN, MAGENTA = "#f3f1ee", "#15171d", "#8b8d95", "#d8d6d1", "#e5383b", "#2fb6d6", "#e53878"
SERIF = "Playfair Display"
MINCHO = "Shippori Mincho B1"
SERIF_STACK = "'Playfair Display', Georgia, 'Times New Roman', serif"
MINCHO_STACK = "'Shippori Mincho B1', 'Hiragino Mincho ProN', 'Yu Mincho', serif"
EASE = "cubic-bezier(0.45, 0.05, 0.55, 0.95)"
EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)"


class Font:
    """读 TrueType 的 cmap / hmtx，算字宽；css() 生成内嵌的 @font-face。"""

    def __init__(self, family, weight, data):
        self.family, self.weight, self.data = family, weight, data
        d = data
        tables = {}
        for i in range(struct.unpack(">H", d[4:6])[0]):
            tag, _, off, _ = struct.unpack(">4sIII", d[12 + 16 * i:28 + 16 * i])
            tables[tag.decode("latin1")] = off
        self.upem = struct.unpack(">H", d[tables["head"] + 18:tables["head"] + 20])[0]
        hh = tables["hhea"]
        nh = struct.unpack(">H", d[hh + 34:hh + 36])[0]
        hm = tables["hmtx"]
        self.adv = [struct.unpack(">H", d[hm + 4 * i:hm + 4 * i + 2])[0] for i in range(nh)]
        self.cmap = self._cmap(tables["cmap"])

    def _cmap(self, off):
        d = self.data
        best = None
        for i in range(struct.unpack(">H", d[off + 2:off + 4])[0]):
            _, _, sub = struct.unpack(">HHI", d[off + 4 + 8 * i:off + 12 + 8 * i])
            fmt = struct.unpack(">H", d[off + sub:off + sub + 2])[0]
            if fmt == 12 or (fmt == 4 and best is None):
                best = (off + sub, fmt)
        o, fmt = best
        m = {}
        if fmt == 12:
            for g in range(struct.unpack(">I", d[o + 12:o + 16])[0]):
                s, e, sg = struct.unpack(">III", d[o + 16 + 12 * g:o + 28 + 12 * g])
                for c in range(s, e + 1):
                    m[c] = sg + c - s
            return m
        seg2 = struct.unpack(">H", d[o + 6:o + 8])[0]
        ends, starts = o + 14, o + 16 + seg2
        deltas, ranges = starts + seg2, starts + 2 * seg2
        for i in range(seg2 // 2):
            e, s = (struct.unpack(">H", d[p + 2 * i:p + 2 * i + 2])[0] for p in (ends, starts))
            delta = struct.unpack(">h", d[deltas + 2 * i:deltas + 2 * i + 2])[0]
            ro = struct.unpack(">H", d[ranges + 2 * i:ranges + 2 * i + 2])[0]
            for c in range(s, e + 1):
                if c == 0xFFFF:
                    continue
                if ro == 0:
                    m[c] = (c + delta) & 0xFFFF
                else:
                    a = ranges + 2 * i + ro + 2 * (c - s)
                    g = struct.unpack(">H", d[a:a + 2])[0]
                    m[c] = (g + delta) & 0xFFFF if g else 0
        return m

    def advance(self, ch, size):
        g = self.cmap.get(ord(ch), 0)
        return self.adv[min(g, len(self.adv) - 1)] * size / self.upem

    def width(self, text, size, spacing=0.0):
        return sum(self.advance(c, size) + spacing for c in text) - spacing

    def css(self):
        data = base64.b64encode(self.data).decode()
        return (f"@font-face {{ font-family: '{self.family}'; font-weight: {self.weight}; font-style: normal; "
                f"src: url(data:font/ttf;base64,{data}) format('truetype'); }}")


def load_font(family, weight, text):
    """只取 text 里的字。返回 None 表示取不到（离线等），调用方退回系统衬线体。"""
    chars = "".join(sorted(set(text + " ")))
    url = ("https://fonts.googleapis.com/css2?family=" + family.replace(" ", "+")
           + f":wght@{weight}&text=" + urllib.parse.quote(chars))
    try:
        css = urllib.request.urlopen(url, timeout=30).read().decode()
        src = re.search(r"url\((https://[^)]+)\) format\('truetype'\)", css).group(1)
        return Font(family, weight, urllib.request.urlopen(src, timeout=30).read())
    except Exception as exc:  # noqa: BLE001
        print(f"font {family} {weight} unavailable: {exc}")
        return None


def letters(font, text, size, cx, y, cls, spacing=0.0, step=0.11, anchor="middle"):
    """每个字一个 <text>，用真实字宽排好，方便逐字做动画。返回 (svg, 左端 x, 宽度)。"""
    w = font.width(text, size, spacing)
    x = cx - w / 2 if anchor == "middle" else cx
    left = x
    out = []
    for i, ch in enumerate(text):
        if ch != " ":
            out.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" style="--i:{i};animation-delay:{i * step:.2f}s, {i * step:.2f}s">{escape(ch)}</text>')
        x += font.advance(ch, size) + spacing
    return "".join(out), left, w



def letters(font, text, size, cx, y, cls, spacing=0.0, step=0.11, anchor="middle"):
    """每个字一个 <text>，按真实字宽排好，方便逐字做动画。返回 (svg, 左端 x, 宽度)。"""
    w = font.width(text, size, spacing)
    x = cx - w / 2 if anchor == "middle" else cx
    left = x
    out = []
    for i, ch in enumerate(text):
        if ch != " ":
            out.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" style="animation-delay:{i * step:.2f}s">{escape(ch)}</text>')
        x += font.advance(ch, size) + spacing
    return "".join(out), left, w


class Art:
    """按层组织一张图：ink 层在深色版里反相，color 层保持原色。"""

    def __init__(self, w, h, label="", role="img"):
        self.w, self.h, self.label, self.role = w, h, label, role
        self.css, self.defs, self.layers = [], [DEFS], []

    def ink(self, svg):
        self.layers.append(("ink", svg))

    def color(self, svg):
        self.layers.append(("color", svg))

    def render(self, mode):
        body = []
        for kind, svg in self.layers:
            if kind == "ink" and mode == "dark":
                body.append(f'<g filter="url(#night)">{svg}</g>')
            else:
                body.append(svg)
        aria = f'role="img" aria-label="{escape(self.label)}"' if self.role == "img" else 'role="presentation"'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" {aria}>\n<style>{BASE_CSS}{"".join(self.css)}</style>\n<defs>{"".join(self.defs)}</defs>\n'
                + "\n".join(body) + "\n</svg>\n")

    def write(self, folder, name):
        for mode in ("light", "dark"):
            (folder / f"{name}-{mode}.svg").write_text(self.render(mode), encoding="utf-8")


# 深色版：先去色，再把纸白映射成墨底、墨黑映射成纸白
NIGHT = ('<filter id="night" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0" />'
         '<feComponentTransfer><feFuncR type="linear" slope="-1.003" intercept="1.011" /><feFuncG type="linear" slope="-0.955" intercept="1.0" />'
         '<feFuncB type="linear" slope="-0.891" intercept="0.979" /></feComponentTransfer></filter>')
MONO = '<filter id="mono" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0" /></filter>'

DEFS = f"""
  {NIGHT}
  {MONO}
  <pattern id="tone" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="2.5" cy="2.5" r="1.05" fill="{INK}" /></pattern>
  <pattern id="toneFine" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="1.7" cy="1.7" r="0.62" fill="{INK}" /></pattern>
  <pattern id="toneBig" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="4" cy="4" r="2.2" fill="{INK}" /></pattern>
  <pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)"><line x1="0" y1="0" x2="0" y2="4" stroke="{INK}" stroke-width="0.7" /></pattern>
  <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" />
    <feColorMatrix values="0 0 0 0 0.08  0 0 0 0 0.08  0 0 0 0 0.08  0 0 0 0.09 0" /></filter>
  <linearGradient id="fadeDown" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="1" stop-color="#fff" /></linearGradient>
  <linearGradient id="fadeRight" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="1" stop-color="#fff" /></linearGradient>
  <mask id="toneDown"><rect x="-10%" y="-10%" width="120%" height="120%" fill="url(#fadeDown)" /></mask>"""

BASE_CSS = f"""
  .float {{ transform-box: fill-box; transform-origin: center bottom; animation: float 4.2s {EASE} infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 35% {{ transform: translateY(-5px) rotate(-1.4deg); }} 70% {{ transform: translateY(-1.5px) rotate(1deg); }} }}
  .cmy-c {{ animation: misC 5.5s {EASE} infinite; }}
  .cmy-m {{ animation: misM 5.5s {EASE} infinite; }}
  @keyframes misC {{ 0%, 100% {{ transform: translate(-1.6px, 0.4px); }} 50% {{ transform: translate(-2.6px, 1px); }} 88% {{ transform: translate(-1.6px, 0.4px); }} 90% {{ transform: translate(-6px, 1px); }} 92% {{ transform: translate(-1.6px, 0.4px); }} }}
  @keyframes misM {{ 0%, 100% {{ transform: translate(1.6px, -0.4px); }} 50% {{ transform: translate(2.4px, -1px); }} 88% {{ transform: translate(1.6px, -0.4px); }} 90% {{ transform: translate(6px, -1px); }} 92% {{ transform: translate(1.6px, -0.4px); }} }}
  .jf {{ animation: jfDrift 7s {EASE} infinite; }}
  @keyframes jfDrift {{ 0%, 100% {{ transform: translate(0, 0) rotate(-3deg); }} 45% {{ transform: translate(4px, -14px) rotate(3deg); }} }}
  .jf-bell {{ animation: jfPulse 3.4s infinite; }}
  @keyframes jfPulse {{
    0% {{ transform: scale(1, 1); animation-timing-function: {EASE_OUT}; }}
    26% {{ transform: scale(1.09, 0.86); animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1); }}
    100% {{ transform: scale(1, 1); }}
  }}
  .jf-thrust {{ animation: jfThrust 3.4s infinite; }}
  @keyframes jfThrust {{
    0% {{ transform: translateY(0); animation-timing-function: {EASE_OUT}; }}
    30% {{ transform: translateY(-9px); animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1); }}
    100% {{ transform: translateY(0); }}
  }}
  .chime {{ animation: chimeSwing 3.8s {EASE} infinite; }}
  .chime-paper {{ animation: paperSwing 3.8s {EASE} infinite; animation-delay: -0.5s; }}
  @keyframes chimeSwing {{ 0%, 100% {{ transform: rotate(5deg); }} 50% {{ transform: rotate(-5deg); }} }}
  @keyframes paperSwing {{ 0%, 100% {{ transform: rotate(13deg); }} 50% {{ transform: rotate(-13deg); }} }}
  .bub-rise {{ animation: bubRise linear infinite; }}
  .bub-wob {{ animation: bubWob 2.4s {EASE} infinite alternate; }}
  @keyframes bubRise {{ 0% {{ opacity: 0; transform: translateY(0); }} 12% {{ opacity: 1; }} 82% {{ opacity: 1; }} 100% {{ opacity: 0; transform: translateY(var(--rise, -120px)); }} }}
  @keyframes bubWob {{ from {{ transform: translateX(-5px); }} to {{ transform: translateX(5px); }} }}
  .petal-fall {{ animation: petalFall linear infinite; }}
  .petal-flip {{ animation: petalFlip 1.9s {EASE} infinite alternate; }}
  @keyframes petalFall {{ 0% {{ opacity: 0; transform: translate(0, -20px) rotate(0deg); }} 10% {{ opacity: 1; }} 88% {{ opacity: 1; }} 100% {{ opacity: 0; transform: translate(var(--dx, 80px), var(--fall, 300px)) rotate(var(--spin, 300deg)); }} }}
  @keyframes petalFlip {{ from {{ transform: scaleX(1) rotate(-10deg); }} to {{ transform: scaleX(-0.35) rotate(18deg); }} }}
  .umbrella {{ animation: umbrella 5.2s {EASE} infinite; }}
  @keyframes umbrella {{ 0%, 100% {{ transform: rotate(-5deg) translateY(0); }} 50% {{ transform: rotate(4deg) translateY(-4px); }} }}
  .focus-a {{ animation: focusA 0.36s steps(1) infinite; }}
  .focus-b {{ animation: focusB 0.36s steps(1) infinite; }}
  @keyframes focusA {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
  @keyframes focusB {{ 0%, 49% {{ opacity: 0; }} 50%, 100% {{ opacity: 1; }} }}
  .draw {{ stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: draw 2.2s 0.3s {EASE} forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  .pop {{ transform-box: fill-box; transform-origin: center bottom; animation: pop 4.8s {EASE} infinite; }}
  @keyframes pop {{ 0%, 100% {{ transform: scale(1) rotate(0deg); }} 8% {{ transform: scale(1.08) rotate(-3deg); }} 16% {{ transform: scale(0.98) rotate(1deg); }} 24% {{ transform: scale(1) rotate(0deg); }} }}
  .rain {{ animation: rain 0.55s linear infinite; }}
  @keyframes rain {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(-14px, 56px); }} }}
  .drop {{ animation: drop 2.6s cubic-bezier(0.55, 0, 1, 0.45) infinite; }}
  @keyframes drop {{ 0%, 55% {{ opacity: 0; transform: translateY(0) scale(0.4); }} 62% {{ opacity: 1; transform: translateY(0) scale(1); }} 100% {{ opacity: 0; transform: translateY(70px) scale(1); }} }}
  .ripple {{ transform-box: fill-box; transform-origin: center; animation: ripple 2.2s {EASE_OUT} infinite; }}
  @keyframes ripple {{ 0% {{ opacity: 0.9; transform: scale(0.1); }} 100% {{ opacity: 0; transform: scale(1); }} }}
  .cy {{ fill: {CYAN} !important; }}
  .mg {{ fill: {MAGENTA} !important; }}
  .twinkle {{ transform-box: fill-box; transform-origin: center; animation: twinkle 3.2s {EASE} infinite; }}
  @keyframes twinkle {{ 0%, 100% {{ opacity: 0.15; transform: scale(0.5) rotate(0deg); }} 50% {{ opacity: 1; transform: scale(1.1) rotate(45deg); }} }}
"""


# ---------------------------------------------------------------- 曲线工具
def smooth(pts):
    """Catmull-Rom 转三次贝塞尔：点之间平滑连接，点数相同的两组可以做形状变形。"""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def morph(states, dur, delay=0.0):
    """在几组同结构的 d 之间平滑往返。"""
    vals = states + [states[0]]
    n = len(vals) - 1
    times = ";".join(f"{i / n:.3f}" for i in range(n + 1))
    splines = ";".join(["0.45 0.05 0.55 0.95"] * n)
    return (f'<animate attributeName="d" dur="{dur}s" begin="{-delay:.2f}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="{times}" keySplines="{splines}" values="{";".join(vals)}" />')


def star(x, y, r):
    k = r * 0.12
    return (f"M{x:.1f} {y - r:.1f}C{x + k:.1f} {y - k:.1f} {x + k:.1f} {y - k:.1f} {x + r:.1f} {y:.1f}"
            f"C{x + k:.1f} {y + k:.1f} {x + k:.1f} {y + k:.1f} {x:.1f} {y + r:.1f}"
            f"C{x - k:.1f} {y + k:.1f} {x - k:.1f} {y + k:.1f} {x - r:.1f} {y:.1f}"
            f"C{x - k:.1f} {y - k:.1f} {x - k:.1f} {y - k:.1f} {x:.1f} {y - r:.1f}Z")


def sparkles(points):
    return "".join(f'<path class="twinkle" d="{star(x, y, r)}" fill="{INK}" style="animation-delay:{d}s" />' for x, y, r, d in points)


# ---------------------------------------------------------------- 水母
def jellyfish(uid, x, y, s=1.0, delay=0.0, reach=1.0, seed=1):
    """线稿水母：扇贝边的伞、内层伞、四叶生殖腺、网点阴影、高光；
    四条褶边口腕和十一根细触手用形状变形摆动，伞体以缘为轴收缩推进。"""
    rng = random.Random(seed)
    R, n = 32, 9
    xs = [R - 2 * R * i / n for i in range(n + 1)]
    bell = f"M{-R} 0C{-R} -28 -18 -44 0 -44C18 -44 {R} -28 {R} 0" + "".join(
        f"Q{(xs[i] + xs[i + 1]) / 2:.1f} 7 {xs[i + 1]:.1f} 0" for i in range(n)) + "Z"
    inner = f"M{-R + 8} -3C{-R + 8} -23 -13 -35 0 -35C13 -35 {R - 8} -23 {R - 8} -3"
    gonads = "".join(
        f'<ellipse cx="{math.cos(a) * 7.5:.1f}" cy="{-18 + math.sin(a) * 5.5:.1f}" rx="5.6" ry="3.1" transform="rotate({math.degrees(a):.0f} {math.cos(a) * 7.5:.1f} {-18 + math.sin(a) * 5.5:.1f})" />'
        for a in (math.pi / 4 + k * math.pi / 2 for k in range(4)))
    rim_dots = "".join(f'<circle cx="{xx:.1f}" cy="0" r="0.9" />' for xx in xs[1:-1])

    def arm(x0, k, phase):
        L = 70 * reach * (0.85 + 0.1 * k)
        left, right = [], []
        for i in range(15):
            t = i / 14
            yy = 3 + t * L
            xc = x0 + math.sin(t * 2.4 * math.pi + phase + k) * (1.5 + 7 * t)
            wdt = (1.6 + 2.6 * math.sin(t * math.pi)) * (1 - 0.35 * t)
            frill = 1.3 * math.sin(t * 24 + phase * 2 + k)
            left.append((xc - wdt - frill, yy))
            right.append((xc + wdt + frill * 0.6, yy))
        r = smooth(right[::-1])
        return smooth(left) + "L" + r[1:] + "Z"

    def tentacle(x0, k, phase, L):
        pts = [(x0 + math.sin(t * 2 * math.pi * 1.2 + phase + k * 0.7) * (0.6 + 9 * t), 1 + t * L) for t in (i / 9 for i in range(10))]
        return smooth(pts)

    arms = "".join(
        f'<path d="{arm(x0, k, 0)}" fill="{PAPER}" fill-opacity="0.9" stroke="{INK}" stroke-width="0.9" stroke-linejoin="round">{morph([arm(x0, k, ph) for ph in (0, 1.7, 3.4)], 7.2, delay + k * 0.3)}</path>'
        for k, x0 in enumerate([-9, -3, 3, 9]))
    tents = []
    for k, x0 in enumerate(xs[1:-1:1]):
        L = rng.uniform(95, 150) * reach
        tents.append(f'<path d="{tentacle(x0, k, 0, L)}" fill="none" stroke="{INK}" stroke-width="{rng.uniform(0.45, 0.75):.2f}" stroke-linecap="round" opacity="{rng.uniform(0.55, 0.9):.2f}">'
                     f'{morph([tentacle(x0, k, ph, L) for ph in (0, 2.1, 4.2)], 6.4, delay + k * 0.21)}</path>')
    return f"""<g transform="translate({x} {y}) scale({s})"><g class="jf" style="animation-delay:{-delay:.2f}s"><g class="jf-thrust" style="animation-delay:{-delay:.2f}s">
  <g>{"".join(tents)}</g>
  <g>{arms}</g>
  <g class="jf-bell" style="animation-delay:{-delay:.2f}s">
    <clipPath id="bell{uid}"><path d="{bell}" /></clipPath>
    <path d="{bell}" fill="{PAPER}" fill-opacity="0.92" />
    <g clip-path="url(#bell{uid})"><rect x="3" y="-48" width="{R}" height="52" fill="url(#tone)" opacity="0.55" /><rect x="{-R}" y="-11" width="{2 * R}" height="14" fill="url(#toneFine)" opacity="0.6" /></g>
    <path d="{inner}" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.8" />
    <g fill="none" stroke="{INK}" stroke-width="0.9">{gonads}</g>
    <path d="{bell}" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round" />
    <g fill="{INK}">{rim_dots}</g>
    <path d="M-23 -24C-20 -33 -12 -39 -3 -40" fill="none" stroke="{PAPER}" stroke-width="2.8" stroke-linecap="round" />
    <path d="M-23 -24C-20 -33 -12 -39 -3 -40" fill="none" stroke="{INK}" stroke-width="0.5" stroke-linecap="round" opacity="0.6" transform="translate(1.6 1.6)" />
  </g>
</g></g></g>"""


# ---------------------------------------------------------------- 风铃
def chime(uid, x, y, s=1.0, kanji="涼"):
    """线稿风铃：玻璃铃（网点阴影、高光）、金鱼、红绳、玻璃珠、短册；短册比铃慢半拍。"""
    def p(dx, dy):
        return f"{x + dx * s:.1f} {y + dy * s:.1f}"
    bell = f"M{p(-16, 40)}C{p(-16, 21)} {p(-9, 14)} {p(0, 14)}C{p(9, 14)} {p(16, 21)} {p(16, 40)}Z"
    return f"""<g class="chime" style="transform-origin:{x}px {y}px">
  <path d="M{p(0, 0)}C{p(1.6, 5)} {p(-1.6, 9)} {p(0, 14)}" fill="none" stroke="{INK}" stroke-width="{1.2 * s:.2f}" />
  <clipPath id="cb{uid}"><path d="{bell}" /></clipPath>
  <path d="{bell}" fill="{PAPER}" fill-opacity="0.85" />
  <g clip-path="url(#cb{uid})"><rect x="{x + 3 * s:.1f}" y="{y + 10 * s:.1f}" width="{16 * s:.1f}" height="{34 * s:.1f}" fill="url(#toneFine)" opacity="0.7" /></g>
  <path d="M{p(-8, 28)}c{2 * s:.1f} {-3.4 * s:.1f} {8 * s:.1f} {-3.4 * s:.1f} {10 * s:.1f} 0c{-2 * s:.1f} {3.4 * s:.1f} {-8 * s:.1f} {3.4 * s:.1f} {-10 * s:.1f} 0z" fill="url(#tone)" stroke="{INK}" stroke-width="{0.8 * s:.2f}" />
  <path d="M{p(2, 28)}l{4 * s:.1f} {-3 * s:.1f}l{-1 * s:.1f} {3 * s:.1f}l{1 * s:.1f} {3 * s:.1f}z" fill="{PAPER}" stroke="{INK}" stroke-width="{0.7 * s:.2f}" stroke-linejoin="round" />
  <circle cx="{x - 5.2 * s:.1f}" cy="{y + 27.4 * s:.1f}" r="{0.65 * s:.2f}" fill="{INK}" />
  <path d="M{p(-12, 35)}q{3 * s:.1f} {-2 * s:.1f} {6 * s:.1f} 0M{p(4, 36)}q{3 * s:.1f} {-2 * s:.1f} {6 * s:.1f} 0" fill="none" stroke="{INK}" stroke-width="{0.6 * s:.2f}" stroke-linecap="round" />
  <path d="{bell}" fill="none" stroke="{INK}" stroke-width="{1.5 * s:.2f}" />
  <ellipse cx="{x}" cy="{y + 40 * s:.1f}" rx="{16 * s:.1f}" ry="{2.5 * s:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="{1.1 * s:.2f}" />
  <path d="M{p(-12, 33)}C{p(-13, 25)} {p(-10, 19)} {p(-5, 17)}" fill="none" stroke="{PAPER}" stroke-width="{2.4 * s:.2f}" stroke-linecap="round" />
  <line x1="{x}" y1="{y + 18 * s:.1f}" x2="{x}" y2="{y + 52 * s:.1f}" stroke="{INK}" stroke-width="{0.8 * s:.2f}" />
  <circle cx="{x}" cy="{y + 45 * s:.1f}" r="{2.3 * s:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="{0.8 * s:.2f}" />
  <g class="chime-paper" style="transform-origin:{x}px {y + 52 * s:.1f}px">
    <rect x="{x - 7 * s:.1f}" y="{y + 52 * s:.1f}" width="{14 * s:.1f}" height="{38 * s:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="{1 * s:.2f}" />
    <rect x="{x - 7 * s:.1f}" y="{y + 80 * s:.1f}" width="{14 * s:.1f}" height="{10 * s:.1f}" fill="url(#toneFine)" opacity="0.7" />
    <text x="{x}" y="{y + 72 * s:.1f}" text-anchor="middle" style="font: 700 {11 * s:.1f}px {MINCHO_STACK}; fill: {INK}">{kanji}</text>
  </g>
</g>"""


# ---------------------------------------------------------------- 泡沫、樱花、雨伞
def bubble(x, y, r, dur, delay, rise):
    return (f'<g transform="translate({x:.0f} {y:.0f})"><g class="bub-rise" style="--rise:{rise:.0f}px;animation-duration:{dur:.1f}s;animation-delay:{-delay:.1f}s">'
            f'<g class="bub-wob" style="animation-delay:{-delay * 0.7:.1f}s">'
            f'<circle r="{r:.1f}" fill="{PAPER}" fill-opacity="0.3" stroke="{INK}" stroke-width="{max(0.7, r * 0.09):.2f}" />'
            f'<path d="M{-r * 0.62:.1f} {-r * 0.1:.1f}A{r * 0.66:.1f} {r * 0.66:.1f} 0 0 1 {-r * 0.08:.1f} {-r * 0.62:.1f}" fill="none" stroke="{INK}" stroke-width="{max(0.6, r * 0.08):.2f}" stroke-linecap="round" />'
            f'<path d="M{r * 0.35:.1f} {r * 0.55:.1f}A{r * 0.7:.1f} {r * 0.7:.1f} 0 0 0 {r * 0.62:.1f} {r * 0.2:.1f}" fill="none" stroke="{INK}" stroke-width="{max(0.4, r * 0.05):.2f}" stroke-linecap="round" opacity="0.6" />'
            f'</g></g></g>')


def bubbles(rng, n, x0, x1, y0, y1, rmin, rmax, rise):
    return "".join(bubble(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(rmin, rmax), rng.uniform(5, 9), rng.uniform(0, 9), -rng.uniform(*rise)) for _ in range(n))


PETAL = "M0 -7C1 -10 3 -12 5 -12C9 -12 11 -6 9 0C7 6 3 10 0 13C-3 10 -7 6 -9 0C-11 -6 -9 -12 -5 -12C-3 -12 -1 -10 0 -7Z"


def petal(x, y, s, dur, delay, dx, fall, spin):
    return (f'<g transform="translate({x:.0f} {y:.0f}) scale({s:.2f})"><g class="petal-fall" style="--dx:{dx:.0f}px;--fall:{fall:.0f}px;--spin:{spin:.0f}deg;animation-duration:{dur:.1f}s;animation-delay:{-delay:.1f}s">'
            f'<g class="petal-flip" style="animation-delay:{-delay * 0.6:.1f}s"><path d="{PETAL}" fill="{PAPER}" stroke="{INK}" stroke-width="0.9" stroke-linejoin="round" />'
            f'<path d="{PETAL}" fill="url(#toneFine)" opacity="0.55" transform="translate(0 4) scale(0.8)" /><path d="M0 9L0 -3" stroke="{INK}" stroke-width="0.5" /></g></g></g>')


def petals(rng, n, x0, x1, y0, fall):
    return "".join(petal(rng.uniform(x0, x1), y0 + rng.uniform(-20, 0), rng.uniform(0.7, 1.25), rng.uniform(7, 12), rng.uniform(0, 12),
                         rng.uniform(-40, 120), fall, rng.uniform(220, 520)) for _ in range(n))


def umbrella(x, y, s=1.0):
    """线稿雨伞：八片伞面隔片上网点，伞骨、扇贝边、伞尖、J 形伞柄；伞边挂着的水珠会滴落。"""
    n, W, top = 8, 86, -64
    rim = [(-W + 2 * W * i / n, 0) for i in range(n + 1)]
    ctrl = [(px * 0.62, -46) for px, _ in rim]
    panels = []
    for i in range(n):
        (ax, ay), (bx, by) = rim[i], rim[i + 1]
        (cax, cay), (cbx, cby) = ctrl[i], ctrl[i + 1]
        d = f"M0 {top}Q{cax:.1f} {cay} {ax:.1f} {ay}Q{(ax + bx) / 2:.1f} -9 {bx:.1f} {by}Q{cbx:.1f} {cby} 0 {top}Z"
        fill = "url(#tone)" if i % 2 else PAPER
        panels.append(f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="1.3" stroke-linejoin="round" />')
    drops = "".join(
        f'<g transform="translate({px:.0f} 2)"><path class="drop" d="M0 0C1.6 2.6 2 4 0 5.4C-2 4 -1.6 2.6 0 0Z" fill="{PAPER}" stroke="{INK}" stroke-width="0.7" style="animation-delay:{-i * 0.37:.2f}s" /></g>'
        for i, (px, _) in enumerate(rim) if i % 2 == 0)
    return f"""<g transform="translate({x} {y}) scale({s})"><g class="umbrella">
  {"".join(panels)}
  <path d="M0 {top}L0 {top - 9}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round" />
  <path d="M0 -2L0 78C0 92 -16 92 -16 81" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" />
  {drops}
</g></g>"""


# ---------------------------------------------------------------- 漫画语法：集中线、雨、对话框、印章
def focus_lines(cx, cy, w, h, n, inner, rng, opacity=0.5):
    """集中线：两组随机线交替闪，模拟动画里的抖动。"""
    def one():
        out = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            far = math.hypot(w, h)
            r0 = inner * rng.uniform(1, 1.5)
            wid = rng.uniform(0.004, 0.012)
            x1, y1 = cx + math.cos(a) * far, cy + math.sin(a) * far
            x2, y2 = cx + math.cos(a + wid) * far, cy + math.sin(a + wid) * far
            x3, y3 = cx + math.cos(a + wid / 2) * r0, cy + math.sin(a + wid / 2) * r0
            out.append(f"M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}L{x3:.0f} {y3:.0f}Z")
        return "".join(out)
    return (f'<g opacity="{opacity}"><path class="focus-a" d="{one()}" fill="{INK}" /><path class="focus-b" d="{one()}" fill="{INK}" /></g>')


def rain(x0, y0, w, h, rng, n=90):
    lines = "".join(f'<line x1="{rng.uniform(x0 - 60, x0 + w):.0f}" y1="{rng.uniform(y0 - h, y0 + h):.0f}" x2="{0:.0f}" y2="0" />' for _ in range(0))
    segs = []
    for _ in range(n):
        x = rng.uniform(x0 - 80, x0 + w + 40)
        y = rng.uniform(y0 - h, y0 + h)
        ln = rng.uniform(10, 22)
        segs.append(f"M{x:.0f} {y:.0f}l{-ln * 0.25:.1f} {ln:.1f}")
    return f'<g class="rain"><path d="{"".join(segs)}" stroke="{INK}" stroke-width="0.8" stroke-linecap="round" opacity="0.55" /></g>{lines}'


def balloon(x, y, w, h, text_svg, tail=(-30, 34)):
    """对话框：手绘感的圆角气泡和尾巴。"""
    tx, ty = tail
    d = (f"M{x - w / 2 + 14:.0f} {y - h / 2:.0f}H{x + w / 2 - 14:.0f}Q{x + w / 2:.0f} {y - h / 2:.0f} {x + w / 2:.0f} {y - h / 2 + 14:.0f}"
         f"V{y + h / 2 - 14:.0f}Q{x + w / 2:.0f} {y + h / 2:.0f} {x + w / 2 - 14:.0f} {y + h / 2:.0f}"
         f"H{x + 6:.0f}L{x + tx:.0f} {y + h / 2 + ty:.0f}L{x - 10:.0f} {y + h / 2:.0f}"
         f"H{x - w / 2 + 14:.0f}Q{x - w / 2:.0f} {y + h / 2:.0f} {x - w / 2:.0f} {y + h / 2 - 14:.0f}V{y - h / 2 + 14:.0f}Q{x - w / 2:.0f} {y - h / 2:.0f} {x - w / 2 + 14:.0f} {y - h / 2:.0f}Z")
    return f'<g class="pop" style="animation-delay:-1.2s"><path d="{d}" fill="{PAPER}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round" />{text_svg}</g>'


def stamp(x, y, w, h, label, size=16, vertical=False):
    """红色印章标签（不反相）。"""
    if vertical:
        chars = "".join(f'<text x="{x + w / 2:.1f}" y="{y + 8 + (i + 1) * size * 1.05:.1f}" text-anchor="middle">{escape(c)}</text>' for i, c in enumerate(label))
    else:
        chars = f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + size * 0.36:.1f}" text-anchor="middle">{escape(label)}</text>'
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{RED}" />'
            f'<g style="font: 800 {size}px {MINCHO_STACK}; fill: #ffffff; letter-spacing: 1px">{chars}</g></g>')


def misregister(text_svg, cls_text):
    """印刷错版：青、品红两层在主字后面轻微错位、偶尔跳一下。返回 (彩色层, 墨层)。"""
    # 复制的字保留原来的浮动动画（与墨字同步），错位和跳动放在外层组上
    c = text_svg.replace('class="', 'class="cy ')
    m = text_svg.replace('class="', 'class="mg ')
    return f'<g opacity="0.72"><g class="cmy-c">{c}</g><g class="cmy-m">{m}</g></g>', text_svg

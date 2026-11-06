"""漫画风（週刊ユキ）共用部件：字体子集嵌入、配色、浅色/深色两版输出，以及水母、风铃、泡沫、樱花、雨伞等线稿。

所有图都先按浅色（纸白墨黑）画；深色版把“墨”层的纸、墨、灰换成夜间配色（白线墨底），
红色印章、夕阳、花火等彩色层不换（花火有浅深两套颜色）。make_art.py 和 decorate.py 都用这里的东西。
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
SHEEN_HI = "#fbfaf8"  # 字面扫光的高光（深色版换成纯白）
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
    """按层组织一张图：ink 层在深色版里换成夜间配色，color 层保持原色（可给深色版单独一份）。"""

    def __init__(self, w, h, label="", role="img"):
        self.w, self.h, self.label, self.role = w, h, label, role
        self.css, self.defs, self.layers = [], [DEFS], []

    def ink(self, svg):
        self.layers.append(("ink", svg, None))

    def color(self, svg, dark=None):
        self.layers.append(("color", svg, dark))

    def render(self, mode):
        conv = to_night if mode == "dark" else (lambda t: t)
        body = []
        for kind, light, dark in self.layers:
            if kind == "ink":
                body.append(conv(light))
            else:
                body.append(dark if mode == "dark" and dark is not None else light)
        aria = f'role="img" aria-label="{escape(self.label)}"' if self.role == "img" else 'role="presentation"'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" {aria}>\n<style>{conv(BASE_CSS + "".join(self.css))}</style>\n<defs>{conv("".join(self.defs))}</defs>\n'
                + "\n".join(body) + "\n</svg>\n")

    def write(self, folder, name):
        for mode in ("light", "dark"):
            (folder / f"{name}-{mode}.svg").write_text(self.render(mode), encoding="utf-8")


def _night_hex(h):
    """和 night 滤镜同一个映射：去色后把纸白映射到 #0f1822、墨黑映射到 #eceae6。"""
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    out = (-1.003 * lum + 1.011, -0.955 * lum + 1.0, -0.891 * lum + 0.979)
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02x}" for v in out)


NIGHT_PAPER, NIGHT_INK, NIGHT_RED = "#0f1822", "#eceae6", "#ff5a5f"


def to_night(svg):
    """墨层换色：纸、墨、灰换成夜间配色。彩色（红、花火等）不在表里，不受影响。"""
    table = {PAPER: NIGHT_PAPER, INK: NIGHT_INK, GRAY: _night_hex(GRAY), TONE_GRAY: _night_hex(TONE_GRAY), SHEEN_HI: "#ffffff"}
    return re.sub("|".join(re.escape(k) for k in table), lambda m: table[m.group().lower()], svg, flags=re.IGNORECASE)


# 深色版的卡片（外部生成、颜色不受控）仍用滤镜：先去色，再把纸白映射成墨底、墨黑映射成纸白
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
  <linearGradient id="fadeUp" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="1" stop-color="#fff" /></linearGradient>
  <mask id="toneDown" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#fadeDown)" /></mask>
  <mask id="toneUp" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#fadeUp)" /></mask>"""

BASE_CSS = f"""
  .float {{ transform-box: fill-box; transform-origin: center bottom; animation: float 4.8s {EASE} infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 35% {{ transform: translateY(-5px) rotate(-1.4deg); }} 70% {{ transform: translateY(-1.5px) rotate(1deg); }} }}
  .jf {{ animation: jfDrift 9.6s {EASE} infinite; }}
  @keyframes jfDrift {{ 0%, 100% {{ transform: translate(0, 0) rotate(-3deg); }} 45% {{ transform: translate(4px, -14px) rotate(3deg); }} }}
  .jf-bell {{ animation: jfPulse 3.2s infinite; }}
  @keyframes jfPulse {{
    0% {{ transform: scale(1, 1); animation-timing-function: {EASE_OUT}; }}
    26% {{ transform: scale(1.09, 0.86); animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1); }}
    100% {{ transform: scale(1, 1); }}
  }}
  .jf-thrust {{ animation: jfThrust 3.2s infinite; }}
  @keyframes jfThrust {{
    0% {{ transform: translateY(0); animation-timing-function: {EASE_OUT}; }}
    30% {{ transform: translateY(-9px); animation-timing-function: cubic-bezier(0.45, 0, 0.55, 1); }}
    100% {{ transform: translateY(0); }}
  }}
  .chime {{ animation: chimeSwing 4.8s {EASE} infinite; }}
  .chime-paper {{ animation: paperSwing 4.8s {EASE} infinite; animation-delay: -0.5s; }}
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
  .umbrella {{ animation: umbrella 6.4s {EASE} infinite; }}
  @keyframes umbrella {{ 0%, 100% {{ transform: rotate(-5deg) translateY(0); }} 50% {{ transform: rotate(4deg) translateY(-4px); }} }}
  .focus-a {{ animation: focusX 3.2s {EASE} infinite alternate; }}
  .focus-b {{ animation: focusX 3.2s {EASE} infinite alternate-reverse; }}
  @keyframes focusX {{ from {{ opacity: 1; }} to {{ opacity: 0.25; }} }}
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
    """集中线：两组随机线缓慢交替明暗。"""
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


# ================================================================ 第二版部件：更精细，可大量堆叠
# 所有循环都用负延迟错开相位：任何一帧暂停，画面上都有正在进行的动作，不会出现全体同时消失的空档。

EXTRA_CSS = f"""
  .fall {{ animation: fall linear infinite; }}
  @keyframes fall {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(var(--dx, -40px), var(--dy, 400px)); }} }}
  .crown {{ transform-box: fill-box; transform-origin: center bottom; animation: crown 1.6s {EASE_OUT} infinite; }}
  @keyframes crown {{ 0% {{ opacity: 0; transform: scale(0.2, 0); }} 8% {{ opacity: 1; }} 35% {{ opacity: 1; transform: scale(1, 1); }} 70%, 100% {{ opacity: 0; transform: scale(1.15, 0.6); }} }}
  .ring {{ transform-box: fill-box; transform-origin: center; animation: ringOut 1.6s {EASE_OUT} infinite; }}
  @keyframes ringOut {{ 0% {{ opacity: 0; transform: scale(0.15); }} 10% {{ opacity: 1; }} 100% {{ opacity: 0; transform: scale(1); }} }}
  .bub {{ animation: bubUp linear infinite; }}
  @keyframes bubUp {{ 0% {{ opacity: 0; transform: translateY(0) scale(0.7); }} 10% {{ opacity: 1; transform: translateY(calc(var(--rise) * 0.1)) scale(1); }} 88% {{ opacity: 1; }} 100% {{ opacity: 0; transform: translateY(var(--rise)) scale(1.06); }} }}
  .sway {{ animation: sway 2.6s {EASE} infinite alternate; }}
  @keyframes sway {{ from {{ transform: translateX(calc(var(--w, 6px) * -1)); }} to {{ transform: translateX(var(--w, 6px)); }} }}
  .breathe {{ transform-box: fill-box; transform-origin: center; animation: breathe 3s {EASE} infinite alternate; }}
  @keyframes breathe {{ from {{ transform: scale(0.96, 1.03); }} to {{ transform: scale(1.03, 0.97); }} }}
  .fw {{ opacity: 0; transform-box: view-box; animation: fwBurst ease-out infinite; }}
  @keyframes fwBurst {{
    0%, 18% {{ opacity: 0; transform: scale(0.05); }}
    20% {{ opacity: 1; transform: scale(0.15); animation-timing-function: {EASE_OUT}; }}
    48% {{ opacity: 1; transform: scale(1) translateY(0); animation-timing-function: cubic-bezier(0.4, 0, 1, 1); }}
    82% {{ opacity: 0.85; }}
    100% {{ opacity: 0; transform: scale(1.06) translateY(var(--droop, 14px)); }}
  }}
  .fw-rise {{ opacity: 0; animation: fwRise ease-out infinite; }}
  @keyframes fwRise {{ 0% {{ opacity: 0; transform: translateY(var(--up)); }} 2% {{ opacity: 1; }} 18% {{ opacity: 1; transform: translateY(0); }} 20%, 100% {{ opacity: 0; transform: translateY(0); }} }}
  .fw-glint {{ animation: fwGlint 0.5s {EASE} infinite alternate; }}
  @keyframes fwGlint {{ to {{ opacity: 0.35; }} }}
  .fw-flash {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: fwFlash ease-out infinite; }}
  @keyframes fwFlash {{ 0%, 18% {{ opacity: 0; transform: scale(0.3); }} 21% {{ opacity: 0.28; transform: scale(1); }} 45%, 100% {{ opacity: 0; transform: scale(1.4); }} }}
  .scroll {{ animation: scroll linear infinite; }}
  @keyframes scroll {{ from {{ transform: translateX(0); }} to {{ transform: translateX(var(--len)); }} }}
  .note {{ animation: noteOut ease-in-out infinite; }}
  @keyframes noteOut {{ 0% {{ opacity: 0; transform: translate(0, 0) rotate(0deg) scale(0.6); }} 15% {{ opacity: 1; transform: translate(calc(var(--dx) * 0.15), -6px) rotate(-8deg) scale(1); }} 85% {{ opacity: 0.9; }} 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) rotate(12deg) scale(0.9); }} }}
  .soundring {{ transform-box: fill-box; transform-origin: var(--ox) center; animation: soundRing 2.4s {EASE_OUT} infinite; }}
  @keyframes soundRing {{ 0% {{ opacity: 0; transform: scale(0.2); }} 12% {{ opacity: 0.9; }} 100% {{ opacity: 0; transform: scale(1); }} }}
"""


def rng_phase(rng, dur):
    return f"animation-duration:{dur:.2f}s;animation-delay:{-rng.uniform(0, dur):.2f}s"


# ---------------------------------------------------------------- 雨：水滴、拖影、水冠、涟漪
DROP = "M0 -10C1.4 -5.4 4 -2.2 4 1.4C4 4 2.2 5.8 0 5.8C-2.2 5.8 -4 4 -4 1.4C-4 -2.2 -1.4 -5.4 0 -10Z"


def raindrop(s=1.0):
    """水滴：纸色填充、墨线、内侧网点暗面、左上高光，拖着一条渐隐的动态线。"""
    return (f'<g transform="scale({s:.2f})"><path d="M0 -12L0 -46" stroke="url(#streak)" stroke-width="1.1" stroke-linecap="round" />'
            f'<path d="{DROP}" fill="{PAPER}" stroke="{INK}" stroke-width="0.8" />'
            f'<path d="M1.2 -1C3 0.6 3.2 3.4 1.4 4.6C2.4 3 2.3 0.8 1.2 -1Z" fill="url(#toneFine)" />'
            f'<path d="M-1.7 -1.8C-2.4 0 -2.3 1.6 -1.4 2.6" fill="none" stroke="{INK}" stroke-width="0.55" stroke-linecap="round" /></g>')


def rain_field(rng, x0, y0, w, h, n_near, n_far, angle=-0.12):
    """远处细雨线 + 近处带形状的水滴，多层速度。"""
    far = []
    for _ in range(n_far):
        x, y = rng.uniform(x0 - 60, x0 + w + 60), rng.uniform(y0 - h, y0 + h)
        ln = rng.uniform(10, 24)
        far.append(f"M{x:.0f} {y:.0f}l{ln * angle:.1f} {ln:.1f}")
    far_svg = (f'<g class="fall" style="--dx:{h * angle * 1.2:.0f}px;--dy:{h * 1.2:.0f}px;animation-duration:0.9s"><path d="{"".join(far)}" stroke="{INK}" stroke-width="0.7" stroke-linecap="round" opacity="0.35" /></g>'
               f'<g class="fall" style="--dx:{h * angle * 1.2:.0f}px;--dy:{h * 1.2:.0f}px;animation-duration:0.9s;animation-delay:-0.45s"><path d="{"".join(far)}" stroke="{INK}" stroke-width="0.7" stroke-linecap="round" opacity="0.35" transform="translate(37 -{h * 0.6:.0f})" /></g>')
    near = []
    for _ in range(n_near):
        x, y = rng.uniform(x0, x0 + w), rng.uniform(y0 - 60, y0)
        dur = rng.uniform(0.9, 1.5)
        s = rng.uniform(0.7, 1.25)
        near.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({-angle * 57:.0f})"><g class="fall" style="--dx:0px;--dy:{h + 80:.0f}px;{rng_phase(rng, dur)}">{raindrop(s)}</g></g>')
    return far_svg + "".join(near)


def splash(x, y, s, dur, delay):
    """落地：皇冠状水花 + 弹起的小水珠 + 两圈涟漪，同一节拍。"""
    crown = ("M-12 0C-10 -3 -9 -7 -10 -12C-7 -8 -6 -5 -5 -2C-4 -7 -3 -11 -2 -15C-1 -10 0 -6 0 -2"
             "C1 -6 2 -10 3 -15C4 -10 4 -6 5 -2C6 -5 7 -8 10 -12C9 -7 10 -3 12 0Z")
    drops = "".join(f'<circle cx="{dx}" cy="{dy}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="0.6" />' for dx, dy, r in [(-9, -18, 1.3), (-3, -22, 1.6), (4, -21, 1.4), (10, -17, 1.2)])
    style = f"animation-duration:{dur:.2f}s;animation-delay:{-delay:.2f}s"
    return (f'<g transform="translate({x:.0f} {y:.0f}) scale({s:.2f})">'
            f'<ellipse class="ring" cx="0" cy="1" rx="26" ry="4.5" fill="none" stroke="{INK}" stroke-width="0.8" style="{style}" />'
            f'<ellipse class="ring" cx="0" cy="1" rx="16" ry="3" fill="none" stroke="{INK}" stroke-width="0.6" style="{style};animation-delay:{-delay + 0.25:.2f}s" />'
            f'<g class="crown" style="{style}"><path d="{crown}" fill="{PAPER}" stroke="{INK}" stroke-width="0.8" stroke-linejoin="round" />{drops}</g></g>')


def splashes(rng, n, x0, x1, y0, y1):
    return "".join(splash(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(0.5, 1.0), rng.uniform(1.3, 2.2), rng.uniform(0, 2.2)) for _ in range(n))


# ---------------------------------------------------------------- 泡沫（精细版）
def bubble2(r):
    """泡沫：细墨圈、右下网点暗面（新月形）、左上窗形高光和小亮点、底部反光弧。"""
    a = r * 0.78
    crescent = (f"M{r * 0.94:.1f} {-r * 0.34:.1f}A{r:.1f} {r:.1f} 0 0 1 {-r * 0.34:.1f} {r * 0.94:.1f}"
                f"A{a:.1f} {a:.1f} 0 0 0 {r * 0.94:.1f} {-r * 0.34:.1f}Z")
    win = (f"M{-r * 0.58:.1f} {-r * 0.22:.1f}C{-r * 0.6:.1f} {-r * 0.5:.1f} {-r * 0.42:.1f} {-r * 0.62:.1f} {-r * 0.18:.1f} {-r * 0.62:.1f}"
           f"C{-r * 0.3:.1f} {-r * 0.5:.1f} {-r * 0.42:.1f} {-r * 0.38:.1f} {-r * 0.58:.1f} {-r * 0.22:.1f}Z")
    sw = max(0.55, r * 0.07)
    return (f'<circle r="{r:.1f}" fill="{PAPER}" fill-opacity="0.22" stroke="{INK}" stroke-width="{sw:.2f}" />'
            f'<path d="{crescent}" fill="url(#toneFine)" opacity="0.75" />'
            f'<path d="{win}" fill="{PAPER}" stroke="{INK}" stroke-width="{sw * 0.7:.2f}" stroke-linejoin="round" />'
            f'<circle cx="{-r * 0.15:.1f}" cy="{-r * 0.36:.1f}" r="{max(0.6, r * 0.07):.1f}" fill="{INK}" />'
            f'<path d="M{r * 0.18:.1f} {r * 0.7:.1f}A{r * 0.72:.1f} {r * 0.72:.1f} 0 0 0 {r * 0.62:.1f} {r * 0.32:.1f}" fill="none" stroke="{INK}" stroke-width="{sw * 0.6:.2f}" stroke-linecap="round" opacity="0.7" />')


def foam(rng, n, x0, x1, y0, y1, rmin, rmax, rise, cluster=0.35):
    """大量泡沫：一部分成团（大泡带几颗小泡）一起上浮，边升边左右晃，相位全部错开。"""
    out = []
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(rmin, rmax)
        group = bubble2(r)
        if rng.random() < cluster:
            for _ in range(rng.randint(2, 4)):
                a = rng.uniform(0, 2 * math.pi)
                rr = r * rng.uniform(0.25, 0.5)
                d = r + rr + rng.uniform(0.5, 2.5)
                group += f'<g transform="translate({math.cos(a) * d:.1f} {math.sin(a) * d:.1f})">{bubble2(rr)}</g>'
        dur = rng.uniform(5, 11)
        out.append(f'<g transform="translate({x:.0f} {y:.0f})"><g class="bub" style="--rise:{-rng.uniform(*rise):.0f}px;{rng_phase(rng, dur)}">'
                   f'<g class="sway" style="--w:{rng.uniform(3, 9):.1f}px;{rng_phase(rng, rng.uniform(1.8, 3.4))}"><g class="breathe" style="{rng_phase(rng, rng.uniform(2.2, 3.6))}">{group}</g></g></g></g>')
    return "".join(out)


# ---------------------------------------------------------------- 蛇の目和伞
def wagasa(x, y, s=1.0):
    """和伞：浅穹顶伞面（深网点）+ 一圈留白的蛇の目环带、二十六根伞骨、波形伞缘、伞面下的内骨、
    竹柄的节、缠藤的握把、顶帽和流苏；伞缘挂的水珠依次滴落。"""
    W, top, n = 118, -80, 28
    rim = [(-W + 2 * W * i / n, 2 * math.sin(math.pi * i / n) ** 0.5) for i in range(n + 1)]

    def on_canopy(t, px):
        """伞面上从顶到缘的二次曲线，t=0 顶点，t=1 伞缘。"""
        cx, cy = px * 0.5, top + 10
        u = 1 - t
        return (u * u * 0 + 2 * u * t * cx + t * t * px, u * u * top + 2 * u * t * cy + t * t * 0)
    edge = "".join(f"Q{(rim[i][0] + rim[i + 1][0]) / 2:.1f} {6 + rim[i][1]:.1f} {rim[i + 1][0]:.1f} {rim[i + 1][1]:.1f}" for i in range(n))
    canopy = f"M0 {top}Q{-W * 0.5:.1f} {top + 10} {-W} 0{edge}Q{W * 0.5:.1f} {top + 10} 0 {top}Z"
    band_in = [on_canopy(0.55, px) for px, _ in rim]
    band_out = [on_canopy(0.7, px) for px, _ in rim]
    band = smooth(band_out) + "L" + smooth(band_in[::-1])[1:] + "Z"
    ribs = "".join(f'<path d="M0 {top}Q{px * 0.5:.1f} {top + 10} {px:.1f} {py:.1f}" />' for px, py in rim)
    under = "".join(f'<path d="M{px * 0.82:.1f} {py - 1:.1f}L0 26" />' for px, py in rim[2:-2:3])
    nodes = "".join(f'<line x1="-2.6" y1="{yy}" x2="2.6" y2="{yy}" />' for yy in (14, 46))
    wrap = "".join(f'<line x1="-3.2" y1="{yy}" x2="3.2" y2="{yy + 1.6}" />' for yy in range(62, 86, 3))
    drops = "".join(
        f'<g transform="translate({px:.0f} {py + 6:.0f})"><g class="drop" style="animation-delay:{-i * 0.41:.2f}s">'
        f'<path d="{DROP}" transform="scale(0.55)" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" /></g></g>'
        for i, (px, py) in enumerate(rim) if i % 3 == 1)
    return f"""<g transform="translate({x} {y}) scale({s})"><g class="umbrella">
  <path d="{canopy}" fill="url(#tone)" />
  <path d="{canopy}" fill="url(#toneFine)" opacity="0.5" />
  <path d="{band}" fill="{PAPER}" />
  <g fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.9">{ribs}</g>
  <path d="{band}" fill="none" stroke="{INK}" stroke-width="0.8" />
  <path d="{canopy}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" />
  <g stroke="{INK}" stroke-width="0.5" opacity="0.7">{under}</g>
  <rect x="-3.5" y="{top - 9}" width="7" height="9" rx="1.5" fill="{PAPER}" stroke="{INK}" stroke-width="1" />
  <path d="M0 {top - 9}C3 {top - 15} 6 {top - 14} 8 {top - 20}" fill="none" stroke="{INK}" stroke-width="0.8" />
  <rect x="-2.2" y="0" width="4.4" height="60" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" />
  <g stroke="{INK}" stroke-width="1">{nodes}</g>
  <rect x="-3.2" y="60" width="6.4" height="28" rx="1.2" fill="url(#hatch)" stroke="{INK}" stroke-width="1.1" />
  <g stroke="{INK}" stroke-width="0.6">{wrap}</g>
  <path d="M0 88C0 98 2 102 6 102" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" />
  {drops}
</g></g>"""


# ---------------------------------------------------------------- 夏祭り花火（彩色层，浅深两套颜色）
FW_DAY = {"red": "#de2846", "pink": "#e44696", "orange": "#ee781c", "gold": "#d09214", "green": "#1ca05c", "cyan": "#1492d2", "blue": "#3652da", "violet": "#8e40dc", "silver": "#647696"}
FW_NIGHT = {"red": "#ff4e60", "pink": "#ff80c8", "orange": "#ff983c", "gold": "#ffcc6a", "green": "#6eee96", "cyan": "#6edcff", "blue": "#7892ff", "violet": "#c680ff", "silver": "#e8f2ff"}
SCHEMES = [("red", "gold", "cyan"), ("pink", "violet", "gold"), ("cyan", "blue", "pink"), ("gold", "red", "green"),
           ("green", "cyan", "pink"), ("violet", "pink", "silver"), ("orange", "red", "cyan"), ("blue", "violet", "gold")]


def firework(uid, kind, x, y, r, scheme, dur, delay, rng, mode, rise=180):
    """一发花火：升空的光点 → 炸开 → 下垂消散，颜色从主色渐变到变色。
    kiku 菊（拖尾）、botan 牡丹（点、末尾闪烁）、kamuro 冠菊（金色垂柳）、wa 輪（倾斜圆环）、jelly 水母型物。"""
    pal = FW_DAY if mode == "light" else FW_NIGHT
    c1, c2, c3 = (pal[c] for c in scheme)
    style = f"animation-duration:{dur:.2f}s;animation-delay:{-delay:.2f}s"
    grad = (f'<radialGradient id="fg{uid}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="{r:.0f}">'
            f'<stop offset="0" stop-color="{c3}" /><stop offset="0.35" stop-color="{c1}" /><stop offset="1" stop-color="{c2}" /></radialGradient>')
    parts = []
    if kind in ("kiku", "botan"):
        n = 34 if kind == "kiku" else 26
        for k in range(n):
            a = 2 * math.pi * k / n + rng.uniform(-0.06, 0.06)
            rr = r * rng.uniform(0.86, 1.0)
            ex, ey = math.cos(a) * rr, math.sin(a) * rr
            if kind == "kiku":
                parts.append(f'<path d="M{ex * 0.18:.1f} {ey * 0.18:.1f}Q{ex * 0.6:.1f} {ey * 0.6 + 2:.1f} {ex:.1f} {ey:.1f}" stroke="url(#fg{uid})" stroke-width="1.5" stroke-linecap="round" fill="none" />')
            parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{2.2 if kind == "kiku" else 2.8}" fill="{c2 if kind == "kiku" else c1}" />')
        for k in range(12):
            a = 2 * math.pi * k / 12
            parts.append(f'<circle cx="{math.cos(a) * r * 0.42:.1f}" cy="{math.sin(a) * r * 0.42:.1f}" r="1.8" fill="{c3}" />')
        body = "".join(parts)
        if kind == "botan":
            body = f'<g class="fw-glint">{body}</g>'
    elif kind == "kamuro":
        for k in range(22):
            a = -math.pi + math.pi * k / 21 + rng.uniform(-0.05, 0.05)
            ex, ey = math.cos(a) * r, math.sin(a) * r * 0.75
            parts.append(f'<path d="M0 0Q{ex * 0.8:.1f} {ey * 0.8 - 6:.1f} {ex:.1f} {ey + r * 0.55:.1f}" stroke="{pal["gold"]}" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.9" />'
                         f'<circle cx="{ex:.1f}" cy="{ey + r * 0.55:.1f}" r="1.6" fill="{pal["gold"]}" />')
        for _ in range(16):
            parts.append(f'<circle cx="{rng.uniform(-r, r):.1f}" cy="{rng.uniform(0, r * 0.9):.1f}" r="1" fill="{pal["gold"]}" class="fw-glint" />')
        body = "".join(parts)
    elif kind == "wa":
        tilt = rng.uniform(-30, 30)
        dots = "".join(f'<circle cx="{math.cos(2 * math.pi * k / 30) * r:.1f}" cy="{math.sin(2 * math.pi * k / 30) * r:.1f}" r="2.4" fill="{c1}" />' for k in range(30))
        body = f'<g transform="rotate({tilt:.0f}) scale(1 0.38)">{dots}</g><circle r="3" fill="{c3}" />'
    else:  # jelly：用光点描出一只水母
        pts = []
        for k in range(17):
            a = math.pi + math.pi * k / 16
            pts.append((math.cos(a) * r * 0.8, math.sin(a) * r * 0.6))
        for k in range(8):
            pts.append((-r * 0.7 + k * r * 0.2, 2))
        for j, x0 in enumerate((-0.5, -0.2, 0.2, 0.5)):
            for t in range(1, 9):
                pts.append((x0 * r + math.sin(t * 0.9 + j) * 4, t * r * 0.13))
        body = "".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.1" fill="{c1 if i < 25 else c2}" />' for i, (px, py) in enumerate(pts))
    flash = f'<circle class="fw-flash" r="{r * 0.5:.0f}" fill="{c3}" opacity="0.25" style="{style}" />'
    return (grad, f'<g transform="translate({x:.0f} {y:.0f})"><circle class="fw-rise" r="2.2" fill="{c3}" style="--up:{rise}px;{style}" />'
                  f'{flash}<g class="fw" style="--droop:{r * 0.18:.0f}px;{style}">{body}</g></g>')


def festival(prefix, spots, rng, mode, period=(5.2, 7.4)):
    """一组花火：周期不同、相位错开，任何时刻都有在开的和在谢的。spots: [(x, y, r, kind)]"""
    defs, body = [], []
    n = len(spots)
    for i, (x, y, r, kind) in enumerate(spots):
        dur = rng.uniform(*period)
        delay = dur * i / n + rng.uniform(0, 0.4)
        d, b = firework(f"{prefix}{i}", kind, x, y, r, SCHEMES[(i * 3 + len(prefix)) % len(SCHEMES)], dur, delay, rng, mode)
        defs.append(d)
        body.append(b)
    return "".join(defs), "".join(body)


# ---------------------------------------------------------------- 胶片边、条形码、音符
def film_strip(y, w, h=30, label="YUKI FILM 400"):
    """胶片边：上下两排齿孔，片号印在中间；齿孔和片号以同一速度向左走（无缝循环）。"""
    pitch, gap, speed = 16, 240, 26.0
    holes = "".join(f'<rect x="{x}" y="{y + 3}" width="8" height="5.5" rx="1.2" /><rect x="{x}" y="{y + h - 8.5}" width="8" height="5.5" rx="1.2" />'
                    for x in range(-pitch * 2, int(w) + pitch * 2, pitch))
    marks = "".join(f'<text x="{x + 30}" y="{y + h / 2 + 3.2:.1f}" class="filmtxt">{i % 36 + 1:02d}A  ▸  {label}</text>' for i, x in enumerate(range(0, int(w) + gap * 2, gap)))
    return (f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{INK}" />'
            f'<g class="scroll" fill="{PAPER}" style="--len:-{pitch}px;animation-duration:{pitch / speed:.3f}s">{holes}</g>'
            f'<g class="scroll" style="--len:-{gap}px;animation-duration:{gap / speed:.3f}s">{marks}</g>')


def barcode(x, y, rng, w=110, h=34, number="4751957779960"):
    bars, cx = [], x
    while cx < x + w:
        bw = rng.choice([1, 1, 1.5, 2, 3])
        if rng.random() < 0.6:
            bars.append(f'<rect x="{cx:.1f}" y="{y}" width="{bw}" height="{h}" />')
        cx += bw + rng.choice([1, 1.5, 2])
    return (f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="{h + 22}" fill="{PAPER}" stroke="{INK}" stroke-width="0.8" />'
            f'<g fill="{INK}">{"".join(bars)}</g>'
            f'<text x="{x + w / 2}" y="{y + h + 11}" text-anchor="middle" style="font: 400 8px {SERIF_STACK}; letter-spacing: 1.6px; fill: {INK}">{number}</text>')


def music_note(kind=0, s=1.0):
    if kind == 0:
        shape = (f'<ellipse cx="0" cy="0" rx="5.6" ry="4" transform="rotate(-22)" fill="{INK}" /><rect x="4.4" y="-24" width="1.5" height="24" fill="{INK}" />'
                 f'<path d="M5.9 -24C10 -21 13 -18 11.6 -11C10.6 -15 8.6 -17 5.9 -18Z" fill="{INK}" />')
    else:
        shape = (f'<ellipse cx="0" cy="0" rx="5.2" ry="3.8" transform="rotate(-22)" fill="{INK}" /><ellipse cx="18" cy="-4" rx="5.2" ry="3.8" transform="rotate(-22 18 -4)" fill="{INK}" />'
                 f'<rect x="4.2" y="-22" width="1.5" height="22" fill="{INK}" /><rect x="22.2" y="-26" width="1.5" height="22" fill="{INK}" />'
                 f'<path d="M4.2 -22L23.7 -26V-21.5L4.2 -17.5Z" fill="{INK}" />')
    return f'<g transform="scale({s:.2f})">{shape}</g>'


# ---------------------------------------------------------------- 标题字：网点立体阴影 + 扫光
def sheen_grad(gid, x0, x1, dur=6.4, delay=0.0, band=70):
    """字面扫光：墨色字里走过一道“红—白—红”的窄光带，走完停一会儿；光带在字上随字一起浮动。"""
    keys = "0;0.32;1"
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{-band}" y1="{-band * 0.7:.0f}" x2="{band}" y2="{band * 0.7:.0f}">'
            f'<stop offset="0" stop-color="{INK}" /><stop offset="0.3" stop-color="{INK}" /><stop offset="0.42" stop-color="{RED}" />'
            f'<stop offset="0.5" stop-color="{SHEEN_HI}" /><stop offset="0.58" stop-color="{RED}" /><stop offset="0.7" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" />'
            f'<animateTransform attributeName="gradientTransform" type="translate" values="{x0 - band * 2:.0f} 0;{x1 + band * 2:.0f} 0;{x1 + band * 2:.0f} 0" keyTimes="{keys}" '
            f'calcMode="spline" keySplines="0.45 0.05 0.55 0.95;0 0 1 1" dur="{dur}s" begin="{-delay:.2f}s" repeatCount="indefinite" /></linearGradient>')


def title_fx(text_svg, depth=6.0, step=1.5):
    """漫画标题字：最底下一层带纸色描边的网点阴影，往上逐层叠出立体厚度，最上面是带扫光的墨字。"""
    layers = []
    k = depth
    first = True
    while k > 0.01:
        cls = "ex ex0" if first else "ex"
        layers.append(f'<g transform="translate({k:.1f} {k:.1f})">{text_svg.replace(chr(34) + ">", chr(34) + ">", 0).replace("class=" + chr(34), "class=" + chr(34) + cls + " ")}</g>')
        first = False
        k -= step
    return "".join(layers) + text_svg


TITLE_CSS = f"""
  .ex {{ fill: url(#tone) !important; stroke: none !important; }}
  .ex0 {{ stroke: {PAPER} !important; stroke-width: 5px !important; paint-order: stroke; stroke-linejoin: round; }}
"""


# ---------------------------------------------------------------- 夕阳（彩色层，浅深两版）
def sun(uid, x, y, r):
    """夕阳：外圈光晕、渐变日轮。返回 (浅色版, 深色版)。日轮上的横纹和网点在墨层另画。"""
    def one(top, mid, bottom, glow, glow_op):
        return (f'<defs><radialGradient id="glow{uid}"><stop offset="0" stop-color="{glow}" stop-opacity="{glow_op}" /><stop offset="0.45" stop-color="{glow}" stop-opacity="{glow_op * 0.35:.2f}" />'
                f'<stop offset="1" stop-color="{glow}" stop-opacity="0" /></radialGradient>'
                f'<linearGradient id="disc{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}" /><stop offset="0.55" stop-color="{mid}" /><stop offset="1" stop-color="{bottom}" /></linearGradient></defs>'
                f'<g class="sunglow" style="transform-origin:{x}px {y}px"><circle cx="{x}" cy="{y}" r="{r * 3.2:.0f}" fill="url(#glow{uid})" /></g>'
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#disc{uid})" />')
    return one("#ffc49a", "#f4734f", RED, "#f28a5b", 0.42), one("#ffb08a", "#ff6a5c", "#e8344a", "#ff6a55", 0.5)


def sun_ink(uid, x, y, r):
    """日轮上的墨层：下半部往上漂的横向留白条纹（夕阳的经典画法）+ 下缘网点 + 细墨圈。"""
    stripes = "".join(f'<rect x="{x - r - 4}" y="{y + r * (0.18 + 0.16 * i) - 1.2 * i:.1f}" width="{2 * r + 8}" height="{1.6 + 1.3 * i:.1f}" />' for i in range(7))
    return (f'<clipPath id="sunclip{uid}"><circle cx="{x}" cy="{y}" r="{r}" /></clipPath>'
            f'<g clip-path="url(#sunclip{uid})">'
            f'<rect x="{x - r}" y="{y + r * 0.2:.0f}" width="{2 * r}" height="{r}" fill="url(#toneFine)" opacity="0.35" mask="url(#toneDown)" />'
            f'<g fill="{PAPER}"><g class="stripes" style="--len:{-r * 0.16:.1f}px">{stripes}</g></g></g>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{INK}" stroke-width="1.1" />')


def sun_rays(x, y, n=44, r0=110, r1=900, opacity=0.13):
    """太阳的放射线（楔形），极慢地转。"""
    d = []
    for k in range(n):
        a = 2 * math.pi * k / n
        wdt = (0.022 if k % 2 else 0.012)
        rr = r1 if k % 3 else r1 * 0.7
        d.append(f"M{x + math.cos(a) * r0:.0f} {y + math.sin(a) * r0:.0f}L{x + math.cos(a - wdt) * rr:.0f} {y + math.sin(a - wdt) * rr:.0f}L{x + math.cos(a + wdt) * rr:.0f} {y + math.sin(a + wdt) * rr:.0f}Z")
    return f'<g class="spin" style="transform-origin:{x}px {y}px" opacity="{opacity}"><path d="{"".join(d)}" fill="{INK}" /></g>'


def sun_rings(x, y, r, n=3, dur=4.8):
    return "".join(f'<circle class="sunring" cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{INK}" stroke-width="{1.1 - 0.2 * i:.1f}" '
                   f'style="animation-duration:{dur}s;animation-delay:{-dur * i / n:.2f}s" />' for i in range(n))


def lens_flare(x, y, tx, ty, mode):
    """镜头光晕：日轮到画面中心方向上的几个光斑和一条横向光带，慢慢呼吸。"""
    cols = ["#f4734f", "#e8a23a", "#2fb6d6", "#e53878", "#f4734f"] if mode == "light" else ["#ff8a6b", "#ffcc6a", "#6edcff", "#ff80c8", "#ff8a6b"]
    op = 0.09 if mode == "light" else 0.14
    out = [f'<ellipse cx="{x}" cy="{y}" rx="300" ry="2.2" fill="{cols[0]}" opacity="{op * 2:.2f}" />']
    for i, (t, rr) in enumerate([(0.32, 12), (0.5, 26), (0.68, 8), (0.86, 40), (1.05, 16)]):
        cx, cy = x + (tx - x) * t, y + (ty - y) * t
        pts = " ".join(f"{cx + math.cos(math.pi / 3 * k + 0.3) * rr:.1f},{cy + math.sin(math.pi / 3 * k + 0.3) * rr:.1f}" for k in range(6))
        out.append(f'<polygon points="{pts}" fill="{cols[i]}" opacity="{op:.2f}" />' if i % 2 else f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr}" fill="none" stroke="{cols[i]}" stroke-width="{2 + rr / 10:.1f}" opacity="{op * 1.4:.2f}" />')
    return f'<g class="flare">{"".join(out)}</g>'


# ---------------------------------------------------------------- 入道雲
def cloud(uid, x, y, w, h, seed, shade_left=True):
    """积雨云：一层层向上收窄的圆团叠成塔，外轮廓一笔、内部几道团块线、背光面上网点；整体慢慢飘、微微鼓胀。"""
    rng = random.Random(seed)
    circ = []
    rows = 5
    for i in range(rows):
        t = i / (rows - 1)
        rw = w * (1 - 0.62 * t ** 0.9)
        cx = x + (rng.uniform(-0.06, 0.06) + 0.05 * t * (1 if shade_left else -1)) * w
        ry = y - h * 0.82 * t
        n = max(2, int(rw / (h * 0.22)))
        for k in range(n):
            u = k / max(1, n - 1)
            px = cx - rw / 2 + rw * u + rng.uniform(-6, 6)
            rr = h * (0.15 + 0.07 * rng.random()) * (1.15 - 0.25 * t) * (0.75 + 0.35 * math.sin(math.pi * u))
            circ.append((px, ry - rr * 0.35 + rng.uniform(-4, 4), rr))
    top = min(cy - r for cx, cy, r in circ)
    sw = 1.7
    union = "".join(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" />' for cx, cy, r in circ)
    outline = "".join(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r + sw:.1f}" />' for cx, cy, r in circ)
    arcs = []
    for cx, cy, r in circ:
        if rng.random() < 0.55:
            a0, a1 = math.radians(rng.uniform(195, 230)), math.radians(rng.uniform(300, 340))
            arcs.append(f"M{cx + math.cos(a0) * r:.1f} {cy + math.sin(a0) * r:.1f}A{r:.1f} {r:.1f} 0 0 1 {cx + math.cos(a1) * r:.1f} {cy + math.sin(a1) * r:.1f}")
    sx = x - w / 2 if shade_left else x
    return f"""<g class="cloud" style="transform-origin:{x:.0f}px {y:.0f}px;{f'animation-delay:{-seed * 2.3:.1f}s'}">
  <clipPath id="cl{uid}">{union}<rect x="{x - w / 2 - 40:.0f}" y="{y - 10:.0f}" width="{w + 80:.0f}" height="400" /></clipPath>
  <g fill="{INK}">{outline}</g>
  <rect x="{x - w / 2 - 40 - sw:.0f}" y="{y - 10 - sw:.0f}" width="{w + 80 + 2 * sw:.0f}" height="400" fill="{INK}" />
  <g fill="{PAPER}">{union}<rect x="{x - w / 2 - 40:.0f}" y="{y - 10:.0f}" width="{w + 80:.0f}" height="400" /></g>
  <g clip-path="url(#cl{uid})">
    <rect x="{sx - 40:.0f}" y="{top:.0f}" width="{w / 2 + 80:.0f}" height="{y - top + 400:.0f}" fill="url(#tone)" opacity="0.5" />
    <rect x="{x - w / 2 - 40:.0f}" y="{y - h * 0.35:.0f}" width="{w + 80:.0f}" height="{h * 0.5 + 400:.0f}" fill="url(#toneFine)" opacity="0.55" mask="url(#toneDown)" />
    <path d="{"".join(arcs)}" fill="none" stroke="{INK}" stroke-width="0.9" stroke-linecap="round" />
  </g>
</g>"""


# ---------------------------------------------------------------- 電柱と電線、金網フェンス
def pole(x, base, s=1.0, top=0.0):
    """电线杆（实墨剪影）：锥形杆身、两层横担、瓷瓶、变压器、脚钉。返回 (svg, 瓷瓶坐标)。"""
    w = 22 * s
    arm1, arm2 = 150 * s, 236 * s
    y1, y2 = top + 40 * s, top + 110 * s
    ins = []

    def insulators(yy, half):
        out = []
        for k in (-1, -0.45, 0.45, 1):
            ix = x + k * half
            ins.append((ix, yy - 13 * s))
            out.append(f'<rect x="{ix - 3.6 * s:.1f}" y="{yy - 14 * s:.1f}" width="{7.2 * s:.1f}" height="{13 * s:.1f}" rx="{3 * s:.1f}" />')
        return "".join(out)
    steps = "".join(f'<rect x="{x + w * 0.45 if i % 2 else x - w * 0.45 - 14 * s:.1f}" y="{top + 300 * s + i * 46 * s:.1f}" width="{14 * s:.1f}" height="{3.6 * s:.1f}" />' for i in range(8))
    svg = (f'<g fill="{INK}"><path d="M{x - w / 2:.1f} {base}L{x - w * 0.36:.1f} {top:.1f}L{x + w * 0.36:.1f} {top:.1f}L{x + w / 2:.1f} {base}Z" />'
           f'<rect x="{x - arm2 / 2:.1f}" y="{y1:.1f}" width="{arm2:.1f}" height="{9 * s:.1f}" /><rect x="{x - arm1 / 2:.1f}" y="{y2:.1f}" width="{arm1:.1f}" height="{8 * s:.1f}" />'
           f'<path d="M{x - arm2 / 2 + 18 * s:.1f} {y1 + 9 * s:.1f}L{x:.1f} {y1 + 52 * s:.1f}L{x + arm2 / 2 - 18 * s:.1f} {y1 + 9 * s:.1f}" stroke="{INK}" stroke-width="{2.6 * s:.1f}" fill="none" />'
           f'{insulators(y1, arm2 / 2 - 12 * s)}{insulators(y2, arm1 / 2 - 9 * s)}'
           f'<rect x="{x + w * 0.5:.1f}" y="{top + 190 * s:.1f}" width="{42 * s:.1f}" height="{76 * s:.1f}" rx="{7 * s:.1f}" />'
           f'<rect x="{x + w * 0.5 - 3 * s:.1f}" y="{top + 200 * s:.1f}" width="{48 * s:.1f}" height="{4.5 * s:.1f}" /><rect x="{x + w * 0.5 - 3 * s:.1f}" y="{top + 248 * s:.1f}" width="{48 * s:.1f}" height="{4.5 * s:.1f}" />'
           f'{steps}</g>'
           f'<path d="M{x - w * 0.18:.1f} {top + 4:.1f}L{x - w * 0.3:.1f} {base}" stroke="{PAPER}" stroke-width="{1.2 * s:.1f}" opacity="0.5" />')
    return svg, ins


def wire(x0, y0, x1, y1, sag, width=1.5, dur=4.8, delay=0.0):
    """电线：悬链（二次曲线），垂度随风轻轻变化。"""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    states = [f"M{x0:.1f} {y0:.1f}Q{mx:.1f} {my + sag * k:.1f} {x1:.1f} {y1:.1f}" for k in (2.0, 2.12, 1.92)]
    return f'<path d="{states[0]}" fill="none" stroke="{INK}" stroke-width="{width}" stroke-linecap="round">{morph(states, dur, delay)}</path>'


def wire_point(x0, y0, x1, y1, sag, t):
    """电线上 t 处的点（垂度取静止值），给挂风铃用。"""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + sag * 2.0
    u = 1 - t
    return u * u * x0 + 2 * u * t * mx + t * t * x1, u * u * y0 + 2 * u * t * my + t * t * y1


def fence(uid, x0, x1, y0, y1, posts, mesh=17):
    """天台的金网：斜格铁丝网（上淡下浓）、顶部扶手、立柱。"""
    return f"""<pattern id="chain{uid}" width="{mesh}" height="{mesh}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0H{mesh}M0 0V{mesh}" stroke="{INK}" stroke-width="1.15" fill="none" /></pattern>
<linearGradient id="ffade{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.35" /><stop offset="0.5" stop-color="#fff" stop-opacity="0.85" /><stop offset="1" stop-color="#fff" /></linearGradient>
<mask id="fmask{uid}"><rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="url(#ffade{uid})" /></mask>
<g mask="url(#fmask{uid})"><rect x="{x0}" y="{y0 + 6}" width="{x1 - x0}" height="{y1 - y0 - 6}" fill="url(#chain{uid})" /></g>
<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="6" fill="{INK}" /><rect x="{x0}" y="{y0 + 8}" width="{x1 - x0}" height="1" fill="{INK}" opacity="0.6" />
{"".join(f'<rect x="{px - 5}" y="{y0 - 6}" width="10" height="{y1 - y0 + 6}" fill="{INK}" /><rect x="{px - 7}" y="{y0 - 9}" width="14" height="5" rx="1" fill="{INK}" />' for px in posts)}"""


# ---------------------------------------------------------------- 爆炸框（红）
def starburst(x, y, r, text_svg, spikes=20, seed=9):
    rng = random.Random(seed)
    pts = []
    for i in range(spikes * 2):
        a = math.pi * i / spikes
        rad = r * (0.74 + rng.uniform(0, 0.06)) if i % 2 else r * (0.96 + rng.uniform(0, 0.06))
        pts.append(f"{x + math.cos(a) * rad:.1f},{y + math.sin(a) * rad:.1f}")
    return (f'<g class="burst" style="transform-origin:{x}px {y}px"><polygon points="{" ".join(pts)}" fill="{RED}" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round" />'
            f'<polygon points="{" ".join(pts)}" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-linejoin="round" transform="translate({x} {y}) scale(0.88) translate({-x} {-y})" opacity="0.7" />{text_svg}</g>')


SCENE_CSS = f"""
  .spin {{ animation: spin 96s linear infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .sunring {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: sunring 4.8s {EASE_OUT} infinite; }}
  @keyframes sunring {{ 0% {{ opacity: 0; transform: scale(1); }} 8% {{ opacity: 0.55; }} 100% {{ opacity: 0; transform: scale(2.4); }} }}
  .sunglow {{ animation: sunglow 6.4s {EASE} infinite alternate; }}
  @keyframes sunglow {{ from {{ transform: scale(0.94); opacity: 0.85; }} to {{ transform: scale(1.06); opacity: 1; }} }}
  .stripes {{ animation: stripes 3.2s linear infinite; }}
  @keyframes stripes {{ to {{ transform: translateY(var(--len)); }} }}
  .flare {{ animation: flare 6.4s {EASE} infinite alternate; }}
  @keyframes flare {{ from {{ opacity: 0.55; }} to {{ opacity: 1; }} }}
  .cloud {{ animation: cloud 19.2s {EASE} infinite alternate; }}
  @keyframes cloud {{ from {{ transform: translateX(-10px) scale(0.995, 0.99); }} to {{ transform: translateX(10px) scale(1.005, 1.015); }} }}
  .burst {{ animation: burst 3.2s {EASE} infinite alternate; }}
  @keyframes burst {{ from {{ transform: rotate(-4deg) scale(0.97); }} to {{ transform: rotate(3deg) scale(1.04); }} }}
"""

BASE_CSS = BASE_CSS + EXTRA_CSS + TITLE_CSS + SCENE_CSS
DEFS = DEFS + (f'<linearGradient id="streak" gradientUnits="userSpaceOnUse" x1="0" y1="-46" x2="0" y2="-12"><stop offset="0" stop-color="{INK}" stop-opacity="0" />'
               f'<stop offset="1" stop-color="{INK}" stop-opacity="0.7" /></linearGradient>')

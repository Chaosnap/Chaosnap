#!/usr/bin/env python3
"""主页上手工设计的动态 SVG：头图、横幅、分区标题、结尾。

改了文字或效果后在仓库根目录运行 `python3 .github/scripts/make_art.py`，
再提交 profile/ 下的结果。只用标准库。横幅把 C.png 直接嵌进 SVG。
"""
import base64
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "profile"

ROSE, WINE, BLUSH, CREAM, INK = "#c96f7f", "#8e3a59", "#e8a0a8", "#fff7f0", "#4a3b3d"
SERIF = "Georgia, 'Times New Roman', serif"
MONO = "'JetBrains Mono', 'SF Mono', Menlo, Consolas, 'Hiragino Sans', 'Yu Gothic', monospace"
JP = "'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif CJK JP', 'Noto Serif JP', serif"


def star(x, y, r):
    k = r * 0.12
    return (f"M{x} {y - r}C{x + k} {y - k} {x + k} {y - k} {x + r} {y}"
            f"C{x + k} {y + k} {x + k} {y + k} {x} {y + r}"
            f"C{x - k} {y + k} {x - k} {y + k} {x - r} {y}"
            f"C{x - k} {y - k} {x - k} {y - k} {x} {y - r}Z")


PETAL = "M0 0C5-7 15-7 18 0C15 6 6 8 0 0Z"
HEART = "M10 18C8 14 0 10 0 4.500 0 0.500 3 -1.500 5.500 -1.500 7.500 -1.500 9 0 10 2 11 0 12.500 -1.500 14.500 -1.500 17 -1.500 20 0.500 20 4.500 20 10 12 14 10 18Z"

# 通用动画：星星闪烁、花瓣飘落、文字 RGB 故障、扫描线
COMMON_CSS = """
    .spark { transform-box: fill-box; transform-origin: center; animation: twinkle 3.6s ease-in-out infinite; }
    @keyframes twinkle {
      0%, 100% { opacity: 0.15; transform: scale(0.6) rotate(0deg); }
      50% { opacity: 1; transform: scale(1.15) rotate(45deg); }
    }
    .petal { transform-box: fill-box; transform-origin: center; opacity: 0; animation: fall linear infinite; }
    @keyframes fall {
      0% { opacity: 0; transform: translate(0, -40px) rotate(0deg); }
      10% { opacity: 0.95; }
      85% { opacity: 0.85; }
      100% { opacity: 0; transform: translate(var(--dx, 70px), var(--dy, 340px)) rotate(560deg); }
    }
    .gl-c, .gl-m { opacity: 0; }
    .gl-c { fill: #4fd8e8; animation: glc 6s steps(1) infinite; }
    .gl-m { fill: #ff5fa2; animation: glm 6s steps(1) infinite; }
    @keyframes glc {
      0%, 86%, 100% { opacity: 0; transform: translate(0, 0); }
      87% { opacity: 0.85; transform: translate(-5px, 1px); }
      89% { opacity: 0.85; transform: translate(4px, -2px); }
      91% { opacity: 0; }
      94% { opacity: 0.7; transform: translate(-3px, 0); }
      95% { opacity: 0; }
    }
    @keyframes glm {
      0%, 86%, 100% { opacity: 0; transform: translate(0, 0); }
      87% { opacity: 0.85; transform: translate(5px, -1px); }
      89% { opacity: 0.85; transform: translate(-4px, 2px); }
      91% { opacity: 0; }
      94% { opacity: 0.7; transform: translate(3px, 0); }
      95% { opacity: 0; }
    }
    .shake { animation: shake 6s steps(1) infinite; }
    @keyframes shake {
      0%, 86%, 100% { transform: translate(0, 0); }
      87% { transform: translate(2px, 0) skewX(-6deg); }
      89% { transform: translate(-2px, 0) skewX(4deg); }
      91% { transform: translate(0, 0); }
    }
"""


def glitch(x, y, text, cls, fill, anchor="middle"):
    """三层文字：青、品红两层平时隐藏，周期性错位闪一下，主层同时轻微抖动。"""
    attrs = f'x="{x}" y="{y}" text-anchor="{anchor}"'
    return (f'<g><text class="{cls} gl-c" {attrs}>{text}</text>'
            f'<text class="{cls} gl-m" {attrs}>{text}</text>'
            f'<text class="{cls} shake" {attrs} fill="{fill}">{text}</text></g>')


def petals(rng, n, width, height, top=-20):
    out = []
    for _ in range(n):
        x = rng.uniform(0, width)
        dur = rng.uniform(7, 13)
        delay = -rng.uniform(0, dur)
        scale = rng.uniform(0.7, 1.3)
        dx = rng.uniform(-60, 120)
        fill = rng.choice(["url(#petalA)", "url(#petalB)"])
        out.append(f'<g transform="translate({x:.0f} {top}) scale({scale:.2f})"><path class="petal" d="{PETAL}" fill="{fill}" '
                   f'style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s;--dx:{dx:.0f}px;--dy:{height + 60:.0f}px"/></g>')
    return "\n  ".join(out)


PETAL_DEFS = """
    <linearGradient id="petalA" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffe3e8" /><stop offset="1" stop-color="#f2a7b6" />
    </linearGradient>
    <linearGradient id="petalB" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fbd0d6" /><stop offset="1" stop-color="#d9798a" />
    </linearGradient>"""


def sparks(points, fill):
    return "\n  ".join(f'<path class="spark" fill="{fill}" d="{star(x, y, r)}" style="animation-delay:{d}s"/>'
                       for x, y, r, d in points)


def wave_paths(top, flip=False):
    """头图 / 结尾的两层波浪；flip 时波浪在上方。"""
    def p(y, a, b):
        if not flip:
            return f"M0 0H1200V{y}C1000 {y + a} 800 {y - b} 600 {y}S200 {y + a} 0 {y}Z"
        return f"M0 300H1200V{y}C1000 {y - a} 800 {y + b} 600 {y}S200 {y - a} 0 {y}Z"
    lift = -40 if flip else 40
    back = [p(top + lift, -40, -40), p(top + lift * 0.55, 45, 40), p(top + lift, -40, -40)]
    front = [p(top, 45, 40), p(top + 14, -40, -38), p(top, 45, 40)]
    return (f'<path fill="url(#bg)" opacity="0.35" d="{back[0]}"><animate attributeName="d" dur="16s" repeatCount="indefinite" values="{";".join(back)}"/></path>\n'
            f'  <path fill="url(#bg)" d="{front[0]}"><animate attributeName="d" dur="12s" repeatCount="indefinite" values="{";".join(front)}"/></path>')


def bg_gradient():
    return f"""
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0.3">
      <stop offset="0" stop-color="#f6cfcc"><animate attributeName="stop-color" dur="10s" repeatCount="indefinite" values="#f6cfcc;#f2b8bd;#f6cfcc" /></stop>
      <stop offset="0.5" stop-color="#d9798a"><animate attributeName="stop-color" dur="10s" repeatCount="indefinite" values="#d9798a;#e38c9b;#d9798a" /></stop>
      <stop offset="1" stop-color="#9c4563"><animate attributeName="stop-color" dur="10s" repeatCount="indefinite" values="#9c4563;#b0566f;#9c4563" /></stop>
    </linearGradient>"""


def kana_rain(rng, width, height, clip):
    """背景里慢慢落下的片假名和 0/1，透明度很低。"""
    chars = "ヨウコソユキノセカイセンヘ01アイ0110サクラコード"
    cols = []
    for i in range(16):
        x = 30 + i * (width - 60) / 15 + rng.uniform(-10, 10)
        text = "".join(rng.choice(chars) for _ in range(9))
        tspans = "".join(f'<tspan x="{x:.0f}" dy="1.25em">{c}</tspan>' for c in text)
        dur = rng.uniform(9, 16)
        cols.append(f'<text class="rain" y="-120" style="animation-duration:{dur:.1f}s;animation-delay:{-rng.uniform(0, dur):.1f}s">{tspans}</text>')
    return f'<g clip-path="url(#{clip})">' + "".join(cols) + "</g>"


PROMPT = "> I am Yuki"
CHAR_W = 18.1  # 30px 等宽字体每个字符的宽度
TYPE_X = round(600 - len(PROMPT) * CHAR_W / 2)


def type_anim(attr, base):
    """逐字打出、停留、再逐字删掉；剪裁宽度和光标位置用同一组关键帧。"""
    n = len(PROMPT)
    steps = list(range(n + 1)) + [n] + list(range(n, -1, -1))
    times = [0.4 * i / n for i in range(n + 1)] + [0.85] + [0.85 + 0.13 * i / n for i in range(n + 1)]
    values = ";".join(f"{base + k * CHAR_W + (6 if attr == 'width' and k else 0):.1f}" for k in steps)
    key = ";".join(f"{t:.3f}" for t in times)
    return f'<animate attributeName="{attr}" dur="8s" repeatCount="indefinite" calcMode="discrete" values="{values}" keyTimes="{key}" />'


def header():
    rng = random.Random(3)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="Hi there, I am Yuki">
  <style>{COMMON_CSS}
    .title {{ font: 700 96px {SERIF}; letter-spacing: 8px; }}
    .prompt {{ font: 500 30px {MONO}; fill: {CREAM}; }}
    .jp {{ font: 400 19px {JP}; letter-spacing: 9px; fill: {CREAM}; opacity: 0; animation: fadein 1.6s 2.6s ease-out forwards; }}
    .rain {{ font: 500 15px {MONO}; fill: {CREAM}; opacity: 0.16; animation: rain linear infinite; }}
    @keyframes rain {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY(330px); }} }}
    .cursor {{ fill: {CREAM}; animation: blink 0.9s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .scan {{ fill: url(#scanGrad); animation: scan 4.5s linear infinite; }}
    @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY(260px); }} }}
    @keyframes fadein {{ to {{ opacity: 0.9; }} }}
  </style>
  <defs>{bg_gradient()}{PETAL_DEFS}
    <linearGradient id="title" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1200" y2="0" spreadMethod="repeat">
      <stop offset="0" stop-color="#fff7f0" /><stop offset="0.42" stop-color="#fff7f0" /><stop offset="0.5" stop-color="#ffd9df" /><stop offset="0.58" stop-color="#fff7f0" /><stop offset="1" stop-color="#fff7f0" />
      <animateTransform attributeName="gradientTransform" type="translate" from="-1200 0" to="1200 0" dur="5s" repeatCount="indefinite" />
    </linearGradient>
    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="0.5" stop-color="#fff" stop-opacity="0.22" /><stop offset="1" stop-color="#fff" stop-opacity="0" />
    </linearGradient>
    <clipPath id="shape"><path d="M0 0H1200V210C1000 255 800 170 600 210S200 255 0 210Z" /></clipPath>
    <clipPath id="typedClip"><rect x="{TYPE_X - 4}" y="146" width="0" height="44">{type_anim("width", 0)}</rect></clipPath>
  </defs>
  {wave_paths(210)}
  {kana_rain(rng, 1200, 300, "shape")}
  <g clip-path="url(#shape)"><rect class="scan" x="0" y="0" width="1200" height="40" /></g>
  {sparks([(150, 46, 17, 0), (285, 132, 11, 1.2), (92, 150, 8, 2.4), (1052, 40, 17, 0.6), (925, 138, 11, 1.8), (1120, 150, 8, 3)], CREAM)}
  {glitch(600, 116, "HI THERE", "title", "url(#title)")}
  <g clip-path="url(#typedClip)"><text class="prompt" x="{TYPE_X}" y="178">&gt; I am Yuki</text></g>
  <rect class="cursor" x="{TYPE_X}" y="152" width="15" height="31">{type_anim("x", TYPE_X + 2)}</rect>
  <text class="jp" x="600" y="210" text-anchor="middle">ようこそ、僕の世界線へ</text>
  {petals(rng, 12, 1200, 300)}
</svg>
"""


def footer():
    rng = random.Random(5)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="The end. Seminar, science, intelligence, future">
  <style>{COMMON_CSS}
    .title {{ font: 700 92px {SERIF}; letter-spacing: 8px; }}
    .desc {{ font: 500 22px {MONO}; letter-spacing: 3px; fill: {CREAM}; }}
    .jp {{ font: 400 19px {JP}; letter-spacing: 9px; fill: {CREAM}; opacity: 0.9; }}
    .rain {{ font: 500 15px {MONO}; fill: {CREAM}; opacity: 0.16; animation: rain linear infinite; }}
    @keyframes rain {{ from {{ transform: translateY(40px); }} to {{ transform: translateY(400px); }} }}
  </style>
  <defs>{bg_gradient()}{PETAL_DEFS}
    <linearGradient id="title" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1200" y2="0" spreadMethod="repeat">
      <stop offset="0" stop-color="#fff7f0" /><stop offset="0.42" stop-color="#fff7f0" /><stop offset="0.5" stop-color="#ffd9df" /><stop offset="0.58" stop-color="#fff7f0" /><stop offset="1" stop-color="#fff7f0" />
      <animateTransform attributeName="gradientTransform" type="translate" from="-1200 0" to="1200 0" dur="5s" repeatCount="indefinite" />
    </linearGradient>
    <clipPath id="shape"><path d="M0 300H1200V90C1000 45 800 130 600 90S200 45 0 90Z" /></clipPath>
  </defs>
  {wave_paths(90, flip=True)}
  {kana_rain(rng, 1200, 300, "shape")}
  {sparks([(150, 222, 17, 0.6), (285, 146, 11, 1.8), (92, 140, 8, 3), (1052, 228, 17, 0), (925, 138, 11, 1.2), (1120, 140, 8, 2.4)], CREAM)}
  <text class="desc" x="600" y="152" text-anchor="middle">SEMINAR // SCIENCE // INTELLIGENCE // FUTURE</text>
  {glitch(600, 238, "THE END", "title", "url(#title)")}
  <text class="jp" x="600" y="280" text-anchor="middle">またね、次の世界線で</text>
  {petals(rng, 10, 1200, 300, top=60)}
</svg>
"""


def title(name, english, japanese):
    w, h = 900, 104
    half = len(english) * 9.6 + 34
    rng = random.Random(len(english))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{english}">
  <style>{COMMON_CSS}
    .title {{ font: 700 34px {SERIF}; letter-spacing: 1.5px; }}
    .jp {{ font: 400 15px {JP}; letter-spacing: 8px; fill: {ROSE}; }}
    .line {{ stroke-dasharray: 400; stroke-dashoffset: 400; animation: draw 1.6s 0.3s ease-out forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    .reveal {{ animation: reveal 1.4s ease-out both; }}
    @keyframes reveal {{ from {{ opacity: 0; transform: translateY(10px); letter-spacing: 12px; }} to {{ opacity: 1; transform: none; }} }}
    .cursor {{ fill: {ROSE}; animation: blink 0.9s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <defs>
    <linearGradient id="shimmer" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="0" spreadMethod="repeat">
      <stop offset="0" stop-color="{WINE}" /><stop offset="0.35" stop-color="{ROSE}" /><stop offset="0.5" stop-color="#f6c9cf" /><stop offset="0.65" stop-color="{ROSE}" /><stop offset="1" stop-color="{WINE}" />
      <animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="{w} 0" dur="4.5s" repeatCount="indefinite" />
    </linearGradient>
    <linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{ROSE}" stop-opacity="0" /><stop offset="1" stop-color="{ROSE}" /></linearGradient>
    <linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="{ROSE}" /><stop offset="1" stop-color="{ROSE}" stop-opacity="0" /></linearGradient>
  </defs>
  <path class="line" d="M{w / 2 - half} 40H{w / 2 - half - 230}" stroke="url(#fadeR)" stroke-width="1.5" />
  <path class="line" d="M{w / 2 + half} 40H{w / 2 + half + 230}" stroke="url(#fadeL)" stroke-width="1.5" />
  {sparks([(w / 2 - half - 248, 40, 8, 0), (w / 2 + half + 248, 40, 8, 1.8), (w / 2 - half + 4, 18, 5, 0.9), (w / 2 + half - 4, 64, 5, 2.7)], ROSE)}
  <g class="reveal">{glitch(w / 2, 52, english, "title", "url(#shimmer)")}</g>
  <text class="jp reveal" x="{w / 2}" y="88" text-anchor="middle" style="animation-delay:0.5s">「{japanese}」</text>
</svg>
"""
    (OUT / f"title-{name}.svg").write_text(svg, encoding="utf-8")


def banner():
    """C.png 加动效：C++ 标志漂浮，NO 心跳，ADHD? 故障闪烁，爱心、花瓣、扫描线和流光边框。"""
    w, h = 1260, 709
    rng = random.Random(9)
    data = base64.b64encode((ROOT / "C.png").read_bytes()).decode()
    hearts = []
    for i in range(7):
        x = rng.uniform(520, 760)
        dur = rng.uniform(4.5, 7)
        hearts.append(f'<g transform="translate({x:.0f} 250) scale({rng.uniform(0.7, 1.25):.2f})"><path class="heart" d="{HEART}" fill="{rng.choice(["#ff8fab", "#f06292", "#ffb3c6"])}" '
                      f'style="animation-duration:{dur:.1f}s;animation-delay:{-rng.uniform(0, dur):.1f}s"/></g>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="ADHD? Python, C++, no problem">
  <style>{COMMON_CSS}
    .kb {{ transform-origin: 630px 354px; animation: kb 16s ease-in-out infinite alternate; }}
    @keyframes kb {{ from {{ transform: scale(1); }} to {{ transform: scale(1.035); }} }}
    .float {{ transform-origin: 1030px 245px; animation: float 4.2s ease-in-out infinite; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 50% {{ transform: translateY(-12px) rotate(-2.5deg); }} }}
    .beat {{ transform-origin: 1015px 500px; animation: beat 1.6s ease-in-out infinite; }}
    @keyframes beat {{ 0%, 40%, 100% {{ transform: scale(1); }} 15% {{ transform: scale(1.1); }} 28% {{ transform: scale(1.04); }} }}
    .rgb {{ mix-blend-mode: multiply; opacity: 0; }}
    .rgb.c {{ animation: glc 5s steps(1) infinite; }}
    .rgb.m {{ animation: glm 5s steps(1) infinite; }}
    .heart {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: rise ease-out infinite; }}
    @keyframes rise {{
      0% {{ opacity: 0; transform: translate(0, 10px) scale(0.4); }}
      20% {{ opacity: 0.95; transform: translate(-6px, -30px) scale(1); }}
      100% {{ opacity: 0; transform: translate(14px, -190px) scale(0.8) rotate(18deg); }}
    }}
    .scanbar {{ fill: url(#scanGrad); animation: scan 5s linear infinite; }}
    @keyframes scan {{ from {{ transform: translateY(-80px); }} to {{ transform: translateY(760px); }} }}
    .sheen {{ animation: sheen 7s ease-in-out infinite; }}
    @keyframes sheen {{ 0%, 55% {{ transform: translateX(-700px) skewX(-20deg); }} 100% {{ transform: translateX(1500px) skewX(-20deg); }} }}
  </style>
  <defs>{PETAL_DEFS}
    <image id="pic" width="{w}" height="{h}" href="data:image/png;base64,{data}" />
    <clipPath id="frame"><rect width="{w}" height="{h}" rx="26" /></clipPath>
    <clipPath id="cpp"><rect x="848" y="40" width="364" height="410" /></clipPath>
    <clipPath id="no"><rect x="938" y="450" width="154" height="100" /></clipPath>
    <clipPath id="adhd"><rect x="28" y="72" width="400" height="128" /></clipPath>
    <filter id="toMagenta"><feColorMatrix type="matrix" values="0 0 0 0 1  0 1 0 0 0  0 0 0 0 1  0 0 0 1 0" /></filter>
    <filter id="toCyan"><feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0" /></filter>
    <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#4a3b3d" /></pattern>
    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ff8fab" stop-opacity="0" /><stop offset="0.5" stop-color="#ff8fab" stop-opacity="0.18" /><stop offset="1" stop-color="#ff8fab" stop-opacity="0" />
    </linearGradient>
    <linearGradient id="sheenGrad" x1="0" x2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="0.5" stop-color="#fff" stop-opacity="0.45" /><stop offset="1" stop-color="#fff" stop-opacity="0" />
    </linearGradient>
    <linearGradient id="glow" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="{h}">
      <stop offset="0" stop-color="{WINE}" /><stop offset="0.3" stop-color="{BLUSH}" /><stop offset="0.5" stop-color="#ffe3e8" /><stop offset="0.7" stop-color="{BLUSH}" /><stop offset="1" stop-color="{WINE}" />
      <animateTransform attributeName="gradientTransform" type="rotate" values="0 {w / 2} {h / 2};360 {w / 2} {h / 2}" dur="7s" repeatCount="indefinite" />
    </linearGradient>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{w}" height="{h}" fill="#fff" />
    <g class="kb">
      <use href="#pic" xlink:href="#pic" />
      <rect x="848" y="40" width="364" height="410" fill="#fff" />
      <g clip-path="url(#cpp)"><g class="float"><use href="#pic" xlink:href="#pic" /></g></g>
      <rect x="938" y="450" width="154" height="100" fill="#fff" />
      <g clip-path="url(#no)"><g class="beat"><use href="#pic" xlink:href="#pic" /></g></g>
      <g clip-path="url(#adhd)">
        <use class="rgb c" href="#pic" xlink:href="#pic" filter="url(#toCyan)" />
        <use class="rgb m" href="#pic" xlink:href="#pic" filter="url(#toMagenta)" />
      </g>
      {sparks([(1214, 70, 16, 0), (836, 300, 11, 1.4), (1236, 400, 9, 2.6), (446, 120, 12, 0.8), (30, 640, 10, 2), (500, 60, 8, 3)], "#f06292")}
      {"".join(hearts)}
    </g>
    {petals(rng, 14, w, h)}
    <rect width="{w}" height="{h}" fill="url(#scanlines)" opacity="0.035" />
    <rect class="scanbar" x="0" y="0" width="{w}" height="80" />
    <rect class="sheen" x="0" y="-60" width="220" height="{h + 120}" fill="url(#sheenGrad)" />
  </g>
  <rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="24" fill="none" stroke="url(#glow)" stroke-width="4" />
</svg>
"""
    (OUT / "banner.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    (OUT / "header.svg").write_text(header(), encoding="utf-8")
    (OUT / "footer.svg").write_text(footer(), encoding="utf-8")
    banner()
    title("achievements", "Achievements", "実績解除")
    title("repos", "My Favorite Repositories", "推しリポジトリ")
    title("stats", "GitHub Stats", "ステータス画面")
    title("playing", "Now Playing", "再生中")
    title("tech", "Tech Stack", "装備一覧")

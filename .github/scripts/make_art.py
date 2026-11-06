#!/usr/bin/env python3
"""主页上手工设计的动态 SVG（黑白漫画风，和 me 站点“週刊ユキ”同一套语言）。

每张图出浅色、深色两版（*-light.svg / *-dark.svg），README 用 <picture> 按访客主题切换。
改了文字或效果后在仓库根目录运行 `python3 .github/scripts/make_art.py`，再提交 profile/。
需要联网取字体（Google Fonts，只取用到的字）。
"""
import base64
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (CYAN, EASE, EASE_OUT, GRAY, INK, MAGENTA, MINCHO, MINCHO_STACK, PAPER, RED, SERIF,  # noqa: E402
                   SERIF_STACK, Art, balloon, bubbles, chime, focus_lines, jellyfish, letters, load_font,
                   misregister, petals, rain, sparkles, stamp, star, umbrella)

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "profile"
EPISODES = [("achievements", "Achievements", "実績解除"), ("repos", "My Favorite Repositories", "推しリポジトリ"),
            ("stats", "GitHub Stats", "ステータス画面"), ("playing", "Now Playing", "再生中"), ("tech", "Tech Stack", "装備一覧")]
HEAD_JP, FOOT_JP, BALLOON = "夏は、まだ終わらない。", "またね、次の夏で。", "はじめまして！"


def panel(w, h, rx=6):
    """漫画分格：纸、颗粒、外粗内细的双线框。"""
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="{PAPER}" />'
            f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" filter="url(#grain)" />')


def frame(w, h, rx=6):
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="none" stroke="{INK}" stroke-width="3.5" />'
            f'<rect x="11" y="11" width="{w - 22}" height="{h - 22}" rx="{max(rx - 4, 1)}" fill="none" stroke="{INK}" stroke-width="0.9" />')


def text_css(fonts, extra=""):
    return "".join(f.css() for f in fonts) + extra


# ---------------------------------------------------------------- 头图
def header(F):
    W, H = 1200, 340
    rng = random.Random(4)
    art = Art(W, H, "Hi there, I am Yuki")
    title, tl, tw = letters(F["black"], "HI THERE", 112, W / 2, 176, "hero float", spacing=4, step=0.1)
    cmy, ink_title = misregister(title, "hero")
    name = "— I am Yuki —"
    nw = F["regular"].width(name, 30, 1.5)
    nx = W / 2 - nw / 2
    widths = [0.0]
    for ch in name:
        widths.append(widths[-1] + F["regular"].advance(ch, 30) + 1.5)
    seq = widths + [widths[-1]] + widths[::-1]
    n = len(name)
    times = ";".join(f"{t:.3f}" for t in [0.45 * i / n for i in range(n + 1)] + [0.86] + [0.86 + 0.12 * i / n for i in range(n + 1)])
    wv = ";".join(f"{v + (3 if v else 0):.1f}" for v in seq)
    cv = ";".join(f"{nx + v + 3:.1f}" for v in seq)
    jp, _, _ = letters(F["jp"], HEAD_JP, 22, W / 2, 292, "jp float", spacing=6, step=0.12)
    bal_text, _, _ = letters(F["jp"], BALLOON, 21, 975, 92, "bal", spacing=1, step=0)
    art.css.append(text_css(F.values(), f"""
  .hero {{ font: 800 112px {SERIF_STACK}; fill: {INK}; animation-duration: 4.6s; }}
  .name {{ font: 400 30px {SERIF_STACK}; fill: {INK}; letter-spacing: 1.5px; }}
  .meta {{ font: 400 12.5px {SERIF_STACK}; fill: {INK}; letter-spacing: 3.5px; }}
  .jp {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; animation-duration: 5s; }}
  .bal {{ font: 800 21px {MINCHO_STACK}; fill: {INK}; }}
  .caret {{ fill: {INK}; animation: blink 0.9s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
"""))
    art.defs.append(f'<clipPath id="inside"><rect x="12" y="12" width="{W - 24}" height="{H - 24}" rx="3" /></clipPath>'
                    f'<clipPath id="typed"><rect x="{nx - 2:.1f}" y="188" width="0" height="40"><animate attributeName="width" dur="9s" repeatCount="indefinite" calcMode="discrete" values="{wv}" keyTimes="{times}" /></rect></clipPath>')
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  {focus_lines(600, 160, W, H, 70, 250, rng, 0.22)}
  <rect x="12" y="{H - 96}" width="{W - 24}" height="84" fill="url(#toneFine)" mask="url(#toneDown)" opacity="0.7" />
  {jellyfish("h1", 150, 130, 1.3, 0.0, 1.0, 1)}
  {jellyfish("h2", 1050, 178, 0.82, 1.3, 0.9, 2)}
  {jellyfish("h3", 700, 40, 0.4, 2.2, 0.7, 3)}
  {chime("h", 1138, 12, 1.2)}
  {bubbles(rng, 16, 40, W - 40, 220, H, 2.5, 8, (90, 220))}
  {petals(rng, 12, 40, W - 40, 10, 360)}
  {sparkles([(250, 210, 9, 0), (960, 250, 8, 1.2), (520, 60, 6, 2.1), (700, 248, 6, 0.6)])}
</g>""")
    art.color(stamp(28, 44, 32, 82, "週刊", 17, vertical=True))
    art.ink(f'<text class="meta" x="74" y="54">WEEKLY YUKI · VOL.01 · SUMMER ISSUE · 2026</text>'
            f'{balloon(975, 86, 196, 52, bal_text, tail=(-56, 30))}')
    art.color(cmy)
    art.ink(ink_title + f'<g clip-path="url(#typed)"><text class="name" x="{nx:.1f}" y="220">{name}</text></g>'
            f'<rect class="caret" x="{nx:.1f}" y="194" width="2" height="32"><animate attributeName="x" dur="9s" repeatCount="indefinite" calcMode="discrete" values="{cv}" keyTimes="{times}" /></rect>'
            f'<path class="draw" d="M{W / 2 - 150} 304H{W / 2 + 150}" stroke="{INK}" stroke-width="1" />{jp}' + frame(W, H))
    art.write(OUT, "header")


# ---------------------------------------------------------------- 结尾
def footer(F):
    W, H = 1200, 340
    rng = random.Random(8)
    art = Art(W, H, "The end. See you next summer")
    title, tl, tw = letters(F["black"], "THE END", 96, W / 2, 196, "hero float", spacing=4, step=0.1)
    cmy, ink_title = misregister(title, "hero")
    jp, _, _ = letters(F["jp"], FOOT_JP, 22, W / 2, 246, "jp float", spacing=6, step=0.12)
    ripples = "".join(f'<ellipse class="ripple" cx="{rng.uniform(40, W - 40):.0f}" cy="{rng.uniform(H - 52, H - 22):.0f}" rx="{rng.uniform(14, 26):.0f}" ry="{rng.uniform(3, 5):.1f}" '
                      f'fill="none" stroke="{INK}" stroke-width="0.8" style="animation-delay:{-rng.uniform(0, 2.2):.2f}s;animation-duration:{rng.uniform(1.8, 2.8):.1f}s" />' for _ in range(16))
    art.css.append(text_css(F.values(), f"""
  .hero {{ font: 800 96px {SERIF_STACK}; fill: {INK}; animation-duration: 4.6s; }}
  .meta {{ font: 400 13px {SERIF_STACK}; fill: {INK}; letter-spacing: 5px; }}
  .jp {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; animation-duration: 5s; }}
  .seal {{ transform-box: fill-box; transform-origin: center; animation: seal 4.8s {EASE_OUT} infinite; }}
  @keyframes seal {{ 0%, 70%, 100% {{ transform: rotate(-8deg) scale(1); }} 74% {{ transform: rotate(-8deg) scale(1.12); }} 80% {{ transform: rotate(-8deg) scale(0.98); }} }}
"""))
    art.defs.append(f'<clipPath id="inside"><rect x="12" y="12" width="{W - 24}" height="{H - 24}" rx="3" /></clipPath>')
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="{H - 70}" width="{W - 24}" height="58" fill="url(#tone)" opacity="0.55" />
  {rain(12, 12, W - 24, H, rng, 150)}
  {ripples}
  {umbrella(210, 176, 1.2)}
  {jellyfish("f1", 1040, 120, 0.95, 0.4, 1.0, 5)}
  {jellyfish("f2", 930, 64, 0.45, 1.9, 0.8, 6)}
  {bubbles(rng, 10, 380, W - 260, 200, H - 60, 2.5, 6, (60, 150))}
  {petals(rng, 8, 300, W - 200, 10, 300)}
</g>
<text class="meta" x="{W / 2}" y="98" text-anchor="middle">SEMINAR · SCIENCE · INTELLIGENCE · FUTURE</text>""")
    art.color(cmy)
    seal_x = tl + tw + 54
    art.ink(ink_title + jp + frame(W, H))
    art.color(f'<g class="seal"><circle cx="{seal_x:.0f}" cy="150" r="30" fill="{RED}" /><circle cx="{seal_x:.0f}" cy="150" r="25" fill="none" stroke="#ffffff" stroke-width="1.2" />'
              f'<text x="{seal_x:.0f}" y="161" text-anchor="middle" style="font: 800 30px {MINCHO_STACK}; fill: #ffffff">完</text></g>')
    art.write(OUT, "footer")


# ---------------------------------------------------------------- 分区标题
def title(i, name, english, japanese, F):
    W, H = 900, 128
    rng = random.Random(i * 13 + 1)
    art = Art(W, H, english)
    size = 40
    tw = F["bold"].width(english, size, 0.5)
    label = f"第{i}話"
    sw = 54
    total = sw + 16 + tw
    x0 = W / 2 - total / 2
    text, _, _ = letters(F["bold"], english, size, x0 + sw + 16, 72, "t float", spacing=0.5, step=0.07, anchor="start")
    cmy, ink_text = misregister(text, "t")
    jp, jl, jw = letters(F["jp"], japanese, 15, W / 2, 110, "j", spacing=8, step=0)
    right = x0 + total
    motif = [lambda: jellyfish(f"t{i}", right + 70, 40, 0.42, i * 0.7, 0.55, i),
             lambda: chime(f"t{i}", right + 64, 6, 0.8),
             lambda: bubbles(rng, 6, right + 30, right + 110, 60, 110, 3, 7, (40, 80))][i % 3]()
    art.css.append(text_css([F["bold"], F["regular"], F["jp"]], f"""
  .t {{ font: 700 {size}px {SERIF_STACK}; fill: {INK}; }}
  .meta {{ font: 400 11.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 4px; }}
  .j {{ font: 800 15px {MINCHO_STACK}; fill: {INK}; }}
"""))
    art.ink(f'<text class="meta" x="{x0 + sw + 16:.1f}" y="30">EPISODE {i:02d} · {english.upper()}</text>'
            f'<path class="draw" d="M{jl - 26:.0f} 105H{jl - 150:.0f}" stroke="{INK}" stroke-width="1" />'
            f'<path class="draw" d="M{jl + jw + 26:.0f} 105H{jl + jw + 150:.0f}" stroke="{INK}" stroke-width="1" />'
            f'{motif}{bubbles(rng, 4, x0 - 90, x0 - 20, 60, 110, 2.5, 5.5, (40, 80))}'
            f'{sparkles([(x0 - 40, 34, 6, 0.3), (right + 18, 26, 5, 1.6)])}')
    art.color(stamp(round(x0), 44, sw, 36, label, 17) + cmy)
    art.ink(ink_text + jp)
    art.write(OUT, f"title-{name}")


# ---------------------------------------------------------------- 分隔线
def divider():
    W, H = 800, 40
    rng = random.Random(2)
    art = Art(W, H, role="presentation")
    art.defs.append(f'<linearGradient id="ruleL" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" /></linearGradient>'
                    f'<linearGradient id="ruleR" x1="0" x2="1"><stop offset="0" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    art.ink(f'<rect x="30" y="19.5" width="340" height="1" fill="url(#ruleL)" /><rect x="430" y="19.5" width="340" height="1" fill="url(#ruleR)" />'
            f'<rect x="30" y="23" width="340" height="0.5" fill="url(#ruleL)" opacity="0.6" /><rect x="430" y="23" width="340" height="0.5" fill="url(#ruleR)" opacity="0.6" />'
            f'<g transform="translate(400 20)"><g class="twinkle" style="animation-duration:5s"><path d="M0 -7C1 -10 3 -12 5 -12C9 -12 11 -6 9 0C7 6 3 10 0 13C-3 10 -7 6 -9 0C-11 -6 -9 -12 -5 -12C-3 -12 -1 -10 0 -7Z" '
            f'transform="scale(0.8)" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" /></g></g>'
            f'{bubbles(rng, 5, 360, 440, 34, 40, 1.8, 3.5, (14, 30))}')
    art.color(f'<circle cx="400" cy="20" r="1.6" fill="{RED}" />')
    art.write(OUT, "divider")


# ---------------------------------------------------------------- 声波
def wings():
    import math
    W, H, N, PITCH, BAR, GAP = 260, 420, 26, 16, 8, 8
    for side in ("left", "right"):
        rng = random.Random(17)
        left = side == "left"
        art = Art(W, H, role="presentation")
        bars = []
        for i in range(N):
            t = (i + 0.5) / N
            length = (50 + 190 * math.sin(math.pi * t) ** 0.85) * rng.uniform(0.82, 1.0)
            x = (W - GAP - length) if left else GAP
            y = 2 + i * PITCH + (PITCH - BAR) / 2
            dur, delay = rng.uniform(0.75, 1.6), -rng.uniform(0, 1.6)
            bars.append(f'<g class="bar" style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s"><rect x="{x:.1f}" y="{y:.1f}" width="{length:.1f}" height="{BAR}" rx="1.5" fill="url(#{"tone" if i % 2 else "toneFine"})" stroke="{INK}" stroke-width="0.9" /></g>')
        origin = "right center" if left else "left center"
        art.css.append(f".bar {{ transform-box: fill-box; transform-origin: {origin}; animation: beat 1.2s {EASE} infinite alternate; }}"
                       "@keyframes beat { from { transform: scaleX(0.26); } to { transform: scaleX(1); } }")
        art.defs.append(f'<linearGradient id="fade" x1="{0 if left else 1}" x2="{1 if left else 0}"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="0.45" stop-color="#fff" stop-opacity="0.9" /><stop offset="1" stop-color="#fff" /></linearGradient>'
                        f'<mask id="side"><rect width="{W}" height="{H}" fill="url(#fade)" /></mask>')
        mx = (lambda v: v) if left else (lambda v: W - v)
        art.ink(f'<g mask="url(#side)">{"".join(bars)}</g>{bubbles(rng, 10, 20, W - 20, 160, H, 3, 8, (90, 220))}'
                f'{petals(rng, 4, 20, W - 20, 0, 420)}{jellyfish(f"w{side}", mx(52), 96, 0.5, 0.9 if left else 2.0, 0.6, 9)}')
        art.write(OUT, f"wing-{side}")


# ---------------------------------------------------------------- 横幅：C.png 漫画化
HEART = "M10 18C8 14 0 10 0 4.5 0 0.5 3 -1.5 5.5 -1.5 7.5 -1.5 9 0 10 2 11 0 12.5 -1.5 14.5 -1.5 17 -1.5 20 0.5 20 4.5 20 10 12 14 10 18Z"


def banner(F):
    w, h = 1260, 709
    rng = random.Random(9)
    data = base64.b64encode((ROOT / "C.png").read_bytes()).decode()
    hearts = "".join(
        f'<g transform="translate({rng.uniform(520, 760):.0f} 250) scale({rng.uniform(0.8, 1.35):.2f})"><path class="heart" d="{HEART}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6" '
        f'style="animation-duration:{(d := rng.uniform(4.5, 7)):.1f}s;animation-delay:{-rng.uniform(0, d):.1f}s" /></g>' for _ in range(7))
    sfx_doki, _, _ = letters(F["jp"], "ドキッ", 54, 0, 0, "sfx", spacing=2, step=0, anchor="start")
    sfx_kira, _, _ = letters(F["jp"], "キラッ", 40, 0, 0, "sfx", spacing=2, step=0, anchor="start")
    art = Art(w, h, "ADHD? Python, C++, no problem")
    art.css.append(text_css([F["jp"], F["regular"]], f"""
    .kb {{ transform-origin: 630px 354px; animation: kb 18s {EASE} infinite alternate; }}
    @keyframes kb {{ from {{ transform: scale(1); }} to {{ transform: scale(1.03); }} }}
    .cppfloat {{ transform-origin: 1030px 245px; animation: cppfloat 4.4s {EASE} infinite; }}
    @keyframes cppfloat {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 30% {{ transform: translateY(-14px) rotate(-3deg); }} 65% {{ transform: translateY(-5px) rotate(2deg); }} }}
    .beat {{ transform-origin: 1015px 500px; animation: beat 1.5s infinite; }}
    @keyframes beat {{ 0% {{ transform: scale(1); animation-timing-function: {EASE_OUT}; }} 12% {{ transform: scale(1.13) rotate(-2deg); }} 26% {{ transform: scale(1.03); }} 40%, 100% {{ transform: scale(1); }} }}
    .mis {{ opacity: 0; }}
    .mis.c {{ animation: misBlink 3.8s steps(1) infinite; }}
    .mis.m {{ animation: misBlink 3.8s steps(1) infinite; animation-delay: -0.05s; }}
    @keyframes misBlink {{ 0%, 68%, 100% {{ opacity: 0; transform: translate(0, 0); }} 70% {{ opacity: 0.85; transform: translate(-6px, 1px); }} 73% {{ opacity: 0.85; transform: translate(5px, -1px); }} 76% {{ opacity: 0; }} 86% {{ opacity: 0.7; transform: translate(-3px, 0); }} 88% {{ opacity: 0; }} }}
    .heart {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: rise {EASE_OUT} infinite; }}
    @keyframes rise {{ 0% {{ opacity: 0; transform: translate(0, 10px) scale(0.4); }} 18% {{ opacity: 1; transform: translate(-6px, -30px) scale(1); }} 100% {{ opacity: 0; transform: translate(14px, -200px) scale(0.85) rotate(16deg); }} }}
    .s54 {{ font-size: 54px; }} .s40 {{ font-size: 40px; }}
    .sfx {{ font: 800 1px {MINCHO_STACK}; fill: {INK}; stroke: {PAPER}; stroke-width: 6px; paint-order: stroke; stroke-linejoin: round; }}
    .sfx-doki {{ transform-origin: 520px 90px; animation: sfx 2.4s infinite; }}
    .sfx-kira {{ transform-origin: 900px 470px; animation: sfx 2.4s infinite; animation-delay: -1.2s; }}
    @keyframes sfx {{ 0% {{ transform: scale(0.8) rotate(-12deg); opacity: 0; animation-timing-function: {EASE_OUT}; }} 12% {{ transform: scale(1.08) rotate(-10deg); opacity: 1; }} 22%, 70% {{ transform: scale(1) rotate(-10deg); opacity: 1; }} 85%, 100% {{ transform: scale(1) rotate(-10deg); opacity: 0; }} }}
"""))
    art.defs.append(f"""
    <image id="pic" width="{w}" height="{h}" href="data:image/png;base64,{data}" />
    <filter id="manga" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0" />
      <feComponentTransfer><feFuncR type="gamma" exponent="1.25" amplitude="1.03" /><feFuncG type="gamma" exponent="1.25" amplitude="1.03" /><feFuncB type="gamma" exponent="1.25" amplitude="1.03" /></feComponentTransfer></filter>
    <filter id="toCyan"><feColorMatrix type="matrix" values="0.18 0 0 0 0.82  0 0.29 0 0 0.71  0 0 0.16 0 0.84  0 0 0 1 0" /></filter>
    <filter id="toMagenta"><feColorMatrix type="matrix" values="0.1 0 0 0 0.9  0 0.78 0 0 0.22  0 0 0.53 0 0.47  0 0 0 1 0" /></filter>
    <clipPath id="frameClip"><rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="6" /></clipPath>
    <clipPath id="cpp"><rect x="848" y="40" width="364" height="410" /></clipPath>
    <clipPath id="no"><rect x="938" y="450" width="154" height="100" /></clipPath>
    <clipPath id="adhd"><rect x="28" y="72" width="400" height="128" /></clipPath>
    <radialGradient id="vign" cx="0.5" cy="0.45" r="0.75"><stop offset="0.55" stop-color="#fff" stop-opacity="0" /><stop offset="1" stop-color="#fff" /></radialGradient>
    <mask id="corners"><rect width="{w}" height="{h}" fill="url(#vign)" /></mask>""")
    art.color(f"""<g clip-path="url(#frameClip)">
    <rect width="{w}" height="{h}" fill="#ffffff" />
    <g class="kb">
      <use class="gray" href="#pic" xlink:href="#pic" />
      <rect x="848" y="40" width="364" height="410" fill="#ffffff" />
      <g clip-path="url(#cpp)"><g class="cppfloat"><use class="gray" href="#pic" xlink:href="#pic" /></g></g>
      <rect x="938" y="450" width="154" height="100" fill="#ffffff" />
      <g clip-path="url(#no)"><g class="beat"><use class="gray" href="#pic" xlink:href="#pic" /></g></g>
      <g clip-path="url(#adhd)" style="mix-blend-mode:multiply"><use class="mis c" href="#pic" xlink:href="#pic" filter="url(#toCyan)" /><use class="mis m" href="#pic" xlink:href="#pic" filter="url(#toMagenta)" /></g>
      <g style="mix-blend-mode:multiply">{focus_lines(600, 230, w, h, 90, 330, rng, 0.3)}</g>
      <rect width="{w}" height="{h}" fill="url(#tone)" mask="url(#corners)" opacity="0.35" style="mix-blend-mode:multiply" />
      {hearts}
    </g>
    <g class="sfx-doki"><g transform="translate(470 108) rotate(-10)">{sfx_doki.replace('class="sfx"', 'class="sfx s54"')}</g></g>
    <g class="sfx-kira"><g transform="translate(860 470) rotate(-10)">{sfx_kira.replace('class="sfx"', 'class="sfx s40"')}</g></g>
    {bubbles(rng, 16, 20, w - 20, 520, h + 10, 6, 16, (220, 480))}
    {petals(rng, 12, 0, w, -10, 760)}
    {sparkles([(1214, 70, 16, 0), (836, 300, 11, 1.4), (1236, 400, 9, 2.6), (446, 210, 12, 0.8), (30, 640, 10, 2), (500, 40, 8, 3)])}
  </g>""")
    art.color(stamp(w - 98, 22, 72, 30, "No.01", 15) + frame(w, h))
    # 横幅是一张白底插画，深浅色都用同一版
    (OUT / "banner.svg").write_text(art.render("light"), encoding="utf-8")


if __name__ == "__main__":
    titles = "".join(e[1] for e in EPISODES)
    jp_all = "".join(e[2] for e in EPISODES) + HEAD_JP + FOOT_JP + BALLOON + "第話週刊完涼ドキッキラッ0123456789"
    F = {
        "black": load_font(SERIF, 800, "HI THERE THE END"),
        "bold": load_font(SERIF, 700, titles),
        "regular": load_font(SERIF, 400, "— I am Yuki — WEEKLY YUKI · VOL.01 · SUMMER ISSUE No.01 2026 SEMINAR SCIENCE INTELLIGENCE FUTURE EPISODE 0123456789 " + titles.upper()),
        "jp": load_font(MINCHO, 800, jp_all),
    }
    if not all(F.values()):
        sys.exit("需要联网取字体")
    header(F)
    footer(F)
    banner(F)
    divider()
    wings()
    for i, (name, en, jp) in enumerate(EPISODES, 1):
        title(i, name, en, jp, F)

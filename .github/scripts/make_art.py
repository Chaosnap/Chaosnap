#!/usr/bin/env python3
"""主页上手工设计的 SVG（黑白漫画风，和 me 站点“週刊ユキ”同一套语言）。

每张图出浅色、深色两版（*-light.svg / *-dark.svg），README 用 <picture> 按访客主题切换。
改了文字或效果后在仓库根目录运行 `python3 .github/scripts/make_art.py`，再提交 profile/。
只重做其中几张：`python3 .github/scripts/make_art.py header quote`。需要联网取字体（Google Fonts，只取用到的字）。

性能上的约定：只有头图、结尾和世界线台词条保留少量很轻的环境动画（风铃、电线、雨、字面扫光），
漫画页、分区标题、分隔线和播放卡全部是静态图；不再有漂浮的水母、泡沫、花瓣，也不再用颗粒滤镜。
"""
import base64
import math
import pathlib
import random
import re
import sys
from html import escape

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (EASE, EASE_OUT, GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_INK, NIGHT_RED, PAPER, RED, SCHEMES, SERIF,  # noqa: E402
                   SERIF_STACK, Art, barcode, chime, cloud, fence, film_strip, firework, lens_flare, letters, load_font,
                   pole, rain_field, sheen_grad, splash, splashes, stamp, starburst, sun, sun_ink, sun_rays, title_fx,
                   wagasa, wire, wire_point)

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "profile"
EPISODES = [("achievements", "Achievements", "実績解除"), ("repos", "My Favorite Repositories", "推しリポジトリ"),
            ("stats", "GitHub Stats", "ステータス画面"), ("playing", "Now Playing", "再生中"), ("tech", "Tech Stack", "装備一覧")]
HEAD_JP, FOOT_JP = "夏は、まだ終わらない。", "またね、次の夏で。"
TOP_LEFT, TOP_RIGHT, TOP_MID = "WEEKLY YUKI  ·  SUMMER ISSUE  ·  2026", "No.01  ·  定価 ¥0（税込）", "週刊ユキ"
SIGN = "夏ノ町"
QUOTES = ["> Initializing World Line 1.048596 ...", "もし世界がバグなら、君は僕のパッチ。", "この世界線で、また君に会いたい。",
          "ERROR 404: Social Life Not Found.", "while (alive) { code(); anime(); sleep(0); }", "Reality is temporary. Code is eternal.", "El Psy Kongroo."]
TONE_GRAY_SKY = "#e6e5e1"  # A 格白天的天空：比纸略深
NIGHT_INK_SFX = "#eceae6"
WORLDLINES = ["1.048596", "0.571024", "0.523299", "1.130205", "0.337187", "1.382733", "0.000000"]
TRACK = ("Hitchcock", "Yorushika", "ヨルシカ")  # 播放卡上的曲子


def panel(w, h, rx=6):
    """漫画分格：纸。"""
    return f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="{PAPER}" />'


def frame(w, h, rx=6):
    """外粗内细的双线框。"""
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="none" stroke="{INK}" stroke-width="3.5" />'
            f'<rect x="11" y="11" width="{w - 22}" height="{h - 22}" rx="{max(rx - 4, 1)}" fill="none" stroke="{INK}" stroke-width="0.9" />')


def card(w, h, rx=6):
    """内页卡片：纸、细边、再一圈发丝线。"""
    return (f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx}" fill="{PAPER}" />'
            f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx}" fill="none" stroke="{INK}" stroke-width="1.5" />'
            f'<rect x="6.5" y="6.5" width="{w - 13}" height="{h - 13}" rx="{max(rx - 3, 1)}" fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.7" />')


def text_css(fonts, extra=""):
    return "".join(f.css() for f in fonts if f) + extra


def inside(w, h):
    return f'<clipPath id="inside"><rect x="12" y="12" width="{w - 24}" height="{h - 24}" rx="3" /></clipPath>'


def tag(x, y, label, size=13, h=24):
    """红色印章标签，返回 (浅色, 深色)。"""
    w = int(size * 1.15 * len(label) + 18)
    s = stamp(x - w if x < 0 else x, y, w, h, label, size)
    return s, s.replace(RED, NIGHT_RED)


# ---------------------------------------------------------------- 头图：夕焼けの屋上
def header(F):
    W, H = 1200, 430
    art = Art(W, H, "Hi there, I am Yuki")
    SX, SY, SR = 948, 200, 86
    title, tl, tw = letters(F["black"], "HI THERE", 118, 54, 200, "hero", spacing=3, step=0, anchor="start")
    name, _, nw = letters(F["regular"], "— I am Yuki —", 32, 60, 252, "name", spacing=1.5, step=0, anchor="start")
    jp, jl, jw = letters(F["jp"], HEAD_JP, 21, 92, 292, "jp", spacing=6, step=0, anchor="start")
    burst_txt, _, _ = letters(F["jp"], "新連載!!", 17, tl + tw + 66, 102, "bt", spacing=0, step=0)
    sign_txt = "".join(f'<text x="0" y="{18 + i * 19}" text-anchor="middle" class="sign">{c}</text>' for i, c in enumerate(SIGN))
    art.css.append(text_css(F.values(), f"""
  .hero {{ font: 800 118px {SERIF_STACK}; fill: url(#sheenH); stroke: {PAPER}; stroke-width: 3px; paint-order: stroke; stroke-linejoin: round; }}
  .name {{ font: 400 32px {SERIF_STACK}; fill: {INK}; letter-spacing: 1.5px; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
  .jp {{ font: 800 21px {MINCHO_STACK}; fill: {INK}; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
  .bt {{ font: 800 17px {MINCHO_STACK}; fill: #ffffff; }}
  .bar {{ font: 400 12.5px {SERIF_STACK}, {MINCHO_STACK}; fill: {PAPER}; letter-spacing: 3px; }}
  .barjp {{ font: 800 15px {MINCHO_STACK}; fill: {PAPER}; letter-spacing: 6px; }}
  .sign {{ font: 800 15px {MINCHO_STACK}; fill: {INK}; }}
  .filmtxt {{ font: 400 9px {SERIF_STACK}; fill: {PAPER}; letter-spacing: 2.5px; }}
"""))
    art.defs.append(inside(W, H) + sheen_grad("sheenH", tl, tl + tw, 6.4, 1.0, 80)
                    + f'<radialGradient id="rayFade" gradientUnits="userSpaceOnUse" cx="{SX}" cy="{SY}" r="620"><stop offset="0.1" stop-color="#fff" /><stop offset="1" stop-color="#fff" stop-opacity="0" /></radialGradient>'
                    f'<mask id="rayMask"><rect width="{W}" height="{H}" fill="url(#rayFade)" /></mask>')

    # 远景：天空网点、放射线（静止）
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="44" width="{W - 24}" height="190" fill="url(#tone)" opacity="0.42" mask="url(#toneUp)" />
  <g mask="url(#rayMask)">{sun_rays(SX, SY, 48, SR + 16, 1100, 0.12).replace('class="spin" ', '')}</g>
</g>""")
    light, dark = sun("H", SX, SY, SR)
    art.color(f'<g clip-path="url(#inside)">{light}</g>', f'<g clip-path="url(#inside)">{dark}</g>')

    # 中景：日轮横纹、积雨云、电线杆和电线、风铃
    big, ins = pole(1112, H, 0.95, 52)
    wires = []
    for i, (ix, iy) in enumerate(ins):
        wires.append(wire(ix, iy, -40, iy - 26 + i * 9, 34 + i * 4, 1.4, 4.8, i * 0.4))
        wires.append(wire(ix, iy, W + 40, iy + 30 + i * 6, 6, 1.4, 4.8, i * 0.3))
    hx, hy = wire_point(ins[1][0], ins[1][1], -40, ins[1][1] - 26 + 9, 38, 0.17)
    art.ink(f"""<g clip-path="url(#inside)">
  {sun_ink("H", SX, SY, SR)}
  {cloud("c1", 1080, 404, 440, 210, 3, shade_left=False)}
  {cloud("c2", 175, 372, 380, 120, 7)}
  {cloud("c3", 640, 392, 300, 90, 12)}
  <g>{"".join(wires)}</g>
  {big}
  <g transform="translate(1098 230)"><rect x="-15" y="0" width="30" height="64" fill="{PAPER}" stroke="{INK}" stroke-width="1.6" />{sign_txt}<rect x="-15" y="64" width="30" height="20" fill="{INK}" /><text x="0" y="79" text-anchor="middle" class="filmtxt" style="font-size:12px">12</text></g>
  {chime("H", round(hx), round(hy), 1.15)}
</g>""")
    art.color(lens_flare(SX, SY, 360, 330, "light").replace('class="flare"', ''), lens_flare(SX, SY, 360, 330, "dark").replace('class="flare"', ''))

    # 近景：天台的金网、胶片边
    art.ink(f"""<g clip-path="url(#inside)">
  {fence("H", 12, W - 12, 318, 388, [96, 420, 760, 1188])}
  {film_strip(388, W)}
</g>
<rect x="12" y="12" width="{W - 24}" height="32" fill="{INK}" />
<text class="bar" x="30" y="32.5">{TOP_LEFT}</text>
<text class="barjp" x="{W / 2}" y="34" text-anchor="middle">{TOP_MID}</text>
<text class="bar" x="{W - 30}" y="32.5" text-anchor="end">{TOP_RIGHT}</text>""")
    art.color(starburst(tl + tw + 66, 96, 46, burst_txt))
    art.ink(title_fx(title, 6.0, 1.5) + name + f'<path d="M62 285H84" stroke="{INK}" stroke-width="1.4" />' + jp
            + f'<g transform="translate(-6 0)">{barcode(1038, 332, random.Random(11), 104, 28, "4 910123 401065")}</g>' + frame(W, H))
    art.color(f'<rect x="62" y="283.5" width="22" height="3" fill="{RED}" />', f'<rect x="62" y="283.5" width="22" height="3" fill="{NIGHT_RED}" />')
    art.write(OUT, "header")


# ---------------------------------------------------------------- 结尾：雨の屋上
def footer(F):
    W, H = 1200, 400
    rng = random.Random(8)
    art = Art(W, H, "The end. See you next summer")
    title, tl, tw = letters(F["black"], "THE END", 100, W / 2, 200, "hero", spacing=4, step=0)
    jp, _, _ = letters(F["jp"], FOOT_JP, 22, W / 2, 248, "jp", spacing=6, step=0)
    seal_x = tl + tw + 58
    floor_y = 318
    puddles = []
    for px, py, rx in [(170, 352, 70), (520, 366, 96), (860, 350, 64), (1080, 372, 80), (380, 340, 40)]:
        puddles.append(f'<ellipse cx="{px}" cy="{py}" rx="{rx}" ry="{rx * 0.16:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="0.9" />'
                       f'<path d="M{px - rx * 0.6:.0f} {py - 1}h{rx * 0.5:.0f}M{px - rx * 0.1:.0f} {py + 3}h{rx * 0.6:.0f}M{px - rx * 0.4:.0f} {py + 6}h{rx * 0.3:.0f}" stroke="{INK}" stroke-width="0.6" opacity="0.7" />'
                       + "".join(f'<ellipse class="ring" cx="{px + rng.uniform(-rx * 0.5, rx * 0.5):.0f}" cy="{py:.0f}" rx="{rx * 0.4:.0f}" ry="{rx * 0.07:.1f}" fill="none" stroke="{INK}" stroke-width="0.7" '
                                 f'style="animation-duration:{(d := rng.uniform(1.4, 2.4)):.2f}s;animation-delay:{-rng.uniform(0, d):.2f}s" />' for _ in range(3)))
    tiles = "".join(f'<path d="M{W / 2 + (x - W / 2) * 0.25:.0f} {floor_y}L{x:.0f} {H}" />' for x in range(-600, W + 700, 120))
    tiles += "".join(f'<path d="M0 {y}H{W}" />' for y in (330, 346, 368, 394))
    canopy_splash = "".join(splash(x, y, 0.42, rng.uniform(1.2, 1.8), rng.uniform(0, 1.8)) for x, y in [(-70, -30), (-28, -52), (24, -54), (66, -34), (100, -14)])
    art.css.append(text_css([F["black"], F["regular"], F["jp"]], f"""
  .hero {{ font: 800 100px {SERIF_STACK}; fill: url(#sheenF); stroke: {PAPER}; stroke-width: 3px; paint-order: stroke; stroke-linejoin: round; }}
  .meta {{ font: 400 13px {SERIF_STACK}; fill: {INK}; letter-spacing: 5px; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
  .jp {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
"""))
    art.defs.append(inside(W, H) + sheen_grad("sheenF", tl, tl + tw, 6.4, 3.2, 70)
                    + f'<radialGradient id="calm"><stop offset="0.35" stop-color="{PAPER}" stop-opacity="0.9" /><stop offset="1" stop-color="{PAPER}" stop-opacity="0" /></radialGradient>')
    umbrella = wagasa(250, 214, 1.05).replace('<g class="umbrella">', '<g class="umbrella">' + canopy_splash, 1)
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="12" width="{W - 24}" height="180" fill="url(#tone)" opacity="0.5" mask="url(#toneUp)" />
  {rain_field(rng, 12, 12, W - 24, H, 0, 220, -0.16)}
  {fence("F", 12, W - 12, 168, floor_y, [70, 330, 610, 890, 1150], 15)}
  <rect x="12" y="{floor_y}" width="{W - 24}" height="{H - floor_y - 12}" fill="url(#toneFine)" opacity="0.6" />
  <g fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.5">{tiles}</g>
  <rect x="12" y="{floor_y - 2}" width="{W - 24}" height="3" fill="{INK}" />
  {"".join(puddles)}
  {splashes(rng, 26, 30, W - 30, floor_y + 12, H - 16)}
  <g transform="rotate(-11 250 220)">{umbrella}</g>
  {chime("F", 1150, 12, 1.05, "雨")}
  {rain_field(random.Random(3), 12, 12, W - 24, H - 30, 64, 0, -0.16)}
  <ellipse cx="{W / 2}" cy="190" rx="360" ry="96" fill="url(#calm)" />
</g>
<text class="meta" x="{W / 2}" y="100" text-anchor="middle">SEMINAR · SCIENCE · INTELLIGENCE · FUTURE</text>""")
    art.ink(title_fx(title, 5.0, 1.25) + jp + frame(W, H))

    def seal(red):
        return (f'<g transform="rotate(-7 {seal_x:.0f} 158)"><circle cx="{seal_x:.0f}" cy="158" r="31" fill="{red}" /><circle cx="{seal_x:.0f}" cy="158" r="26" fill="none" stroke="#ffffff" stroke-width="1.2" />'
                f'<text x="{seal_x:.0f}" y="169" text-anchor="middle" style="font: 800 30px {MINCHO_STACK}; fill: #ffffff">完</text></g>')
    art.color(seal(RED), seal(NIGHT_RED))
    art.write(OUT, "footer")


# ---------------------------------------------------------------- 分区标题：目次风，静态
def title(i, name, english, japanese):
    W, H = 900, 116
    bold = load_font(SERIF, 700, english + "0123456789")
    jp = load_font(MINCHO, 800, f"第{i}話" + japanese)
    art = Art(W, H, english, lean=True)
    cx = W / 2
    art.css.append(text_css([bold, jp], f"""
  .num {{ font: 700 104px {SERIF_STACK}; fill: url(#toneBig); }}
  .t {{ font: 700 36px {SERIF_STACK}; fill: {INK}; letter-spacing: 0.5px; stroke: {PAPER}; stroke-width: 8px; paint-order: stroke; stroke-linejoin: round; }}
  .j {{ font: 800 12.5px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 7px; stroke: {PAPER}; stroke-width: 6px; paint-order: stroke; }}
"""))
    # 背后一枚淡淡的网点话数，上面是短线夹着的红章、英文标题、日文副题
    art.ink(f'<text class="num" x="{cx}" y="104" text-anchor="middle" opacity="0.5">{i:02d}</text>'
            f'<path d="M{cx - 150:.0f} 25H{cx - 42:.0f}M{cx + 42:.0f} 25H{cx + 150:.0f}" stroke="{INK}" stroke-width="0.8" />'
            f'<circle cx="{cx - 154:.0f}" cy="25" r="1.6" fill="{INK}" /><circle cx="{cx + 154:.0f}" cy="25" r="1.6" fill="{INK}" />'
            f'<text class="t" x="{cx}" y="76" text-anchor="middle">{escape(english)}</text>'
            f'<text class="j" x="{cx + 3.5}" y="104" text-anchor="middle">{japanese}</text>')
    s, d = tag(round(cx - 28), 14, f"第{i}話", 12, 22)
    s = s.replace(f'width="{int(12 * 1.15 * 3 + 18)}"', 'width="56"')
    art.color(s, s.replace(RED, NIGHT_RED))
    art.write(OUT, f"title-{name}")


# ---------------------------------------------------------------- 分隔线：一枚菱形，静态
def divider():
    W, H, CY = 800, 36, 18
    art = Art(W, H, role="presentation", lean=True)
    art.defs.append(f'<linearGradient id="ruleL" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" /></linearGradient>'
                    f'<linearGradient id="ruleR" x1="0" x2="1"><stop offset="0" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    art.ink(f'<rect x="30" y="{CY - 0.5}" width="330" height="1" fill="url(#ruleL)" /><rect x="440" y="{CY - 0.5}" width="330" height="1" fill="url(#ruleR)" />'
            f'<circle cx="381" cy="{CY}" r="1.3" fill="{INK}" /><circle cx="419" cy="{CY}" r="1.3" fill="{INK}" />'
            f'<rect x="394.5" y="{CY - 5.5}" width="11" height="11" fill="{PAPER}" stroke="{INK}" stroke-width="1" transform="rotate(45 400 {CY})" />')
    art.color(f'<circle cx="400" cy="{CY}" r="1.9" fill="{RED}" />', f'<circle cx="400" cy="{CY}" r="1.9" fill="{NIGHT_RED}" />')
    art.write(OUT, "divider")


# ---------------------------------------------------------------- 播放卡：封面、唱片、曲名，静态
def spotify_mark(x, y, r=7.5):
    return (f'<g transform="translate({x} {y})"><circle r="{r}" fill="{INK}" />'
            f'<path d="M-4.6 -1.8Q0 -4.6 4.6 -1.8" fill="none" stroke="{PAPER}" stroke-width="1.6" stroke-linecap="round" />'
            f'<path d="M-3.8 0.9Q0 -1.3 3.8 0.9" fill="none" stroke="{PAPER}" stroke-width="1.4" stroke-linecap="round" />'
            f'<path d="M-3 3.4Q0 1.8 3 3.4" fill="none" stroke="{PAPER}" stroke-width="1.2" stroke-linecap="round" /></g>')


def vinyl(cx, cy, r):
    grooves = "".join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" />' for rr in range(int(r * 0.42), int(r) - 4, 5))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{INK}" />'
            f'<g fill="none" stroke="{PAPER}" stroke-width="0.5" opacity="0.35">{grooves}</g>'
            f'<path d="M{cx + r * 0.78 * math.cos(-2.1):.1f} {cy + r * 0.78 * math.sin(-2.1):.1f}A{r * 0.78:.1f} {r * 0.78:.1f} 0 0 1 {cx + r * 0.78 * math.cos(-1.1):.1f} {cy + r * 0.78 * math.sin(-1.1):.1f}" '
            f'fill="none" stroke="{PAPER}" stroke-width="2.4" stroke-linecap="round" opacity="0.55" />'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.36:.1f}" fill="{PAPER}" /><circle cx="{cx}" cy="{cy}" r="{r * 0.36:.1f}" fill="url(#toneFine)" opacity="0.55" />'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.36:.1f}" fill="none" stroke="{INK}" stroke-width="1" />'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.22:.1f}" fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.7" />'
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="{INK}" />')


def now_playing():
    W, H = 900, 262
    song, artist, artist_jp = TRACK
    bold = load_font(SERIF, 700, song)
    reg = load_font(SERIF, 400, artist + "NOW PLAYING ON SPOTIFY")
    jp = load_font(MINCHO, 800, artist_jp + "再生中")
    art = Art(W, H, f"Now playing on Spotify: {artist} - {song}", lean=True)
    cover = base64.b64encode((OUT / "images" / "cover.jpg").read_bytes()).decode()
    art.css.append(text_css([bold, reg, jp], f"""
  .np-l {{ font: 400 11px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 4px; }}
  .np-t {{ font: 700 40px {SERIF_STACK}; fill: {INK}; }}
  .np-a {{ font: 400 20px {SERIF_STACK}; fill: {INK}; opacity: 0.8; }}
  .np-j {{ font: 800 14px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
"""))
    art.defs.append('<clipPath id="coverClip"><rect x="44" y="30" width="200" height="200" rx="4" /></clipPath>')
    X = 420
    # 静态的频谱：一串正弦叠出来的高低
    bars = []
    for k in range(46):
        env = 0.55 + 0.45 * math.sin(k * 0.53 + 0.8) * math.sin(k * 0.21 + 2.1)
        hgt = 4 + 30 * abs(env) * (0.75 + 0.25 * math.sin(k * 1.7))
        bars.append(f'<rect x="{X + k * 6.5:.1f}" y="{200 - hgt:.1f}" width="3" height="{hgt:.1f}" rx="1.5" />')
    played = X + (W - 44 - X) * 0.58
    art.ink(card(W, H) + vinyl(280, 130, 96))
    art.color(f'<image x="44" y="30" width="200" height="200" preserveAspectRatio="xMidYMid slice" clip-path="url(#coverClip)" href="data:image/jpeg;base64,{cover}" />')
    art.ink(f'<rect x="44" y="30" width="200" height="200" rx="4" fill="none" stroke="{INK}" stroke-width="1.6" />'
            f'{spotify_mark(X + 8, 61)}<text class="np-l" x="{X + 24}" y="65">NOW PLAYING ON SPOTIFY</text>'
            f'<text class="np-t" x="{X}" y="118">{escape(song)}</text>'
            f'<text class="np-a" x="{X}" y="150">{escape(artist)}</text>'
            f'<text class="np-j" x="{X + (reg.width(artist, 20) if reg else 100) + 16:.1f}" y="150">{artist_jp}</text>'
            f'<g fill="{INK}" opacity="0.85">{"".join(bars)}</g>'
            f'<rect x="{X}" y="223.5" width="{W - 44 - X}" height="1" fill="{INK}" opacity="0.3" />'
            f'<rect x="{X}" y="223" width="{played - X:.0f}" height="2" fill="{INK}" />')
    art.color(f'<circle cx="{played:.0f}" cy="224" r="3.6" fill="{RED}" />', f'<circle cx="{played:.0f}" cy="224" r="3.6" fill="{NIGHT_RED}" />')
    art.color(*tag(-(W - 26), 16, "再生中"))
    art.write(OUT, "now-playing")


# ---------------------------------------------------------------- 世界线：替代打字机的台词条
def quote(F):
    W, H = 960, 96
    art = Art(W, H, " / ".join(QUOTES))
    n, slot, tr, stag = len(QUOTES), 4.0, 0.55, 0.009
    C = n * slot
    lines = []
    for k, q in enumerate(QUOTES):
        jp = any(ord(c) > 0x3000 for c in q)
        font = F["jp"] if jp else F["bold"]
        svg, _, _ = letters(font, q, 25 if jp else 26, 610, 66, "q " + ("qj" if jp else "ql"), spacing=1.5 if jp else 0.4, step=0)
        out = []
        for i, chunk in enumerate(svg.split("<text ")[1:]):
            out.append("<text " + chunk.replace("animation-delay:0.00s", f"animation-delay:{k * slot + i * stag - C:.3f}s"))
        lines.append("".join(out))

    def p(t):
        return f"{100 * t / C:.3f}%"
    # 世界线变动率：数字像里程表一样滚到下一条世界线
    cells, digit_css = [], []
    cx0 = 40
    for j in range(8):
        x = cx0 + j * 26
        if j == 1:
            cells.append(f'<circle cx="{x + 5}" cy="72" r="2.4" fill="{INK}" />')
            continue
        frames = []
        for k in range(n):
            prev, cur = WORLDLINES[k - 1][j], WORLDLINES[k][j]
            frames.append(f"{p(k * slot)} {{ transform: translateY({-int(prev) * 34}px); animation-timing-function: {EASE_OUT}; }}")
            frames.append(f"{p(k * slot + 0.5 + j * 0.06)} {{ transform: translateY({-int(cur) * 34}px); }}")
        frames.append(f"100% {{ transform: translateY({-int(WORLDLINES[-1][j]) * 34}px); }}")
        digit_css.append(f".d{j} {{ animation: d{j} {C}s infinite; }} @keyframes d{j} {{ {' '.join(frames)} }}")
        col = "".join(f'<text x="{x + 10}" y="{70 + v * 34}" text-anchor="middle" class="dg">{v % 10}</text>' for v in range(10))
        cells.append(f'<rect x="{x - 1}" y="40" width="22" height="42" rx="5" fill="{PAPER}" stroke="{INK}" stroke-width="1.2" />'
                     f'<g clip-path="url(#tube)"><g class="d{j}">{col}</g></g>'
                     f'<rect x="{x + 1}" y="42" width="18" height="38" rx="4" fill="url(#tubeGlass)" />')
    art.css.append(text_css([F["bold"], F["regular"], F["jp"]], f"""
  .q {{ animation: q {C}s infinite; }}
  .ql {{ font: 700 26px {SERIF_STACK}; fill: {RED}; }}
  .qj {{ font: 800 25px {MINCHO_STACK}; fill: {RED}; }}
  .qlN {{ font: 700 26px {SERIF_STACK}; fill: {NIGHT_RED}; }}
  .qjN {{ font: 800 25px {MINCHO_STACK}; fill: {NIGHT_RED}; }}
  @keyframes q {{
    0% {{ transform: translateY(42px); animation-timing-function: {EASE}; }}
    {p(tr)} {{ transform: translateY(0); }}
    {p(slot)} {{ transform: translateY(0); animation-timing-function: {EASE}; }}
    {p(slot + tr)} {{ transform: translateY(-42px); }}
    100% {{ transform: translateY(-42px); }}
  }}
  .dg {{ font: 700 25px {SERIF_STACK}; fill: {INK}; }}
  .wl {{ font: 400 9.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
  {" ".join(digit_css)}
"""))
    art.defs.append('<linearGradient id="winFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="0.3" stop-color="#fff" />'
                    '<stop offset="0.78" stop-color="#fff" /><stop offset="1" stop-color="#fff" stop-opacity="0" /></linearGradient>'
                    f'<mask id="window"><rect x="270" y="32" width="{W - 270}" height="50" fill="url(#winFade)" /></mask>')
    art.defs.append(f'<clipPath id="tube"><rect x="0" y="42" width="{W}" height="38" /></clipPath>'
                    f'<linearGradient id="tubeGlass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER}" stop-opacity="0.9" /><stop offset="0.3" stop-color="{PAPER}" stop-opacity="0" />'
                    f'<stop offset="0.7" stop-color="{PAPER}" stop-opacity="0" /><stop offset="1" stop-color="{PAPER}" stop-opacity="0.9" /></linearGradient>')
    art.ink(f'<text class="wl" x="{cx0 - 1}" y="30">DIVERGENCE METER</text>{"".join(cells)}'
            f'<path d="M262 30V86" stroke="{INK}" stroke-width="0.8" opacity="0.5" />')
    body = "".join(lines)
    win = '<g mask="url(#window)">{}</g>'
    art.color(win.format(body), win.format(body.replace("q ql", "q qlN").replace("q qj", "q qjN")))
    art.write(OUT, "quote")


# ---------------------------------------------------------------- 第1話：自己紹介（me 站点的漫画页，静态）
HELLO = ["はじめまして、", "ユキです。"]
NARRATION = ["これは、ある夏の日から", "始まった小さな物語。"]
MONOLOGUE = ["你好，我是 Yuki。一个喜欢夏天、漫画和代码的人。白天写程序，晚上画画，偶尔在凌晨三点思考人生。",
             "我喜欢把脑子里的画面做成能动的东西——网页、小工具、短动画。最在意的是那些「多看一眼才会发现」的细节。",
             "如果你也喜欢黑白漫画、蝉鸣、汽水和日落时分的电线杆，我们大概会很聊得来。"]
SMALL_KANA = set("っゃゅょぁぃぅぇぉッャュョァィゥェォ")
NO_LINE_START = set("，。、；：！？」）』》…—")


def vtext(cols, x, y, size, cls, gap=1.6):
    """竖排：每列从右往左，逐字摆放；、。挪到格子右上，小假名稍微靠右上。"""
    out = []
    for c, col in enumerate(cols):
        cx = x - c * size * gap
        for i, ch in enumerate(col):
            dx, dy = 0.0, 0.0
            if ch in "、。":
                dx, dy = size * 0.58, -size * 0.6
            elif ch in SMALL_KANA:
                dx, dy = size * 0.1, -size * 0.1
            out.append(f'<text class="{cls}" x="{cx + dx:.1f}" y="{y + (i + 1) * size * 1.08 + dy:.1f}" text-anchor="middle">{ch}</text>')
    return "".join(out)


def wrap(font, text, size, width):
    """按真实字宽折行，句读不放行首。"""
    lines, cur, w = [], "", 0.0
    for ch in text:
        a = font.advance(ch, size)
        if w + a > width and cur and ch not in NO_LINE_START:
            lines.append(cur)
            cur, w = "", 0.0
        cur += ch
        w += a
    return lines + [cur]


def sfx(font, text, x, y, size, cls, depth=6, rot=-8):
    """拟声词：纸色字、墨描边，往右下叠出墨色厚度（颜色另外按模式给）。"""
    body, _, _ = letters(font, text, size, x, y, cls, spacing=-size * 0.04, step=0, anchor="start")
    shadow = "".join(f'<g transform="translate({k:.1f} {k:.1f})">{body.replace(chr(34) + cls, chr(34) + cls + " sfxsh")}</g>' for k in [depth * t / 4 for t in range(4, 0, -1)])
    return f'<g transform="rotate({rot} {x} {y})">{shadow}{body}</g>'


def still_hanabi(prefix, spots, rng, mode):
    """画在天上的花火：用花火的形状，不带升空、闪光和消散的动画。"""
    defs, body = [], []
    for i, (x, y, r, kind) in enumerate(spots):
        g, b = firework(f"{prefix}{i}", kind, x, y, r, SCHEMES[(i * 3 + len(prefix)) % len(SCHEMES)], 6, 0, rng, mode)
        b = re.sub(r'<circle class="fw-(?:rise|flash)"[^>]*/>', "", b)
        b = re.sub(r'<g class="fw" style="[^"]*">', "<g>", b).replace(' class="fw-glint"', "")
        defs.append(g)
        body.append(b)
    return "".join(defs), "".join(body)


def manga_page(F):
    W, H = 1200, 840
    art = Art(W, H, "第1話 自己紹介 — はじめまして、ユキです。", lean=True)
    chara = base64.b64encode((OUT / "images" / "chara.webp").read_bytes()).decode()
    avatar = base64.b64encode((OUT / "images" / "avatar.webp").read_bytes()).decode()

    def bx(yy):  # B 格左边（斜线）
        return 802 - 20 * (yy - 16) / 460
    A = f"16,16 {bx(16) - 12:.1f},16 {bx(476) - 12:.1f},476 16,476"
    B = f"{bx(16):.1f},16 1184,16 1184,{H - 16} {bx(H - 16):.1f},{H - 16}"
    C = f"16,488 340,488 340,{H - 16} 16,{H - 16}"
    D = f"352,488 {bx(488) - 12:.1f},488 {bx(H - 16) - 12:.1f},{H - 16} 352,{H - 16}"
    ax = bx(16) - 12

    # A：天台的金网、夜空的花火、立绘、对话框、旁白、ザァ…
    fw_spots = [(566, 300, 72, "kiku"), (662, 138, 50, "botan"), (330, 66, 58, "kamuro"), (692, 336, 42, "wa"),
                (404, 226, 38, "botan"), (642, 44, 36, "kiku"), (520, 410, 40, "jelly"), (726, 436, 32, "botan")]
    fl_defs, fl_body = still_hanabi("pl", fw_spots, random.Random(5), "light")
    fd_defs, fd_body = still_hanabi("pd", fw_spots, random.Random(5), "dark")
    bubble_d = "M432 60C470 30 560 34 590 92C620 150 606 250 548 282C500 308 446 290 430 246L392 262L418 226C390 170 396 92 432 60Z"
    hello = vtext(HELLO, 530, 102, 22, "hello", 1.5)
    narr = vtext(NARRATION, 754, 52, 17, "narr", 1.75)
    art.defs.append(f'<clipPath id="pA"><polygon points="{A}" /></clipPath><clipPath id="pB"><polygon points="{B}" /></clipPath>'
                    f'<clipPath id="pC"><polygon points="{C}" /></clipPath><clipPath id="pD"><polygon points="{D}" /></clipPath>'
                    f'<image id="chara" width="331" height="480" href="data:image/webp;base64,{chara}" />'
                    f'<filter id="charaShadow" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 0.08  0 0 0 0 0.09  0 0 0 0 0.11  0 0 0 0.18 0" /></filter>')
    art.css.append(text_css([F["jp"], F["regular"], F["sc"]], f"""
  .hello {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; }}
  .narr {{ font: 800 17px {MINCHO_STACK}; fill: {INK}; }}
  .sfxA {{ font: 800 96px {MINCHO_STACK}; }}
  .sfxC {{ font: 800 30px {MINCHO_STACK}; }}
  .sfxA, .sfxC {{ fill: #ffffff; stroke: {INK}; stroke-width: 3px; paint-order: stroke; stroke-linejoin: round; }}
  .sfxsh {{ fill: {INK}; stroke: {INK}; }}
  .mono {{ font: 500 16px 'Noto Serif SC', 'Songti SC', serif; fill: {INK}; }}
  .label {{ font: 400 11px {SERIF_STACK}; fill: {RED}; letter-spacing: 4px; }}
  .note {{ font: 800 20px {MINCHO_STACK}; fill: {RED}; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
  .sfxN {{ fill: {NIGHT_INK_SFX}; stroke: #070b10; }}
  .sfxN.sfxsh {{ fill: #070b10; }}
"""))
    art.ink(f'<rect width="{W}" height="{H}" rx="8" fill="{PAPER}" />'
            f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="{TONE_GRAY_SKY}" />'
            f'<rect x="16" y="16" width="{ax}" height="240" fill="url(#tone)" opacity="0.55" mask="url(#toneUp)" /></g>')
    art.color(f'<defs>{fl_defs}</defs><g clip-path="url(#pA)"><g style="mix-blend-mode:multiply" opacity="0.8">{fl_body}</g></g>',
              f'<defs>{fd_defs}<linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1119" /><stop offset="0.55" stop-color="#1d2a3d" /><stop offset="1" stop-color="#35324a" /></linearGradient></defs>'
              f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="url(#nightSky)" />'
              f'<rect x="16" y="16" width="{ax}" height="260" fill="url(#tone)" opacity="0.25" mask="url(#toneUp)" /><g opacity="0.9">{fd_body}</g></g>')
    art.ink(f'<g clip-path="url(#pA)">{fence("P", 16, ax + 4, 232, 480, [64, 330, 600], 22)}</g>')
    art.color(f'<g clip-path="url(#pA)"><use href="#chara" xlink:href="#chara" x="38" y="38" filter="url(#charaShadow)" />'
              f'<use href="#chara" xlink:href="#chara" x="30" y="30" /></g>')
    art.ink(f'<g clip-path="url(#pA)">'
            f'<path d="{bubble_d}" fill="{PAPER}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round" />{hello}'
            f'<rect x="704" y="36" width="70" height="{len(NARRATION[0]) * 17 * 1.08 + 26:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="2" />{narr}</g>')
    sfx_a = sfx(F["jp"], "ザァ…", 452, 452, 96, "sfxA", 7, -8)
    art.color(f'<g clip-path="url(#pA)">{sfx_a}</g>', f'<g clip-path="url(#pA)">{sfx_a.replace("sfxA", "sfxA sfxN")}</g>')

    # B：本人
    art.ink(f'<g clip-path="url(#pB)"><rect x="760" y="16" width="430" height="{H}" fill="url(#tone)" /></g>')
    art.color(f'<g clip-path="url(#pB)"><image x="{bx(H - 16):.0f}" y="16" width="{1184 - bx(H - 16):.0f}" height="{H - 32}" preserveAspectRatio="xMidYMid slice" '
              f'href="data:image/webp;base64,{avatar}" /></g>')
    note_arrow = f'<path d="M1012 566H1052M1012 566l10 -6M1012 566l10 6" fill="none" stroke="{RED}" stroke-width="2.2" stroke-linecap="round" />'
    art.ink(f'<text class="note" x="1060" y="573">本人</text>')
    art.color(note_arrow, note_arrow.replace(RED, NIGHT_RED))

    # C：头像（me 站点的 icon），夏天的天空；小字的蝉鸣贴在右上角
    icon = base64.b64encode((OUT / "images" / "icon.webp").read_bytes()).decode()
    art.color(f'<g clip-path="url(#pC)"><image x="16" y="488" width="324" height="{H - 504}" preserveAspectRatio="xMidYMid slice" '
              f'href="data:image/webp;base64,{icon}" /></g>')
    sfx_c = sfx(F["jp"], "ミーン", 226, 532, 30, "sfxC", 3, -6) + sfx(F["jp"], "ミンミン", 212, 568, 30, "sfxC", 3, -6)
    art.color(f'<g clip-path="url(#pC)">{sfx_c}</g>', f'<g clip-path="url(#pC)">{sfx_c.replace("sfxC", "sfxC sfxN")}</g>')

    # D：MONOLOGUE
    y = 556
    paras = []
    for para in MONOLOGUE:
        for ln in wrap(F["sc"], para, 16, 360):
            paras.append(f'<text class="mono" x="384" y="{y}">{ln}</text>')
            y += 29
        y += 10
    lines_y = [float(t.split('y="')[1].split('"')[0]) for t in paras]
    art.ink(f'<g clip-path="url(#pD)"><rect x="352" y="488" width="420" height="{H - 504}" fill="{PAPER}" />'
            f'<path d="M370 {lines_y[0] - 16}V{lines_y[-1] + 6}" stroke="{INK}" stroke-width="0.6" opacity="0.4" />{"".join(paras)}</g>'
            f'<text class="label" x="384" y="522">MONOLOGUE</text>')
    marker = f'<rect x="368" y="{lines_y[0] - 15:.0f}" width="4" height="19" rx="2" fill="{RED}" />'
    art.color(marker, marker.replace(RED, NIGHT_RED))

    # 分格的框线
    art.ink("".join(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round" />' for pts in (A, B, C, D)))
    art.write(OUT, "manga")


if __name__ == "__main__":
    titles = "".join(e[1] for e in EPISODES)
    quotes = "".join(QUOTES)
    jp_all = ("".join(e[2] for e in EPISODES) + HEAD_JP + FOOT_JP + TOP_RIGHT + TOP_MID + SIGN + quotes + "".join(HELLO + NARRATION)
              + "新連載!!第話週刊完涼雨ザァ…ミーンミンミン本人0123456789")
    F = {
        "black": load_font(SERIF, 800, "HI THERE THE END"),
        "bold": load_font(SERIF, 700, titles + quotes + "0123456789"),
        "regular": load_font(SERIF, 400, "▸— I am Yuki — SEMINAR SCIENCE INTELLIGENCE FUTURE EPISODE DIVERGENCE METER YUKI FILM 400 A · ¥()"
                             + TOP_LEFT + TOP_RIGHT + "0123456789" + titles.upper()),
        "jp": load_font(MINCHO, 800, jp_all),
        "sc": load_font("Noto Serif SC", 500, "".join(MONOLOGUE)),
    }
    if not all(F.values()):
        sys.exit("需要联网取字体")
    only = set(sys.argv[1:])
    for name, fn in [("header", lambda: header(F)), ("footer", lambda: footer(F)), ("manga", lambda: manga_page(F)), ("divider", divider),
                     ("playing", now_playing), ("quote", lambda: quote(F))]:
        if not only or name in only:
            fn()
    if not only or "titles" in only:
        for i, (name, en, jp) in enumerate(EPISODES, 1):
            title(i, name, en, jp)

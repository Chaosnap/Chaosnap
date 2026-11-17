#!/usr/bin/env python3
"""主页上手工设计的 SVG（黑白漫画风，和 me 站点“週刊ユキ”同一套语言）。

每张图出浅色、深色两版（*-light.svg / *-dark.svg），README 用 <picture> 按访客主题切换。
改了文字或效果后在仓库根目录运行 `python3 .github/scripts/make_art.py`，再提交 profile/。
只重做其中几张：`python3 .github/scripts/make_art.py header quote`。需要联网取字体（Google Fonts，只取用到的字）。

性能上的约定：动效一律“逐格”（<set> 翻页或 CSS steps()），不用滤镜和漂浮粒子。
头图、结尾、世界线台词条、分隔线的风铃有很轻的环境动画；播放卡里唱片在转、波形在跳、进度在走（十格一秒）；
漫画页和分区标题是静态图。分区标题和播放卡与 decorate.py 的内页卡片同一套版式（发丝线卡片、明朝体副题、朱印）。
"""
import base64
import math
import pathlib
import random
import re
import sys
from html import escape

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (EASE, EASE_OUT, GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_INK, NIGHT_RED, PAPER, RED, SERIF,  # noqa: E402
                   SERIF_STACK, TICK, Art, barcode, cel, chime, clock, cloud, fence, film_strip, flipbook, furin, hanabi_show, lens_flare,
                   letters, load_font, pole, poster, rain_field, sheen_grad, splash, splashes, stamp, starburst, sun, sun_ink, sun_rays,
                   title_fx, wagasa, wire, wire_point)

from decorate import HEAD_Y, RULE_Y, SEAL, both, heading, rule, seal, sheet  # noqa: E402
from decorate import card as shadow_card  # noqa: E402
from manga import to_night  # noqa: E402

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


def text_css(fonts, extra=""):
    return "".join(f.css() for f in fonts if f) + extra


def paper_fade(gid):
    """盖在网点上的渐变：上端透明、下端纸色。网点于是自上而下淡出，效果和渐变蒙版一样，但不用开离屏图层。"""
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER}" stop-opacity="0" />'
            f'<stop offset="1" stop-color="{PAPER}" /></linearGradient>')


def inside(w, h):
    return f'<clipPath id="inside"><rect x="12" y="12" width="{w - 24}" height="{h - 24}" rx="3" /></clipPath>'


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
                    + f'<radialGradient id="rayFade" gradientUnits="userSpaceOnUse" cx="{SX}" cy="{SY}" r="620"><stop offset="0.1" stop-color="{INK}" stop-opacity="0.12" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></radialGradient>'
                    + paper_fade("paperUp"))

    # 远景：天空网点、放射线（静止）。网点的淡出是盖一层“透明→纸色”的渐变，放射线的淡出直接写进填充的渐变里——都不用蒙版
    rays = re.sub(r'<g class="spin"[^>]*>(<path d="[^"]*") fill="[^"]*" /></g>', r'\1 fill="url(#rayFade)" />', sun_rays(SX, SY, 48, SR + 16, 1100, 0.12))
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="44" width="{W - 24}" height="190" fill="url(#tone)" fill-opacity="0.42" /><rect x="12" y="43" width="{W - 24}" height="192" fill="url(#paperUp)" />
  {rays}
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
    art.defs.append(inside(W, H) + paper_fade("paperUp") + sheen_grad("sheenF", tl, tl + tw, 6.4, 3.2, 70)
                    + f'<radialGradient id="calm"><stop offset="0.35" stop-color="{PAPER}" stop-opacity="0.9" /><stop offset="1" stop-color="{PAPER}" stop-opacity="0" /></radialGradient>')
    umbrella = wagasa(250, 214, 1.05).replace('<g class="umbrella">', '<g class="umbrella">' + canopy_splash, 1)
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="12" width="{W - 24}" height="180" fill="url(#tone)" fill-opacity="0.5" /><rect x="12" y="11" width="{W - 24}" height="182" fill="url(#paperUp)" />
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


# ---------------------------------------------------------------- 分区标题：静态，居中三行
KANJI_NUM = "〇一二三四五六七八九十"


def title(i, name, english, japanese):
    """两道两端淡出的发丝线夹着朱色的“第一話”，下面是英文标题和疏排的日文副题。"""
    W, H = 900, 100
    bold = load_font(SERIF, 700, english)
    ep = f"第{KANJI_NUM[i]}話"
    jp = load_font(MINCHO, 800, ep + japanese)
    art = Art(W, H, english, lean=True)
    cx = W / 2
    art.css.append(text_css([bold, jp], f"""
  .t {{ font: 700 32px {SERIF_STACK}; fill: {INK}; letter-spacing: 0.3px; }}
  .j {{ font: 800 13px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 8px; }}
  .e {{ font: 800 12px {MINCHO_STACK}; letter-spacing: 5px; }}
"""))
    art.defs.append(f'<linearGradient id="tl" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" stop-opacity="0.5" /></linearGradient>'
                    f'<linearGradient id="tr" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0.5" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    jw = jp.width(ep, 12, 5) if jp else 48
    gap = jw / 2 + 18
    art.ink(f'<rect x="{cx - gap - 130:.1f}" y="17.6" width="130" height="0.8" fill="url(#tl)" />'
            f'<rect x="{cx + gap:.1f}" y="17.6" width="130" height="0.8" fill="url(#tr)" />'
            f'<text class="t" x="{cx}" y="62" text-anchor="middle">{escape(english)}</text>'
            f'<text class="j" x="{cx + 4}" y="90" text-anchor="middle">{escape(japanese)}</text>')
    ep_svg = f'<text class="e" x="{cx + 2.5}" y="22" text-anchor="middle" fill="{RED}">{ep}</text>'
    art.color(*both(ep_svg))
    art.write(OUT, f"title-{name}")


# ---------------------------------------------------------------- 分隔线：一根电线，中间挂着一只小风铃
def divider():
    """两根两端淡出的电线，最低处挂一只风铃；每隔几秒来一阵风，红色的短册摆几下、铃边荡开两道声纹，然后又静下来。
    摆动是六格翻页（<set>），静止的那几秒里浏览器什么都不用做。"""
    W, H = 800, 86
    cx, top = W / 2, 13
    art = Art(W, H, role="presentation", lean=True)
    art.defs.append(f'<linearGradient id="wire" gradientUnits="userSpaceOnUse" x1="0" x2="{W}" y1="0" y2="0"><stop offset="0.02" stop-color="{INK}" stop-opacity="0" />'
                    f'<stop offset="0.2" stop-color="{INK}" /><stop offset="0.8" stop-color="{INK}" /><stop offset="0.98" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    sag = 22
    hang = top + sag / 2  # 二次曲线中点的高度
    wires = (f'<path d="M14 {top}Q{cx} {top + sag} {W - 14} {top}" fill="none" stroke="url(#wire)" stroke-width="1.3" />'
             f'<path d="M14 {top + 9}Q{cx} {top + sag + 4} {W - 14} {top + 9}" fill="none" stroke="url(#wire)" stroke-width="0.8" stroke-opacity="0.5" />')
    # 电线上的几枚小结：左右对称，离中心越远越小
    knots = "".join(f'<rect x="{cx + sx * dx - r:.1f}" y="{top + sag * (1 - (dx / (cx - 14)) ** 2) / 2 - r:.1f}" width="{2 * r}" height="{2 * r}" fill="{PAPER}" stroke="{INK}" stroke-width="0.9" '
                    f'transform="rotate(45 {cx + sx * dx:.1f} {top + sag * (1 - (dx / (cx - 14)) ** 2) / 2:.1f})" />'
                    for dx, r in ((118, 2.6), (196, 2.0), (262, 1.5)) for sx in (-1, 1))
    art.ink(wires + knots)
    # 风铃：静止的姿势平时显示，起风的 0.96 秒里换成六个摆动的姿势
    poses = [(4, 15), (-3, -11), (2.4, 8), (-1.6, -5), (1, 3), (-0.5, -1.5)]
    dur, t0, period = 0.16, 1.6, 6.4
    rest_i, rest_c = furin(cx, hang, 0.92)
    hide = f'<set attributeName="visibility" to="hidden" begin="k.begin+{t0:.2f}s" dur="{dur * len(poses):.2f}s" />'
    ink, col = [clock("k", period), f"<g>{rest_i}{hide}</g>"], [f"<g>{rest_c}{hide}</g>"]
    for i, (tilt, paper) in enumerate(poses):
        pi, pc = furin(cx, hang, 0.92, tilt, paper)
        ring = ""
        if i < 2:  # 头两格：铃边两道声纹
            r = 17 + 7 * i
            ring = (f'<path d="M{cx - r:.1f} {hang + 9:.1f}a{r} {r} 0 0 0 0 {r * 0.9:.1f}M{cx + r:.1f} {hang + 9:.1f}a{r} {r} 0 0 1 0 {r * 0.9:.1f}" fill="none" stroke="{INK}" '
                    f'stroke-width="{1.1 - 0.3 * i:.1f}" stroke-linecap="round" stroke-opacity="{0.8 - 0.3 * i:.1f}" />')
        ink.append(cel("k", [(t0 + i * dur, dur)], pi + ring))
        col.append(cel("k", [(t0 + i * dur, dur)], pc))
    art.ink("".join(ink))
    art.color(*both("".join(col)))
    art.write(OUT, "divider")


# ---------------------------------------------------------------- 播放卡：封面、转着的唱片、跳动的波形、走着的进度
def spotify_mark(x, y, r=7.5):
    return (f'<g transform="translate({x} {y})"><circle r="{r}" fill="{INK}" />'
            f'<path d="M-4.6 -1.8Q0 -4.6 4.6 -1.8" fill="none" stroke="{PAPER}" stroke-width="1.6" stroke-linecap="round" />'
            f'<path d="M-3.8 0.9Q0 -1.3 3.8 0.9" fill="none" stroke="{PAPER}" stroke-width="1.4" stroke-linecap="round" />'
            f'<path d="M-3 3.4Q0 1.8 3 3.4" fill="none" stroke="{PAPER}" stroke-width="1.2" stroke-linecap="round" /></g>')


def vinyl(cx, cy, r, dark):
    """唱片不转的部分：盘面、纹路、两道反光（反光不跟着转）。深色版也保持一张黑胶，只是加一圈浅色的边。"""
    disc, line = ("#0b0d11", "#eceae6") if dark else (INK, PAPER)
    grooves = "".join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" />' for rr in range(int(r * 0.45), int(r) - 3, 4))

    def glint(a0, a1, rr):
        return f"M{cx + rr * math.cos(a0):.1f} {cy + rr * math.sin(a0):.1f}A{rr:.1f} {rr:.1f} 0 0 1 {cx + rr * math.cos(a1):.1f} {cy + rr * math.sin(a1):.1f}"
    shine = "".join(glint(a, a + 0.62 - 0.06 * k, r * (0.9 - 0.12 * k)) for a in (-2.35, 0.79) for k in range(4))
    rim = f'<circle cx="{cx}" cy="{cy}" r="{r - 0.5}" fill="none" stroke="{line}" stroke-width="1" stroke-opacity="0.35" />' if dark else ""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{disc}" />{rim}'
            f'<g fill="none" stroke="{line}" stroke-width="0.5" stroke-opacity="{0.16 if dark else 0.22}">{grooves}</g>'
            f'<path d="{shine}" fill="none" stroke="{line}" stroke-width="2" stroke-linecap="round" stroke-opacity="{0.22 if dark else 0.32}" />')


def now_playing():
    """每 0.1 秒换一格（十格一秒）：唱片的标签转过一个角度、波形换一组高度——两样在同一格里一起换，每 0.1 秒只重画一次。
    整首歌 3 分 24 秒走完一遍：播放头每 3.2 秒往前一步，走过的波形是实墨、没走到的是淡墨；时间每秒跳一下。全部是 <set> 翻页。"""
    W, H = 900, 268
    song, artist, artist_jp = TRACK
    ring = f"{artist.upper()}  ·  {song.upper()}  ·  ヨルシカ  ·  "
    bold = load_font(SERIF, 700, song + "Now Playing")
    reg = load_font(SERIF, 400, artist + ring + "SPOTIFY 0123456789:")
    jp = load_font(MINCHO, 800, artist_jp + "再生中音" + ring)
    art = sheet(W, H, f"Now playing on Spotify: {artist} - {song}")
    cover = base64.b64encode((OUT / "images" / "cover.jpg").read_bytes()).decode()
    art.css.append(text_css([bold, reg, jp], f"""
  .h {{ font: 700 17px {SERIF_STACK}; fill: {INK}; }}
  .hj {{ font: 800 11px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 4px; }}
  .np-l {{ font: 400 9.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
  .np-t {{ font: 700 36px {SERIF_STACK}; fill: {INK}; }}
  .np-a {{ font: 400 17px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.8; }}
  .np-j {{ font: 800 12px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
  .np-c {{ font: 400 11px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.7; }}
  .np-r {{ font: 400 6.4px {SERIF_STACK}, {MINCHO_STACK}; fill: #ffffff; fill-opacity: 0.92; letter-spacing: 1.2px; }}
"""))
    CX0, CY0, CS = 30, 80, 164          # 封面
    VX, VY, VR = CX0 + CS + 36, CY0 + CS / 2, 80   # 唱片：从封面后面滑出一半
    LR = 28                             # 标签半径
    X, X1 = 368, W - 30                 # 右边的文字栏
    art.defs.append(f'<clipPath id="coverClip"><rect x="{CX0}" y="{CY0}" width="{CS}" height="{CS}" rx="5" /></clipPath>'
                    f'<path id="lbl" d="M{VX - LR + 7} {VY}a{LR - 7} {LR - 7} 0 1 1 {2 * (LR - 7)} 0a{LR - 7} {LR - 7} 0 1 1 {-2 * (LR - 7)} 0" />')
    art.ink(shadow_card(W, H) + heading(30, HEAD_Y, "Now Playing", "再生中", bold) + rule(30, W - 30, RULE_Y)
            + f'{spotify_mark(W - 30 - SEAL - 92, HEAD_Y - 4.5, 6.5)}<text class="np-l" x="{W - 30 - SEAL - 80}" y="{HEAD_Y - 1}">SPOTIFY</text>')
    art.color(vinyl(VX, VY, VR, False), vinyl(VX, VY, VR, True))

    # ---- 一格画面：标签转一个角度 + 一组波形高度 ----
    F, FRAME = 32, 0.1
    rng = random.Random(11)
    NB = 66
    pitch = (X1 - X) / (NB - 1)
    WY, WA = 196, 17                    # 波形的中线、最大半高
    # 整首歌的“轮廓”：几段起伏叠出来的包络，前奏轻、副歌满
    env = []
    for k in range(NB):
        u = k / (NB - 1)
        e = 0.32 + 0.5 * (0.5 + 0.5 * math.sin(u * 9.4 - 1.2)) * (0.6 + 0.4 * math.sin(u * 3.1 + 0.4)) + rng.uniform(0, 0.22)
        env.append(min(1.0, e * (0.55 if u < 0.06 or u > 0.95 else 1)))
    wob = [(rng.choice([1, 2, 2, 3, 3, 4]), rng.uniform(0, 6.28), rng.uniform(0, 6.28)) for _ in range(NB)]

    def label(a):
        return (f'<g transform="rotate({a:.2f} {VX} {VY})">'
                f'<circle cx="{VX}" cy="{VY}" r="{LR}" fill="{RED}" />'
                f'<circle cx="{VX}" cy="{VY}" r="{LR - 12}" fill="none" stroke="#ffffff" stroke-width="0.5" stroke-opacity="0.55" />'
                f'<text class="np-r"><textPath href="#lbl">{escape(ring)}</textPath></text>'
                f'<path d="M{VX} {VY - LR + 13}v5" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round" stroke-opacity="0.85" /></g>'
                f'<circle cx="{VX}" cy="{VY}" r="3" fill="{PAPER}" />')

    def wave(f):
        ph = 2 * math.pi * f / F
        beat = max(0.0, math.cos(ph * 4)) ** 6  # 一圈四拍
        d = []
        for k in range(NB):
            f1, p1, p2 = wob[k]
            live = 0.62 + 0.26 * math.sin(ph * f1 + p1) + 0.12 * math.sin(ph * 2 * f1 + p2) + 0.18 * beat
            h = max(1.4, WA * env[k] * min(1.15, live))
            d.append(f"M{X + k * pitch:.1f} {WY - h:.1f}V{WY + h:.1f}")
        return f'<path d="{"".join(d)}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" fill="none" />'
    frames = clock("e", F * FRAME) + poster(label(0) + wave(5)) + "".join(cel("e", [(f * FRAME, FRAME)], label(360 * f / F) + wave(f)) for f in range(F))
    art.color(frames, to_night(frames).replace(RED, NIGHT_RED))

    # 封面盖在唱片上面；唱臂搭在唱片外圈
    art.color(f'<image x="{CX0}" y="{CY0}" width="{CS}" height="{CS}" preserveAspectRatio="xMidYMid slice" clip-path="url(#coverClip)" href="data:image/jpeg;base64,{cover}" />')
    PX, PY = VX + VR + 18, CY0 + 6
    HX, HY = VX + 34, VY + 46
    art.ink(f'<rect x="{CX0}" y="{CY0}" width="{CS}" height="{CS}" rx="5" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity="0.5" />'
            f'<circle cx="{PX}" cy="{PY}" r="8" fill="{PAPER}" stroke="{INK}" stroke-width="1" /><circle cx="{PX}" cy="{PY}" r="2.6" fill="{INK}" />'
            f'<path d="M{PX} {PY}L{PX - 4} {HY - 44}L{HX + 6} {HY - 6}" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />'
            f'<rect x="{HX - 3}" y="{HY - 9}" width="9" height="13" rx="1.5" fill="{INK}" transform="rotate(40 {HX + 1.5} {HY - 2.5})" />'
            f'<text class="np-t" x="{X}" y="{CY0 + 40}">{escape(song)}</text>'
            f'<text class="np-a" x="{X}" y="{CY0 + 70}">{escape(artist)}</text>'
            f'<text class="np-j" x="{X + (reg.width(artist, 17) if reg else 90) + 14:.1f}" y="{CY0 + 70}">{artist_jp}</text>')

    # ---- 进度：每 3.2 秒往前一步，一共 64 步走完；没走到的波形盖一层半透明的纸 ----
    STEPS = 64
    SONG = STEPS * F * FRAME  # 204.8 秒
    TY = H - 30               # 时间和按钮那一行

    def progress(i):
        x = X + (X1 - X) * i / (STEPS - 1)
        return f'<rect x="{x + 2:.1f}" y="{WY - WA - 3}" width="{X1 - x + 1:.1f}" height="{2 * WA + 6}" fill="{PAPER}" fill-opacity="0.7" />'

    def head(i):
        x = X + (X1 - X) * i / (STEPS - 1)
        return f'<path d="M{x:.1f} {WY - WA - 5}V{WY + WA + 5}" stroke="{RED}" stroke-width="1.4" stroke-linecap="round" /><circle cx="{x:.1f}" cy="{WY - WA - 5}" r="2.6" fill="{RED}" />'

    def digit(x, v):
        return f'<text class="np-c" x="{x}" y="{TY}" text-anchor="middle">{v}</text>'
    DX = [X + 3.2, X + 12.8, X + 19.6]  # 分、十秒、秒 三位的位置；冒号在 X + 8
    secs = int(SONG)
    clockface = [cel("s", [(60 * m, min(60, SONG - 60 * m))], digit(DX[0], m)) for m in range(secs // 60 + 1)]
    clockface += [cel("s", [(60 * m + 10 * v, min(10, SONG - 60 * m - 10 * v)) for m in range(secs // 60 + 1) if 60 * m + 10 * v < SONG], digit(DX[1], v)) for v in range(6)]
    clockface += [cel("s", [(10 * q + v, min(1, SONG - 10 * q - v)) for q in range(secs // 10 + 1) if 10 * q + v < SONG], digit(DX[2], v)) for v in range(10)]
    still_i = 36
    dim = clock("s", SONG) + poster(progress(still_i) + "".join(digit(x, v) for x, v in zip(DX, (1, 5, 5)))) + "".join(cel("s", [(i * F * FRAME, F * FRAME)], progress(i)) for i in range(STEPS)) + "".join(clockface)
    art.ink(dim + f'<text class="np-c" x="{X + 8}" y="{TY - 1}" text-anchor="middle">:</text>'
            f'<text class="np-c" x="{X1}" y="{TY}" text-anchor="end">3:24</text>')
    heads = poster(head(still_i)) + "".join(cel("s", [(i * F * FRAME, F * FRAME)], head(i)) for i in range(STEPS))
    art.color(*both(heads))

    # ---- 按钮：随机、上一首、暂停（正在播放）、下一首、循环 ----
    bx, by = (X + X1) / 2, TY - 4
    sw = f'fill="none" stroke="{INK}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"'
    art.ink(f'<g {sw} stroke-opacity="0.55">'
            f'<path d="M{bx - 92} {by - 4}h4c4 0 6 8 10 8h4M{bx - 92} {by + 4}h4c4 0 6 -8 10 -8h4M{bx - 76} {by - 6.5}l2.5 2.5l-2.5 2.5M{bx - 76} {by + 1.5}l2.5 2.5l-2.5 2.5" />'
            f'<path d="M{bx + 74} {by - 2}v-1.5a3 3 0 0 1 3 -3h10l-2.5 -2.5M{bx + 92} {by + 2}v1.5a3 3 0 0 1 -3 3h-10l2.5 2.5" /></g>'
            f'<path d="M{bx - 40} {by - 6}v12M{bx - 37} {by}l10 -6.5v13z" fill="{INK}" fill-opacity="0.8" stroke="{INK}" stroke-width="1.3" stroke-opacity="0.8" stroke-linejoin="round" />'
            f'<path d="M{bx + 40} {by - 6}v12M{bx + 37} {by}l-10 -6.5v13z" fill="{INK}" fill-opacity="0.8" stroke="{INK}" stroke-width="1.3" stroke-opacity="0.8" stroke-linejoin="round" />'
            f'<circle cx="{bx}" cy="{by}" r="14" fill="{INK}" />'
            f'<path d="M{bx - 3.2} {by - 5}v10M{bx + 3.2} {by - 5}v10" stroke="{PAPER}" stroke-width="2.4" stroke-linecap="round" />')
    art.color(*seal(W - 30, HEAD_Y - 18, "音"))
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
    # 一场 12.8 秒的花火：点火时刻（格）、位置、大小、种类、配色。成对的两发同一刻炸开，共用换格的时刻
    shots = [(0, 572, 206, 252, "kiku", ("gold", "orange", "silver")),
             (24, 704, 350, 72, "botan", ("pink", "violet", "gold")), (24, 64, 142, 54, "botan", ("cyan", "blue", "silver")),
             (46, 556, 118, 214, "kamuro", ("gold", "gold", "silver")),
             (80, 694, 150, 62, "wa", ("green", "cyan", "gold")), (80, 430, 362, 60, "botan", ("orange", "red", "gold")),
             (100, 616, 248, 236, "kiku", ("cyan", "blue", "silver")), (106, 70, 104, 46, "botan", ("gold", "orange", "silver"))]
    fl_defs, fl_body, n_frames = hanabi_show("fw", shots, random.Random(5), "light", 160)
    fd_defs, fd_body, _ = hanabi_show("fw", shots, random.Random(5), "dark", 160)
    bubble_d = "M432 60C470 30 560 34 590 92C620 150 606 250 548 282C500 308 446 290 430 246L392 262L418 226C390 170 396 92 432 60Z"
    hello = vtext(HELLO, 530, 102, 22, "hello", 1.5)
    narr = vtext(NARRATION, 754, 52, 17, "narr", 1.75)
    art.defs.append(f'<clipPath id="pA"><polygon points="{A}" /></clipPath><clipPath id="pB"><polygon points="{B}" /></clipPath>'
                    f'<clipPath id="pC"><polygon points="{C}" /></clipPath><clipPath id="pD"><polygon points="{D}" /></clipPath>'
)
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
    art.ink(f'<rect width="{W}" height="{H}" rx="8" fill="{PAPER}" />')
    # 天空：整块铺网点，再盖一层“透明→天色”的渐变，网点就自上而下淡出（不用蒙版）；花火直接画在上面，不叠混合模式
    night = ["#0a1119", "#1d2a3d", "#35324a"]
    mix = lambda a, b, t: "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02x}" for i in (1, 3, 5))  # noqa: E731
    hd = 260 / 460  # 深色版网点铺到的高度占整片天的比例
    art.color(f'<defs>{fl_defs}<linearGradient id="skyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TONE_GRAY_SKY}" stop-opacity="0" />'
              f'<stop offset="1" stop-color="{TONE_GRAY_SKY}" /></linearGradient></defs>'
              f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="{TONE_GRAY_SKY}" />'
              f'<rect x="16" y="16" width="{ax}" height="240" fill="url(#tone)" fill-opacity="0.55" /><rect x="16" y="16" width="{ax}" height="241" fill="url(#skyFade)" />'
              f'{fl_body}</g>',
              f'<defs>{fd_defs}<linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{night[0]}" /><stop offset="0.55" stop-color="{night[1]}" /><stop offset="1" stop-color="{night[2]}" /></linearGradient>'
              f'<linearGradient id="skyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{night[0]}" stop-opacity="0" />'
              f'<stop offset="{0.55 / hd:.4f}" stop-color="{night[1]}" stop-opacity="{0.55 / hd:.4f}" /><stop offset="1" stop-color="{mix(night[1], night[2], (hd - 0.55) / 0.45)}" /></linearGradient></defs>'
              f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="url(#nightSky)" />'
              f'<rect x="16" y="16" width="{ax}" height="260" fill="url(#tone)" fill-opacity="0.2" /><rect x="16" y="16" width="{ax}" height="261" fill="url(#skyFade)" />'
              f'{fd_body}</g>')
    art.ink(f'<g clip-path="url(#pA)">{fence("P", 16, ax + 4, 232, 480, [64, 330, 600], 22)}</g>')
    art.color(f'<g clip-path="url(#pA)"><image x="30" y="30" width="331" height="480" href="data:image/webp;base64,{chara}" /></g>')
    art.ink(f'<g clip-path="url(#pA)">'
            f'<path d="{bubble_d}" fill="{PAPER}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round" />{hello}'
            f'<rect x="704" y="36" width="70" height="{len(NARRATION[0]) * 17 * 1.08 + 26:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="2" />{narr}</g>')
    sfx_a = sfx(F["jp"], "ザァ…", 452, 452, 96, "sfxA", 7, -8)
    art.color(f'<g clip-path="url(#pA)">{sfx_a}</g>', f'<g clip-path="url(#pA)">{sfx_a.replace("sfxA", "sfxA sfxN")}</g>')

    # B：本人
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
    print(f"wrote manga light/dark ({n_frames} firework frames per {160 * TICK:.1f}s)")


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

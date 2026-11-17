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
                   SERIF_STACK, TICK, Art, barcode, cel, chime, clock, cloud, fence, film_strip, flipbook, furin, lens_flare,
                   letters, load_font, pole, poster, rain_field, sheen_grad, splash, splashes, stamp, starburst, sun, sun_ink, sun_rays,
                   title_fx, wagasa, wire, wire_point)

from decorate import HEAD_Y, RULE_Y, SEAL, both, heading, rule, seal, sheet  # noqa: E402
from decorate import card as shadow_card  # noqa: E402
from manga import FW_DAY, FW_NIGHT, SCHEMES, TITLE_CSS, firework, music_note, star, to_night  # noqa: E402

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
        # 小一号的“完”字章，贴在 D 的右上角，不压住字
        sx, sy = seal_x + 8, 150
        return (f'<g transform="rotate(-7 {sx:.0f} {sy})"><circle cx="{sx:.0f}" cy="{sy}" r="21" fill="{red}" /><circle cx="{sx:.0f}" cy="{sy}" r="17.5" fill="none" stroke="#ffffff" stroke-width="0.9" />'
                f'<text x="{sx:.0f}" y="{sy + 7.4}" text-anchor="middle" style="font: 800 20px {MINCHO_STACK}; fill: #ffffff">完</text></g>')
    art.color(seal(RED), seal(NIGHT_RED))
    art.write(OUT, "footer")


# ---------------------------------------------------------------- 分区标题：日文为主、英文为副，顶上一枚朱色圆印写着话数
KANJI_NUM = "〇一二三四五六七八九十"


def title(i, name, english, japanese):
    """朱色圆印（话数）两侧拉出两端淡出的发丝线；中间是疏排的明朝体日文标题，下面一行小号的英文，两头各一粒朱点。静态。"""
    W, H = 900, 104
    eng = english.upper()
    reg = load_font(SERIF, 400, eng)
    jp = load_font(MINCHO, 800, KANJI_NUM[i] + japanese)
    art = Art(W, H, english, lean=True)
    cx = W / 2
    art.css.append(text_css([reg, jp], f"""
  .tj {{ font: 800 26px {MINCHO_STACK}; fill: {INK}; letter-spacing: 9px; }}
  .te {{ font: 400 11px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 5px; }}
"""))
    art.defs.append(f'<linearGradient id="tl" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" stop-opacity="0.55" /></linearGradient>'
                    f'<linearGradient id="tr" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0.55" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    ew = (reg.width(eng, 11, 5) if reg else 7 * len(eng))
    art.ink(f'<rect x="{cx - 22 - 170}" y="17.6" width="170" height="0.8" fill="url(#tl)" />'
            f'<rect x="{cx + 22}" y="17.6" width="170" height="0.8" fill="url(#tr)" />'
            f'<text class="tj" x="{cx + 4.5}" y="64" text-anchor="middle">{escape(japanese)}</text>'
            f'<text class="te" x="{cx + 2.5}" y="92" text-anchor="middle">{escape(eng)}</text>')
    dot_x = ew / 2 + 16
    mark = (f'<circle cx="{cx}" cy="18" r="11" fill="{RED}" />'
            f'<circle cx="{cx}" cy="18" r="8.6" fill="none" stroke="#ffffff" stroke-width="0.6" stroke-opacity="0.6" />'
            f'<text x="{cx}" y="22.2" text-anchor="middle" style="font: 800 12px {MINCHO_STACK}; fill: #ffffff">{KANJI_NUM[i]}</text>'
            f'<circle cx="{cx - dot_x:.1f}" cy="88.5" r="1.6" fill="{RED}" /><circle cx="{cx + dot_x:.1f}" cy="88.5" r="1.6" fill="{RED}" />')
    art.color(*both(mark))
    art.write(OUT, f"title-{name}")


# ---------------------------------------------------------------- 分隔线：一根红白的绳，挂满一排御守和风铃
OMAMORI = [("#d9412b", "#c79a2c"), ("#24396b", "#d9b45a"), ("#f7f4ee", "#d9412b"), ("#6b4c8a", "#e2c46a"),
           ("#e48aa8", "#ffffff"), ("#1f6b5c", "#e2c46a")]  # 袋子的颜色、绳结和刺绣的颜色


def omamori(uid, body, cord, hang):
    """一只御守（挂点在原点）：一段细绳、花结、上角斜切的布袋、正中一条白色的刺绣签、袋口一道横纹。"""
    out = "#15171d"
    y0 = hang
    return (f'<g id="{uid}"><path d="M0 0V{y0 + 2}" stroke="{cord}" stroke-width="1" />'
            f'<ellipse cx="-2.6" cy="{y0 + 2.5}" rx="2.8" ry="1.7" fill="none" stroke="{cord}" stroke-width="1.1" />'
            f'<ellipse cx="2.6" cy="{y0 + 2.5}" rx="2.8" ry="1.7" fill="none" stroke="{cord}" stroke-width="1.1" />'
            f'<path d="M-7.5 {y0 + 7}L-5.5 {y0 + 5}H5.5L7.5 {y0 + 7}V{y0 + 27}Q7.5 {y0 + 29} 5.5 {y0 + 29}H-5.5Q-7.5 {y0 + 29} -7.5 {y0 + 27}Z" fill="{body}" stroke="{out}" stroke-width="0.8" />'
            f'<path d="M-7.5 {y0 + 9.5}H7.5" stroke="{cord}" stroke-width="1" stroke-opacity="0.9" />'
            f'<rect x="-2.4" y="{y0 + 12}" width="4.8" height="13" rx="0.6" fill="#ffffff" fill-opacity="0.92" stroke="{cord}" stroke-width="0.5" />'
            f'<path d="M0 {y0 + 14.5}v2M0 {y0 + 18.5}v2M0 {y0 + 22}v1.6" stroke="{out}" stroke-width="0.9" stroke-opacity="0.7" /></g>')


def divider():
    """一根垂下来的红白绳（花火大会、神社那种），等距挂着御守和风铃。每 6.4 秒吹过一阵风：从左到右一只接一只地摆几下，
    然后又静下来。所有挂件在 <defs> 里只画一次，每一格只是一组 <use> 换角度（<set> 翻页），静止的几秒里浏览器什么都不做。"""
    W, H = 800, 108
    x0, x1, top, sag = 18, W - 18, 12, 20
    art = Art(W, H, role="presentation", lean=True)

    def rope_pt(t):
        mx, my = (x0 + x1) / 2, top + sag * 2
        u = 1 - t
        return u * u * x0 + 2 * u * t * mx + t * t * x1, u * u * top + 2 * u * t * my + t * t * top
    items = []  # (类型, t, 吊绳长度)
    n = 29  # 挂得满满的：相邻两只一高一低错开，远看连成一整排
    for i in range(n):
        t = 0.035 + 0.93 * i / (n - 1)
        hang = (3 if i % 2 == 0 else 15) + (i % 3) * 2
        items.append(("fu" if i % 4 in (1, 3) and i % 8 != 5 else "om", t, hang))
    period, t0, pose_dur, lag = 6.4, 1.2, 0.16, 0.035
    swing = [9, -6.5, 4.5, -3, 1.6, -0.6]  # 一阵风里每只挂件依次摆到的角度

    def body(mode):
        red = RED if mode == "light" else NIGHT_RED
        ink = INK if mode == "light" else NIGHT_INK
        defs = []
        for k, (body_c, cord) in enumerate(OMAMORI):
            for hang in sorted({h for kind, _, h in items if kind == "om"}):
                defs.append(omamori(f"om{k}_{hang}", body_c, cord, hang))
        for hang in sorted({h for kind, _, h in items if kind == "fu"}):
            for tilt_k, paper in ((0, 0.0), (1, 12.0), (2, -9.0)):
                fi, fc = furin(0, hang, 0.6, 0, paper, red)
                fi = fi if mode == "light" else to_night(fi)
                defs.append(f'<g id="fu{hang}_{tilt_k}"><path d="M0 0V{hang}" stroke="{ink}" stroke-width="0.8" />{fi}{fc}</g>')
        a, b = rope_pt(0.5)
        rope_d = f"M{x0} {top}Q{(x0 + x1) / 2} {top + sag * 2} {x1} {top}"
        rope = (f'<path d="{rope_d}" fill="none" stroke="{red}" stroke-width="2.4" stroke-linecap="round" />'
                f'<path d="{rope_d}" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-dasharray="2.4 2.4" stroke-opacity="0.9" />'
                + "".join(f'<path d="M{x} {top}c-2 6 -3 14 -2 22M{x} {top}c0 7 0 15 0 24M{x} {top}c2 6 3 14 2 22" stroke="#c79a2c" stroke-width="1" fill="none" stroke-linecap="round" />'
                          f'<circle cx="{x}" cy="{top}" r="3" fill="{red}" />' for x in (x0, x1)))

        def pose(angles):
            out = []
            for i, (kind, t, hang) in enumerate(items):
                px, py = rope_pt(t)
                a = angles[i]
                if kind == "om":
                    ref = f"om{(i * 5 // 3) % len(OMAMORI)}_{hang}"
                else:
                    ref = f"fu{hang}_{0 if abs(a) < 1 else (1 if a > 0 else 2)}"
                out.append(f'<use href="#{ref}" transform="translate({px:.1f} {py:.1f}) rotate({a:.1f})" />')
            return "".join(out)
        frames, k = [], 0
        end = t0 + lag * (n - 1) + pose_dur * len(swing)
        tick = 0.08
        while t0 + k * tick < end:
            tt = t0 + k * tick
            angles = []
            for i in range(n):
                j = int((tt - t0 - lag * i) // pose_dur)
                angles.append(swing[j] * (1.25 if items[i][0] == "fu" else 1) if 0 <= j < len(swing) else 0)
            frames.append(cel("dv", [(tt, tick)], pose(angles)))
            k += 1
        rest = f'<g>{pose([0] * n)}<set attributeName="visibility" to="hidden" begin="dv.begin+{t0:.2f}s" dur="{k * tick:.2f}s" /></g>'
        return f'<defs>{"".join(defs)}</defs>' + rope + clock("dv", period) + rest + "".join(frames)
    art.color(body("light"), body("dark"))
    art.write(OUT, "divider")


# ---------------------------------------------------------------- 播放卡：夏天的漫画分格
def qwave(k, amp, phase, cy, x0, x1):
    """一条正弦声波，每半个波长用一段二次贝塞尔（控制点在波峰处），比逐点采样省很多字节。amp(x) 是包络。返回 (d, 点列)。"""
    xs = [x0]
    n = math.floor((k * x0 + phase) / math.pi) + 1
    while True:
        x = (n * math.pi - phase) / k
        if x >= x1:
            break
        xs.append(x)
        n += 1
    xs.append(x1)
    segs = []
    for a, b in zip(xs, xs[1:]):
        m = (a + b) / 2
        h = amp(m) * math.sin(k * m + phase)
        segs.append((m, h, b))
    return segs


def wave_d(segs, cy, flip=1, start=True):
    out = f"M{segs[0][0] - (segs[0][2] - segs[0][0]):.1f} {cy}" if start else ""
    for m, h, b in segs:
        out += f"Q{m:.1f} {cy - 2 * h * flip:.1f} {b:.1f} {cy}"
    return out


def cumulus(base):
    """入道云：一团团圆叠成塔，墨色外轮廓、平平的云底，背光的下半部铺网点。静态。"""
    rows = [(base - 24, [(694, 30), (738, 36), (788, 38), (838, 34), (884, 32)]),
            (base - 66, [(718, 28), (762, 36), (810, 32), (854, 28)]),
            (base - 106, [(744, 26), (788, 32), (828, 24)]),
            (base - 140, [(770, 23), (804, 21)]),
            (base - 166, [(788, 17)])]
    circ = [(x, y, r) for y, row in rows for x, r in row]
    union = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" />' for x, y, r in circ)
    ring = "".join(f'<circle cx="{x}" cy="{y}" r="{r + 1.6}" />' for x, y, r in circ)
    bumps = []
    for x, y, r in circ[5:]:
        a0, a1 = math.radians(150), math.radians(250)
        bumps.append(f"M{x + r * math.cos(a0):.1f} {y + r * math.sin(a0):.1f}A{r} {r} 0 0 1 {x + r * math.cos(a1):.1f} {y + r * math.sin(a1):.1f}")
    return (f'<clipPath id="cuBase"><rect x="600" y="0" width="320" height="{base}" /></clipPath>'
            f'<clipPath id="cuBody">{union}</clipPath>'
            f'<linearGradient id="cuFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER}" /><stop offset="1" stop-color="{PAPER}" stop-opacity="0" /></linearGradient>'
            f'<g clip-path="url(#cuBase)"><g fill="{INK}">{ring}</g><g fill="{PAPER}">{union}</g>'
            f'<g clip-path="url(#cuBody)"><rect x="640" y="{base - 90}" width="280" height="90" fill="url(#tone)" fill-opacity="0.6" />'
            f'<rect x="640" y="{base - 91}" width="280" height="60" fill="url(#cuFade)" />'
            f'<path d="{"".join(bumps)}" fill="none" stroke="{INK}" stroke-width="0.9" stroke-linecap="round" stroke-opacity="0.75" /></g></g>'
            f'<path d="M{664} {base}H{900}" stroke="{INK}" stroke-width="1.2" />')


def now_playing():
    """一格夏天的漫画：网点天空、入道云、两根电线和一只风铃；左边一张用纸胶带贴着的拍立得（封面），
    右边是叙述框“NOW PLAYING 再生中”、漫画标题字的曲名、明朝体的歌手名；底下横贯一道会动的声波（网点填充 + 墨线 + 一根朱线）。
    声波每 0.08 秒换一格（二十格一个循环）；风铃每 6.4 秒被风吹动一次；音符一上一下。全部是 <set> 翻页，不用滤镜。"""
    W, H = 900, 300
    song, artist, artist_jp = TRACK
    song_jp = "ヒッチコック"
    black = load_font(SERIF, 800, song)
    reg = load_font(SERIF, 400, "NOW PLAYING — Yorushika")
    jp = load_font(MINCHO, 800, artist_jp + song_jp + "再生中ミーンミン…夏の音")
    art = Art(W, H, f"Now playing on Spotify: {artist} - {song}", lean=True)
    cover = base64.b64encode((OUT / "images" / "cover.jpg").read_bytes()).decode()
    art.css.append(text_css([black, reg, jp], TITLE_CSS + f"""
  .np-hero {{ font: 800 68px {SERIF_STACK}; fill: {INK}; stroke: {PAPER}; stroke-width: 3px; paint-order: stroke; stroke-linejoin: round; }}
  .np-jp {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; letter-spacing: 5px; stroke: {PAPER}; stroke-width: 6px; paint-order: stroke; stroke-linejoin: round; }}
  .np-en {{ font: 400 15px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.8; stroke: {PAPER}; stroke-width: 5px; paint-order: stroke; }}
  .np-cap {{ font: 400 10.5px {SERIF_STACK}; fill: {INK}; letter-spacing: 3.5px; }}
  .np-cj {{ font: 800 12px {MINCHO_STACK}; fill: {RED}; letter-spacing: 3px; }}
  .np-sfx {{ font: 800 18px {MINCHO_STACK}; fill: {PAPER}; stroke: {INK}; stroke-width: 2.6px; paint-order: stroke; stroke-linejoin: round; }}
  .np-pol {{ font: 800 12px {MINCHO_STACK}; fill: #2b2d33; letter-spacing: 3px; }}
"""))
    art.defs.append(inside(W, H) + paper_fade("skyUp"))

    # ---- 天空、入道云、电线 ----
    cl = cumulus(206)
    wires = (f'<path d="M12 58Q450 112 888 46" fill="none" stroke="{INK}" stroke-width="1.5" />'
             f'<path d="M12 72Q450 128 888 60" fill="none" stroke="{INK}" stroke-width="1" />')
    art.ink(panel(W, H) + f'<g clip-path="url(#inside)">'
            f'<rect x="12" y="12" width="{W - 24}" height="190" fill="url(#tone)" fill-opacity="0.55" /><rect x="12" y="11" width="{W - 24}" height="192" fill="url(#skyUp)" />'
            f'{cl}{wires}'
            f'<g transform="rotate(-7 600 40)"><text class="np-sfx" x="576" y="48">ミーン</text><text class="np-sfx" x="590" y="68" style="font-size:13px">ミンミン…</text></g></g>')

    # ---- 风铃：挂在上面那根电线的右端，每 6.4 秒一阵风 ----
    fx, fy = 842, 54
    poses = [(5, 16), (-4, -12), (3, 9), (-2, -6), (1.2, 3.5), (-0.5, -1.5)]
    dur, t0 = 0.16, 2.4
    hide = f'<set attributeName="visibility" to="hidden" begin="fw.begin+{t0:.2f}s" dur="{dur * len(poses):.2f}s" />'
    ri, rc = furin(fx, fy, 1.0)
    fi, fc = [clock("fw", 6.4), f"<g>{ri}{hide}</g>"], [f"<g>{rc}{hide}</g>"]
    for i, (tilt, paper) in enumerate(poses):
        pi, pc = furin(fx, fy, 1.0, tilt, paper)
        fi.append(cel("fw", [(t0 + i * dur, dur)], pi))
        fc.append(cel("fw", [(t0 + i * dur, dur)], pc))
    art.ink(f'<g clip-path="url(#inside)">{"".join(fi)}</g>')
    art.color(*both(f'<g clip-path="url(#inside)">{"".join(fc)}</g>'))

    # ---- 声波：横贯底部，网点填充的波形 + 一粗一细两根墨线 + 一根朱线 ----
    F, FRAME = 20, 0.08
    X0, X1, CY = 12, W - 12, 250

    def env(x, beat, ph):
        u = (x - X0) / (X1 - X0)
        return math.sin(math.pi * u) ** 1.6 * (0.72 + 0.28 * math.sin(3 * math.pi * u - ph)) * beat
    ink_frames, red_frames = [], []
    for f in range(F + 1):
        ph = 2 * math.pi * (f % F) / F
        beat = 0.82 + 0.18 * abs(math.sin(2 * ph))
        main = qwave(2 * math.pi / 92, lambda x: 24 * env(x, beat, ph), -ph, CY, X0, X1)
        echo = qwave(2 * math.pi / 58, lambda x: 15 * env(x, beat, ph + 1), 2 * ph + 1, CY, X0, X1)
        accent = qwave(2 * math.pi / 130, lambda x: 18 * env(x, beat, ph + 2), -ph + 2, CY, X0, X1)
        upper = wave_d(main, CY)
        lower = "".join(f"Q{m:.1f} {CY + 2 * h:.1f} {a:.1f} {CY}" for (m, h, _), a in zip(reversed(main), [s[2] for s in reversed(main[:-1])] + [main[0][0] - (main[0][2] - main[0][0])]))
        ink_frames.append(f'<path d="{upper}{lower}Z" fill="url(#toneFine)" fill-opacity="0.75" />'
                          f'<path d="{upper}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round" />'
                          f'<path d="{wave_d(echo, CY)}" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity="0.5" />')
        red_frames.append(f'<path d="{wave_d(accent, CY)}" fill="none" stroke="{RED}" stroke-width="1.5" stroke-linecap="round" />')
    art.ink(f'<g clip-path="url(#inside)"><path d="M{X0} {CY}H{X1}" stroke="{INK}" stroke-width="0.6" stroke-opacity="0.4" />'
            + clock("w", F * FRAME) + poster(ink_frames[3]) + "".join(cel("w", [(f * FRAME, FRAME)], ink_frames[f]) for f in range(F)) + "</g>")
    art.color(*both(f'<g clip-path="url(#inside)">' + poster(red_frames[3]) + "".join(cel("w", [(f * FRAME, FRAME)], red_frames[f]) for f in range(F)) + "</g>"))

    # ---- 拍立得：封面，纸胶带贴着，微微歪着 ----
    PX, PY, PW, PH, PI = 62, 34, 196, 230, 12
    pc = (PX + PW / 2, PY + PH / 2)
    art.defs.append(f'<clipPath id="photo"><rect x="{PX + PI}" y="{PY + PI}" width="{PW - 2 * PI}" height="{PW - 2 * PI}" /></clipPath>'
                    f'<pattern id="tapeStripe" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3" height="6" fill="{RED}" fill-opacity="0.35" /></pattern>')
    tape = (f'<g transform="rotate(-4 {pc[0]} {PY})"><rect x="{pc[0] - 38}" y="{PY - 10}" width="76" height="20" fill="#f1e7c4" fill-opacity="0.88" />'
            f'<rect x="{pc[0] - 38}" y="{PY - 10}" width="76" height="20" fill="url(#tapeStripe)" />'
            f'<path d="M{pc[0] - 38} {PY - 10}l-2 3l2 3l-2 3l2 3l-2 3l2 3l-2 2M{pc[0] + 38} {PY - 10}l2 3l-2 3l2 3l-2 3l2 3l-2 3l2 2" stroke="#f1e7c4" stroke-width="1" fill="none" /></g>')
    polaroid = (f'<g transform="rotate(-5 {pc[0]} {pc[1]})">'
                f'<rect x="{PX + 5}" y="{PY + 7}" width="{PW}" height="{PH}" fill="#000000" fill-opacity="0.22" />'
                f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="#fbfaf6" stroke="#15171d" stroke-opacity="0.35" stroke-width="0.8" />'
                f'<image x="{PX + PI}" y="{PY + PI}" width="{PW - 2 * PI}" height="{PW - 2 * PI}" preserveAspectRatio="xMidYMid slice" clip-path="url(#photo)" href="data:image/jpeg;base64,{cover}" />'
                f'<rect x="{PX + PI}" y="{PY + PI}" width="{PW - 2 * PI}" height="{PW - 2 * PI}" fill="none" stroke="#15171d" stroke-opacity="0.25" stroke-width="0.6" />'
                f'<text class="np-pol" x="{pc[0]}" y="{PY + PH - 12}" text-anchor="middle">夏の音 · {song_jp}</text>{tape}</g>')
    art.color(polaroid)

    # ---- 音符：拍立得右上，一上一下 ----
    def notes(dy):
        return (f'<g transform="translate(286 {84 + dy}) rotate(12)">{music_note(0, 1.0)}</g>'
                f'<g transform="translate(300 {128 - dy}) rotate(-10)">{music_note(1, 0.8)}</g>')
    art.ink(clock("nt", 1.2) + poster(notes(0)) + cel("nt", [(0, 0.6)], notes(-3)) + cel("nt", [(0.6, 0.6)], notes(3)))

    # ---- 文字：叙述框、标题字、歌手名 ----
    X = 344
    cap_w = 210
    hero = f'<text class="np-hero" x="{X}" y="150">{escape(song)}</text>'
    art.ink(f'<rect x="{X + 3}" y="{37}" width="{cap_w}" height="28" fill="{INK}" />'
            f'<rect x="{X}" y="34" width="{cap_w}" height="28" fill="{PAPER}" stroke="{INK}" stroke-width="1.6" />'
            f'<text class="np-cap" x="{X + 14}" y="52">NOW PLAYING</text>'
            + title_fx(hero, 5.0, 1.25)
            + f'<text class="np-jp" x="{X + 2}" y="190">{artist_jp}</text>'
            f'<text class="np-en" x="{X + (jp.width(artist_jp, 22, 5) if jp else 96) + 14:.1f}" y="189">— {escape(artist)}</text>')
    art.color(*both(f'<text class="np-cj" x="{X + cap_w - 14}" y="53" text-anchor="end">再生中</text>'
                    f'<circle cx="{X + 132}" cy="48" r="2.4" fill="{RED}" />'))
    art.ink(frame(W, H))
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


def crackle(spots, rng, mode, period=3.2):
    """火星：三阵、每阵三格（0.12 秒一格），每格十来颗小四角星落在几朵花的外缘。只靠 <set> 翻页，一个周期只重画九次。"""
    pal = FW_DAY if mode == "light" else FW_NIGHT
    hot = ["#ffffff", pal["gold"], pal["silver"]] if mode == "dark" else [pal["gold"], pal["orange"], pal["red"]]
    rims = [(x, y, r) for x, y, r, kind in spots if kind in ("kiku", "botan", "wa")]
    out = [clock("cr", period)]
    for burst, t0 in enumerate((0.3, 1.4, 2.3)):
        x, y, r = rims[(burst * 2) % len(rims)]
        pts = [(x + r * rng.uniform(0.75, 1.15) * math.cos(a), y + r * rng.uniform(0.75, 1.15) * math.sin(a))
               for a in (rng.uniform(0, 2 * math.pi) for _ in range(9))]
        for f, size in enumerate((1.0, 1.6, 0.8)):
            stars = "".join(f'<path d="{star(px + rng.uniform(-2, 2), py + rng.uniform(-2, 2), size * rng.uniform(2.2, 3.6))}" fill="{rng.choice(hot)}" />' for px, py in pts)
            out.append(cel("cr", [(t0 + f * 0.12, 0.12)], stars))
    return "".join(out)


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
    # 夜空里一直开着的花火（静态，彩色），再加一层很轻的“噼啪”：每 3.2 秒有三小阵火星在几朵花的外缘闪一下
    fw_spots = [(566, 300, 72, "kiku"), (662, 138, 50, "botan"), (330, 66, 58, "kamuro"), (692, 336, 42, "wa"),
                (404, 226, 38, "botan"), (642, 44, 36, "kiku"), (520, 410, 40, "jelly"), (726, 436, 32, "botan")]
    fl_defs, fl_body = still_hanabi("pl", fw_spots, random.Random(5), "light")
    fd_defs, fd_body = still_hanabi("pd", fw_spots, random.Random(5), "dark")
    fl_body += crackle(fw_spots, random.Random(9), "light")
    fd_body += crackle(fw_spots, random.Random(9), "dark")
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
              f'<g opacity="0.85">{fl_body}</g></g>',
              f'<defs>{fd_defs}<linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{night[0]}" /><stop offset="0.55" stop-color="{night[1]}" /><stop offset="1" stop-color="{night[2]}" /></linearGradient>'
              f'<linearGradient id="skyFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{night[0]}" stop-opacity="0" />'
              f'<stop offset="{0.55 / hd:.4f}" stop-color="{night[1]}" stop-opacity="{0.55 / hd:.4f}" /><stop offset="1" stop-color="{mix(night[1], night[2], (hd - 0.55) / 0.45)}" /></linearGradient></defs>'
              f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="url(#nightSky)" />'
              f'<rect x="16" y="16" width="{ax}" height="260" fill="url(#tone)" fill-opacity="0.2" /><rect x="16" y="16" width="{ax}" height="261" fill="url(#skyFade)" />'
              f'<g opacity="0.92">{fd_body}</g></g>')
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
    print("wrote manga light/dark")


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

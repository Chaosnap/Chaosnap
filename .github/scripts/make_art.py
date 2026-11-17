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
from manga import FW_DAY, FW_NIGHT, NIGHT_PAPER, SCHEMES, TITLE_CSS, firework, hanabi_show, music_note, star, to_night  # noqa: E402

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


# ---------------------------------------------------------------- 分隔线：一根发丝线，正中一颗斜放的四角星，隔一会儿转半圈
def divider():
    """简洁的分隔线：两边是一根往外淡出的墨色发丝线，正中一颗朱色的四角星（斜放成 ×）。
    每 4.8 秒星星缓缓转半圈（约 1.4 秒，慢进慢出），其余时间静止；图很小，转的时候重画也不费事。
    不跑动画的环境里就是一颗斜放的星。上下留白相等（下面的分区标题图自带一点顶部空白，这里下面少留一点）。"""
    W = 760
    R = 12.5
    cx, cy = W / 2, 12 + R
    H = round(cy + R + 6)
    art = Art(W, H, role="presentation", lean=True)
    art.css.append(f"""
  .twirl {{ animation: twirl 4.8s infinite; }}
  @keyframes twirl {{
    0%, 70% {{ transform: rotate(0deg); animation-timing-function: cubic-bezier(0.45, 0, 0.2, 1); }}
    100% {{ transform: rotate(180deg); }}
  }}
  @media (prefers-reduced-motion: reduce) {{ .twirl {{ animation: none; }} }}
""")
    art.defs.append(
        f'<linearGradient id="hairL" gradientUnits="userSpaceOnUse" x1="60" x2="{cx - 30}" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" stop-opacity="0.6" /></linearGradient>'
        f'<linearGradient id="hairR" gradientUnits="userSpaceOnUse" x1="{cx + 30}" x2="{W - 60}" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0.6" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    gap = R + 12
    art.ink(f'<rect x="60" y="{cy - 0.4:.1f}" width="{cx - gap - 60:.1f}" height="0.8" fill="url(#hairL)" />'
            f'<rect x="{cx + gap:.1f}" y="{cy - 0.4:.1f}" width="{cx - gap - 60:.1f}" height="0.8" fill="url(#hairR)" />'
            + "".join(f'<path d="{star(cx + sx * (gap + 4), cy, 2.6)}" fill="{INK}" fill-opacity="0.7" transform="rotate(45 {cx + sx * (gap + 4):.1f} {cy})" />' for sx in (-1, 1)))
    # 星的形状斜放 45°（×）画在原点，外面再平移到正中；CSS 只转里面那一层。
    # 白色的星：浅色版在纸上描一圈细墨边才看得见，深色版就是一颗干净的白星
    diag = f'<path d="{star(0, 0, R)}" transform="rotate(45)" />'

    def body(fill, line):
        return f'<g transform="translate({cx} {cy})"><g class="twirl" fill="{fill}"{line} stroke-linejoin="round">{diag}</g></g>'
    art.color(body("#ffffff", f' stroke="{INK}" stroke-width="1.1"'), body("#f6f2ea", ""))
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


def cumulus(base, cx=770):
    """入道云（漫画画法，手排的鼓包）：宽宽的云脚、两边肩膀一层层往上收、顶上一团云冠，略向右倾。
    所有圆先描一圈墨、再整体盖纸，只留外面那道起伏的轮廓；整团铺网点，再盖上每团往左上挪的“受光圆”，
    网点于是只留在鼓包右下和鼓包之间的缝里（光从左上来）；几团关键的鼓包往里描一段弧，表示前后叠着。静态。"""
    lobes = [  # (dx, dy, r, 往里描弧的角度区间 或 None)
        (-120, -15, 20, None), (-98, -30, 29, (-30, 60)), (-80, -66, 31, (-20, 75)), (-64, -101, 27, (-10, 80)),
        (-48, -131, 24, (0, 85)), (-30, -156, 21, None), (-10, -171, 20, (20, 120)), (12, -177, 22, (40, 150)),
        (33, -167, 18, None), (48, -144, 23, (95, 190)), (62, -114, 27, (100, 195)), (76, -82, 30, (105, 200)),
        (92, -48, 32, (110, 200)), (112, -22, 25, None), (130, -11, 17, None),
        (-58, -18, 30, None), (-14, -20, 32, None), (34, -18, 32, None), (74, -16, 30, None),
    ]
    fill = [(-40, -50, 46), (12, -50, 50), (52, -48, 38), (-22, -96, 44), (22, -104, 42), (-6, -138, 32), (16, -142, 30), (40, -80, 36)]
    circ = [(cx + dx, base + dy, r, arc) for dx, dy, r, arc in lobes] + [(cx + dx, base + dy, r, None) for dx, dy, r in fill]
    ring = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 1.4:.1f}" />' for x, y, r, _ in circ)
    union = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" />' for x, y, r, _ in circ)
    lit = "".join(f'<circle cx="{x - r * 0.3:.1f}" cy="{y - r * 0.34:.1f}" r="{r * 0.84:.1f}" />' for x, y, r, _ in circ)
    arcs = []
    for x, y, r, arc in circ:
        if not arc:
            continue
        a0, a1 = (math.radians(t) for t in arc)
        arcs.append(f"M{x + r * math.cos(a0):.1f} {y + r * math.sin(a0):.1f}A{r} {r} 0 0 1 {x + r * math.cos(a1):.1f} {y + r * math.sin(a1):.1f}")
    return (f'<defs><clipPath id="cuBase"><rect x="560" y="0" width="360" height="{base}" /></clipPath>'
            f'<clipPath id="cuBody">{union}</clipPath>'
            f'<linearGradient id="cuFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER}" /><stop offset="1" stop-color="{PAPER}" stop-opacity="0" /></linearGradient></defs>'
            f'<g clip-path="url(#cuBase)"><g fill="{INK}">{ring}</g><g fill="{PAPER}">{union}</g>'
            f'<g clip-path="url(#cuBody)"><rect x="580" y="{base - 210}" width="340" height="210" fill="url(#tone)" fill-opacity="0.6" />'
            f'<g fill="{PAPER}">{lit}</g>'
            f'<rect x="580" y="{base - 40}" width="340" height="40" fill="url(#toneFine)" fill-opacity="0.8" />'
            f'<rect x="580" y="{base - 41}" width="340" height="26" fill="url(#cuFade)" />'
            f'<path d="{"".join(arcs)}" fill="none" stroke="{INK}" stroke-width="1" stroke-linecap="round" stroke-opacity="0.85" /></g></g>'
            f'<path d="M{cx - 146:.0f} {base}H{cx + 152:.0f}" stroke="{INK}" stroke-width="1.3" stroke-linecap="round" />')


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
    # 和头图同一种画法的积雨云（manga.cloud）；云底以下那截平切掉，像头图里被屋顶挡住一样
    # 云脚不硬切：往下渐渐化进地平线的薄雾里（一层“透明→纸色”的渐变盖在云的下半截）
    cl = (f'<clipPath id="cloudCut"><rect x="560" y="0" width="340" height="262" /></clipPath>'
          f'<linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER}" stop-opacity="0" />'
          f'<stop offset="0.55" stop-color="{PAPER}" stop-opacity="0.75" /><stop offset="1" stop-color="{PAPER}" /></linearGradient>'
          f'<g clip-path="url(#cloudCut)">' + re.sub(r'<rect [^>]*height="400"[^>]*/>', "", cloud("np", 772, 240, 300, 178, 3, shade_left=False).replace('<g class="cloud"', "<g")) + "</g>"
          f'<rect x="560" y="176" width="340" height="88" fill="url(#haze)" />')
    wires = (f'<path d="M12 58Q450 112 888 46" fill="none" stroke="{INK}" stroke-width="1.5" />'
             f'<path d="M12 72Q450 128 888 60" fill="none" stroke="{INK}" stroke-width="1" />')
    art.ink(panel(W, H) + f'<g clip-path="url(#inside)">'
            f'<rect x="12" y="12" width="{W - 24}" height="190" fill="url(#tone)" fill-opacity="0.55" /><rect x="12" y="11" width="{W - 24}" height="192" fill="url(#skyUp)" />'
            f'{cl}{wires}'
            f'<g transform="rotate(-7 600 40)"><text class="np-sfx" x="576" y="48">ミーン</text><text class="np-sfx" x="590" y="68" style="font-size:13px">ミンミン…</text></g></g>')

    # ---- 风铃：和头图同一只（manga.chime）：铃身轻轻来回摆，短册慢半拍 ----
    art.css.append(f"""
  .chime {{ animation: chimeSwing 4.8s {EASE} infinite; }}
  .chime-paper {{ animation: paperSwing 4.8s {EASE} infinite; animation-delay: -0.5s; }}
  @keyframes chimeSwing {{ 0%, 100% {{ transform: rotate(5deg); }} 50% {{ transform: rotate(-5deg); }} }}
  @keyframes paperSwing {{ 0%, 100% {{ transform: rotate(13deg); }} 50% {{ transform: rotate(-13deg); }} }}
  @media (prefers-reduced-motion: reduce) {{ .chime, .chime-paper {{ animation: none; }} }}
""")
    art.ink(f'<g clip-path="url(#inside)">{chime("np", 838, 52, 0.82, "涼")}</g>')

    # ---- 声波：横贯底部的一条“丝带”——七根细线相位依次错开，拧成一股，正中一根略粗；一根朱线以别的频率穿过去。两端用渐变描边淡出 ----
    F, FRAME = 20, 0.08
    X0, X1, CY = 12, W - 12, 248
    art.defs.append(f'<linearGradient id="wvInk" gradientUnits="userSpaceOnUse" x1="{X0}" x2="{X1}" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0" />'
                    f'<stop offset="0.14" stop-color="{INK}" /><stop offset="0.86" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    red_grad = (f'<linearGradient id="wvRed" gradientUnits="userSpaceOnUse" x1="{X0}" x2="{X1}" y1="0" y2="0"><stop offset="0" stop-color="{RED}" stop-opacity="0" />'
                f'<stop offset="0.2" stop-color="{RED}" /><stop offset="0.8" stop-color="{RED}" /><stop offset="1" stop-color="{RED}" stop-opacity="0" /></linearGradient>')

    def env(x, beat):
        u = (x - X0) / (X1 - X0)
        return math.sin(math.pi * u) ** 1.3 * beat
    strands = [(-3, 0.55, 0.22), (-2, 0.65, 0.34), (-1, 0.75, 0.5), (0, 1.5, 1.0), (1, 0.75, 0.5), (2, 0.65, 0.34), (3, 0.55, 0.22)]
    ink_frames, red_frames = [], []
    for f in range(F):
        ph = 2 * math.pi * f / F
        beat = 0.86 + 0.14 * math.sin(2 * ph)
        lines = []
        for j, w, op in strands:
            segs = qwave(2 * math.pi / 104, lambda x, j=j: (19 - 1.6 * abs(j)) * env(x, beat), -ph + 0.32 * j, CY, X0, X1)
            lines.append(f'<path d="{wave_d(segs, CY)}" stroke-width="{w}" stroke-opacity="{op}" />')
        ink_frames.append(f'<g fill="none" stroke="url(#wvInk)" stroke-linecap="round">{"".join(lines)}</g>')
        accent = qwave(2 * math.pi / 156, lambda x: 15 * env(x, beat), ph + 1.4, CY, X0, X1)
        red_frames.append(f'<path d="{wave_d(accent, CY)}" fill="none" stroke="url(#wvRed)" stroke-width="1.1" stroke-linecap="round" />')
    art.ink(f'<g clip-path="url(#inside)">' + clock("w", F * FRAME) + poster(ink_frames[3]) + "".join(cel("w", [(f * FRAME, FRAME)], ink_frames[f]) for f in range(F)) + "</g>")
    reds = f'<defs>{red_grad}</defs><g clip-path="url(#inside)">' + poster(red_frames[3]) + "".join(cel("w", [(f * FRAME, FRAME)], red_frames[f]) for f in range(F)) + "</g>"
    art.color(reds, reds.replace(RED, NIGHT_RED))

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


def festival_shots(rng, period=112):
    """排一场花火：每 4～6 格点一发，三成的时候两发一起；位置散在夜空里（立绘右边、对话框四周、金网后面），大小 90～200。"""
    kinds = ["kiku"] * 7 + ["botan"] * 6 + ["kamuro"] * 3 + ["wa"] * 2
    schemes = [("gold", "orange", "silver"), ("pink", "violet", "gold"), ("cyan", "blue", "silver"), ("red", "gold", "silver"),
               ("violet", "pink", "silver"), ("green", "cyan", "gold"), ("orange", "red", "gold"), ("blue", "violet", "silver")]
    shots, t, k = [], 0, 0
    while t < period - 8:
        for _ in range(2 if rng.random() < 0.3 else 1):
            kind = rng.choice(kinds)
            R = rng.uniform(90, 200) if kind != "wa" else rng.uniform(70, 120)
            x, y = rng.uniform(380, 780), rng.uniform(70, 380)
            if rng.random() < 0.18:  # 偶尔一发开在立绘头顶上方的那块天
                x, y = rng.uniform(90, 330), rng.uniform(40, 110)
            names = ("gold", "gold", "silver") if kind == "kamuro" else schemes[k % len(schemes)]
            shots.append((t, round(x), round(y), round(R), kind, names))
            k += 1
        t += rng.randint(4, 6)
    return shots


def hanabi_cycle(prefix, spots, rng, mode, period=6.4, tick=0.16):
    """会动的夜空花火：每一发 升空（三格）→ 炸开（两格，由小到大）→ 盛开（停留三秒半）→ 变成灰烬往下飘、渐渐淡掉（四格），然后暗下来等下一轮。
    八发错开起点，任何时候都有五六朵正开着。花火的形状只在 <defs> 里画一次（彩色一份、灰烬一份），每一格只是一只 <use> 换位置、大小和透明度；
    所有换格时刻对齐到 0.16 秒的整数倍，整张漫画页一秒最多重画六次。不跑动画的环境里显示全部盛开的定格。"""
    pal = FW_DAY if mode == "light" else FW_NIGHT
    ash = "#a19e96" if mode == "light" else "#5d6470"
    defs, frames, still = [], [clock(prefix + "k", period)], []
    n = len(spots)

    def spans(at, dur, t0):
        st = (t0 + at) % period
        if st + dur <= period + 1e-6:
            return [(st, dur)]
        return [(st, period - st), (0.0, dur - (period - st))]
    for i, (x, y, r, kind) in enumerate(spots):
        g, b = firework(f"{prefix}{i}", kind, 0, 0, r, SCHEMES[(i * 3 + 2) % len(SCHEMES)], 6, 0, rng, mode)
        b = re.sub(r'<circle class="fw-(?:rise|flash)"[^>]*/>', "", b)
        b = re.sub(r'<g class="fw" style="[^"]*">', "<g>", b).replace(' class="fw-glint"', "")
        gray = re.sub(r"url\(#fg[^)]*\)", ash, re.sub(r"#[0-9a-fA-F]{6}", ash, b))
        defs.append(g + f'<g id="{prefix}c{i}">{b}</g><g id="{prefix}a{i}">{gray}</g>')
        still.append(f'<use href="#{prefix}c{i}" transform="translate({x} {y})" />')
        t0 = round(i * period / n / tick) * tick
        spark = pal["gold"] if mode == "light" else "#fff3cf"
        rise = 150
        for k, u in enumerate((0.0, 0.5, 0.85)):  # 升空：一颗光点拖着越来越短的尾巴
            yy = y + rise * (1 - u) ** 1.6
            frames.append(cel(prefix + "k", spans(k * tick, tick, t0),
                              f'<path d="M{x} {yy:.0f}v{26 * (1 - u) + 8:.0f}" stroke="{spark}" stroke-width="1.6" stroke-linecap="round" stroke-opacity="0.75" /><circle cx="{x}" cy="{yy:.0f}" r="2.2" fill="{spark}" />'))
        for k, sc in enumerate((0.45, 0.8)):  # 炸开
            frames.append(cel(prefix + "k", spans((3 + k) * tick, tick, t0), f'<use href="#{prefix}c{i}" transform="translate({x} {y}) scale({sc})" />'))
        frames.append(cel(prefix + "k", spans(5 * tick, 22 * tick, t0), f'<use href="#{prefix}c{i}" transform="translate({x} {y})" />'))  # 盛开（3.5 秒）
        for k, (dy, op, sc) in enumerate(((3, 0.8, 1.02), (9, 0.6, 1.04), (17, 0.4, 1.06), (27, 0.2, 1.08))):  # 灰烬往下飘
            frames.append(cel(prefix + "k", spans((27 + 2 * k) * tick, 2 * tick, t0),
                              f'<use href="#{prefix}a{i}" transform="translate({x} {y + dy}) scale({sc})" opacity="{op}" />'))
    body = "".join(frames) + poster("".join(still))
    return "".join(defs), body


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
    # 夜空的花火：一发发升空、炸开、盛开，再化成灰烬飘落（见 hanabi_cycle）
    fw_spots = [(566, 300, 72, "kiku"), (662, 138, 50, "botan"), (330, 66, 58, "kamuro"), (692, 336, 42, "wa"),
                (404, 226, 38, "botan"), (642, 44, 36, "kiku"), (520, 410, 40, "jelly"), (726, 436, 32, "botan")]
    # 一场花火大会：约 9 秒一轮、二十多发，常常两发一起上；菊（拖尾）、牡丹（亮点、末尾噼啪）、冠菊（金色垂柳）、輪，大小交错，铺满整片夜空。
    # 用 manga.hanabi_show：弹道 + 阻力 + 重力、光晕、炸开的闪光、拖尾、芯、噼啪；对称的部分用 <use> 转出来，文件不至于太大。
    shots = festival_shots(random.Random(31), period=112)
    fl_defs, fl_body, _ = hanabi_show("fwl", shots, random.Random(5), "light", 112)
    fd_defs, fd_body, n_frames = hanabi_show("fwd", shots, random.Random(5), "dark", 112)
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
    print(f"wrote manga light/dark ({len(shots)} shells, {n_frames} frames per {112 * TICK:.2f}s)")


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

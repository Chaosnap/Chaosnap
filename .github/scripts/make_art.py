#!/usr/bin/env python3
"""主页上手工设计的动态 SVG（黑白漫画风，和 me 站点“週刊ユキ”同一套语言）。

每张图出浅色、深色两版（*-light.svg / *-dark.svg），README 用 <picture> 按访客主题切换。
改了文字或效果后在仓库根目录运行 `python3 .github/scripts/make_art.py`，再提交 profile/。
只重做其中几张：`python3 .github/scripts/make_art.py header quote`。需要联网取字体（Google Fonts，只取用到的字）。

动画的约定：节拍统一在 1.6 秒的倍数上；所有循环用负延迟错开相位，
任何时刻定格，主体（字、景物）都完整可见，只有粒子在流动，不出现空白帧，也不用闪烁。
"""
import base64
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (EASE, EASE_OUT, GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_INK, NIGHT_RED, PAPER, RED, SERIF,  # noqa: E402
                   SERIF_STACK, Art, barcode, chime, cloud, fence, festival, film_strip, foam, jellyfish, lens_flare,
                   letters, load_font, morph, music_note, petals, pole, rain_field, sheen_grad, smooth, sparkles, splash,
                   splashes, stamp, starburst, sun, sun_ink, sun_rays, sun_rings, title_fx, wagasa, wire, wire_point)

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


def panel(w, h, rx=6):
    """漫画分格：纸、颗粒。"""
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="{PAPER}" />'
            f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" filter="url(#grain)" />')


def frame(w, h, rx=6):
    """外粗内细的双线框。"""
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{rx}" fill="none" stroke="{INK}" stroke-width="3.5" />'
            f'<rect x="11" y="11" width="{w - 22}" height="{h - 22}" rx="{max(rx - 4, 1)}" fill="none" stroke="{INK}" stroke-width="0.9" />')


def text_css(fonts, extra=""):
    return "".join(f.css() for f in fonts) + extra


def inside(w, h):
    return f'<clipPath id="inside"><rect x="12" y="12" width="{w - 24}" height="{h - 24}" rx="3" /></clipPath>'


# ---------------------------------------------------------------- 头图：夕焼けの屋上
def header(F):
    W, H = 1200, 430
    rng = random.Random(4)
    art = Art(W, H, "Hi there, I am Yuki")
    SX, SY, SR = 948, 200, 86
    title, tl, tw = letters(F["black"], "HI THERE", 118, 54, 200, "hero float", spacing=3, step=0.12, anchor="start")
    name, _, nw = letters(F["regular"], "— I am Yuki —", 32, 60, 252, "name float", spacing=1.5, step=0.09, anchor="start")
    jp, jl, jw = letters(F["jp"], HEAD_JP, 21, 92, 292, "jp float", spacing=6, step=0.1, anchor="start")
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

    # 远景：天空网点、放射线、日轮外的光圈
    art.ink(panel(W, H) + f"""<g clip-path="url(#inside)">
  <rect x="12" y="44" width="{W - 24}" height="190" fill="url(#tone)" opacity="0.42" mask="url(#toneUp)" />
  <g mask="url(#rayMask)">{sun_rays(SX, SY, 48, SR + 16, 1100, 0.12)}</g>
  {sun_rings(SX, SY, SR + 6)}
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
  {jellyfish("h1", 760, 226, 0.78, 0.0, 0.95, 1)}
  {jellyfish("h2", 548, 76, 0.36, 1.1, 0.7, 2)}
  {jellyfish("h3", 330, 318, 0.3, 2.3, 0.6, 3)}
  {jellyfish("h4", 1040, 292, 0.42, 1.7, 0.7, 4)}
</g>""")
    art.color(lens_flare(SX, SY, 360, 330, "light"), lens_flare(SX, SY, 360, 330, "dark"))

    # 近景：天台的金网、胶片边、泡沫和樱花
    art.ink(f"""<g clip-path="url(#inside)">
  {fence("H", 12, W - 12, 318, 388, [96, 420, 760, 1188])}
  {film_strip(388, W)}
  {foam(rng, 44, 30, W - 30, 300, 400, 2.5, 11, (140, 330))}
  {petals(rng, 22, 20, W - 140, -10, 420)}
  {sparkles([(250, 96, 8, 0), (700, 330, 7, 1.1), (1170, 300, 6, 2.2), (835, 60, 7, 0.6), (40, 250, 6, 1.7)])}
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
    title, tl, tw = letters(F["black"], "THE END", 100, W / 2, 200, "hero float", spacing=4, step=0.12)
    jp, _, _ = letters(F["jp"], FOOT_JP, 22, W / 2, 248, "jp float", spacing=6, step=0.1)
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
  .seal {{ transform-box: fill-box; transform-origin: center; animation: seal 6.4s {EASE} infinite alternate; }}
  @keyframes seal {{ from {{ transform: rotate(-9deg) scale(1); }} to {{ transform: rotate(-5deg) scale(1.05); }} }}
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
  {jellyfish("f1", 1000, 118, 0.92, 0.4, 1.0, 5)}
  {jellyfish("f2", 890, 66, 0.42, 1.9, 0.8, 6)}
  {jellyfish("f3", 1110, 236, 0.34, 2.6, 0.6, 7)}
  {chime("F", 1150, 12, 1.05, "雨")}
  {foam(rng, 22, 120, W - 120, floor_y + 6, H - 20, 2.2, 8, (90, 220))}
  {petals(rng, 12, 60, W - 200, -10, 360)}
  {rain_field(random.Random(3), 12, 12, W - 24, H - 30, 64, 0, -0.16)}
  <ellipse cx="{W / 2}" cy="190" rx="360" ry="96" fill="url(#calm)" />
</g>
<text class="meta" x="{W / 2}" y="100" text-anchor="middle">SEMINAR · SCIENCE · INTELLIGENCE · FUTURE</text>""")
    art.ink(title_fx(title, 5.0, 1.25) + jp + frame(W, H))

    def seal(red):
        return (f'<g class="seal"><circle cx="{seal_x:.0f}" cy="158" r="31" fill="{red}" /><circle cx="{seal_x:.0f}" cy="158" r="26" fill="none" stroke="#ffffff" stroke-width="1.2" />'
                f'<text x="{seal_x:.0f}" y="169" text-anchor="middle" style="font: 800 30px {MINCHO_STACK}; fill: #ffffff">完</text></g>')
    art.color(seal(RED), seal(NIGHT_RED))
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
    text, tl, _ = letters(F["bold"], english, size, x0 + sw + 16, 74, "t float", spacing=0.5, step=0.07, anchor="start")
    jp, jl, jw = letters(F["jp"], japanese, 15, W / 2, 112, "j", spacing=8, step=0)
    right = x0 + total
    motif = [lambda: jellyfish(f"t{i}", right + 72, 42, 0.42, i * 0.7, 0.55, i),
             lambda: chime(f"t{i}", right + 64, 6, 0.8),
             lambda: foam(rng, 7, right + 30, right + 110, 70, 118, 2.5, 7, (40, 90))][i % 3]()
    art.css.append(text_css([F["bold"], F["regular"], F["jp"]], f"""
  .t {{ font: 700 {size}px {SERIF_STACK}; fill: url(#sheenT); stroke: {PAPER}; stroke-width: 2.5px; paint-order: stroke; stroke-linejoin: round; }}
  .meta {{ font: 400 11.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 4px; }}
  .j {{ font: 800 15px {MINCHO_STACK}; fill: {INK}; }}
"""))
    art.defs.append(sheen_grad("sheenT", tl, tl + tw, 6.4, i * 1.28, 46))
    art.ink(f'<text class="meta" x="{x0 + sw + 16:.1f}" y="30">EPISODE {i:02d} · {english.upper()}</text>'
            f'<path d="M{jl - 26:.0f} 107H{jl - 150:.0f}" stroke="{INK}" stroke-width="1" /><path d="M{jl + jw + 26:.0f} 107H{jl + jw + 150:.0f}" stroke="{INK}" stroke-width="1" />'
            f'<circle cx="{jl - 154:.0f}" cy="107" r="2" fill="{INK}" /><circle cx="{jl + jw + 154:.0f}" cy="107" r="2" fill="{INK}" />'
            f'{motif}{foam(rng, 6, x0 - 110, x0 - 14, 64, 122, 2.2, 6.5, (40, 90))}'
            f'{petals(rng, 4, 40, W - 40, -10, 150)}'
            f'{sparkles([(x0 - 44, 34, 6, 0.3), (right + 18, 26, 5, 1.6), (x0 - 80, 70, 4, 2.4), (right + 130, 96, 4, 0.9)])}')
    art.color(stamp(round(x0), 46, sw, 36, label, 17), stamp(round(x0), 46, sw, 36, label, 17).replace(RED, NIGHT_RED))
    art.ink(title_fx(text, 3.0, 1.0) + jp)
    art.write(OUT, f"title-{name}")


# ---------------------------------------------------------------- 分隔线
def divider():
    W, H = 800, 44
    rng = random.Random(2)
    art = Art(W, H, role="presentation")
    art.defs.append(f'<linearGradient id="ruleL" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity="0" /><stop offset="1" stop-color="{INK}" /></linearGradient>'
                    f'<linearGradient id="ruleR" x1="0" x2="1"><stop offset="0" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    art.ink(f'<rect x="30" y="21.5" width="340" height="1" fill="url(#ruleL)" /><rect x="430" y="21.5" width="340" height="1" fill="url(#ruleR)" />'
            f'<rect x="30" y="25" width="340" height="0.5" fill="url(#ruleL)" opacity="0.6" /><rect x="430" y="25" width="340" height="0.5" fill="url(#ruleR)" opacity="0.6" />'
            f'<g transform="translate(400 22)"><g class="breathe" style="animation-duration:3.2s"><path d="M0 -7C1 -10 3 -12 5 -12C9 -12 11 -6 9 0C7 6 3 10 0 13C-3 10 -7 6 -9 0C-11 -6 -9 -12 -5 -12C-3 -12 -1 -10 0 -7Z" '
            f'transform="scale(0.8)" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" /></g></g>'
            f'{foam(rng, 7, 350, 450, 36, 44, 1.6, 3.4, (16, 34), 0.2)}'
            f'{sparkles([(352, 22, 4, 0), (448, 22, 4, 1.6)])}')
    art.color(f'<circle cx="400" cy="22" r="1.6" fill="{RED}" />', f'<circle cx="400" cy="22" r="1.6" fill="{NIGHT_RED}" />')
    art.write(OUT, "divider")


# ---------------------------------------------------------------- 播放卡两侧：频谱、声波、音符
def wings():
    W, H, CY = 260, 420, 210
    for side in ("left", "right"):
        rng = random.Random(17 if side == "left" else 23)
        left = side == "left"
        art = Art(W, H, role="presentation")

        def X(v):
            """v 是离播放卡的距离（0 = 紧挨着卡片）。"""
            return W - v if left else v
        # 对称频谱：竖条以中线为轴伸缩
        bars = []
        for k in range(24):
            v = 6 + k * 10.4
            env = math.exp(-k / 13) * (0.55 + 0.45 * math.sin(k * 0.9) ** 2)
            hgt = 30 + 150 * env
            dur = rng.uniform(0.8, 1.6)
            bars.append(f'<rect class="eq" x="{X(v) - 1.7:.1f}" y="{CY - hgt / 2:.1f}" width="3.4" height="{hgt:.1f}" rx="1.7" fill="{INK}" opacity="{0.85 - k * 0.02:.2f}" '
                        f'style="animation-duration:{dur:.2f}s;animation-delay:{-rng.uniform(0, dur):.2f}s" />')

        # 声波丝带：从卡片向外衰减的波，形状在几组相位之间变形
        def ribbon(phase, amp, freq, off, thick):
            top, bot = [], []
            for j in range(27):
                v = j * 10
                env = math.exp(-v / 170)
                yy = CY + off + math.sin(v * freq + phase) * amp * env
                t = thick * (0.4 + env)
                top.append((X(v), yy - t))
                bot.append((X(v), yy + t))
            return smooth(top) + "L" + smooth(bot[::-1])[1:] + "Z"

        def line(phase, amp, freq, off):
            return smooth([(X(v), CY + off + math.sin(v * freq + phase) * amp * math.exp(-v / 190)) for v in range(0, 270, 10)])
        waves = (f'<path d="{ribbon(0, 70, 0.045, 0, 5)}" fill="url(#toneFine)" stroke="{INK}" stroke-width="1">{morph([ribbon(p, 70, 0.045, 0, 5) for p in (0, 2.1, 4.2)], 4.8)}</path>'
                 f'<path d="{line(1, 52, 0.06, -10)}" fill="none" stroke="{INK}" stroke-width="1.4">{morph([line(p, 52, 0.06, -10) for p in (1, 3.1, 5.2)], 3.2)}</path>'
                 f'<path d="{line(2, 38, 0.08, 12)}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.7">{morph([line(p, 38, 0.08, 12) for p in (2, 4.1, 0.2)], 2.4)}</path>')
        rings = "".join(f'<circle class="soundring2" cx="{X(-24)}" cy="{CY}" r="40" fill="none" stroke="{INK}" stroke-width="{1.1 - 0.2 * i:.2f}" vector-effect="non-scaling-stroke" '
                        f'style="animation-delay:{-3.2 * i / 4:.2f}s" />' for i in range(4))
        notes = "".join(
            f'<g transform="translate({X(14)} {CY + rng.uniform(-60, 60):.0f})"><g class="note" style="--dx:{(-1 if left else 1) * rng.uniform(150, 230):.0f}px;--dy:{-rng.uniform(60, 170):.0f}px;'
            f'animation-duration:{(d := rng.uniform(4.8, 6.4)):.2f}s;animation-delay:{-d * k / 6:.2f}s">{music_note(k % 2, rng.uniform(0.75, 1.05))}</g></g>' for k in range(6))
        art.css.append(f"""
  .eq {{ transform-box: fill-box; transform-origin: center; animation: eq 1.2s {EASE} infinite alternate; }}
  @keyframes eq {{ from {{ transform: scaleY(0.22); }} to {{ transform: scaleY(1); }} }}
  .soundring2 {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: soundRing2 3.2s {EASE_OUT} infinite; }}
  @keyframes soundRing2 {{ 0% {{ opacity: 0; transform: scale(0.4); }} 10% {{ opacity: 0.8; }} 100% {{ opacity: 0; transform: scale(6.6); }} }}
""")
        art.defs.append(f'<linearGradient id="fade" x1="{0 if left else 1}" x2="{1 if left else 0}"><stop offset="0" stop-color="#fff" stop-opacity="0" /><stop offset="0.4" stop-color="#fff" stop-opacity="0.85" /><stop offset="1" stop-color="#fff" /></linearGradient>'
                        f'<mask id="side"><rect width="{W}" height="{H}" fill="url(#fade)" /></mask>')
        art.ink(f'<g mask="url(#side)">{rings}{"".join(bars)}{waves}</g>{notes}'
                f'{foam(rng, 26, 10, W - 10, 260, H, 2.4, 9, (150, 360))}'
                f'{petals(rng, 7, 10, W - 10, -10, 440)}'
                f'{jellyfish(f"w{side}", X(200), 84, 0.46, 0.9 if left else 2.0, 0.6, 9)}'
                f'{sparkles([(X(120), 40, 6, 0.4), (X(60), 380, 5, 1.8), (X(230), 300, 5, 2.6)])}')
        art.write(OUT, f"wing-{side}")


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


# ---------------------------------------------------------------- 第1話：自己紹介（me 站点的漫画页）
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
    rng = random.Random(31)
    art = Art(W, H, "第1話 自己紹介 — はじめまして、ユキです。")
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
    fl_defs, fl_body = festival("pl", fw_spots, random.Random(5), "light", (4.8, 6.4))
    fd_defs, fd_body = festival("pd", fw_spots, random.Random(5), "dark", (4.8, 6.4))
    wind = "".join(f'<g transform="translate({rng.uniform(80, 900):.0f} {rng.uniform(40, 460):.0f})"><path class="wind" d="M0 0h{rng.uniform(40, 120):.0f}" stroke="{INK}" stroke-width="{rng.uniform(0.6, 1.2):.1f}" stroke-linecap="round" '
                   f'style="animation-duration:{(d := rng.uniform(1.6, 2.4)):.2f}s;animation-delay:{-rng.uniform(0, d):.2f}s" /></g>' for _ in range(18))
    bubble_d = "M432 60C470 30 560 34 590 92C620 150 606 250 548 282C500 308 446 290 430 246L392 262L418 226C390 170 396 92 432 60Z"
    hello = vtext(HELLO, 530, 102, 22, "hello", 1.5)
    narr = vtext(NARRATION, 754, 52, 17, "narr", 1.75)
    art.defs.append(f'<clipPath id="pA"><polygon points="{A}" /></clipPath><clipPath id="pB"><polygon points="{B}" /></clipPath>'
                    f'<clipPath id="pC"><polygon points="{C}" /></clipPath><clipPath id="pD"><polygon points="{D}" /></clipPath>'
                    f'<image id="chara" width="331" height="480" href="data:image/webp;base64,{chara}" />'
                    f'<filter id="charaShadow" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 0.08  0 0 0 0 0.09  0 0 0 0 0.11  0 0 0 0.18 0" /></filter>'
                    f'<linearGradient id="portraitGlint" x1="0" y1="0" x2="1" y2="1"><stop offset="0.38" stop-color="#fff" stop-opacity="0" /><stop offset="0.5" stop-color="#fff" stop-opacity="0.22" /><stop offset="0.62" stop-color="#fff" stop-opacity="0" /></linearGradient>')
    art.css.append(text_css([F["jp"], F["regular"], F["sc"]], f"""
  .hello {{ font: 800 22px {MINCHO_STACK}; fill: {INK}; }}
  .narr {{ font: 800 17px {MINCHO_STACK}; fill: {INK}; }}
  .sfxA {{ font: 800 96px {MINCHO_STACK}; }}
  .sfxC {{ font: 800 62px {MINCHO_STACK}; }}
  .sfxA, .sfxC {{ fill: #ffffff; stroke: {INK}; stroke-width: 3px; paint-order: stroke; stroke-linejoin: round; }}
  .sfxsh {{ fill: {INK}; stroke: {INK}; }}
  .mono {{ font: 500 16px 'Noto Serif SC', 'Songti SC', serif; fill: {INK}; }}
  .label {{ font: 400 11px {SERIF_STACK}; fill: {RED}; letter-spacing: 4px; }}
  .note {{ font: 800 20px {MINCHO_STACK}; fill: {RED}; stroke: {PAPER}; stroke-width: 4px; paint-order: stroke; }}
  .wind {{ opacity: 0; animation: wind linear infinite; }}
  @keyframes wind {{ 0% {{ opacity: 0; transform: translateX(120px); }} 15% {{ opacity: 0.5; }} 70% {{ opacity: 0.35; }} 100% {{ opacity: 0; transform: translateX(-260px); }} }}
  .bob {{ animation: bob 4.8s {EASE} infinite; }}
  @keyframes bob {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 50% {{ transform: translateY(-4px) rotate(-0.6deg); }} }}
  .breath {{ transform-origin: 190px 476px; animation: breath 4.8s {EASE} infinite; }}
  @keyframes breath {{ 0%, 100% {{ transform: scale(1, 1); }} 45% {{ transform: scale(1.004, 1.008); }} }}
  .kenburns {{ transform-origin: 980px 360px; animation: kb 19.2s {EASE} infinite alternate; }}
  @keyframes kb {{ from {{ transform: scale(1); }} to {{ transform: scale(1.05) translateY(-6px); }} }}
  .glintB {{ animation: glintB 6.4s {EASE} infinite; }}
  @keyframes glintB {{ 0% {{ transform: translate(-500px, -500px); }} 40%, 100% {{ transform: translate(500px, 500px); }} }}
  .buzz {{ transform-box: fill-box; transform-origin: center; animation: buzz 1.6s {EASE} infinite alternate; }}
  @keyframes buzz {{ from {{ transform: scale(1) rotate(0deg); }} to {{ transform: scale(1.035) rotate(-0.8deg); }} }}
  .sfxsway {{ transform-box: fill-box; transform-origin: center; animation: sfxsway 6.4s {EASE} infinite alternate; }}
  @keyframes sfxsway {{ from {{ transform: translateX(0) scale(1); }} to {{ transform: translateX(-8px) scale(1.03); }} }}
  .read {{ animation: read 12.8s {EASE} infinite; }}
"""))
    art.ink(f'<rect width="{W}" height="{H}" rx="8" fill="{PAPER}" /><rect width="{W}" height="{H}" rx="8" filter="url(#grain)" />'
            f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="{TONE_GRAY_SKY}" />'
            f'<rect x="16" y="16" width="{ax}" height="240" fill="url(#tone)" opacity="0.55" mask="url(#toneUp)" /></g>')
    art.color(f'<g clip-path="url(#pA)">{fl_body}</g>{fl_defs}',
              f'<g clip-path="url(#pA)"><rect x="16" y="16" width="{ax}" height="460" fill="url(#nightSky)" />'
              f'<rect x="16" y="16" width="{ax}" height="260" fill="url(#tone)" opacity="0.25" mask="url(#toneUp)" />{fd_body}</g>{fd_defs}'
              f'<defs><linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1119" /><stop offset="0.55" stop-color="#1d2a3d" /><stop offset="1" stop-color="#35324a" /></linearGradient></defs>')
    art.ink(f'<g clip-path="url(#pA)">{fence("P", 16, ax + 4, 232, 480, [64, 330, 600], 22)}{wind}'
            f'{petals(rng, 10, 260, 760, 0, 470)}</g>')
    art.color(f'<g clip-path="url(#pA)"><use href="#chara" xlink:href="#chara" x="38" y="38" filter="url(#charaShadow)" />'
              f'<g class="breath"><use href="#chara" xlink:href="#chara" x="30" y="30" /></g></g>')
    art.ink(f'<g clip-path="url(#pA)">'
            f'<g class="bob"><path d="{bubble_d}" fill="{PAPER}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round" />{hello}</g>'
            f'<rect x="704" y="36" width="70" height="{len(NARRATION[0]) * 17 * 1.08 + 26:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="2" />{narr}'
            f'{foam(rng, 12, 380, 760, 420, 480, 2.4, 7, (120, 260))}</g>')
    sfx_a = sfx(F["jp"], "ザァ…", 452, 452, 96, "sfxA", 7, -8)
    art.color(f'<g clip-path="url(#pA)"><g class="sfxsway">{sfx_a}</g></g>',
              f'<g clip-path="url(#pA)"><g class="sfxsway">{sfx_a.replace("sfxA", "sfxA sfxN")}</g></g>')

    # B：本人
    art.ink(f'<g clip-path="url(#pB)"><rect x="760" y="16" width="430" height="{H}" fill="url(#tone)" /></g>')
    art.color(f'<g clip-path="url(#pB)"><g class="kenburns"><image x="{bx(H - 16):.0f}" y="16" width="{1184 - bx(H - 16):.0f}" height="{H - 32}" preserveAspectRatio="xMidYMid slice" '
              f'href="data:image/webp;base64,{avatar}" /></g><g class="glintB"><rect x="700" y="0" width="560" height="{H}" fill="url(#portraitGlint)" /></g></g>')
    note_arrow = f'<path d="M1012 566H1052M1012 566l10 -6M1012 566l10 6" fill="none" stroke="{RED}" stroke-width="2.2" stroke-linecap="round" />'
    art.ink(f'<g clip-path="url(#pB)">{foam(rng, 16, 800, 1180, 700, 830, 3, 10, (200, 520))}{petals(rng, 6, 800, 1180, 0, 860)}'
            f'{sparkles([(1150, 60, 9, 0.2), (830, 420, 6, 1.4), (1160, 700, 7, 2.5)])}</g>'
            f'<text class="note" x="1060" y="573">本人</text>')
    art.color(f'<g class="bob">{note_arrow}</g>', f'<g class="bob">{note_arrow.replace(RED, NIGHT_RED)}</g>')

    # C：集中線とミーンミンミン
    from manga import focus_lines
    art.ink(f'<g clip-path="url(#pC)"><rect x="16" y="488" width="324" height="{H - 504}" fill="{PAPER}" />'
            f'<g class="spinslow" style="transform-origin:178px 660px">{focus_lines(178, 660, 700, 700, 90, 70, random.Random(6), 0.95)}</g></g>')
    sfx_c = (sfx(F["jp"], "ミーン", 46, 640, 62, "sfxC", 5, -7) + sfx(F["jp"], "ミンミン", 30, 724, 62, "sfxC", 5, -7))
    art.color(f'<g clip-path="url(#pC)"><g class="buzz">{sfx_c}</g></g>', f'<g clip-path="url(#pC)"><g class="buzz">{sfx_c.replace("sfxC", "sfxC sfxN")}</g></g>')

    # D：MONOLOGUE
    y = 556
    paras = []
    for para in MONOLOGUE:
        for ln in wrap(F["sc"], para, 16, 360):
            paras.append(f'<text class="mono" x="384" y="{y}">{ln}</text>')
            y += 29
        y += 10
    lines_y = [float(t.split('y="')[1].split('"')[0]) for t in paras]
    frames = []
    n = len(lines_y)
    for k, ly in enumerate(lines_y):
        frames.append(f"{100 * k / n:.2f}% {{ transform: translateY({ly - lines_y[0]:.0f}px); }} {100 * (k + 0.75) / n:.2f}% {{ transform: translateY({ly - lines_y[0]:.0f}px); }}")
    art.css.append(f"@keyframes read {{ {' '.join(frames)} 100% {{ transform: translateY(0px); }} }}")
    art.ink(f'<g clip-path="url(#pD)"><rect x="352" y="488" width="420" height="{H - 504}" fill="{PAPER}" />'
            f'<path d="M370 {lines_y[0] - 16}V{lines_y[-1] + 6}" stroke="{INK}" stroke-width="0.6" opacity="0.4" />{"".join(paras)}'
            f'{foam(rng, 8, 640, 750, 790, 830, 2.2, 5.5, (60, 140))}</g>'
            f'<text class="label" x="384" y="522">MONOLOGUE</text>')
    marker = f'<g class="read"><rect x="368" y="{lines_y[0] - 15:.0f}" width="4" height="19" rx="2" fill="{RED}" /></g>'
    art.color(marker, marker.replace(RED, NIGHT_RED))

    # 分格的框线
    art.ink("".join(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round" />' for pts in (A, B, C, D)))
    art.css.append(f"""
  .sfxN {{ fill: {NIGHT_INK_SFX}; stroke: #070b10; }}
  .sfxN.sfxsh {{ fill: #070b10; }}
  .spinslow {{ animation: spin 96s linear infinite; }}
""")
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
                     ("wings", wings), ("quote", lambda: quote(F))]:
        if not only or name in only:
            fn()
    if not only or "titles" in only:
        for i, (name, en, jp) in enumerate(EPISODES, 1):
            title(i, name, en, jp, F)

#!/usr/bin/env python3
"""把 Action 生成的卡片重画成和モダン的卡片，各出浅色、深色两版，由 PersonalStatus.yml 调用。

原始卡片（stats.svg 等）保持不动，每次只从里面读出数据，再用主页自己的字体、线条重新画一遍：
- 统计 + 语言：合成一张卡（左右两栏），一张图就不会有两张图高低对不齐的问题
- 置顶仓库、活动折线图、奖杯：整张重画
- 贪吃蛇：只取 snk 算好的路线，画成在墨点上走的一笔“一筆書き”

版面的约定（所有内页卡片同一套）：
- 整宽的卡片画布都是 900 宽，README 里 width=100%，于是各卡的字号缩放一致；并排的两张置顶卡各 440 宽；
- 卡片：纸底、一圈很淡的发丝线、四角一对小小的角标；标题是英文 + 竖线 + 明朝体日文副题，右上角一枚朱印；
- 一张卡只有一处朱色（印章之外），其余都是墨与灰。

动效的约定（详见 manga.py 里“逐格动画”一节）：
- 卡片上的小动作（水波、光标、游标）用 <set> 翻页，两次换格之间浏览器不计时也不重画；
- 贪吃蛇用 CSS steps() 按固定格数走，所有窗口共用一个动画；
- 不用滤镜、蒙版、混合模式，带透明度的地方用 fill-opacity / stroke-opacity，避免离屏图层。
"""
import datetime
import math
import pathlib
import random
import re
import sys
import xml.etree.ElementTree as ET
from html import escape

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_INK, NIGHT_RED, PAPER, RED, SERIF, SERIF_STACK,  # noqa: E402
                   Art, cel, clock, load_font, poster, smooth, star, to_night)

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "profile"
NS = "{http://www.w3.org/2000/svg}"
OCTICON = {
    "star": "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z",
    "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z",
    "fork": "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z",
}
# 语言条和色点：用墨的浓淡和网点代替颜色
FILLS = [INK, "url(#tone)", "url(#hatch)", "url(#toneFine)", "url(#toneBig)", GRAY, "url(#tone)", "url(#hatch)"]
W_FULL = 900   # 整宽卡片的画布宽度
PAD = 30       # 卡片内左右留白
HEAD_Y, RULE_Y = 44, 60  # 标题基线、标题下细线的高度
SEAL = 24      # 朱印边长
SH = 0         # 旧版的网点投影已经去掉；留着这个名字给 make_art 用


# ---------------------------------------------------------------- 读上游卡片
def read(name):
    path = PROFILE / f"{name}.svg"
    return path.read_text(encoding="utf-8") if path.exists() else None


def parse(svg):
    root = ET.fromstring(svg)
    parents = {c: p for p in root.iter() for c in p}
    return root, parents


def tid(root, name):
    return [el for el in root.iter() if el.get("data-testid") == name]


def txt(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def icon_path(el, parents):
    """testid 文本所在那一行里的 octicon 路径（往上找几层，取第一个 <svg><path>）。"""
    node = el
    for _ in range(4):
        node = parents.get(node)
        if node is None:
            break
        p = node.find(f".//{NS}svg/{NS}path")
        if p is not None:
            return p.get("d")
    return None


def size(svg):
    w = float(re.search(r'<svg[^>]*?\bwidth="([\d.]+)', svg).group(1))
    h = float(re.search(r'<svg[^>]*?\bheight="([\d.]+)', svg).group(1))
    return w, h


# ---------------------------------------------------------------- 共用的版面部件
def sheet(w, h, label):
    return Art(w, h, label, lean=True)


def card(w, h, rx=12):
    """内页卡片：纸底、一圈很淡的发丝线，四角各一只小小的角标——像装裱时留的边。"""
    m, k = 9, 9
    corners = (f"M{m} {m + k}V{m}H{m + k}M{w - m - k} {m}H{w - m}V{m + k}"
               f"M{w - m} {h - m - k}V{h - m}H{w - m - k}M{m + k} {h - m}H{m}V{h - m - k}")
    return (f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="{PAPER}" stroke="{INK}" stroke-width="1" stroke-opacity="0.32" />'
            f'<path d="{corners}" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity="0.6" />')


def rule(x0, x1, y):
    """标题下的线：一条很淡的发丝线，左端一小段墨。"""
    return (f'<rect x="{x0}" y="{y - 0.35:.2f}" width="{x1 - x0:.0f}" height="0.7" fill="{INK}" fill-opacity="0.22" />'
            f'<rect x="{x0}" y="{y - 0.8:.1f}" width="18" height="1.6" fill="{INK}" />')


def heading(x, y, en, jp, bold, size=17):
    """英文标题 + 一道短竖线 + 明朝体的日文副题。"""
    w = bold.width(en, size) if bold else 0.56 * size * len(en)
    sx = x + w + 13
    return (f'<text class="h" x="{x}" y="{y}" style="font-size:{size}px">{escape(en)}</text>'
            f'<rect x="{sx:.1f}" y="{y - 11.5}" width="0.8" height="12" fill="{INK}" fill-opacity="0.35" />'
            f'<text class="hj" x="{sx + 12:.1f}" y="{y - 1}">{escape(jp)}</text>')


def seal(right, y, ch, s=SEAL):
    """朱印：圆角方块、白文、内侧一圈细白线。right 是右边缘。返回 (浅色, 深色)。"""
    x = right - s
    svg = (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="3.5" fill="{RED}" />'
           f'<rect x="{x + 2.4}" y="{y + 2.4}" width="{s - 4.8}" height="{s - 4.8}" rx="1.8" fill="none" stroke="#ffffff" stroke-width="0.6" stroke-opacity="0.6" />'
           f'<text x="{x + s / 2}" y="{y + s / 2 + s * 0.2:.1f}" text-anchor="middle" style="font: 800 {s * 0.56:.1f}px {MINCHO_STACK}; fill: #ffffff">{escape(ch)}</text>')
    return svg, svg.replace(RED, NIGHT_RED)


def both(svg):
    """红色的东西：浅色版原样，深色版换成夜间红。"""
    return svg, svg.replace(RED, NIGHT_RED)


def leaders(x0, x1, y, pitch=5):
    """目次式的点线引导。"""
    if x1 - x0 < pitch:
        return ""
    d = "".join(f"M{x0 + k * pitch:.1f} {y}h0.01" for k in range(int((x1 - x0) // pitch) + 1))
    return f'<path d="{d}" stroke="{INK}" stroke-width="1.1" stroke-linecap="round" stroke-opacity="0.3" />'


def icon(d, x, y, s=1.0, opacity=1.0):
    return f'<g transform="translate({x} {y}) scale({s})" fill="{INK}" fill-opacity="{opacity}"><path fill-rule="evenodd" d="{d}" /></g>'


def arc(cx, cy, r, p):
    """从正上方顺时针走 p 圈的弧。"""
    p = max(0.001, min(0.999, p))
    a = -math.pi / 2 + 2 * math.pi * p
    return f"M{cx} {cy - r}A{r} {r} 0 {1 if p > 0.5 else 0} 1 {cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}"


def star5(x, y, r, rot=-90):
    pts = []
    for i in range(10):
        a = math.radians(rot + 36 * i)
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{x + rr * math.cos(a):.1f} {y + rr * math.sin(a):.1f}")
    return "M" + "L".join(pts) + "Z"


def base_css(fonts, extra=""):
    return "".join(f.css() for f in fonts if f) + f"""
  .h {{ font: 700 17px {SERIF_STACK}; fill: {INK}; }}
  .hj {{ font: 800 11px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 4px; }}
  .l {{ font: 400 13px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.85; }}
  .v {{ font: 700 14px {SERIF_STACK}; fill: {INK}; }}
  .d {{ font: 400 12.5px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.8; }}
  .s {{ font: 400 10px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 2.5px; }}
  .ax {{ font: 400 10px {SERIF_STACK}; fill: {GRAY}; }}
  .m {{ font: 800 10px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 1.5px; }}
""" + extra


def wrap(font, text, size, width, max_lines=2):
    """按真实字宽折行（按词），超出的行数用省略号收尾。"""
    if not font:
        return [text]
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if font.width(trial, size) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and font.width(last + " …", size) > width:
            last = last[:-1].rstrip()
        lines = lines[:max_lines - 1] + [last + " …"]
    return lines


# ---------------------------------------------------------------- 统计 + 语言（一张卡，左右两栏）
def stats_data():
    svg = read("stats")
    if not svg:
        return None
    root, parents = parse(svg)
    heads = tid(root, "header")
    head = txt(heads[0]) if heads else "GitHub Stats"
    rows = []
    for name in ("stars", "commits", "prs", "issues", "contribs", "reviews", "discussions_started", "discussions_answered"):
        for el in tid(root, name):
            sib = [t for t in parents[el].findall(f"{NS}text") if t is not el]
            label = (txt(sib[0]) if sib else name).rstrip(":")
            rows.append((label, txt(el), icon_path(el, parents)))
    if not rows:
        return None
    rank_el = tid(root, "level-rank-icon")
    rank = txt(rank_el[0]) if rank_el else ""
    m = re.search(r"@keyframes rankAnimation.*?to\s*\{\s*stroke-dashoffset:\s*([\d.]+)", svg, re.S)
    prog = max(0.0, min(1.0, 1 - float(m.group(1)) / (2 * math.pi * 40))) if m else 0.0
    return head, rows, rank, prog


def langs_data():
    svg = read("top-langs")
    if not svg:
        return None
    root, _ = parse(svg)
    heads = tid(root, "header")
    head = txt(heads[0]) if heads else "Most Used Languages"
    widths = [float(r.get("width") or 0) for r in tid(root, "lang-progress")]
    items = []
    for k, el in enumerate(tid(root, "lang-name")):
        name = txt(el)
        parts = name.rsplit(" ", 1)
        name, pct = (parts[0], parts[1]) if len(parts) == 2 and parts[1].endswith("%") else (name, "")
        items.append((name, pct, widths[k] if k < len(widths) else 0))
    return (head, items) if items else None


def count_up(x, y, value, cls, anchor="end", dur=1.1, n=11, delay=0.2):
    """数字从 0 数到 value：只在图片刚载入时跑一遍（十一格），之后就是一张静态图；不跑动画的环境直接显示最终值。"""
    attrs = f'class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"'
    if not re.fullmatch(r"\d[\d,]*", value):
        return f'<text {attrs}>{escape(value)}</text>'
    v = int(value.replace(",", ""))
    step = dur / n
    out = []
    for i in range(n):
        u = 1 - (1 - i / n) ** 3
        at, d = (0.0, delay + step) if i == 0 else (delay + i * step, step)
        out.append(f'<text {attrs} visibility="hidden">{round(v * u):,}<set attributeName="visibility" to="visible" begin="{at:.2f}s" dur="{d:.2f}s" /></text>')
    out.append(f'<text {attrs}>{escape(value)}<set attributeName="visibility" to="hidden" begin="0s" dur="{delay + dur:.2f}s" /></text>')
    return "".join(out)


INTRO_CSS = """  .draw { stroke-dasharray: 1 1; animation: draw 1.6s 0.2s cubic-bezier(0.2, 0.7, 0.2, 1) backwards; }
  @keyframes draw { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
  .fade { animation: fade 1.2s 0.5s ease-out backwards; }
  @keyframes fade { from { opacity: 0; } }
  @media (prefers-reduced-motion: reduce) { .draw, .fade, .grow { animation: none; } }
"""

# 统计卡和语言卡并排：宽度比 595 : 395 正好等于 README 里的 59.5% : 39.5%，同一个高度，渲染出来上下边都对齐
STATS_W, LANGS_W = 595, 395


def stats_height(st, lg):
    rows = len(st[1]) if st else 0
    lrows = (len(lg[1]) + 1) // 2 if lg else 0
    return max(232, RULE_Y + 12 + 30 * max(0, rows - 1) + 52, RULE_Y + 12 + 38 + 26 * max(0, lrows - 1) + 52)


def stats(data, H):
    """能力値：几项数字（载入时从 0 数上来）+ 等级表盘（弧线画出来）；之后每 2.4 秒有一行的点线染成朱色，等级弧尽头隔几秒荡开一圈水波。"""
    head, rows, rank, prog = data
    W = STATS_W
    bold = load_font(SERIF, 700, head + "".join(v for _, v, _ in rows) + rank + "0123456789,.")
    reg = load_font(SERIF, 400, "".join(lb for lb, _, _ in rows) + "RANK")
    jp = load_font(MINCHO, 800, "能力値力")
    art = sheet(W, H, f"{head}: " + ", ".join(f"{lb} {v}" for lb, v, _ in rows) + (f", rank {rank}" if rank else ""))
    art.css.append(base_css([bold, reg, jp], f"""  .rank {{ font: 700 32px {SERIF_STACK}; fill: {INK}; }}
  .rk {{ font: 400 7.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 2.6px; }}
""" + INTRO_CSS))
    X0, XV = PAD, 352
    mid_y = (RULE_Y + 12 + H - 24) / 2
    body = [card(W, H), heading(X0, HEAD_Y, head, "能力値", bold), rule(X0, W - PAD, RULE_Y)]
    y0 = mid_y - 30 * (len(rows) - 1) / 2 + 4.5
    lead = []
    for k, (lb, value, d) in enumerate(rows):
        y = round(y0 + k * 30)
        lw = reg.width(lb, 13) if reg else 7 * len(lb)
        lead.append((X0 + 25 + lw + 10, XV - 38, y - 1))
        body.append((icon(d, X0, y - 12, 0.85, 0.7) if d else "")
                    + f'<text class="l" x="{X0 + 25}" y="{y}">{escape(lb)}</text>'
                    + leaders(*lead[-1])
                    + count_up(XV, y, value, "v"))
    cx, cy, r = W - PAD - 64, round(mid_y, 1), 40
    ticks = []
    for i in range(60):
        a = 2 * math.pi * i / 60
        r0, r1 = r + 6, r + (10.5 if i % 5 == 0 else 8.5)
        ticks.append(f"M{cx + r0 * math.cos(a):.1f} {cy + r0 * math.sin(a):.1f}L{cx + r1 * math.cos(a):.1f} {cy + r1 * math.sin(a):.1f}")
    body.append(f'<path d="{"".join(ticks)}" stroke="{INK}" stroke-width="0.7" stroke-opacity="0.32" fill="none" />'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity="0.18" />'
                f'<path class="draw" pathLength="1" d="{arc(cx, cy, r, prog)}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" />'
                f'<text class="rank" x="{cx}" y="{cy + 8:.1f}" text-anchor="middle">{escape(rank)}</text>'
                f'<text class="rk" x="{cx + 1.3}" y="{cy + 22:.1f}" text-anchor="middle">RANK</text>')
    art.ink("".join(body))
    # 朱色依次走过每一行的点线
    n = len(rows)
    walk = clock("r", 2.4 * n) + "".join(cel("r", [(2.4 * k + 1.6, 2.4)], leaders(*lead[k]).replace(f'stroke="{INK}"', f'stroke="{RED}"').replace('stroke-opacity="0.3"', 'stroke-opacity="0.9"'))
                                          for k in range(n))
    a = -math.pi / 2 + 2 * math.pi * prog
    dx, dy = cx + r * math.cos(a), cy + r * math.sin(a)
    ripple = clock("k", 4.8) + "".join(
        cel("k", [(2.0 + i * 0.12, 0.12)], f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{rr}" fill="none" stroke="{RED}" stroke-width="{sw}" stroke-opacity="{op}" />')
        for i, (rr, sw, op) in enumerate([(6, 1.4, 0.8), (9, 1.1, 0.55), (12, 0.9, 0.32), (15, 0.7, 0.15)]))
    art.color(*both(walk + ripple + f'<circle class="fade" cx="{dx:.1f}" cy="{dy:.1f}" r="3.6" fill="{RED}" style="animation-delay:1.5s;animation-duration:0.4s" />'))
    art.color(*seal(W - PAD, HEAD_Y - 18, "力"))
    art.write(PROFILE, "stats")
    print("wrote stats light/dark")


def top_langs(data, H):
    """言語：比例条（载入时从左往右长出来）+ 两列图例；一枚朱色小三角每 2.4 秒移到下一种语言。"""
    head, items = data
    W, P = LANGS_W, 28
    n = len(items)
    lrows = (n + 1) // 2
    bold = load_font(SERIF, 700, head + "".join(p for _, p, _ in items) + "0123456789.%")
    reg = load_font(SERIF, 400, "".join(nm for nm, _, _ in items))
    jp = load_font(MINCHO, 800, "言語")
    art = sheet(W, H, f"{head}: " + ", ".join(f"{nm} {p}" for nm, p, _ in items))
    X0, X1, BH = P, W - P, 8
    mid_y = (RULE_Y + 12 + H - 24) / 2
    BY = round(mid_y - (BH + 30 + 26 * max(0, lrows - 1)) / 2 + 2)
    art.css.append(base_css([bold, reg, jp], f"  .pct {{ font: 700 12px {SERIF_STACK}; fill: {INK}; }}\n"
                            f"  .grow {{ transform-origin: {X0}px 0; animation: grow 1.3s 0.2s cubic-bezier(0.2, 0.7, 0.2, 1) backwards; }}\n"
                            "  @keyframes grow { from { transform: scaleX(0.002); } }\n" + INTRO_CSS))
    total = sum(w for _, _, w in items) or 1
    art.defs.append(f'<clipPath id="bar"><rect x="{X0}" y="{BY}" width="{X1 - X0}" height="{BH}" rx="{BH / 2}" /></clipPath>')
    segs, mids, x = [], [], X0
    for k, (_, _, w) in enumerate(items):
        sw = (X1 - X0) * w / total
        segs.append(f'<rect x="{x + (0 if k == 0 else 1):.1f}" y="{BY}" width="{max(0, sw - (1 if k else 0) - (1 if k < n - 1 else 0)):.1f}" height="{BH}" fill="{FILLS[k % len(FILLS)]}" />')
        mids.append(x + sw / 2)
        x += sw
    body = [card(W, H), heading(X0, HEAD_Y, head, "言語", bold), rule(X0, X1, RULE_Y),
            f'<g clip-path="url(#bar)"><g class="grow">{"".join(segs)}</g></g>'
            f'<rect x="{X0}" y="{BY}" width="{X1 - X0}" height="{BH}" rx="{BH / 2}" fill="none" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.8" />']
    col_w = (X1 - X0 - 20) / 2
    spots = []
    for k, (name, pct, _) in enumerate(items):
        col, row = k // lrows, k % lrows
        x, y = X0 + col * (col_w + 20), BY + BH + 30 + row * 26
        spots.append((x, y))
        body.append(f'<g class="fade" style="animation-delay:{0.5 + 0.08 * k:.2f}s"><rect x="{x:.1f}" y="{y - 8.5}" width="8.5" height="8.5" rx="1.5" fill="{FILLS[k % len(FILLS)]}" stroke="{INK}" stroke-width="0.7" />'
                    f'<text class="d" x="{x + 15:.1f}" y="{y}">{escape(name)}</text>'
                    f'<text class="pct" x="{x + col_w:.1f}" y="{y}" text-anchor="end">{escape(pct)}</text></g>')
    art.ink("".join(body))

    def mark(k):
        mx = mids[k]
        return f'<path d="M{mx - 4:.1f} {BY + BH + 9.5}L{mx:.1f} {BY + BH + 3}L{mx + 4:.1f} {BY + BH + 9.5}Z" fill="{RED}" />'
    hop = clock("j", 2.4 * n) + poster(mark(0)) + "".join(cel("j", [(2.4 * k, 2.4)], mark(k)) for k in range(n))
    art.color(*both(hop))
    art.color(*seal(X1, HEAD_Y - 18, "語"))
    art.write(PROFILE, "top-langs")
    print("wrote top-langs light/dark")


# ---------------------------------------------------------------- 置顶仓库卡
def pin(name, index=1, count=1):
    svg = read(name)
    if not svg:
        return
    root, parents = parse(svg)
    heads = tid(root, "header")
    repo = txt(heads[0]) if heads else name
    desc_el = next((t for t in root.iter(f"{NS}text") if "description" in (t.get("class") or "")), None)
    desc = " ".join(t.strip() for t in desc_el.itertext() if t.strip()) if desc_el is not None else ""
    langs, stars, forks = tid(root, "lang-name"), tid(root, "stargazers"), tid(root, "forkcount")
    lang = txt(langs[0]) if langs else ""
    star_n = txt(stars[0]) if stars else "0"
    fork_n = txt(forks[0]) if forks else ""
    star_d = (icon_path(stars[0], parents) if stars else None) or OCTICON["star"]
    fork_d = (icon_path(forks[0], parents) if forks else None) or OCTICON["fork"]

    W, H = 440, 156
    bold = load_font(SERIF, 700, repo + "0123456789")
    reg = load_font(SERIF, 400, desc + lang + star_n + fork_n + "0123456789 …")
    jp = load_font(MINCHO, 800, "推")
    art = sheet(W, H, f"{repo}: {desc}")
    art.css.append(base_css([bold, reg, jp], f"  .no {{ font: 700 40px {SERIF_STACK}; fill: none; stroke: {INK}; stroke-width: 0.8; stroke-opacity: 0.28; }}\n"))
    X0, X1 = 26, W - 26
    lines = wrap(reg, desc, 12.5, X1 - X0 - 8, 2)
    # 右下角一枚空心的序号：No.01、No.02 …
    body = [card(W, H),
            icon(OCTICON["repo"], X0, HEAD_Y - 14, 0.95, 0.75), f'<text class="h" x="{X0 + 24}" y="{HEAD_Y}" style="font-size:16px">{escape(repo)}</text>',
            rule(X0, X1, RULE_Y)]
    body += [f'<text class="d" x="{X0}" y="{86 + k * 19}">{escape(ln)}</text>' for k, ln in enumerate(lines)]
    y, x = H - 22, X0
    if lang:
        body.append(f'<circle cx="{x + 4.5}" cy="{y - 4}" r="4" fill="url(#tone)" stroke="{INK}" stroke-width="0.8" /><text class="d" x="{x + 15}" y="{y}">{escape(lang)}</text>')
        x += 15 + (reg.width(lang, 12.5) if reg else 7 * len(lang)) + 22
    body.append(icon(star_d, x, y - 12, 0.8, 0.7) + f'<text class="d" x="{x + 18}" y="{y}">{escape(star_n)}</text>')
    x += 18 + (reg.width(star_n, 12.5) if reg else 8 * len(star_n)) + 22
    if fork_n:
        body.append(icon(fork_d, x, y - 12, 0.8, 0.7) + f'<text class="d" x="{x + 18}" y="{y}">{escape(fork_n)}</text>')
    art.ink("".join(body))
    art.color(*seal(X1, HEAD_Y - 18, "推"))
    art.write(PROFILE, name)
    print("wrote", name, "light/dark")


# ---------------------------------------------------------------- 活动折线图
def monotone(pts):
    """单调三次插值（Fritsch–Carlson）：曲线经过每个点，但不会在两点之间冲过头（不会跌到 0 以下）。"""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    n = len(pts)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [(d[i - 1] + d[i]) / 2 if d[i - 1] * d[i] > 0 else 0.0 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        if a * a + b * b > 9:
            t = 3 / math.sqrt(a * a + b * b)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    out = f"M{xs[0]:.1f} {ys[0]:.1f}"
    for i in range(n - 1):
        h = (xs[i + 1] - xs[i]) / 3
        out += f"C{xs[i] + h:.1f} {ys[i] + m[i] * h:.1f} {xs[i + 1] - h:.1f} {ys[i + 1] - m[i + 1] * h:.1f} {xs[i + 1]:.1f} {ys[i + 1]:.1f}"
    return out


def activity():
    """活動記録：柔和的面积曲线（墨色渐变）、周末淡淡的竖带、只标最高的一天。
    载入时曲线从左往右画出来；之后一根读数的游标一天一格地走，牌子上写着日期和数目。"""
    svg = read("activity")
    if not svg:
        return
    pts = re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)"[^>]*class="ct-point"[^>]*ct:value="([\d.]+)"', svg)
    labels = re.findall(r'class="ct-label ct-horizontal[^"]*">([^<]*)</text>', svg)
    values = [float(v) for _, _, v in pts]
    n = len(values)
    if n < 2:
        return
    labels = [lb.strip() for lb in labels][:n] + [""] * max(0, n - len(labels))
    # 哪天是哪月：末尾那个日期对得上今天（前后一天内），就往回推
    today = datetime.date.today()
    start = None
    if labels[-1].isdigit():
        for d in (today - datetime.timedelta(days=1), today, today + datetime.timedelta(days=1)):
            if d.day == int(labels[-1]):
                start = d - datetime.timedelta(days=n - 1)
                break
    dates = [start + datetime.timedelta(days=i) for i in range(n)] if start else [None] * n

    W, H = W_FULL, 318
    head = "Activity"
    total, vmax = sum(values), max(values) or 1
    summary = f"TOTAL {total:g}   ·   PEAK {vmax:g}   ·   AVG {total / n:.1f}"
    bold = load_font(SERIF, 700, head + "0123456789")
    reg = load_font(SERIF, 400, summary + "0123456789" + "JANFEBMARAPRMAYJUNJULAUGSEPOCTNOVDEC ")
    jp = load_font(MINCHO, 800, "活動記録録" + "".join(MONTHS_JP))
    art = sheet(W, H, f"Activity graph: {total:g} contributions over the past {n} days, peak {vmax:g}")
    art.css.append(base_css([bold, reg, jp], f"""  .sunv {{ font: 700 12px {SERIF_STACK}; fill: #ffffff; }}
  .fv {{ font: 700 11.5px {SERIF_STACK}; fill: {PAPER}; }}
  .fd {{ font: 400 8.5px {SERIF_STACK}; fill: {PAPER}; letter-spacing: 1.4px; fill-opacity: 0.8; }}
  .m {{ font-size: 9.5px; }}
""" + INTRO_CSS))
    X0, X1 = PAD, W - PAD
    px0, px1, py0, py1 = 62, W - 44, 116, 250
    step = 5 if vmax <= 30 else (10 if vmax <= 80 else 20)
    ymax = max(step, math.ceil(vmax / step) * step)
    xs = [px0 + (px1 - px0) * i / (n - 1) for i in range(n)]
    ys = [py1 - (py1 - py0) * v / ymax for v in values]
    line = monotone(list(zip(xs, ys)))
    dx = (px1 - px0) / (n - 1)
    art.defs.append(f'<linearGradient id="actFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{INK}" stop-opacity="0.12" />'
                    f'<stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    # 青海波：一片片半圆鳞，三道同心弧；铺在曲线下面，像一座座浪做的山
    def scale(cx, cy):
        arcs = "".join(f"M{cx - r} {cy}A{r} {r} 0 0 1 {cx + r} {cy}" for r in (10, 7, 4))
        return (f'<path d="M{cx - 10} {cy}A10 10 0 0 1 {cx + 10} {cy}Z" fill="{PAPER}" />'
                f'<path d="{arcs}" fill="none" stroke="{INK}" stroke-width="0.6" stroke-opacity="0.5" />')
    art.defs.append(f'<pattern id="seigaiha" width="20" height="10" patternUnits="userSpaceOnUse" x="{px0}" y="{py1}">'
                    + "".join(scale(cx, cy) for cx, cy in ((0, 5), (20, 5), (10, 10), (0, 15), (20, 15))) + "</pattern>"
                    f'<clipPath id="under"><path d="{line}L{px1:.1f} {py1}L{px0:.1f} {py1}Z" /></clipPath>')
    body = [card(W, H), heading(X0, HEAD_Y, head, "活動記録", bold),
            f'<text class="s" x="{X1 - SEAL - 16}" y="{HEAD_Y - 1}" text-anchor="end">{summary}</text>', rule(X0, X1, RULE_Y)]
    # 霞：屏风画里那种横着的云带，淡淡地铺在背后
    kasumi = [(px0 + 40, py0 + 6, 230), (px0 + 120, py0 + 24, 190), (px1 - 300, py0 + 14, 250), (px1 - 210, py0 + 32, 170)]
    body.append("".join(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w}" height="12" rx="6" fill="url(#toneFine)" fill-opacity="0.45" stroke="{INK}" stroke-width="0.6" stroke-opacity="0.28" />'
                        for x, y, w in kasumi))
    for t in (0, ymax // 2, ymax):
        y = py1 - (py1 - py0) * t / ymax
        dash = "" if t == 0 else ' stroke-dasharray="1.5 3.5"'
        body.append(f'<path d="M{px0} {y:.1f}H{px1}" stroke="{INK}" stroke-width="0.6" stroke-opacity="{0.45 if t == 0 else 0.16}"{dash} />'
                    f'<text class="ax" x="{px0 - 14}" y="{y + 3.5:.1f}" text-anchor="end">{t}</text>')
    art.ink("".join(body))
    # 日之丸：最高的那座“山”背后升起一轮朱日，日里写着最高的数
    k = values.index(vmax)
    sx, sy = xs[k], ys[k] - 6
    art.color(*both(f'<g class="fade" style="animation-delay:1.2s"><circle cx="{sx:.1f}" cy="{sy:.1f}" r="15" fill="{RED}" /></g>'))
    body = [f'<g class="fade"><rect x="{px0}" y="{py0 - 20}" width="{px1 - px0}" height="{py1 - py0 + 20}" fill="url(#seigaiha)" clip-path="url(#under)" />'
            f'<path d="{line}L{px1:.1f} {py1}L{px0:.1f} {py1}Z" fill="url(#actFill)" /></g>',
            f'<path class="draw" pathLength="1" d="{line}" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" />']
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.9" fill="{INK}" />' for i, (x, y, v) in enumerate(zip(xs, ys, values)) if v and i != k)
    body.append(f'<g class="fade">{dots}</g>')
    # 日期：隔两天标一个（最后一天一定标），月份用汉字写在下面
    body.append("".join(f'<text class="ax" x="{x:.1f}" y="{py1 + 20}" text-anchor="middle">{escape(lb)}</text>'
                        for i, (x, lb) in enumerate(zip(xs, labels)) if (n - 1 - i) % 3 == 0))
    for i, d in enumerate(dates):
        if d and (d.day == 1 or i == 0):
            body.append(f'<text class="m" x="{xs[i] - (0 if i else 4):.1f}" y="{py1 + 40}" text-anchor="{"start" if i == 0 else "middle"}">{MONTHS_JP[d.month - 1]}</text>')
    art.ink("".join(body))
    art.color(f'<g class="fade" style="animation-delay:1.4s"><text class="sunv" x="{sx:.1f}" y="{sy + 4.3:.1f}" text-anchor="middle">{vmax:g}</text></g>')

    # 读数的游标：一天一格从左走到右
    FW, FH, fy = 84, 20, 76

    def cursor(i):
        x, y, v = xs[i], ys[i], values[i]
        fx = min(max(x, px0 + FW / 2 - 10), px1 - FW / 2 + 10)
        date = dates[i].strftime("%b %-d").upper() if dates[i] else f"DAY {i + 1}"
        return (f'<path d="M{x:.1f} {fy + FH + 4}V{py1}" stroke="{INK}" stroke-width="0.7" stroke-dasharray="1.5 2.5" stroke-opacity="0.55" />'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{PAPER}" stroke="{INK}" stroke-width="1.2" /><circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{INK}" />'
                f'<rect x="{fx - FW / 2:.1f}" y="{fy}" width="{FW}" height="{FH}" rx="10" fill="{INK}" />'
                f'<text class="fd" x="{fx - FW / 2 + 11:.1f}" y="{fy + 13.3}">{date}</text>'
                f'<text class="fv" x="{fx + FW / 2 - 11:.1f}" y="{fy + 14.2}" text-anchor="end">{v:g}</text>')
    dwell = 1.2
    scan = clock("c", dwell * n) + poster(cursor(k)) + "".join(cel("c", [(dwell * i, dwell)], cursor(i)) for i in range(n))
    art.ink(scan)
    art.color(*seal(X1, HEAD_Y - 18, "録"))
    art.write(PROFILE, "activity")
    print("wrote activity light/dark")


# ---------------------------------------------------------------- 奖杯：读出上游的名次，自己画一柜奖杯
def trophy_data(svg):
    """每个奖杯的：名称、等级（S / AAA / B …）、称号、点数、离下一级的进度、是不是隐藏奖杯。只取露在画面里的第一行。"""
    _, th = size(svg)
    marks = [m for m in re.finditer(r'<svg\s+x="([\d.]+)"\s+y="([\d.]+)"\s+width="110"', svg)]
    out = []
    for i, m in enumerate(marks):
        if float(m.group(2)) >= th:
            continue
        block = svg[m.start():marks[i + 1].start() if i + 1 < len(marks) else len(svg)]

        def grab(fs):
            t = re.search(rf'font-size="{fs}"[^>]*>([^<]+)</text>', block)
            return t.group(1).strip() if t else ""
        rank = "".join(re.findall(r'font-size="7"[^>]*>\s*([^<\s]+)\s*</text>', block))
        prog = re.search(r"to\s*\{\s*width:\s*([\d.]+)px", block)
        out.append({"title": grab("13"), "rank": rank or "?", "sub": grab("10.5"), "pt": grab("10"),
                    "prog": min(1.0, float(prog.group(1)) / 80) if prog else 0.0, "secret": "url(#SECRET)" in block})
    return out


LEAF = "M0 0C2.6 -2.9 7.2 -3 10.4 0C7.2 3 2.6 2.9 0 0Z"


def laurel(cx, cy, filled):
    """杯子两侧的月桂：沿一段圆弧摆叶子，左右对称。"""
    leaves = []
    for k in range(7):
        a = math.radians(118 + k * 19)
        x, y = 31 * math.cos(a), -6 + 31 * math.sin(a)
        rot = math.degrees(a) + 90 + (26 if k % 2 else -22)
        leaves.append(f'<path d="{LEAF}" transform="translate({x:.1f} {y:.1f}) rotate({rot:.0f})" />')
    stem = "M" + "L".join(f"{31 * math.cos(math.radians(a)):.1f} {-6 + 31 * math.sin(math.radians(a)):.1f}" for a in range(112, 246, 12))
    style = f'fill="{INK}"' if filled else f'fill="{PAPER}" stroke="{INK}" stroke-width="0.8" stroke-linejoin="round"'
    half = f'<path d="{stem}" fill="none" stroke="{INK}" stroke-width="0.8" /><g {style}>{"".join(leaves)}</g>'
    return f'<g transform="translate({cx:.1f} {cy})">{half}<g transform="scale(-1 1)">{half}</g></g>'


def one_cup(x, y, tier, secret, s=1.0):
    """一只奖杯（可缩放）：杯身按等级“浓淡”——C 留白、B 斜线、A 网点、S 实墨，隐藏奖杯是朱色的。返回 (垫在下面的朱色, 墨线)。"""
    bowl = "M-17 -22H17V-17C17 -3 9 5 0 5C-9 5 -17 -3 -17 -17Z"
    fill = {"S": INK, "A": "url(#tone)", "B": "url(#hatch)"}.get(tier, PAPER)
    tr = f'translate({x:.1f} {y:.1f}) scale({s})'
    under = ""  # 奖杯本身不带红：隐藏奖杯也画成实墨
    letter_fill = PAPER if tier == "S" or secret else INK
    halo = "" if tier == "S" or secret else f' stroke="{PAPER}" stroke-width="3.2" paint-order="stroke" stroke-linejoin="round"'
    ink = (f'<g transform="{tr}">'
           f'<path d="M-17 -15C-28 -15 -27 0 -12 1M17 -15C28 -15 27 0 12 1" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" />'
           + f'<path d="{bowl}" fill="{PAPER}" /><path d="{bowl}" fill="{INK if secret else fill}" />'
           + f'<path d="{bowl}" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round" />'
           f'<rect x="-19.5" y="-25.5" width="39" height="5" rx="2" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" />'
           f'<path d="M-3 5V12H3V5" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" /><ellipse cx="0" cy="8.5" rx="5.4" ry="1.9" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" />'
           f'<path d="M-10 12H10L12.5 19H-12.5Z" fill="{INK}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round" />'
           f'<rect x="-16" y="19" width="32" height="5" rx="1" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" />'
           f'<text x="0" y="-3.6" text-anchor="middle" class="rk" fill="{letter_fill}"{halo}>{escape(tier)}</text></g>')
    return under, ink


def cup(cx, cy, rank, secret):
    """一组奖杯，和原版一样按等级的字母数摆杯：S / A 一只（两侧有月桂），SS / AA 一大一小，SSS / AAA 中间大、两边各一只小的。
    小杯先画、在后面；返回 (垫在下面的朱色, 墨线, 盖在上面的朱色)。"""
    tier, n = rank[:1], min(3, len(rank))
    big_x = cx - 7 if n == 2 else cx
    smalls = {1: [], 2: [(cx + 21, cy + 6)], 3: [(cx - 26, cy + 6), (cx + 26, cy + 6)]}[n]
    under, ink = [], []
    if n == 1 and (tier in "SA" or secret):
        ink.append(laurel(cx, cy, tier == "S" or secret))
    for x, y in smalls:
        u, i = one_cup(x, y, tier, secret, 0.66)
        under.append(u)
        ink.append(i)
    u, i = one_cup(big_x, cy, tier, secret, 1.0)
    under.append(u)
    ink.append(i)
    return "".join(under), "".join(ink), ""


PETAL = "M0 0C-3.6 -2.6 -4.6 -7.4 -2.3 -10.2L0 -8.6L2.3 -10.2C4.6 -7.4 3.6 -2.6 0 0Z"  # 一片樱花瓣：尖上一道小缺口
SAKURA = {"light": (RED, "#a8231f", "#ffffff"), "dark": (NIGHT_RED, "#c23a3e", "#ffffff")}  # 花瓣用页面上现有的朱红，花心、花蕊留白


def blossom(x, y, s, rot, mode):
    """一朵樱花：五片带缺口的花瓣、深一点的花心和一圈花蕊。"""
    fill, edge, core = SAKURA[mode]
    petals = "".join(f'<path d="{PETAL}" transform="rotate({rot + 72 * k:.0f})" />' for k in range(5))
    stamens = "".join(f'<circle cx="{3.4 * math.cos(math.radians(rot + 36 + 72 * k)):.1f}" cy="{3.4 * math.sin(math.radians(rot + 36 + 72 * k)):.1f}" r="0.55" />' for k in range(5))
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})"><g fill="{fill}" stroke="{edge}" stroke-width="0.5" stroke-linejoin="round">{petals}</g>'
            f'<circle r="1.7" fill="{core}" fill-opacity="0.9" /><g fill="{core}">{stamens}</g></g>')


def petal(x, y, s, rot, mode, flat=1.0):
    fill, edge, _ = SAKURA[mode]
    return f'<path d="{PETAL}" transform="translate({x:.1f} {y:.1f}) rotate({rot:.0f}) scale({s} {s * flat:.2f})" fill="{fill}" stroke="{edge}" stroke-width="0.5" />'


def sakura_layer(mode, W, X0, X1, SHELF, CY):
    """奖杯柜旁的樱花：右上角伸进来一枝（墨色枝干、几簇花和花苞），左边陈列架尽头一小簇，几片花瓣飘在杯子之间、落在架子上。静态。"""
    rng = random.Random(17)
    ink = INK if mode == "light" else NIGHT_INK
    fill, edge, core = SAKURA[mode]
    # 枝干贴着标题线下面从右边伸进来，不压到杯子；最右边垂下一小枝，落在最后一只杯子右边的空处
    branch = (f'<path d="M{W - 4} 63C{W - 40} 66 {W - 80} 70 {W - 120} 71C{W - 140} 71.5 {W - 160} 69 {W - 182} 66" fill="none" stroke="{ink}" stroke-width="2.6" stroke-linecap="round" />'
              f'<path d="M{W - 120} 71C{W - 132} 76 {W - 146} 78 {W - 158} 78" fill="none" stroke="{ink}" stroke-width="1.2" stroke-linecap="round" />'
              f'<path d="M{W - 34} 65C{W - 30} 80 {W - 32} 96 {W - 40} 112" fill="none" stroke="{ink}" stroke-width="1.4" stroke-linecap="round" />'
              f'<path d="M{W - 70} 68C{W - 74} 62 {W - 80} 59 {W - 88} 58" fill="none" stroke="{ink}" stroke-width="1" stroke-linecap="round" />')
    flowers = [(W - 182, 66, 0.8, 10), (W - 150, 70, 0.95, 40), (W - 112, 70, 0.85, 70), (W - 158, 79, 0.65, 20), (W - 62, 66, 0.9, 55),
               (W - 33, 84, 0.8, 30), (W - 38, 103, 0.75, 5), (W - 42, 118, 0.6, 60), (W - 12, 64, 0.7, 25)]
    buds = [(W - 196, 63), (W - 90, 59), (W - 28, 96), (W - 128, 75)]
    out = [branch]
    out += [f'<ellipse cx="{x}" cy="{y}" rx="2.2" ry="3" transform="rotate(-30 {x} {y})" fill="{fill}" stroke="{edge}" stroke-width="0.5" />'
            f'<path d="M{x + 1} {y + 2.4}l1.4 2.2" stroke="{ink}" stroke-width="0.7" />' for x, y in buds]
    out += [blossom(x, y, sc, rot, mode) for x, y, sc, rot in flowers]
    # 左边陈列架尽头的一小簇
    out += [blossom(X0 + 14, SHELF - 8, 0.9, 15, mode), blossom(X0 + 30, SHELF - 4, 0.7, 50, mode), blossom(X0 + 6, SHELF - 22, 0.6, 35, mode)]
    # 飘着的花瓣、落在架子上的花瓣
    col = (X1 - X0) / 6
    for k in range(6):
        gx = X0 + col * (k + 0.5)
        out.append(petal(gx + col * 0.42, CY - 34 + rng.uniform(-8, 8), 0.75, rng.uniform(0, 360), mode))
        out.append(petal(gx - col * 0.38 + rng.uniform(-6, 6), SHELF - 1.5, 0.7, rng.choice([80, 100, 260, 280]), mode, 0.55))
    return "".join(out)


def trophy():
    svg = read("trophy")
    if not svg:
        return
    items = trophy_data(svg)
    if not items:
        return
    n = len(items)
    W, H = W_FULL, 250
    head, right = "Trophies", f"全 {n} 種"
    names = "".join(t["title"] + t["sub"] + t["pt"] + t["rank"] for t in items)
    bold = load_font(SERIF, 700, head + names + "0123456789pt")
    reg = load_font(SERIF, 400, names + "0123456789")
    jp = load_font(MINCHO, 800, "実績全種賞0123456789")
    art = sheet(W, H, "GitHub trophies: " + ", ".join(f'{t["title"]} {t["rank"]} ({t["sub"]}, {t["pt"]})' for t in items))
    art.css.append(base_css([bold, reg, jp], f"""  .rk {{ font: 700 16px {SERIF_STACK}; }}
  .tt {{ font: 700 14px {SERIF_STACK}; fill: {INK}; }}
  .ts {{ font: 400 11px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.65; }}
  .tp {{ font: 700 10.5px {SERIF_STACK}; fill: {INK}; fill-opacity: 0.85; letter-spacing: 0.6px; }}
"""))
    X0, X1 = PAD, W - PAD
    col = (X1 - X0) / n
    CY, SHELF = 114, 141
    under, ink, over = [], [], []
    ink.append(card(W, H) + heading(X0, HEAD_Y, head, "実績", bold)
               + f'<text class="m" x="{X1 - SEAL - 16}" y="{HEAD_Y - 1}" text-anchor="end" style="letter-spacing:3px">{right}</text>' + rule(X0, X1, RULE_Y))
    # 陈列架：一道细墨线，两端淡出
    art.defs.append(f'<linearGradient id="shelf" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0" />'
                    f'<stop offset="0.08" stop-color="{INK}" /><stop offset="0.92" stop-color="{INK}" /><stop offset="1" stop-color="{INK}" stop-opacity="0" /></linearGradient>')
    ink.append(f'<rect x="{X0}" y="{SHELF}" width="{X1 - X0}" height="1.4" fill="url(#shelf)" />')
    shine = [clock("k", 9.6)]
    for k, t in enumerate(items):
        cx = X0 + col * (k + 0.5)
        u, i, o = cup(cx, CY, t["rank"], t["secret"])
        under.append(u)
        ink.append(i)
        over.append(o)
        bw = 72
        ink.append(f'<text class="tt" x="{cx:.1f}" y="{SHELF + 32}" text-anchor="middle">{escape(t["title"])}</text>'
                   f'<text class="ts" x="{cx:.1f}" y="{SHELF + 49}" text-anchor="middle">{escape(t["sub"])}</text>'
                   f'<rect x="{cx - bw / 2:.1f}" y="{SHELF + 60}" width="{bw}" height="2.4" rx="1.2" fill="{INK}" fill-opacity="0.16" />'
                   f'<rect x="{cx - bw / 2:.1f}" y="{SHELF + 60}" width="{max(2.4, bw * t["prog"]):.1f}" height="2.4" rx="1.2" fill="{INK}" />'
                   f'<text class="tp" x="{cx:.1f}" y="{SHELF + 80}" text-anchor="middle">{escape(t["pt"])}</text>')
        # 杯口右上的“キラッ”：从左到右一只接一只地亮（三格）
        sx, sy, red = cx + 23, CY - 27, False  # 奖杯本身不带红
        for at, dur, rr in [(0, 0.08, 3.5), (0.08, 0.16, 7.5), (0.24, 0.08, 4.5)]:
            shine.append(cel("k", [(0.8 + k * 0.72 + at, dur)],
                             f'<path d="{star(sx, sy, rr)}" fill="{RED if red else INK}" />' + (f'<path d="{star(sx + 8, sy + 9, rr * 0.42)}" fill="{RED if red else INK}" />' if rr > 6 else "")))
    art.ink(ink[0])  # 卡片底先铺
    art.color(sakura_layer("light", W, X0, X1, SHELF, CY), sakura_layer("dark", W, X0, X1, SHELF, CY))  # 樱花在杯子后面
    art.ink("".join(ink[1:]))
    ink_shine = "".join(s for s in shine if RED not in s)
    red_shine = "".join(s for s in shine[1:] if RED in s)
    art.ink(ink_shine)
    art.color(*both("".join(over) + red_shine))
    art.color(*seal(X1, HEAD_Y - 18, "賞"))
    art.write(PROFILE, "trophy")
    print("wrote trophy light/dark")


# ---------------------------------------------------------------- 贪吃蛇：一筆書き
SNAKE_P = 15.0                          # 格距（snk 原图是 16）
SNAKE_TICK, SNAKE_SPEED = 0.04, 44.0    # 一格 0.04 秒（25 格/秒）；每秒游 44 像素，约三格
LEVEL_R = [1.0, 2.0, 2.9, 3.8, 4.7]     # 没有贡献的日子是一粒很淡的小点，其余按多少点大小不同的墨点
MONTHS_JP = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]


def snake_data(svg):
    """从 snk 的 SVG 里取：每格位置/等级、蛇头走过的路线（折点）。"""
    level = {m.group(1): int(m.group(2)) for m in re.finditer(r"\.c\.(c\w+)\{fill:var\(--c(\d)\)", svg)}
    cells = []
    for m in re.finditer(r'<rect class="c(?: (c\w+))?" x="([\d.]+)" y="([\d.]+)"', svg):
        cells.append((float(m.group(2)) + 6, float(m.group(3)) + 6, level.get(m.group(1), 0)))
    body = svg[svg.index("@keyframes s0{"):]
    body = body[:body.index("}}") + 2]
    pts = []
    for keys, x, y in re.findall(r"([\d.,%]+)\{transform:translate\(([-\d.]+)px,([-\d.]+)px\)\}", body):
        for k in keys.split(","):
            pts.append((float(k.rstrip("%")), float(x) + 8, float(y) + 8))
    pts.sort()
    route = [(pts[0][1], pts[0][2])]
    for _, x, y in pts[1:]:
        if (x, y) != route[-1]:
            route.append((x, y))
    return cells, route


def snake_route(route, ox, oy, radius=7.0):
    """把折线路线画成转角带圆弧的路径，返回 (d, 总长, 是否闭合)。
    圆角用三小段折线近似：折线的长度各家浏览器算出来分毫不差，虚线窗口才能在一整圈里始终对齐
    （贝塞尔曲线的弧长各家量法不同，一圈下来会差出十几二十像素）。"""
    closed = len(route) > 2 and route[0] == route[-1]
    v = route[:-1] if closed else route
    n = len(v)

    def corner(i):
        """返回转角处的折线点列：入点、中间两点、出点；直行就只有顶点自己。"""
        p, c, q = v[(i - 1) % n], v[i], v[(i + 1) % n]
        la, lb = math.hypot(c[0] - p[0], c[1] - p[1]), math.hypot(q[0] - c[0], q[1] - c[1])
        a, b = ((c[0] - p[0]) / la, (c[1] - p[1]) / la), ((q[0] - c[0]) / lb, (q[1] - c[1]) / lb)
        if abs(a[0] * b[0] + a[1] * b[1]) > 0.99:
            return [c]
        r = min(radius, la / 2, lb / 2)
        o = (c[0] - a[0] * r + b[0] * r, c[1] - a[1] * r + b[1] * r)  # 圆心
        out = []
        for t in (0, 30, 60, 90):
            ct, st = math.cos(math.radians(t)), math.sin(math.radians(t))
            out.append((round(o[0] - b[0] * r * ct + a[0] * r * st, 1), round(o[1] - b[1] * r * ct + a[1] * r * st, 1)))
        return out
    order = (list(range(1, n)) + [0]) if closed else list(range(1, n - 1))
    pts = [corner(0)[-1]] if closed else [v[0]]
    for i in order:
        pts += corner(i)
    if not closed:
        pts.append(v[-1])
    total = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))
    num = lambda f: f"{f:.1f}".rstrip("0").rstrip(".")  # noqa: E731
    d = f"M{num(ox + pts[0][0])} {num(oy + pts[0][1])}"
    for p, q in zip(pts, pts[1:]):
        dx, dy = round(q[0] - p[0], 1), round(q[1] - p[1], 1)
        d += (f"h{num(dx)}" if dy == 0 else f"v{num(dy)}" if dx == 0 else f"l{num(dx)} {num(dy)}")
    return d + ("z" if closed else ""), total, closed, pts


TAIL_POSES = [-14, -9, -2, 6, 13, 9, 2, -6]  # 尾鳍左右摆的角度，0.08 秒一格，八格一个来回


def goldfish_parts(mode):
    """一条更紗琉金（红白花、长尾），从上往下看，头朝 +x，身体中心在原点。
    身体：径向渐变（背上橙、腹侧朱）、头顶和背鞍两块白斑、细鳞、金色虹膜的凸眼、一道半透明的背鳍；
    胸鳍、腹鳍半透明带鳍条；尾巴是长长的两叶纱尾，外层浅、里层深，边缘起伏，鳍条细密，尾端渐渐透明。
    返回 (defs, 身体, 尾巴(角度), 胸鳍(角度), 影子)。"""
    if mode == "light":
        core, mid, edge, dark, scale, white, iris = "#ff9d52", "#ec4e2e", "#c02a22", "#8f1c18", "#ffd7b0", "#fff8f0", "#e6a93c"
    else:
        core, mid, edge, dark, scale, white, iris = "#ffb06a", "#ff6a46", "#e4483b", "#b3302d", "#ffe3c6", "#fffaf5", "#f2c060"
    defs = (f'<radialGradient id="gfBody{mode}" cx="0.6" cy="0.45" r="0.6"><stop offset="0" stop-color="{core}" /><stop offset="0.6" stop-color="{mid}" /><stop offset="1" stop-color="{edge}" /></radialGradient>'
            f'<linearGradient id="gfFin{mode}" gradientUnits="userSpaceOnUse" x1="-8" y1="0" x2="-40" y2="0"><stop offset="0" stop-color="{mid}" stop-opacity="0.85" />'
            f'<stop offset="0.5" stop-color="{mid}" stop-opacity="0.5" /><stop offset="1" stop-color="{core}" stop-opacity="0.12" /></linearGradient>'
            f'<linearGradient id="gfFinIn{mode}" gradientUnits="userSpaceOnUse" x1="-8" y1="0" x2="-30" y2="0"><stop offset="0" stop-color="{edge}" stop-opacity="0.75" /><stop offset="1" stop-color="{edge}" stop-opacity="0.08" /></linearGradient>')
    body_d = "M15 0C15 -4.5 12.2 -7.5 6.4 -7.8C0.6 -8.1 -4.2 -5.6 -7.6 -2.7C-9 -1.5 -9 1.5 -7.6 2.7C-4.2 5.6 0.6 8.1 6.4 7.8C12.2 7.5 15 4.5 15 0Z"
    # 一叶纱尾（上半；下半镜像）：边缘几道起伏，尾尖拉长
    lobe = ("M-7.6 -1C-11 -3.8 -15.6 -10.6 -23.4 -15.4C-28 -18.2 -34 -19.4 -38.6 -17.2C-36.2 -16.4 -35 -14.6 -35.6 -12.4"
            "C-33.4 -12 -32 -10.2 -32.6 -8C-30.4 -7.6 -29 -5.8 -29.6 -3.8C-27.2 -3.2 -25.4 -1.6 -24.6 0H-7.6Z")
    inner = "M-7.6 -0.8C-10.6 -3 -14.2 -7.4 -19.6 -10.4C-22 -11.6 -25 -11.8 -26.8 -10.6C-24.6 -8.6 -23.2 -5.2 -21.6 0H-7.6Z"
    rays = "".join(f"M-8.2 -0.4Q{(-8.2 + x) / 2 + 1:.1f} {y * 0.55:.1f} {x} {y}" for x, y in
                   ((-23, -14.6), (-27.6, -16.8), (-32.6, -17.6), (-37.2, -16.6), (-35, -12.2), (-32.2, -7.8), (-29.2, -3.6), (-25.6, -0.6)))

    def tail(a):
        half = (f'<path d="{lobe}" fill="url(#gfFin{mode})" stroke="{edge}" stroke-width="0.4" stroke-opacity="0.65" stroke-linejoin="round" />'
                f'<path d="{inner}" fill="url(#gfFinIn{mode})" />'
                f'<path d="{rays}" fill="none" stroke="{white}" stroke-width="0.35" stroke-opacity="0.5" />')
        return (f'<g transform="rotate({a} -7.6 0)"><g transform="rotate({a * 0.45:.1f} -7.6 0)">{half}</g>'
                f'<g transform="scale(1 -1) rotate({-a * 0.3:.1f} -7.6 0)">{half}</g></g>')
    pfin = "M5.4 -6.8C4.4 -11.4 0.8 -14.6 -2.6 -14.2C-2.2 -11.6 -0.2 -8.8 5.4 -6.8Z"
    pray = "M5 -7L-1.8 -13.6M5 -7L-2.4 -11.6M5 -7L-0.2 -14.2M5 -7L-2 -9.6"

    def fins(a):
        one = (f'<path d="{pfin}" fill="{mid}" fill-opacity="0.45" stroke="{edge}" stroke-width="0.35" stroke-opacity="0.6" />'
               f'<path d="{pray}" stroke="{white}" stroke-width="0.3" stroke-opacity="0.55" />')
        pelvic = "M-1.6 -5.8C-3.4 -9 -6.2 -9.8 -7.6 -8.6C-6 -7.4 -4.2 -6.2 -1.6 -5.8Z"
        return (f'<g transform="rotate({a} 5.4 -6.8)">{one}</g><g transform="scale(1 -1)"><g transform="rotate({-a} 5.4 -6.8)">{one}</g></g>'
                f'<path d="{pelvic}" fill="{mid}" fill-opacity="0.45" /><path d="{pelvic}" transform="scale(1 -1)" fill="{mid}" fill-opacity="0.45" />')
    scales = "".join(f"M{x - 1.1:.1f} {y:.1f}a1.2 1.2 0 0 0 2.2 0" for y in (-3.8, -1.6, 0.6, 2.8) for x in (-5.6, -3.4, -1.2, 1.0, 3.2) if abs(y + 0.5) < 4.6 - abs(x) * 0.12)
    body = (f'<path d="M7.4 0C3.6 -1.6 -2 -1.7 -7.2 -0.4C-2 0.6 3.6 0.9 7.4 0Z" fill="{edge}" fill-opacity="0.45" />'  # 背鳍（从上看是一道窄窄的半透明脊）
            f'<path d="{body_d}" fill="url(#gfBody{mode})" stroke="{edge}" stroke-width="0.55" />'
            f'<path d="M15 0C15 -3.4 13.2 -5.6 10 -6.2C8.2 -3.8 7.9 -1 8.8 0.6C9.8 2.6 12 3.8 14.2 2.8C14.7 1.9 15 0.9 15 0Z" fill="{white}" fill-opacity="0.94" />'
            f'<path d="M-1.2 -7.5C-4 -6.4 -6.4 -4.2 -7.8 -2.2C-5.4 -2.8 -2.6 -2.8 -0.4 -4.6C0.4 -5.6 -0.2 -6.9 -1.2 -7.5Z" fill="{white}" fill-opacity="0.9" />'
            f'<path d="M2.6 6.6C1.4 5.2 1.6 3.6 3 3.2C4.8 3.6 5.6 5.4 5 7.2C4.2 7.4 3.4 7.2 2.6 6.6Z" fill="{white}" fill-opacity="0.7" />'
            f'<path d="{scales}" fill="none" stroke="{scale}" stroke-width="0.35" stroke-opacity="0.6" />'
            f'<path d="M7.2 0C3.4 -0.8 -2 0.8 -8 0" fill="none" stroke="{dark}" stroke-width="0.9" stroke-opacity="0.5" stroke-linecap="round" />'
            f'<path d="M7 -6Q5.8 0 7 6" fill="none" stroke="{dark}" stroke-width="0.45" stroke-opacity="0.45" />'
            f'<ellipse cx="2.6" cy="-3.2" rx="5.6" ry="1.1" fill="#ffffff" fill-opacity="0.32" transform="rotate(-6 2.6 -3.2)" />'
            + "".join(f'<circle cx="10" cy="{sy * 6.1}" r="2.5" fill="{iris}" stroke="{edge}" stroke-width="0.4" />'
                      f'<circle cx="10.3" cy="{sy * 6.2}" r="1.6" fill="#141418" />'
                      f'<circle cx="10.8" cy="{sy * 6.7}" r="0.6" fill="#ffffff" />' for sy in (-1, 1))
            + f'<path d="M14.6 -1.1Q15.6 0 14.6 1.1" fill="none" stroke="{dark}" stroke-width="0.5" stroke-opacity="0.6" stroke-linecap="round" />')
    shadow = f'<path d="{body_d}" /><path d="{lobe}" /><path d="{lobe}" transform="scale(1 -1)" />'
    return defs, body, tail, fins, shadow


def raindrops(cells, period=8.0, tick=0.04, seed=11):
    """雨点打在水面：每粒有贡献的墨点每个周期被一滴雨打中一次（时刻随机、对齐到金鱼的 0.04 秒一格），
    外面依次荡开两圈细环，越来越大、越来越淡。每滴雨就是两只 <circle>，用 <set> 改半径和透明度。"""
    rng = random.Random(seed)
    out = [clock("rn", period)]
    stages = [(0.0, 1.8, 0.85), (0.12, 4.6, 0.55), (0.24, 7.6, 0.32), (0.36, 10.6, 0.14)]
    for x, y, lv in cells:
        if not lv:
            continue
        t = round(rng.uniform(0, period - 0.6) / tick) * tick
        r0 = LEVEL_R[min(lv, 4)]
        for lag in (0.0, 0.12):  # 第二圈晚一格出来
            rs = ";".join(f"{r0 + dr:.1f}" for _, dr, _ in stages)
            ops = ";".join(f"{op * (0.7 if lag else 1):.2f}" for _, _, op in stages)
            b = f"rn.begin+{t + lag:.2f}s"
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0" fill="none" stroke="{INK}" stroke-width="0.75">'
                       f'<animate attributeName="r" values="{rs}" calcMode="discrete" begin="{b}" dur="0.48s" />'
                       f'<animate attributeName="stroke-opacity" values="{ops}" calcMode="discrete" begin="{b}" dur="0.48s" /></circle>')
    return "".join(out)


def snake():
    """金魚すくい：一年的贡献是一池大小不一的墨点，一条小金鱼沿着 snk 算好的路线游过去，把墨点一粒粒“吃掉”，
    吃的地方荡开一圈水纹；吃掉的墨点只剩一粒淡点，七秒后再长回来。
    - 金鱼用 CSS offset-path 沿路线游（steps，25 格/秒），尾鳍每 0.1 秒换一个摆角（<set> 翻页）；
    - 吃掉：纸色的宽“虚线窗口”跟在鱼后面盖住墨点（和鱼同一个时长、同样的格数，所以对得齐）；
    - 水纹：每粒墨点在鱼游到它的那一刻（按路线长度算好）荡开三圈，<set> 改半径。"""
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    cells, route = snake_data(raw.read_text(encoding="utf-8"))
    W, H = W_FULL, 268
    k = SNAKE_P / 16
    cols = int(max(c[0] for c in cells) // 16) + 1
    gx, gy = (W - (cols - 1) * SNAKE_P) / 2, 120

    def at(x, y):
        return gx + (x - 8) * k, gy + (y - 8) * k
    cells = [(*at(x, y), lv) for x, y, lv in cells]
    route = [at(x, y) for x, y in route]
    d, total, closed, pts = snake_route(route, 0, 0, radius=6.0)
    steps = round(total / SNAKE_SPEED / SNAKE_TICK)
    C = steps * SNAKE_TICK
    head_txt, foot_txt = "Contribution Pond", "ONE YEAR  ·  ONE LITTLE GOLDFISH"
    bold = load_font(SERIF, 700, head_txt)
    reg = load_font(SERIF, 400, foot_txt)
    jp = load_font(MINCHO, 800, "金魚すくい魚少多月水金" + "".join(MONTHS_JP))
    active = sum(1 for c in cells if c[2])
    art = sheet(W, H, f"Contribution pond: a little goldfish swims through a year of contributions ({active} active days)")

    # 月份（汉字）、星期（月 水 金）
    today = datetime.date.today()
    months, last, last_x = [], None, -99.0
    for c in range(cols):
        day = today - datetime.timedelta(weeks=cols - 1 - c)
        x = gx + c * SNAKE_P - 3
        if day.month != last and c < cols - 2:
            if x - last_x < 44 and months:
                months.pop()
            months.append(f'<text class="m" x="{x:.1f}" y="{gy - 24}">{MONTHS_JP[day.month - 1]}</text>')
            last_x = x
        last = day.month
    days = "".join(f'<text class="m" x="{gx - 14:.1f}" y="{gy + r * SNAKE_P + 3.5:.1f}" text-anchor="end">{nm}</text>' for r, nm in ((1, "月"), (3, "水"), (5, "金")))

    def dot(x, y, r):
        return f"M{x - r:.1f} {y:.1f}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0z"
    faint = "".join(dot(x, y, LEVEL_R[0]) for x, y, _ in cells)
    ink_dots = "".join(dot(x, y, LEVEL_R[min(lv, 4)]) for x, y, lv in cells if lv)
    fy = H - 26
    lx = W - PAD - 22
    legend_x = [lx - 14 - 15 * (4 - i) for i in range(5)]
    legend_f = dot(legend_x[0], fy - 3.5, LEVEL_R[0])
    legend_d = "".join(dot(legend_x[i], fy - 3.5, LEVEL_R[i]) for i in range(1, 5))

    # 盖住吃掉的墨点：从鱼头往后一段纸色的宽窗口，尾端五层淡出
    T = total

    def window(L, ahead=0.0):
        return f"{ahead:.1f} {T - L:.1f} {L - ahead:.1f} 0"
    art.defs.append(f'<path id="route" d="{d}" />')
    regrow = 7.0 * SNAKE_SPEED
    cover = "".join(f'<use href="#route" stroke-width="12.5" stroke-dasharray="{window(regrow + SNAKE_P * j, 14)}" stroke-opacity="{op}" />'
                    for j, op in ((4, 0.2), (3, 0.4), (2, 0.6), (1, 0.8), (0, 1)))

    # 水纹：每粒墨点第一次被鱼经过的时刻
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    ripples = []
    for cx, cy, lv in cells:
        if not lv:
            continue
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            sx, sy = q[0] - p[0], q[1] - p[1]
            L2 = sx * sx + sy * sy or 1
            t = max(0.0, min(1.0, ((cx - p[0]) * sx + (cy - p[1]) * sy) / L2))
            if math.hypot(p[0] + sx * t - cx, p[1] + sy * t - cy) < 3.5:
                s_hit = cum[i] + t * math.sqrt(L2)
                break
        else:
            continue
        t_eat = (s_hit - 14) / SNAKE_SPEED % C
        b = f"rp.begin+{t_eat:.2f}s"
        ripples.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="0" fill="none" stroke="{INK}" stroke-width="0.9">'
                       f'<animate attributeName="r" values="5;9;13" calcMode="discrete" begin="{b}" dur="0.42s" />'
                       f'<animate attributeName="stroke-opacity" values="0.6;0.35;0.15" calcMode="discrete" begin="{b}" dur="0.42s" /></circle>')

    art.css.append(base_css([bold, reg, jp], f"""  .m {{ font-size: 9.5px; }}
  .go {{ fill: none; stroke-linejoin: round; animation: go {C:.2f}s steps({steps}) infinite; }}
  @keyframes go {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: {-T:.1f}; }} }}
  .cv {{ stroke: {PAPER}; stroke-linecap: round; }}
  .fish {{ offset-path: path('{d}'); offset-rotate: auto; animation: swim {C:.2f}s steps({steps}) infinite; }}
  @keyframes swim {{ from {{ offset-distance: 0%; }} to {{ offset-distance: 100%; }} }}
  @media (prefers-reduced-motion: reduce) {{ .go, .fish {{ animation: none; }} }}
"""))
    art.ink(card(W, H) + heading(PAD, HEAD_Y, head_txt, "金魚すくい", bold) + rule(PAD, W - PAD, RULE_Y)
            + f'<path d="{ink_dots}{legend_d}" fill="{INK}" />'
            + f'<g class="go cv">{cover}</g>'
            + f'<path d="{faint}{legend_f}" fill="{INK}" fill-opacity="0.28" />'
            + "".join(months) + days
            + f'<text class="m" x="{legend_x[0] - 12:.1f}" y="{fy}" text-anchor="end">少</text>'
            f'<text class="m" x="{legend_x[-1] + 12:.1f}" y="{fy}">多</text>'
            f'<text class="s" x="{PAD}" y="{fy}">{foot_txt}</text>'
            + clock("rp", C) + "".join(ripples)
            + raindrops(cells))

    def fish(mode):
        defs, body, tail, fins, shadow = goldfish_parts(mode)
        shade, op = ("#15171d", 0.1) if mode == "light" else ("#000000", 0.32)
        tl = 0.08
        anim = clock("tl", tl * len(TAIL_POSES)) + poster(tail(0) + fins(0)) + "".join(
            cel("tl", [(tl * i, tl)], tail(a) + fins(-a * 0.8)) for i, a in enumerate(TAIL_POSES))
        return (f'<defs>{defs}</defs><g class="fish"><g transform="scale(0.92)">'
                f'<g fill="{shade}" fill-opacity="{op}" transform="translate(4 5)">{shadow}</g>'
                f'<g fill="{shade}" fill-opacity="{op * 0.6:.2f}" transform="translate(5.5 6.5) scale(1.04)">{shadow}</g>'
                f'{anim}{body}</g></g>')
    art.color(fish("light"), fish("dark"))
    art.color(*seal(W - PAD, HEAD_Y - 18, "魚"))
    art.write(PROFILE, "snake")
    print(f"wrote goldfish pond light/dark ({C:.0f}s lap, {steps} steps, route {total:.0f}px, {len(ripples)} ripples)")


if __name__ == "__main__":
    st, lg = stats_data(), langs_data()
    H = stats_height(st, lg)
    if st:
        stats(st, H)
    if lg:
        top_langs(lg, H)
    pins = sorted(p.stem for p in PROFILE.glob("pin-*.svg") if not p.stem.endswith(("-light", "-dark")))
    for i, name in enumerate(pins, 1):
        pin(name, i, len(pins))
    trophy()
    activity()
    snake()

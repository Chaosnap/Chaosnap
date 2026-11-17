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
import re
import sys
import xml.etree.ElementTree as ET
from html import escape

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_RED, PAPER, RED, SERIF, SERIF_STACK,  # noqa: E402
                   Art, cel, clock, load_font, poster, smooth, star)

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


def stats_card(st, lg):
    """左栏：几项数字 + 等级表盘；右栏：语言比例条 + 两列图例。中间一道发丝竖线。"""
    head, rows, rank, prog = st or ("GitHub Stats", [], "", 0.0)
    lhead, items = lg or ("Most Used Languages", [])
    W = W_FULL
    lrows = (len(items) + 1) // 2
    top = RULE_Y + 12
    H = max(236, top + 30 * max(0, len(rows) - 1) + 52, top + 44 + 26 * max(0, lrows - 1) + 52)
    mid_y = (top + H - 24) / 2  # 内容区的垂直中线

    bold = load_font(SERIF, 700, head + lhead + "".join(v for _, v, _ in rows) + rank + "".join(p for _, p, _ in items) + "0123456789,.%")
    reg = load_font(SERIF, 400, "".join(lb for lb, _, _ in rows) + "".join(nm for nm, _, _ in items) + "RANK")
    jp = load_font(MINCHO, 800, "能力値言語力")
    label = (f"{head}: " + ", ".join(f"{lb} {v}" for lb, v, _ in rows) + (f", rank {rank}" if rank else "")
             + f". {lhead}: " + ", ".join(f"{nm} {p}" for nm, p, _ in items))
    art = sheet(W, H, label)
    art.css.append(base_css([bold, reg, jp], f"""  .rank {{ font: 700 32px {SERIF_STACK}; fill: {INK}; }}
  .rk {{ font: 400 7.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 2.6px; }}
  .pct {{ font: 700 12px {SERIF_STACK}; fill: {INK}; }}
"""))
    LX0, LX1 = PAD, 494          # 左栏
    RX0, RX1 = 546, W - PAD      # 右栏
    body = [card(W, H),
            heading(LX0, HEAD_Y, head, "能力値", bold), rule(LX0, LX1, RULE_Y),
            heading(RX0, HEAD_Y, lhead, "言語", bold), rule(RX0, RX1, RULE_Y),
            f'<rect x="{(LX1 + RX0) / 2 - 0.35:.2f}" y="30" width="0.7" height="{H - 60}" fill="{INK}" fill-opacity="0.16" />']

    # ---- 左栏：数字 ----
    XV = 318
    y0 = mid_y - 30 * (len(rows) - 1) / 2 + 4.5
    for k, (lb, value, d) in enumerate(rows):
        y = round(y0 + k * 30)
        lw = reg.width(lb, 13) if reg else 7 * len(lb)
        body.append((icon(d, LX0, y - 12, 0.85, 0.7) if d else "")
                    + f'<text class="l" x="{LX0 + 25}" y="{y}">{escape(lb)}</text>'
                    + leaders(LX0 + 25 + lw + 10, XV - 36, y - 1)
                    + f'<text class="v" x="{XV}" y="{y}" text-anchor="end">{escape(value)}</text>')
    # 等级表盘：一圈细刻度、底环、进度弧、等级字母
    cx, cy, r = 418, round(mid_y, 1), 38
    ticks = []
    for i in range(60):
        a = 2 * math.pi * i / 60
        r0, r1 = r + 6, r + (10.5 if i % 5 == 0 else 8.5)
        ticks.append(f"M{cx + r0 * math.cos(a):.1f} {cy + r0 * math.sin(a):.1f}L{cx + r1 * math.cos(a):.1f} {cy + r1 * math.sin(a):.1f}")
    body.append(f'<path d="{"".join(ticks)}" stroke="{INK}" stroke-width="0.7" stroke-opacity="0.32" fill="none" />'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity="0.18" />'
                f'<path d="{arc(cx, cy, r, prog)}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" />'
                f'<text class="rank" x="{cx}" y="{cy + 8:.1f}" text-anchor="middle">{escape(rank)}</text>'
                f'<text class="rk" x="{cx + 1.3}" y="{cy + 22:.1f}" text-anchor="middle">RANK</text>')

    # ---- 右栏：语言 ----
    n = len(items)
    BH = 8
    BY = round(mid_y - (BH + 30 + 26 * max(0, lrows - 1)) / 2 + 2)
    total = sum(w for _, _, w in items) or 1
    art.defs.append(f'<clipPath id="bar"><rect x="{RX0}" y="{BY}" width="{RX1 - RX0}" height="{BH}" rx="{BH / 2}" /></clipPath>')
    segs, mids, x = [], [], RX0
    for k, (_, _, w) in enumerate(items):
        sw = (RX1 - RX0) * w / total
        segs.append(f'<rect x="{x + (0 if k == 0 else 1):.1f}" y="{BY}" width="{max(0, sw - (1 if k else 0) - (1 if k < n - 1 else 0)):.1f}" height="{BH}" fill="{FILLS[k % len(FILLS)]}" />')
        mids.append(x + sw / 2)
        x += sw
    body.append(f'<g clip-path="url(#bar)">{"".join(segs)}</g>'
                f'<rect x="{RX0}" y="{BY}" width="{RX1 - RX0}" height="{BH}" rx="{BH / 2}" fill="none" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.8" />')
    col_w = (RX1 - RX0 - 24) / 2
    spots = []
    for k, (name, pct, _) in enumerate(items):
        col, row = k // lrows, k % lrows
        x, y = RX0 + col * (col_w + 24), BY + BH + 30 + row * 26
        spots.append((x, y))
        body.append(f'<rect x="{x:.1f}" y="{y - 8.5}" width="8.5" height="8.5" rx="1.5" fill="{FILLS[k % len(FILLS)]}" stroke="{INK}" stroke-width="0.7" />'
                    f'<text class="d" x="{x + 15:.1f}" y="{y}">{escape(name)}</text>'
                    f'<text class="pct" x="{x + col_w:.1f}" y="{y}" text-anchor="end">{escape(pct)}</text>')
    art.ink("".join(body))

    # 等级弧的尽头一颗朱点，每隔几秒荡开一圈水波（四格）
    a = -math.pi / 2 + 2 * math.pi * prog
    dx, dy = cx + r * math.cos(a), cy + r * math.sin(a)
    ripple = clock("k", 4.8) + "".join(
        cel("k", [(0.6 + i * 0.12, 0.12)], f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{rr}" fill="none" stroke="{RED}" stroke-width="{sw}" stroke-opacity="{op}" />')
        for i, (rr, sw, op) in enumerate([(6, 1.4, 0.8), (9, 1.1, 0.55), (12, 0.9, 0.32), (15, 0.7, 0.15)]))
    art.color(*both(ripple + f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="3.6" fill="{RED}" />'))

    # 一枚朱色的小三角每两秒移到下一种语言：指着条上对应的一段，图例那一行下面同时划一道细线
    if n:
        def mark(k):
            mx, (lx, ly) = mids[k], spots[k]
            return (f'<path d="M{mx - 4:.1f} {BY + BH + 9.5}L{mx:.1f} {BY + BH + 3}L{mx + 4:.1f} {BY + BH + 9.5}Z" fill="{RED}" />'
                    f'<rect x="{lx:.1f}" y="{ly + 5}" width="{col_w:.1f}" height="1.2" fill="{RED}" />')
        hop = clock("j", 2.4 * n) + poster(mark(0)) + "".join(cel("j", [(2.4 * k, 2.4)], mark(k)) for k in range(n))
        art.color(*both(hop))
    art.color(*seal(RX1, HEAD_Y - 18, "力"))
    art.write(PROFILE, "stats")
    print("wrote stats light/dark (stats + languages)")


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
    body = [card(W, H), f'<text class="no" x="{X1 - 6}" y="{H - 20}" text-anchor="end">{index:02d}</text>',
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
    # 简介末尾一根打字机光标，一亮一灭
    last = lines[-1] if lines else ""
    cx_ = X0 + (reg.width(last, 12.5) if reg else 6.6 * len(last)) + 4
    cy_ = 86 + (len(lines) - 1) * 19
    cursor = f'<rect x="{cx_:.1f}" y="{cy_ - 11}" width="1.5" height="13" fill="{INK}" fill-opacity="0.8" />'
    body.append(clock("b", 1.6) + poster(cursor) + cel("b", [(0, 0.8)], cursor))
    art.ink("".join(body))
    art.color(*seal(X1, HEAD_Y - 18, "推"))
    art.write(PROFILE, name)
    print("wrote", name, "light/dark")


# ---------------------------------------------------------------- 活动折线图
def activity():
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
    months, dates = [], [None] * n
    if start:
        for i in range(n):
            d = start + datetime.timedelta(days=i)
            dates[i] = d
            if d.day == 1 or (i == 0 and not any((start + datetime.timedelta(days=j)).day == 1 for j in range(1, 3))):
                months.append((i, d.strftime("%b").upper()))

    W, H = W_FULL, 330
    head = "Activity"
    caption = f"PAST {n} DAYS"
    bold = load_font(SERIF, 700, head + "0123456789")
    reg = load_font(SERIF, 400, caption + "0123456789" + "JANFEBMARAPRMAYJUNJULAUGSEPOCTNOVDEC")
    jp = load_font(MINCHO, 800, "活動記録録")
    art = sheet(W, H, f"Activity graph: contributions over the past {n} days")
    art.css.append(base_css([bold, reg, jp], f"""  .peak {{ font: 700 11.5px {SERIF_STACK}; fill: {RED}; }}
  .fv {{ font: 700 12px {SERIF_STACK}; fill: {PAPER}; }}
  .fd {{ font: 400 9px {SERIF_STACK}; fill: {PAPER}; letter-spacing: 1.5px; fill-opacity: 0.8; }}
"""))
    X0, X1 = PAD, W - PAD
    px0, px1, py0, py1 = 72, W - 44, 108, 262
    vmax = max(values) or 1
    step = 5 if vmax <= 30 else (10 if vmax <= 80 else 20)
    ymax = max(step, math.ceil(vmax / step) * step)
    xs = [px0 + (px1 - px0) * i / (n - 1) for i in range(n)]
    ys = [py1 - (py1 - py0) * v / ymax for v in values]
    line = smooth(list(zip(xs, ys)))
    body = [card(W, H), heading(X0, HEAD_Y, head, "活動記録", bold),
            f'<text class="s" x="{X1 - SEAL - 16}" y="{HEAD_Y - 1}" text-anchor="end">{caption}</text>', rule(X0, X1, RULE_Y)]
    grid = []
    for t in range(0, ymax + 1, step):
        y = py1 - (py1 - py0) * t / ymax
        grid.append(f'<path d="M{px0} {y:.1f}H{px1}" stroke="{INK}" stroke-width="0.6" stroke-dasharray="1.5 3.5" stroke-opacity="{0.5 if t == 0 else 0.22}" />'
                    f'<text class="ax" x="{px0 - 14}" y="{y + 3.5:.1f}" text-anchor="end">{t}</text>')
    body.append("".join(grid))
    body.append(f'<path d="{line}L{px1:.1f} {py1}L{px0:.1f} {py1}Z" fill="url(#toneFine)" fill-opacity="0.35" />'
                f'<path d="{line}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" />')
    body.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{PAPER}" stroke="{INK}" stroke-width="1" />' for x, y in zip(xs, ys)))
    body.append("".join(f'<text class="ax" x="{x:.1f}" y="{py1 + 20}" text-anchor="middle">{escape(lb)}</text>' for x, lb in zip(xs, labels)))
    body.append("".join(f'<text class="s" x="{xs[i]:.1f}" y="{py1 + 40}" text-anchor="{"start" if i == 0 else "middle"}">{m}</text>' for i, m in months))
    art.ink("".join(body))
    k = values.index(vmax)
    peak = (f'<circle cx="{xs[k]:.1f}" cy="{ys[k]:.1f}" r="4" fill="{RED}" />'
            f'<text class="peak" x="{xs[k]:.1f}" y="{ys[k] - 11:.1f}" text-anchor="middle">{vmax:g}</text>')
    art.color(*both(peak))

    # 读数的游标：一天一格从左走到右，竖线套住当天的点，上方的小牌子写着日期和数目
    FW, FH, fy = 74, 20, 74
    def cursor(i):
        x, y, v = xs[i], ys[i], values[i]
        fx = min(max(x, px0 + FW / 2 - 12), px1 - FW / 2 + 12)
        date = dates[i].strftime("%b %-d").upper() if dates[i] else f"DAY {i + 1}"
        return (f'<path d="M{x:.1f} {fy + FH}V{py1}" stroke="{INK}" stroke-width="0.8" stroke-dasharray="2 3" stroke-opacity="0.6" />'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="none" stroke="{INK}" stroke-width="1.1" />'
                f'<path d="M{x - 3.5:.1f} {fy + FH - 0.5}h7l-3.5 4.5z" fill="{INK}" />'
                f'<rect x="{fx - FW / 2:.1f}" y="{fy}" width="{FW}" height="{FH}" rx="3" fill="{INK}" />'
                f'<text class="fd" x="{fx - FW / 2 + 8:.1f}" y="{fy + 13.5}">{date}</text>'
                f'<text class="fv" x="{fx + FW / 2 - 8:.1f}" y="{fy + 14.5}" text-anchor="end">{v:g}</text>')
    dwell = 0.96
    scan = clock("k", dwell * n) + poster(cursor(n - 1)) + "".join(cel("k", [(dwell * i, dwell)], cursor(i)) for i in range(n))
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


def cup(cx, cy, rank, secret):
    """一只奖杯。等级越高杯身越“浓”：C 留白、B 斜线、A 网点、S 实墨（隐藏奖杯是朱色的）；S 和 A 两侧有月桂，头上按字母数排星。
    返回 (垫在下面的朱色, 墨线, 盖在上面的朱色)。"""
    tier = rank[:1]
    bowl = "M-17 -22H17V-17C17 -3 9 5 0 5C-9 5 -17 -3 -17 -17Z"
    fill = {"S": INK, "A": "url(#tone)", "B": "url(#hatch)"}.get(tier, PAPER)
    under = f'<path d="{bowl}" transform="translate({cx:.1f} {cy})" fill="{RED}" />' if secret else ""
    letter_fill = PAPER if tier == "S" or secret else INK
    halo = "" if tier == "S" or secret else f' stroke="{PAPER}" stroke-width="3.2" paint-order="stroke" stroke-linejoin="round"'
    ink = [laurel(cx, cy, tier == "S" or secret) if tier in "SA" or secret else "",
           f'<g transform="translate({cx:.1f} {cy})">'
           f'<path d="M-17 -15C-28 -15 -27 0 -12 1M17 -15C28 -15 27 0 12 1" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" />'
           + ("" if secret else f'<path d="{bowl}" fill="{PAPER}" /><path d="{bowl}" fill="{fill}" />')
           + f'<path d="{bowl}" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round" />'
           f'<rect x="-19.5" y="-25.5" width="39" height="5" rx="2" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" />'
           f'<path d="M-3 5V12H3V5" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" /><ellipse cx="0" cy="8.5" rx="5.4" ry="1.9" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" />'
           f'<path d="M-10 12H10L12.5 19H-12.5Z" fill="{INK}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round" />'
           f'<rect x="-16" y="19" width="32" height="5" rx="1" fill="{PAPER}" stroke="{INK}" stroke-width="1.3" />'
           f'<text x="0" y="-3.6" text-anchor="middle" class="rk" fill="{letter_fill}"{halo}>{escape(tier)}</text></g>']
    pips = ""
    if tier in "SA" or secret:
        n = len(rank)
        pips = "".join(f'<path d="{star5(cx + (j - (n - 1) / 2) * 11, cy - 38, 4)}" fill="{RED if tier == "S" or secret else INK}" />' for j in range(n))
    over = pips if tier == "S" or secret else ""
    if pips and not over:
        ink.append(pips)
    return under, "".join(ink), over


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
        sx, sy, red = cx + 23, CY - 27, t["rank"][:1] == "S" or t["secret"]
        for at, dur, rr in [(0, 0.08, 3.5), (0.08, 0.16, 7.5), (0.24, 0.08, 4.5)]:
            shine.append(cel("k", [(0.8 + k * 0.72 + at, dur)],
                             f'<path d="{star(sx, sy, rr)}" fill="{RED if red else INK}" />' + (f'<path d="{star(sx + 8, sy + 9, rr * 0.42)}" fill="{RED if red else INK}" />' if rr > 6 else "")))
    art.ink(ink[0])  # 卡片底先铺，隐藏奖杯的朱色杯身垫在墨线下面
    art.color(*both("".join(under)))
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
SNAKE_TICK, SNAKE_SPEED = 0.05, 46.0    # 一格 0.05 秒（20 格/秒）；每秒走 46 像素，约三格
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
    return d + ("z" if closed else ""), total, closed


def snake():
    """一筆書き：一年的贡献是一片大小不一的墨点，一支笔从中穿过——笔尖一点朱，身后是由粗到细、渐渐收锋的墨迹。
    笔走过的地方墨点被“吃掉”，留下一道空白，几秒后又一粒粒长回来。

    整条笔画都是同一条路径（<use> 引用）上的“虚线窗口”：
    - 笔尖：零长度的虚线 + 圆头线帽，就是一颗朱点；
    - 笔身：九段由细到粗、由长到短的窗口叠在一起，于是从笔尖往后一点点收细，像毛笔的“払い”；
    - 吃掉：一条纸色的宽窗口从笔尖往后盖住走过的格子，尾端分三层淡出。
    所有窗口共用外层 <g> 上的一个 stroke-dashoffset 动画（steps）；墨点全是静态路径。"""
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    cells, route = snake_data(raw.read_text(encoding="utf-8"))
    W, H = W_FULL, 268
    k = SNAKE_P / 16
    cols = int(max(c[0] for c in cells) // 16) + 1
    gx, gy = (W - (cols - 1) * SNAKE_P) / 2, 120  # 第一格的中心

    def at(x, y):
        return gx + (x - 8) * k, gy + (y - 8) * k
    cells = [(*at(x, y), lv) for x, y, lv in cells]
    route = [at(x, y) for x, y in route]
    d, total, closed = snake_route(route, 0, 0, radius=6.0)
    steps = round(total / SNAKE_SPEED / SNAKE_TICK)
    C = steps * SNAKE_TICK
    head_txt, foot_txt = "Contribution Snake", "ONE YEAR  ·  ONE STROKE"
    bold = load_font(SERIF, 700, head_txt)
    reg = load_font(SERIF, 400, foot_txt)
    jp = load_font(MINCHO, 800, "一筆書き蛇少多月水金" + "".join(MONTHS_JP))
    active = sum(1 for c in cells if c[2])
    art = sheet(W, H, f"Contribution snake: one stroke of ink through a year of contributions ({active} active days)")

    # 月份（汉字）、星期（月 水 金）
    today = datetime.date.today()
    months, last, last_x = [], None, -99.0
    for c in range(cols):
        day = today - datetime.timedelta(weeks=cols - 1 - c)
        x = gx + c * SNAKE_P - 3
        # 月份换了才写；离上一个太近（开头那半个月）就让给下一个月
        if day.month != last and c < cols - 2:
            if x - last_x < 44 and months:
                months.pop()
            months.append(f'<text class="m" x="{x:.1f}" y="{gy - 24}">{MONTHS_JP[day.month - 1]}</text>')
            last_x = x
        last = day.month
    days = "".join(f'<text class="m" x="{gx - 14:.1f}" y="{gy + r * SNAKE_P + 3.5:.1f}" text-anchor="end">{nm}</text>' for r, nm in ((1, "月"), (3, "水"), (5, "金")))

    def dot(x, y, r):
        return f"M{x - r:.1f} {y:.1f}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0z"
    faint = "".join(dot(x, y, LEVEL_R[0]) for x, y, _ in cells)  # 每格都有：墨点被吃掉以后，那里就只剩这一粒淡点
    ink_dots = "".join(dot(x, y, LEVEL_R[min(lv, 4)]) for x, y, lv in cells if lv)
    fy = H - 26
    lx = W - PAD - 22  # 图例：少 · · · · · 多
    legend_x = [lx - 14 - 15 * (4 - i) for i in range(5)]
    legend_f = dot(legend_x[0], fy - 3.5, LEVEL_R[0])
    legend_d = "".join(dot(legend_x[i], fy - 3.5, LEVEL_R[i]) for i in range(1, 5))

    # 窗口：从笔尖往后 L 长的一段（ahead > 0 时再往前探出一点）。图案周期等于路线全长，绕一圈正好接上
    T = total

    def window(L, ahead=0.0):
        return f"{ahead:.1f} {T - L:.1f} {L - ahead:.1f} 0"

    def use(width, dash, extra=""):
        return f'<use href="#route" stroke-width="{width}" stroke-dasharray="{dash}"{extra} />'
    art.defs.append(f'<path id="route" d="{d}" />')
    regrow = 6.0 * SNAKE_SPEED  # 被吃掉的墨点大约六秒后长回来
    # 盖住墨点的纸：尾端分五层、每层退一格，墨点一格比一格浓地长回来
    cover = "".join(use(12.5, window(regrow + SNAKE_P * j, 6), f' stroke-opacity="{op}"') for j, op in ((4, 0.2), (3, 0.4), (2, 0.6), (1, 0.8), (0, 1)))
    LB = 9 * SNAKE_P  # 笔身长度
    brush = []
    for i in range(14):
        t = i / 13
        L = LB * (1 - 0.9 * t)
        w = 0.6 + 5.4 * t ** 1.4
        op = 0.3 + 0.7 * min(1.0, t * 1.8)
        brush.append(use(round(w, 2), window(L), f' stroke-opacity="{op:.2f}"' if op < 1 else ""))
    tip = use(7.4, f"0 {T:.1f}")

    art.css.append(base_css([bold, reg, jp], f"""  .m {{ font-size: 9.5px; }}
  .go {{ fill: none; stroke-linejoin: round; animation: go {C:.2f}s steps({steps}) infinite; }}
  @keyframes go {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: {-T:.1f}; }} }}
  .cv {{ stroke: {PAPER}; stroke-linecap: round; }}
  .br {{ stroke: {INK}; stroke-linecap: round; }}
  @media (prefers-reduced-motion: reduce) {{ .go {{ animation: none; }} }}
"""))
    art.ink(card(W, H) + heading(PAD, HEAD_Y, head_txt, "一筆書き", bold) + rule(PAD, W - PAD, RULE_Y)
            + f'<path d="{ink_dots}{legend_d}" fill="{INK}" />'
            + f'<g class="go cv">{cover}</g>'
            + f'<path d="{faint}{legend_f}" fill="{INK}" fill-opacity="0.28" />'
            + "".join(months) + days
            + f'<text class="m" x="{legend_x[0] - 12:.1f}" y="{fy}" text-anchor="end">少</text>'
            f'<text class="m" x="{legend_x[-1] + 12:.1f}" y="{fy}">多</text>'
            f'<text class="s" x="{PAD}" y="{fy}">{foot_txt}</text>'
            f'<g class="go br">{"".join(brush)}</g>')
    art.color(*both(f'<g class="go" stroke="{RED}" stroke-linecap="round">{tip}</g>'))
    art.color(*seal(W - PAD, HEAD_Y - 18, "蛇"))
    art.write(PROFILE, "snake")
    print(f"wrote snake light/dark ({C:.0f}s lap, {steps} steps, route {total:.0f}px, closed={closed})")


if __name__ == "__main__":
    st, lg = stats_data(), langs_data()
    if st or lg:
        stats_card(st, lg)
    pins = sorted(p.stem for p in PROFILE.glob("pin-*.svg") if not p.stem.endswith(("-light", "-dark")))
    for i, name in enumerate(pins, 1):
        pin(name, i, len(pins))
    trophy()
    activity()
    snake()

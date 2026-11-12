#!/usr/bin/env python3
"""把 Action 生成的卡片重新排成静态的黑白漫画风卡片，各出浅色、深色两版，由 PersonalStatus.yml 调用。

原始卡片（stats.svg 等）保持不动，每次从它们里读出数据，再用主页自己的字体和线条重新画一遍：
- 统计、语言、置顶仓库、活动折线图：只取数字和文字，整张重画（不套滤镜，也没有动画）
- 奖杯：上游的图去色后摆进同样的框里
- 贪吃蛇：唯一还在动的一张——白蛇沿路径吃草，草过一会儿又长回来；其余装饰全是静态
"""
import datetime
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from html import escape

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from manga import (DEFS, EASE, GRAY, INK, MINCHO, MINCHO_STACK, NIGHT_RED, PAPER, RED, SERIF, SERIF_STACK,  # noqa: E402
                   Art, load_font, smooth, stamp, to_night)

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "profile"
NS = "{http://www.w3.org/2000/svg}"
OCTICON = {
    "star": "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z",
    "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z",
    "fork": "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z",
}
# 语言条和色点：黑白漫画里用墨、网点、斜线代替颜色
FILLS = [INK, "url(#tone)", "url(#hatch)", "url(#toneFine)", "url(#toneBig)", GRAY, "url(#tone)", "url(#hatch)"]


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


def split(svg):
    """拆成根标签和内容。"""
    i = svg.index(">", svg.index("<svg")) + 1
    return svg[:i], svg[i:svg.rfind("</svg>")]


# ---------------------------------------------------------------- 共用的版面部件
def card(w, h, rx=6):
    """内页卡片：纸、细边、再一圈发丝线。"""
    return (f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx}" fill="{PAPER}" />'
            f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx}" fill="none" stroke="{INK}" stroke-width="1.5" />'
            f'<rect x="6.5" y="6.5" width="{w - 13}" height="{h - 13}" rx="{max(rx - 3, 1)}" fill="none" stroke="{INK}" stroke-width="0.6" opacity="0.7" />')


def rule(x0, x1, y):
    return f'<rect x="{x0}" y="{y - 0.4:.1f}" width="{x1 - x0:.0f}" height="0.8" fill="{INK}" />'


def leaders(x0, x1, y, pitch=5):
    """目次式的点线引导。"""
    if x1 - x0 < pitch:
        return ""
    d = "".join(f"M{x0 + k * pitch:.1f} {y}h0.01" for k in range(int((x1 - x0) // pitch) + 1))
    return f'<path d="{d}" stroke="{INK}" stroke-width="1.3" stroke-linecap="round" opacity="0.4" />'


def tag(x, y, label, size=13, h=24):
    """红色印章标签；x 为负表示右边缘贴在 -x。返回 (浅色, 深色)。"""
    w = int(size * 1.15 * len(label) + 18)
    s = stamp(x if x >= 0 else -x - w, y, w, h, label, size)
    return s, s.replace(RED, NIGHT_RED)


def icon(d, x, y, s=1.0, opacity=1.0):
    return f'<g transform="translate({x} {y}) scale({s})" fill="{INK}" opacity="{opacity}"><path fill-rule="evenodd" d="{d}" /></g>'


def arc(cx, cy, r, p):
    """从正上方顺时针走 p 圈的弧。"""
    p = max(0.001, min(0.999, p))
    a = -math.pi / 2 + 2 * math.pi * p
    return f"M{cx} {cy - r}A{r} {r} 0 {1 if p > 0.5 else 0} 1 {cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}"


def base_css(fonts, extra=""):
    return "".join(f.css() for f in fonts if f) + f"""
  .h {{ font: 700 18px {SERIF_STACK}; fill: {INK}; }}
  .l {{ font: 400 13px {SERIF_STACK}; fill: {INK}; }}
  .v {{ font: 700 14px {SERIF_STACK}; fill: {INK}; }}
  .d {{ font: 400 12.5px {SERIF_STACK}; fill: {INK}; opacity: 0.85; }}
  .s {{ font: 400 10.5px {SERIF_STACK}; fill: {GRAY}; letter-spacing: 2.5px; }}
  .ax {{ font: 400 10.5px {SERIF_STACK}; fill: {GRAY}; }}
  .m {{ font: 800 12px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
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


# ---------------------------------------------------------------- 统计卡
def stats():
    svg = read("stats")
    if not svg:
        return
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
        return
    rank_el = tid(root, "level-rank-icon")
    rank = txt(rank_el[0]) if rank_el else ""
    m = re.search(r"@keyframes rankAnimation.*?to\s*\{\s*stroke-dashoffset:\s*([\d.]+)", svg, re.S)
    prog = max(0.0, min(1.0, 1 - float(m.group(1)) / (2 * math.pi * 40))) if m else 0.0

    W = 560
    H = max(200, 86 + 27 * len(rows) + 28)
    bold = load_font(SERIF, 700, head + "".join(v for _, v, _ in rows) + rank + "0123456789,.")
    reg = load_font(SERIF, 400, "".join(lb for lb, _, _ in rows))
    jp = load_font(MINCHO, 800, "能力値")
    art = Art(W, H, f"{head}: " + ", ".join(f"{lb} {v}" for lb, v, _ in rows) + (f", rank {rank}" if rank else ""), lean=True)
    art.css.append(base_css([bold, reg, jp], f"  .rank {{ font: 700 34px {SERIF_STACK}; fill: {INK}; }}\n"))
    X0, XV = 30, 340
    body = [card(W, H), f'<text class="h" x="{X0}" y="42">{escape(head)}</text>', rule(X0, W - 30, 56)]
    for k, (label, value, d) in enumerate(rows):
        y = 90 + k * 27
        lw = reg.width(label, 13) if reg else 7 * len(label)
        body.append((icon(d, X0, y - 12, 0.9, 0.8) if d else "")
                    + f'<text class="l" x="{X0 + 26}" y="{y}">{escape(label)}</text>'
                    + leaders(X0 + 26 + lw + 9, XV - 34, y - 1)
                    + f'<text class="v" x="{XV}" y="{y}" text-anchor="end">{escape(value)}</text>')
    cx, cy, r = 462, 60 + (H - 60) / 2, 42
    body.append(f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{INK}" stroke-width="1" opacity="0.28" />'
                f'<circle cx="{cx}" cy="{cy:.1f}" r="{r - 8}" fill="none" stroke="{INK}" stroke-width="0.8" stroke-dasharray="1 3.5" opacity="0.45" />'
                f'<path d="{arc(cx, cy, r, prog)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" />'
                f'<text class="rank" x="{cx}" y="{cy + 12:.1f}" text-anchor="middle">{escape(rank)}</text>')
    art.ink("".join(body))
    a = -math.pi / 2 + 2 * math.pi * prog
    dot = f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="3.6" fill="{RED}" />'
    art.color(dot, dot.replace(RED, NIGHT_RED))
    art.color(*tag(-(W - 30), 18, "能力値"))
    art.write(PROFILE, "stats")
    print("wrote stats light/dark")


# ---------------------------------------------------------------- 语言卡
def top_langs():
    svg = read("top-langs")
    if not svg:
        return
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
    if not items:
        return
    n = len(items)
    rows = (n + 1) // 2
    W = 370
    H = max(200, 114 + rows * 24 + 26)
    bold = load_font(SERIF, 700, head + "".join(p for _, p, _ in items) + "0123456789.%")
    reg = load_font(SERIF, 400, "".join(nm for nm, _, _ in items))
    jp = load_font(MINCHO, 800, "言語")
    art = Art(W, H, f"{head}: " + ", ".join(f"{nm} {p}" for nm, p, _ in items), lean=True)
    art.css.append(base_css([bold, reg, jp], f"  .pct {{ font: 700 12px {SERIF_STACK}; fill: {INK}; }}\n"))
    X0, X1, BY, BH = 30, W - 30, 72, 10
    total = sum(w for _, _, w in items) or 1
    art.defs.append(f'<clipPath id="bar"><rect x="{X0}" y="{BY}" width="{X1 - X0}" height="{BH}" rx="{BH / 2}" /></clipPath>')
    segs, x = [], X0
    for k, (_, _, w) in enumerate(items):
        sw = (X1 - X0) * w / total
        segs.append(f'<rect x="{x + (0 if k == 0 else 0.8):.1f}" y="{BY}" width="{max(0, sw - (0.8 if k else 0) - (0.8 if k < n - 1 else 0)):.1f}" height="{BH}" fill="{FILLS[k % len(FILLS)]}" />')
        x += sw
    body = [card(W, H), f'<text class="h" x="{X0}" y="42">{escape(head)}</text>', rule(X0, X1, 56),
            f'<g clip-path="url(#bar)">{"".join(segs)}</g>'
            f'<rect x="{X0}" y="{BY}" width="{X1 - X0}" height="{BH}" rx="{BH / 2}" fill="none" stroke="{INK}" stroke-width="0.9" />']
    col_w = (X1 - X0 - 14) / 2
    for k, (name, pct, _) in enumerate(items):
        col, row = k // rows, k % rows
        x, y = X0 + col * (col_w + 14), 114 + row * 24
        body.append(f'<rect x="{x:.1f}" y="{y - 9}" width="9" height="9" rx="1.5" fill="{FILLS[k % len(FILLS)]}" stroke="{INK}" stroke-width="0.8" />'
                    f'<text class="d" x="{x + 16:.1f}" y="{y}">{escape(name)}</text>'
                    f'<text class="pct" x="{x + col_w:.1f}" y="{y}" text-anchor="end">{escape(pct)}</text>')
    art.ink("".join(body))
    art.color(*tag(-(W - 30), 18, "言語"))
    art.write(PROFILE, "top-langs")
    print("wrote top-langs light/dark")


# ---------------------------------------------------------------- 置顶仓库卡
def pin(name):
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

    W, H = 440, 150
    bold = load_font(SERIF, 700, repo)
    reg = load_font(SERIF, 400, desc + lang + star_n + fork_n + "0123456789 …")
    jp = load_font(MINCHO, 800, "推し")
    art = Art(W, H, f"{repo}: {desc}", lean=True)
    art.css.append(base_css([bold, reg, jp]))
    X0, X1 = 26, W - 26
    lines = wrap(reg, desc, 12.5, X1 - X0, 2)
    body = [card(W, H), icon(OCTICON["repo"], X0, 22, 1.0, 0.9), f'<text class="h" x="{X0 + 24}" y="36">{escape(repo)}</text>', rule(X0, X1, 52)]
    body += [f'<text class="d" x="{X0}" y="{76 + k * 18}">{escape(ln)}</text>' for k, ln in enumerate(lines)]
    y, x = 128, X0
    if lang:
        body.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="4.5" fill="url(#tone)" stroke="{INK}" stroke-width="0.9" /><text class="d" x="{x + 16}" y="{y}">{escape(lang)}</text>')
        x += 16 + (reg.width(lang, 12.5) if reg else 7 * len(lang)) + 22
    body.append(icon(star_d, x, y - 12.5, 0.85, 0.85) + f'<text class="d" x="{x + 19}" y="{y}">{escape(star_n)}</text>')
    x += 19 + (reg.width(star_n, 12.5) if reg else 8 * len(star_n)) + 22
    if fork_n:
        body.append(icon(fork_d, x, y - 12.5, 0.85, 0.85) + f'<text class="d" x="{x + 19}" y="{y}">{escape(fork_n)}</text>')
    art.ink("".join(body))
    art.color(*tag(-(W - 26), 16, "推し"))
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
    months = []
    if start:
        for i in range(n):
            d = start + datetime.timedelta(days=i)
            if d.day == 1 or (i == 0 and not any((start + datetime.timedelta(days=j)).day == 1 for j in range(1, 3))):
                months.append((i, d.strftime("%b").upper()))

    W, H = 1200, 380
    head = "Activity Graph"
    caption = f"CONTRIBUTIONS  ·  PAST {n} DAYS"
    bold = load_font(SERIF, 700, head + "0123456789")
    reg = load_font(SERIF, 400, caption + "0123456789" + "".join(m for _, m in months))
    jp = load_font(MINCHO, 800, "活動記録")
    art = Art(W, H, f"{head}: {caption.lower()}", lean=True)
    art.css.append(base_css([bold, reg, jp], f"  .h {{ font-size: 20px; }}\n  .peak {{ font: 700 12px {SERIF_STACK}; fill: {RED}; }}\n"))
    X0, X1 = 36, W - 36
    tw = bold.width(head, 20) if bold else 150
    px0, px1, py0, py1 = 86, W - 40, 98, 304
    vmax = max(values) or 1
    step = 5 if vmax <= 30 else (10 if vmax <= 80 else 20)
    ymax = max(step, math.ceil(vmax / step) * step)
    xs = [px0 + (px1 - px0) * i / (n - 1) for i in range(n)]
    ys = [py1 - (py1 - py0) * v / ymax for v in values]
    line = smooth(list(zip(xs, ys)))
    body = [card(W, H), f'<text class="h" x="{X0}" y="44">{head}</text>',
            f'<text class="s" x="{X1}" y="44" text-anchor="end">{caption}</text>', rule(X0, X1, 60)]
    for t in range(0, ymax + 1, step):
        y = py1 - (py1 - py0) * t / ymax
        body.append(f'<path d="M{px0} {y:.1f}H{px1}" stroke="{INK}" stroke-width="0.6" stroke-dasharray="2 3" opacity="{0.6 if t == 0 else 0.3}" />'
                    f'<text class="ax" x="{px0 - 14}" y="{y + 3.5:.1f}" text-anchor="end">{t}</text>')
    body.append(f'<path d="{line}L{px1:.1f} {py1}L{px0:.1f} {py1}Z" fill="url(#toneFine)" opacity="0.45" />'
                f'<path d="{line}" fill="none" stroke="{INK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />')
    body.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{PAPER}" stroke="{INK}" stroke-width="1.2" />' for x, y in zip(xs, ys)))
    body.append("".join(f'<text class="ax" x="{x:.1f}" y="{py1 + 22}" text-anchor="middle">{escape(lb)}</text>' for x, lb in zip(xs, labels)))
    body.append("".join(f'<text class="s" x="{xs[i]:.1f}" y="{py1 + 42}" text-anchor="{"start" if i == 0 else "middle"}">{m}</text>' for i, m in months))
    art.ink("".join(body))
    k = values.index(vmax)
    peak = (f'<circle cx="{xs[k]:.1f}" cy="{ys[k]:.1f}" r="4.6" fill="{RED}" />'
            f'<text class="peak" x="{xs[k]:.1f}" y="{ys[k] - 13:.1f}" text-anchor="middle">{vmax:g}</text>')
    art.color(peak, peak.replace(RED, NIGHT_RED))
    art.color(*tag(X0 + tw + 14, 22, "活動記録"))
    art.write(PROFILE, "activity")
    print("wrote activity light/dark")


# ---------------------------------------------------------------- 奖杯：上游的图去色，摆进同样的框
def trophy():
    svg = read("trophy")
    if not svg:
        return
    tw, th = size(svg)
    _, inner = split(svg)
    count, depth = 0, 0
    for m in re.finditer(r"<svg\b[^>]*>|</svg>", inner):  # 只数最外层、露在画面里的奖杯格子（上游多画的几行被裁掉了）
        if m.group().startswith("<svg"):
            y = re.search(r'\by="([\d.]+)"', m.group())
            count += depth == 0 and (not y or float(y.group(1)) < th)
            depth += 1
        else:
            depth -= 1
    L, T = 40, 44
    W, H = tw + 2 * L, T + th + 46
    reg = load_font(SERIF, 400, "TROPHY CABINET · COLLECT THEM ALL 0123456789")
    jp = load_font(MINCHO, 800, "実績全種")
    tag_w = int(13 * 1.15 * 2 + 18)
    right = f"全 {count} 種  ·  COLLECT THEM ALL" if count else "COLLECT THEM ALL"
    css = base_css([reg, jp])
    shelf_y = T + th + 3
    under = (card(W, H) + f'<text class="s" x="{L}" y="30">TROPHY CABINET</text>'
             f'<text class="s" x="{W - 30 - tag_w - 16:.0f}" y="30" text-anchor="end">{right}</text>'
             f'<rect x="{L - 14}" y="{shelf_y}" width="{tw + 28:.0f}" height="2.5" fill="{INK}" />'
             f'<rect x="{L - 10}" y="{shelf_y + 2.5}" width="{tw + 20:.0f}" height="9" fill="url(#hatch)" opacity="0.55" />')
    body = f'<svg x="{L}" y="{T}" width="{tw:.0f}" height="{th:.0f}" viewBox="0 0 {tw:.0f} {th:.0f}">{inner}</svg>'
    root = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W:.0f}" height="{H:.0f}" '
            f'viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="GitHub Trophies">')
    light, dark = tag(-(W - 30), 18, "実績")
    for mode, flt in (("light", "mono"), ("dark", "night")):
        conv = (lambda t: t) if mode == "light" else to_night
        out = (f"{root}\n<style>{conv(css)}</style>\n<defs>{conv(DEFS)}</defs>\n{conv(under)}"
               f'<g filter="url(#{flt})">{body}</g>{light if mode == "light" else dark}\n</svg>\n')
        (PROFILE / f"trophy-{mode}.svg").write_text(out, encoding="utf-8")
    print("wrote trophy light/dark")


# ---------------------------------------------------------------- 贪吃蛇：白蛇吃网点草，草过一会儿又长回来
LEVEL_R = [0, 2.3, 3.4, 4.5, 5.7]


def snake_data(svg):
    """从 snk 的 SVG 里取：周期、每格位置/等级/被吃的时刻、蛇头的路径关键帧。"""
    cycle = float(re.search(r"animation:none (?:linear )?(\d+)ms", svg).group(1)) / 1000
    level = {m.group(1): int(m.group(2)) for m in re.finditer(r"\.c\.(c\w+)\{fill:var\(--c(\d)\)", svg)}
    eaten = {m.group(1): float(m.group(2)) / 100 for m in re.finditer(r"@keyframes (c\w+)\{[^{]*\{[^}]*\}([\d.]+)%,100%", svg)}
    cells = []
    for m in re.finditer(r'<rect class="c(?: (c\w+))?" x="([\d.]+)" y="([\d.]+)"', svg):
        k = m.group(1)
        cells.append((float(m.group(2)) + 6, float(m.group(3)) + 6, level.get(k, 0), eaten.get(k)))
    body = svg[svg.index("@keyframes s0{"):]
    body = body[:body.index("}}") + 2]
    pts = []
    for keys, x, y in re.findall(r"([\d.,%]+)\{transform:translate\(([-\d.]+)px,([-\d.]+)px\)\}", body):
        for k in keys.split(","):
            pts.append((float(k.rstrip("%")), float(x) + 8, float(y) + 8))
    pts.sort()
    if pts[-1][0] < 100:
        pts.append((100.0, pts[0][1], pts[0][2]))
    return cycle, cells, pts


def snake_keyframes(pts):
    """蛇头：位置 + 朝向（转角处在 0.12% 内转过去，角度展开避免绕远路）；蛇身只要位置。"""
    pos = " ".join(f"{p:.2f}% {{ transform: translate({x:.1f}px, {y:.1f}px); }}" for p, x, y in pts)
    frames, prev = [], None
    for i, (p, x, y) in enumerate(pts):
        nxt = pts[i + 1] if i + 1 < len(pts) else pts[1]
        ang = math.degrees(math.atan2(nxt[2] - y, nxt[1] - x)) if (nxt[1], nxt[2]) != (x, y) else (prev if prev is not None else 0)
        if prev is not None:
            while ang - prev > 180:
                ang -= 360
            while ang - prev < -180:
                ang += 360
        before = prev if prev is not None else ang
        frames.append(f"{p:.2f}% {{ transform: translate({x:.1f}px, {y:.1f}px) rotate({before:.0f}deg); }}")
        if i + 1 < len(pts) and pts[i + 1][0] - p > 0.25:
            q = p + 0.12
            f = 0.12 / (pts[i + 1][0] - p)
            frames.append(f"{q:.2f}% {{ transform: translate({x + (nxt[1] - x) * f:.1f}px, {y + (nxt[2] - y) * f:.1f}px) rotate({ang:.0f}deg); }}")
        prev = ang
    return pos, " ".join(frames)


def snake():
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    svg = raw.read_text(encoding="utf-8")
    C, cells, pts = snake_data(svg)
    W, H = 932, 258
    gx, gy = 42, 98
    head_txt, jp_txt, foot_txt = "Contribution Snake", "草を食べる蛇  ·  365日", "SHIROHEBI  ·  一年分の草を食べる白蛇、草はまた生える"
    bold = load_font(SERIF, 700, head_txt)
    reg = load_font(SERIF, 400, "JanFebMarAprMayJunJulAugSepOctNovDec MonWedFri Less More SHIROHEBI · 0123456789")
    jp = load_font(MINCHO, 800, jp_txt + foot_txt + "連載中")
    art = Art(W, H, "Contribution snake", lean=True)

    today = datetime.date.today()
    cols = int(max(c[0] for c in cells) // 16) + 1
    months, last = [], None
    for k in range(cols):
        day = today - datetime.timedelta(weeks=cols - 1 - k)
        if day.month != last and k < cols - 2:
            months.append(f'<text class="zm" x="{gx + k * 16 + 2}" y="{gy - 12}">{day.strftime("%b")}</text>')
        last = day.month
    days = "".join(f'<text class="zm" x="{gx - 8}" y="{gy + r * 16 + 11}" text-anchor="end">{nm}</text>' for r, nm in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    grid = "".join(f"M{gx + x - 0.9:.1f} {gy + y:.1f}a0.9 0.9 0 1 0 1.8 0a0.9 0.9 0 1 0 -1.8 0" for x, y, _, _ in cells)
    grass = []
    for x, y, lv, e in cells:
        if lv:
            delay = (e if e is not None else 0) * C - C
            grass.append(f'<circle class="gd" cx="{gx + x:.1f}" cy="{gy + y:.1f}" r="{LEVEL_R[lv]}" style="animation-delay:{delay:.2f}s" />')
    ly = gy + 6 * 16 + 32
    legend = "".join(f'<circle cx="{W - 150 + i * 16}" cy="{ly - 4}" r="{max(LEVEL_R[i], 1)}" fill="{INK}" opacity="{0.3 if i == 0 else 1}" />' for i in range(5))
    pos, head_kf = snake_keyframes(pts)
    beads, n = [], 12
    for k in range(n, 0, -1):
        r = 6.3 - 3.6 * (k - 1) / (n - 1)
        beads.append(f'<g class="zb" style="animation-delay:{0.055 * k * 1.15 - C:.3f}s"><circle r="{r:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" />'
                     f'<circle r="{r * 0.5:.1f}" cx="{r * 0.18:.1f}" cy="{r * 0.18:.1f}" fill="url(#toneFine)" /></g>')
    head = (f'<g transform="translate({gx} {gy})"><g class="zh" style="animation-delay:{-C:.2f}s"><g class="tongue"><path d="M8 0H15.5M15.5 0l3.2 -2.6M15.5 0l3.2 2.6" fill="none" stroke="{RED}" stroke-width="1.3" stroke-linecap="round" /></g>'
            f'<path d="M-8.5 -6C-2 -8.6 6.5 -6.6 9.6 0C6.5 6.6 -2 8.6 -8.5 6C-10.4 2.4 -10.4 -2.4 -8.5 -6Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round" />'
            f'<path d="M-6 -3.4Q-3.6 0 -6 3.4" fill="none" stroke="{INK}" stroke-width="0.7" />'
            f'<circle cx="3.2" cy="-3.3" r="1.6" fill="{INK}" /><circle cx="3.2" cy="3.3" r="1.6" fill="{INK}" />'
            f'<circle cx="3.7" cy="-3.8" r="0.5" fill="{PAPER}" /><circle cx="3.7" cy="2.8" r="0.5" fill="{PAPER}" />'
            f'<ellipse cx="0.5" cy="-5.2" rx="1.6" ry="0.8" fill="{RED}" opacity="0.55" /><ellipse cx="0.5" cy="5.2" rx="1.6" ry="0.8" fill="{RED}" opacity="0.55" /></g></g>')
    art.css.append(base_css([bold, reg, jp], f"""
  .zj {{ font: 800 12px {MINCHO_STACK}; fill: {GRAY}; letter-spacing: 3px; }}
  .zm {{ font: 400 9.5px {SERIF_STACK}, {MINCHO_STACK}; fill: {INK}; opacity: 0.7; letter-spacing: 1px; }}
  .zf {{ font: 400 9.5px {SERIF_STACK}, {MINCHO_STACK}; fill: {INK}; opacity: 0.7; letter-spacing: 1px; }}
  .gd {{ fill: {INK}; animation: gd {C}s linear infinite; }}
  @keyframes gd {{ 0% {{ opacity: 1; }} 1.2% {{ opacity: 0; }} 27% {{ opacity: 0; }} 31%, 100% {{ opacity: 1; }} }}
  .zb {{ animation: zb {C}s linear infinite; }}
  @keyframes zb {{ {pos} }}
  .zh {{ animation: zh {C}s linear infinite; }}
  @keyframes zh {{ {head_kf} }}
  .tongue {{ transform-origin: 8px 0; animation: tongue 1.6s {EASE} infinite; }}
  @keyframes tongue {{ 0%, 55% {{ transform: scaleX(0); }} 65% {{ transform: scaleX(1); }} 72% {{ transform: scaleX(0.35); }} 80% {{ transform: scaleX(1); }} 92%, 100% {{ transform: scaleX(0); }} }}
"""))
    tag_w = int(13 * 1.15 * 3 + 18)
    art.ink(card(W, H) + f'<text class="h" x="30" y="42" style="font-size:20px">{head_txt}</text>'
            f'<text class="zj" x="{W - 30 - tag_w - 18}" y="42" text-anchor="end">{jp_txt}</text>' + rule(30, W - 30, 60)
            + "".join(months) + days + f'<path d="{grid}" fill="{INK}" opacity="0.28" />'
            + f'<text class="zf" x="{W - 162}" y="{ly}" text-anchor="end">Less</text>{legend}<text class="zf" x="{W - 72}" y="{ly}">More</text>'
            f'<text class="zf" x="{gx}" y="{ly}">{foot_txt}</text>'
            f'<g>{"".join(grass)}</g><g transform="translate({gx} {gy})">{"".join(beads)}</g>')
    art.color(head, to_night(head).replace(RED, NIGHT_RED))
    art.color(*tag(-(W - 30), 18, "連載中"))
    art.write(PROFILE, "snake")
    print("wrote snake light/dark")


if __name__ == "__main__":
    stats()
    top_langs()
    for path in sorted(PROFILE.glob("pin-*.svg")):
        if not path.stem.endswith(("-light", "-dark")):
            pin(path.stem)
    trophy()
    activity()
    snake()

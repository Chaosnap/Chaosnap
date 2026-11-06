#!/usr/bin/env python3
"""给 Action 生成的卡片加动效，由 PersonalStatus.yml 在生成卡片之后运行。

- 统计、语言、仓库卡片和活动图：流动的玫瑰色边框和一道扫光
- 活动图：折线反复描出来，一个光点沿着折线跑
- 贪吃蛇：snk 生成的 snake-raw.svg 包进一张带标题的奶油色卡片 snake.svg
"""
import pathlib
import re

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "profile"
MARK = "<!-- decorated -->"
ROSE, WINE, BLUSH = "#c96f7f", "#8e3a59", "#e8a0a8"


def size(svg):
    w = float(re.search(r'<svg[^>]*?\bwidth="([\d.]+)', svg).group(1))
    h = float(re.search(r'<svg[^>]*?\bheight="([\d.]+)', svg).group(1))
    return w, h


def overlay(w, h, rx=12, prefix="zz"):
    """边框流光 + 扫光，叠在卡片最上层，不影响点击。"""
    cx, cy = w / 2, h / 2
    return f"""{MARK}
<defs>
  <linearGradient id="{prefix}Glow" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="{h}">
    <stop offset="0" stop-color="{ROSE}" stop-opacity="0.15" />
    <stop offset="0.42" stop-color="{ROSE}" stop-opacity="0.15" />
    <stop offset="0.5" stop-color="{BLUSH}" />
    <stop offset="0.58" stop-color="{WINE}" stop-opacity="0.15" />
    <stop offset="1" stop-color="{ROSE}" stop-opacity="0.15" />
    <animateTransform attributeName="gradientTransform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" dur="6s" repeatCount="indefinite" />
  </linearGradient>
  <linearGradient id="{prefix}Sheen" x1="0" x2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0" />
    <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.55" />
    <stop offset="1" stop-color="#ffffff" stop-opacity="0" />
  </linearGradient>
  <clipPath id="{prefix}Clip"><rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" /></clipPath>
</defs>
<style>
  .{prefix}-sheen {{ animation: {prefix}Sheen 6.5s ease-in-out infinite; }}
  @keyframes {prefix}Sheen {{
    0%, 60% {{ transform: translateX({-w * 0.45:.0f}px) skewX(-20deg); }}
    100% {{ transform: translateX({w * 1.3:.0f}px) skewX(-20deg); }}
  }}
</style>
<g pointer-events="none">
  <g clip-path="url(#{prefix}Clip)"><rect class="{prefix}-sheen" x="0" y="{-h * 0.2:.0f}" width="{w * 0.18:.0f}" height="{h * 1.4:.0f}" fill="url(#{prefix}Sheen)" /></g>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{rx}" fill="none" stroke="url(#{prefix}Glow)" stroke-width="2" />
</g>
"""


def insert_before_end(svg, extra):
    end = svg.rfind("</svg>")
    return svg[:end] + extra + svg[end:]


def decorate_card(name):
    path = PROFILE / name
    if not path.exists():
        return
    svg = path.read_text(encoding="utf-8")
    if MARK in svg:
        return
    w, h = size(svg)
    path.write_text(insert_before_end(svg, overlay(w, h)), encoding="utf-8")
    print("decorated", name)


def decorate_activity():
    path = PROFILE / "activity.svg"
    if not path.exists():
        return
    svg = path.read_text(encoding="utf-8")
    if MARK in svg:
        return
    w, h = size(svg)
    # 折线：统一长度后反复描出，区域跟着淡入淡出，光点沿线跑
    svg, n = re.subn(r'<path([^>]*class="ct-line")', r'<path id="zzLine" pathLength="1000"\1', svg, count=1)
    extra = f"""
<style>
  .ct-line {{ stroke-dasharray: 1000; animation: zzDraw 9s ease-in-out infinite; }}
  .ct-area {{ animation: zzArea 9s ease-in-out infinite; }}
  @keyframes zzDraw {{ 0% {{ stroke-dashoffset: 1000; }} 45%, 85% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -1000; }} }}
  @keyframes zzArea {{ 0%, 10% {{ opacity: 0; }} 45%, 85% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
</style>
""" if n else ""
    if n:
        extra += f"""<g pointer-events="none">
  <circle r="11" fill="{BLUSH}" opacity="0.35"><animate attributeName="r" values="8;14;8" dur="1.2s" repeatCount="indefinite" />
    <animateMotion dur="9s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.45;1" calcMode="linear"><mpath href="#zzLine" /></animateMotion></circle>
  <circle r="5" fill="{WINE}">
    <animateMotion dur="9s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.45;1" calcMode="linear"><mpath href="#zzLine" /></animateMotion></circle>
</g>
"""
    path.write_text(insert_before_end(svg, extra + overlay(w, h)), encoding="utf-8")
    print("decorated activity.svg", "with line" if n else "without line")


def snake_card():
    raw = PROFILE / "snake-raw.svg"
    if not raw.exists():
        return
    svg = raw.read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', svg).group(1)
    sw, sh = size(svg)
    inner = svg[svg.index(">", svg.index("<svg")) + 1: svg.rfind("</svg>")]
    pad, top = 22, 74
    w, h = sw + pad * 2, sh + top + 18
    card = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Contribution snake">
<defs>
  <linearGradient id="snakeBg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fffaf5" /><stop offset="1" stop-color="#f9ebe1" /></linearGradient>
  <linearGradient id="snakeTitle" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w:.0f}" y2="0" spreadMethod="repeat">
    <stop offset="0" stop-color="{WINE}" /><stop offset="0.4" stop-color="{ROSE}" /><stop offset="0.5" stop-color="#f6c9cf" /><stop offset="0.6" stop-color="{ROSE}" /><stop offset="1" stop-color="{WINE}" />
    <animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="{w:.0f} 0" dur="5s" repeatCount="indefinite" />
  </linearGradient>
</defs>
<style>
  .zz-t {{ font: 700 22px Georgia, 'Times New Roman', serif; }}
  .zz-j {{ font: 400 13px 'Hiragino Mincho ProN', 'Yu Mincho', 'Noto Serif CJK JP', serif; letter-spacing: 6px; fill: {ROSE}; }}
  .zz-dot {{ animation: zzBlink 1.4s ease-in-out infinite; }}
  @keyframes zzBlink {{ 50% {{ opacity: 0.2; }} }}
</style>
<rect x="0.5" y="0.5" width="{w - 1:.0f}" height="{h - 1:.0f}" rx="12" fill="url(#snakeBg)" stroke="#eadbcd" />
<circle class="zz-dot" cx="{pad + 6}" cy="38" r="5" fill="{ROSE}" />
<text class="zz-t" x="{pad + 20}" y="45" fill="url(#snakeTitle)">Contribution Snake</text>
<text class="zz-j" x="{w - pad:.0f}" y="44" text-anchor="end">草を食べる蛇 · 365 days</text>
<svg x="{pad}" y="{top}" width="{sw:.0f}" height="{sh:.0f}" viewBox="{view}">{inner}</svg>
{overlay(w, h, prefix="zs")}</svg>
"""
    (PROFILE / "snake.svg").write_text(card, encoding="utf-8")
    print("wrote snake.svg")


if __name__ == "__main__":
    for card in ("stats.svg", "top-langs.svg", "pin-typewriter-nocturne.svg", "pin-yohaku.svg"):
        decorate_card(card)
    decorate_activity()
    snake_card()

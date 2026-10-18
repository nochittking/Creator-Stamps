# -*- coding: utf-8 -*-
"""大阪市24区 メイン画像（240×240）とタブ画像（96×74）の3案。

2026-10-18 ユーザーの指摘: 色分け地図だけのメイン画像は「何を伝えたいのかわからん」。
ストアの一覧で目に入るのはメイン画像だけなので、中身の売り（劇画の顔・しゃべる・24区）を入れる。

  A: いちばん強い1枚（大正区「大正解！」）をそのまま大きく
  B: 24区の色分け地図の真ん中に大きな劇画顔 ＋ 集中線 ＋「大阪市24区」の札
  C: 劇画顔の区を3体並べる ＋「大阪市24区」の札
  タブ: 大正区の形と顔のアップ（96×74 は字が読めないので顔だけ）

部品（形・顔・集中線）は generate_osaka_24ku_v2.py のものを使う。
"""
import html
import math
import pathlib

import generate_osaka_24ku_v2 as v2
from generate_osaka_24ku_v2 import (COLORS, DATA, FONT, FONT_LINK, INK, WARDS, area, bbox, face, path,
                                    pole, stamp_svg)

HERE = pathlib.Path(__file__).parent
OUT = HERE / "build" / "osaka_24ku_main"
M = 10           # メイン画像の外周の余白
COLOR_OF = {code: COLORS[i % len(COLORS)] for i, (code, _, _) in enumerate(WARDS)}
FACE_OF = {code: f for code, _, f in WARDS}


def head(w, h, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><style>@import url("{FONT_LINK}");</style>{extra}</defs>')


def fit(rings, box, align="center"):
    """box に収まるよう拡大縮小。align="bottom" は下にそろえる。"""
    x0, y0, x1, y1 = bbox(rings)
    bx0, by0, bx1, by1 = box
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
    if align == "bottom":
        oy = by1 - (y1 - y0) * s - y0 * s
    else:
        oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
    return s, ox, oy


def rings_of(code):
    return [[tuple(p) for p in r] for r in DATA[code]["rings"]]


def focus(cx, cy, r0, r1, n=40, opacity=0.35):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + (0.03 if i % 2 else 0)
        ra = r0 + (i * 37 % 20)
        w = 0.025 + (i * 13 % 7) * 0.003
        p1 = (cx + ra * math.cos(a), cy + ra * math.sin(a))
        p2 = (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w))
        p3 = (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))
        out.append(f"M{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} L{p3[0]:.1f},{p3[1]:.1f}Z")
    return f'<path d="{"".join(out)}" fill="#3B3540" opacity="{opacity}"/>'


def plate(text, x, y, size, anchor="start"):
    """黒い札に白い字。スタンプの区名の札と同じ見た目。"""
    w = size * len(text) * 0.98 + size * 0.7
    h = size * 1.42
    rx = {"start": x, "middle": x - w / 2}[anchor]
    return (f'<rect x="{rx:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{INK}"/>'
            f'<text x="{rx + w / 2:.1f}" y="{y + h * 0.76:.1f}" font-size="{size}" text-anchor="middle" '
            f'font-family="{FONT}" font-weight="800" fill="#fff">{html.escape(text)}</text>')


def frame_clip(uid, w, h, m):
    return f'<clipPath id="fr{uid}"><rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}"/></clipPath>'


def ward_with_face(code, box, stroke=4, rmax=None, align="center"):
    """区の形を box に置き、到達不能極に劇画の顔を描く。(svg, 顔の中心x, y) を返す。"""
    rs = rings_of(code)
    s, ox, oy = fit(rs, box, align)
    q = [[(x * s + ox, y * s + oy) for x, y in r] for r in rs]
    cx, cy, r = pole(max(q, key=area))
    bw = box[2] - box[0]
    r = max(bw * 0.24, min(r, rmax or bw * 0.42))
    k = r * 1.7 / 210
    d = path(q)
    svg = (f'<path d="{d}" fill="{COLOR_OF[code]}" stroke="{INK}" stroke-width="{stroke}" stroke-linejoin="round"/>'
           f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face(FACE_OF[code])}</g>')
    return svg, cx, cy


# ------------------------------------------------------------------ A
def main_a():
    """大正区のスタンプ（370×320）を 220 幅に縮めて真ん中に置く。"""
    i = next(n for n, (c, _, _) in enumerate(WARDS) if c == "27108")
    code, serif, f = WARDS[i]
    inner = stamp_svg(i, code, serif, f, mono=False)
    body = inner[inner.index(">") + 1: inner.rindex("</svg>")]
    k = (240 - 2 * M) / v2.W
    y = (240 - v2.H * k) / 2
    return head(240, 240) + f'<g transform="translate({M},{y:.1f}) scale({k:.4f})">{body}</g></svg>'


# ------------------------------------------------------------------ B
def city_layer(box, stroke=1.6):
    every = [p for c in DATA for r in DATA[c]["rings"] for p in r]
    s, ox, oy = fit([every], box)
    out = ""
    for c, u in DATA.items():
        d = "".join("M" + " L".join(f"{x * s + ox:.1f},{y * s + oy:.1f}" for x, y in r) + "Z" for r in u["rings"])
        out += f'<path d="{d}" fill="{COLOR_OF[c]}" stroke="{INK}" stroke-width="{stroke}" stroke-linejoin="round"/>'
    return out, s, ox, oy


def main_b():
    uid = "b"
    city, s, ox, oy = city_layer((M + 4, M + 2, 240 - M - 4, 240 - M - 34))
    # 顔の位置: 市全体の外形の到達不能極（全区の点をまとめた外接ではなく、市の真ん中寄り）
    cx, cy = 132, 112
    k = 0.62
    # 顔の後ろに白い光（色の境目で顔の線が埋もれないように）
    glow = (f'<radialGradient id="gl{uid}"><stop offset="0" stop-color="#fff" stop-opacity=".8"/>'
            f'<stop offset=".55" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
            f'</radialGradient>')
    return (head(240, 240, frame_clip(uid, 240, 240, M) + glow)
            + f'<g clip-path="url(#fr{uid})">{focus(cx, cy, 92, 260, n=44, opacity=.3)}</g>'
            + city
            + f'<ellipse cx="{cx}" cy="{cy + 8}" rx="78" ry="66" fill="url(#gl{uid})"/>'
            + f'<g transform="translate({cx},{cy}) scale({k})">{face("劇画スマイル")}</g>'
            + plate("大阪市24区", 120, 240 - M - 31, 19, "middle")
            + "</svg>")


# ------------------------------------------------------------------ C
# 枠どうしは少し重ねて、1体ずつを大きく見せる
C_TRIO = [("27108", (M + 2, M + 4, 98, 196)), ("27111", (80, M + 2, 164, 186)), ("27127", (146, M + 10, 240 - M - 2, 196))]


def main_c():
    uid = "c"
    out = head(240, 240, frame_clip(uid, 240, 240, M)) + f'<g clip-path="url(#fr{uid})">{focus(120, 110, 70, 260, n=44, opacity=.3)}</g>'
    for code, box in C_TRIO:
        svg, _, _ = ward_with_face(code, box, stroke=3.5, align="bottom")
        out += svg
    return out + plate("大阪市24区", 120, 240 - M - 36, 21, "middle") + "</svg>"


# ------------------------------------------------------------------ タブ
def tab_face():
    """大正区の形と顔だけ。96×74。"""
    rs = rings_of("27108")
    s, ox, oy = fit(rs, (4, 3, 92, 71))
    q = [[(x * s + ox, y * s + oy) for x, y in r] for r in rs]
    cx, cy, r = pole(max(q, key=area))
    k = max(r, 20) * 1.75 / 210
    return (head(96, 74)
            + f'<path d="{path(q)}" fill="{COLOR_OF["27108"]}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
            + f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face("劇画スマイル")}</g></svg>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {"main_A.svg": main_a(), "main_B.svg": main_b(), "main_C.svg": main_c(), "tab_face.svg": tab_face()}
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
    print("done:", ", ".join(files))


if __name__ == "__main__":
    main()

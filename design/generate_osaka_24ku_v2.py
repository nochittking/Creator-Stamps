# -*- coding: utf-8 -*-
"""大阪市24区 試作 v2 — 形をはっきり ＋ 劇画調の顔。

v1 への指摘（2026-10-02）
  1. 区名の札を見て初めて「24区の形か」と分かる程度に、形がぼんやりしている
  2. 顔がマイルドすぎてパンチがない。劇画調にしたい

1 の原因は v1 の作り方にあった。1%に簡素化済みのデータをさらに 5〜28点まで間引き、
角を丸め、細い区は横に太らせていた。似顔絵を描くのに写真をぼかして太らせたのと同じ。
  → 国土数値情報のほぼ元のままの輪郭（区ごと 200〜800点）を使い、
    誤差 1%（外接の長辺比）だけ間引く。丸めない・太らせない。島も残す（此花・住之江）。
  → 右上に大阪市の全体図を置き、その区だけ赤く塗る。形を知らない人にも一発で分かる。

2 は「劇画っぽい描き方」で作る。特定作品のキャラクターは真似しない。
  極太の吊りまゆ・三白眼・目の下の影・ほうれい線・食いしばった歯・カケアミ・集中線。
  セリフはゆるいまま。顔だけ真剣、のギャップで笑わせる。

色は 2 案を同時に出して比べる（ユーザー指定 C）。
  A: v1 の6色 ＋ 影の斜線
  B: 白黒 ＋ 網点（マンガのトーン）
"""
import html
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
DATA = json.loads((HERE / "data" / "osaka_24ku_detail.json").read_text(encoding="utf-8"))["units"]

W, H, MARGIN = 370, 320, 10
INK = "#1E1A1D"
RED = "#D8312A"
COLORS = ["#FFC65C", "#8FD3A8", "#FFB0A8", "#9CC8F0", "#C9B3F2", "#F7D98B"]
FONT = "'Shippori Mincho B1','Hiragino Mincho ProN',serif"
FONT_LINK = "https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@800&display=swap"

TEXT_BOX = (MARGIN + 10, MARGIN + 8, 186, 172)    # 左上。白フチ（字の 13%）が外周 10px に入らない位置
MAP_BOX = (W - MARGIN - 86, MARGIN + 4, W - MARGIN - 4, MARGIN + 92)
SHAPE_BOX = (60, 64, W - MARGIN - 8, H - MARGIN - 8)
# 全体図なし版。右上が空くぶん上へ広げる（左上の文字とは白フチ越しに重なってよい）
SHAPE_BOX_NOMAP = (60, 44, W - MARGIN - 8, H - MARGIN - 8)


# ------------------------------------------------------------------ 幾何
def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


def despike(p, min_deg=22):
    """運河・防波堤の細いトゲを落とす（此花・住之江で目立った）。"""
    p = list(p)
    changed = True
    while changed and len(p) > 4:
        changed = False
        for i in range(len(p)):
            a, b, c = p[i - 1], p[i], p[(i + 1) % len(p)]
            v1 = (a[0] - b[0], a[1] - b[1])
            v2 = (c[0] - b[0], c[1] - b[1])
            n = math.hypot(*v1) * math.hypot(*v2) or 1
            ang = math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / n))))
            if ang < min_deg:
                del p[i]
                changed = True
                break
    return p


def place(rings, box):
    x0, y0, x1, y1 = bbox(rings)
    bx0, by0, bx1, by1 = box
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
    oy = by1 - (y1 - y0) * s - y0 * s                    # 下にそろえる
    return [[(x * s + ox, y * s + oy) for x, y in r] for r in rings]


def hits_map(rings, pad=8):
    x0, y0, x1, y1 = MAP_BOX
    return any(x0 - pad < x < x1 + pad and y0 - pad < y < y1 + pad for r in rings for x, y in r)


def fit_shape(rings, with_map=True):
    """形を大きく置く。右上の全体図に当たるなら、全体図をよける箱のうち大きく置ける方を選ぶ。"""
    if not with_map:
        return place(rings, SHAPE_BOX_NOMAP)
    q = place(rings, SHAPE_BOX)
    if not hits_map(q):
        return q
    below = (SHAPE_BOX[0], MAP_BOX[3] + 10, SHAPE_BOX[2], SHAPE_BOX[3])     # 全体図の下
    left = (SHAPE_BOX[0], SHAPE_BOX[1], MAP_BOX[0] - 10, SHAPE_BOX[3])      # 全体図の左
    cands = [place(rings, b) for b in (below, left)]
    def size(rs):
        x0, y0, x1, y1 = bbox(rs)
        return (x1 - x0) * (y1 - y0)
    return max(cands, key=size)


def inside(x, y, p):
    c = False
    for i in range(len(p)):
        (x1, y1), (x2, y2) = p[i - 1], p[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def seg_dist(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def pole(p, n=48):
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    best = (0, 0, -1)
    for i in range(n + 1):
        for j in range(n + 1):
            x = min(xs) + (max(xs) - min(xs)) * i / n
            y = min(ys) + (max(ys) - min(ys)) * j / n
            if inside(x, y, p):
                d = min(seg_dist(x, y, p[k - 1], p[k]) for k in range(len(p)))
                if d > best[2]:
                    best = (x, y, d)
    return best


def path(rings):
    return "".join("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in r) + "Z" for r in rings)


# ------------------------------------------------------------------ 劇画の顔
# 顔の座標系: 中心 (0,0)、幅 ≒ 200。B（白黒）でも A（カラー）でも同じ線。
def S(d, w=7, color=INK, cap="round"):
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="{cap}" stroke-linejoin="round"/>')


def F(d, fill=INK):
    return f'<path d="{d}" fill="{fill}"/>'


def brows(kind):
    if kind == "down":       # 怒り・決意。中央へ鋭く下がる極太まゆ
        return F("M-98,-58 L-14,-30 L-10,-12 L-94,-36Z") + F("M98,-58 L14,-30 L10,-12 L94,-36Z")
    if kind == "up":         # 泣き・困り。中央が上がる
        return F("M-96,-30 L-16,-58 L-12,-42 L-92,-16Z") + F("M96,-30 L16,-58 L12,-42 L92,-16Z")
    return F("M-98,-46 L-14,-40 L-12,-24 L-94,-28Z") + F("M98,-46 L14,-40 L12,-24 L94,-28Z")


def eye(cx, kind, flip=1):
    """三白眼。白目を広く、黒目は小さく。"""
    if kind == "closed":
        return S(f"M{cx - 34},-6 q34,14 68,0", 8)
    if kind == "wide":       # 驚愕: 見開き、点のような黒目
        return (f'<ellipse cx="{cx}" cy="-4" rx="34" ry="22" fill="#fff" stroke="{INK}" stroke-width="7"/>'
                f'<circle cx="{cx}" cy="-4" r="5" fill="{INK}"/>')
    if kind == "half":       # ニヒル・疲労: まぶたが重い
        return (F(f"M{cx - 34},-2 Q{cx},-12 {cx + 34},-2 Q{cx},14 {cx - 34},-2Z", "#fff")
                + S(f"M{cx - 38},-6 Q{cx},-16 {cx + 38},-6", 10)
                + S(f"M{cx - 34},-2 Q{cx},14 {cx + 34},-2", 5)
                + f'<circle cx="{cx + 6 * flip}" cy="1" r="6" fill="{INK}"/>')
    # sharp: 吊り目
    return (F(f"M{cx - 36 * flip},4 Q{cx - 6 * flip},-20 {cx + 34 * flip},-6 Q{cx},14 {cx - 36 * flip},4Z", "#fff")
            + S(f"M{cx - 36 * flip},4 Q{cx - 6 * flip},-20 {cx + 34 * flip},-6", 8)
            + S(f"M{cx - 30 * flip},8 Q{cx},14 {cx + 30 * flip},0", 4)
            + f'<circle cx="{cx + 8 * flip}" cy="-2" r="6" fill="{INK}"/>')


def nose():
    return S("M4,-8 L12,34 q-8,8 -20,4", 5)


def creases():
    """ほうれい線と目の下の影。劇画らしさの大半はここ。"""
    return (S("M-58,26 q-14,34 -2,66", 5) + S("M58,26 q14,34 2,66", 5)
            + S("M-78,18 l26,8", 4) + S("M78,18 l-26,8", 4))


def mouth(kind):
    if kind == "grit":       # 食いしばった歯
        teeth = "".join(S(f"M{x},64 v22", 3) for x in (-24, -8, 8, 24))
        return (f'<rect x="-42" y="62" width="84" height="26" rx="3" fill="#fff" stroke="{INK}" stroke-width="6"/>'
                + S("M-42,75 h84", 3) + teeth)
    if kind == "shout":      # 怒号: 大きく開いた口に上下の歯
        return (F("M-50,52 L50,52 L34,108 L-34,108Z")
                + F("M-44,56 L44,56 L40,68 L-40,68Z", "#fff")
                + F("M-32,96 L32,96 L30,104 L-30,104Z", "#fff"))
    if kind == "smirk":
        return S("M-30,74 q30,4 54,-14", 7) + S("M24,60 l8,-4", 5)
    if kind == "smile":      # 劇画スマイル: 歯を見せて口角を上げる
        return (F("M-46,58 Q0,74 46,58 Q34,94 0,96 Q-34,94 -46,58Z", "#fff")
                + S("M-46,58 Q0,74 46,58 Q34,94 0,96 Q-34,94 -46,58Z", 6)
                + S("M-40,66 Q0,80 40,66", 3))
    if kind == "tremble":    # 漢泣き: 波打つ口
        return S("M-38,78 q10,-10 19,0 q10,10 19,0 q10,-10 19,0 q10,10 19,0", 6)
    if kind == "flat":
        return S("M-30,76 h60", 7)
    return S("M-24,74 q24,8 48,0", 7)


def tears():
    return (F("M-52,8 C-58,40 -66,70 -60,104 L-46,104 C-48,70 -44,40 -40,10Z", "#BFE6FF")
            + S("M-52,8 C-58,40 -66,70 -60,104", 3) + F("M52,8 C58,40 66,70 60,104 L46,104 C48,70 44,40 40,10Z", "#BFE6FF")
            + S("M52,8 C58,40 66,70 60,104", 3))


def sweat():
    return (F("M112,-60 C126,-34 132,-20 130,-8 a18,18 0 0 1 -34,-2 C98,-20 104,-36 112,-60Z", "#BFE6FF")
            + S("M112,-60 C126,-34 132,-20 130,-8 a18,18 0 0 1 -34,-2 C98,-20 104,-36 112,-60Z", 5))


def vein():
    return "".join(S(d, 7, RED) for d in ("M96,-96 q12,0 16,-14", "M126,-92 q0,12 14,16",
                                           "M122,-62 q-12,0 -16,14", "M92,-66 q0,-12 -14,-16"))


FACES = {
    # 名前: (まゆ, 目, 口, おまけ)
    "決意": ("down", "sharp", "grit", ""),
    "驚愕": ("up", "wide", "shout", "sweat"),
    "怒号": ("down", "sharp", "shout", "vein"),
    "ニヒル": ("flat", "half", "smirk", ""),
    "漢泣き": ("up", "closed", "tremble", "tears"),
    "渋い笑み": ("flat", "closed", "smile0", ""),
    "劇画スマイル": ("down", "sharp", "smile", ""),
    "疲労": ("up", "half", "flat", "sweat"),
}


def face(name):
    b, e, m, extra = FACES[name]
    s = brows(b) + eye(-50, e, 1) + eye(50, e, -1) + nose() + creases() + mouth(m)
    s += {"sweat": sweat(), "vein": vein(), "tears": tears(), "": ""}[extra]
    return s


# ------------------------------------------------------------------ 背景・トーン
def focus_lines(cx, cy, mono):
    """集中線。顔に向かって細くなる三角を放射状に並べる。"""
    color = INK if mono else "#3B3540"
    out = []
    n = 46
    for i in range(n):
        a = 2 * math.pi * i / n + (0.03 if i % 2 else 0)
        r0 = 150 + (i * 37 % 40)
        r1 = 460
        w = 0.022 + (i * 13 % 7) * 0.003
        p1 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
        p2 = (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w))
        p3 = (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))
        out.append(f"M{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} L{p3[0]:.1f},{p3[1]:.1f}Z")
    return f'<path d="{"".join(out)}" fill="{color}" opacity="{0.55 if mono else 0.35}"/>'


def defs(uid, mono):
    return (f'<pattern id="hatch{uid}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
            f'<line x1="0" y1="0" x2="0" y2="7" stroke="{INK}" stroke-width="{2.2 if mono else 1.8}"/></pattern>'
            f'<pattern id="tone{uid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<circle cx="3" cy="3" r="1.5" fill="{INK}"/></pattern>')


# ------------------------------------------------------------------ 部品
def citymap(target):
    allr = DATA
    every = [p for c in allr for r in allr[c]["rings"] for p in r]
    xs = [p[0] for p in every]
    ys = [p[1] for p in every]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    bx0, by0, bx1, by1 = MAP_BOX
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
    oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
    out = ""
    for c, u in allr.items():
        d = "".join("M" + " L".join(f"{x * s + ox:.1f},{y * s + oy:.1f}" for x, y in r) + "Z" for r in u["rings"])
        hit = c == target
        out += (f'<path d="{d}" fill="{RED if hit else "#fff"}" stroke="{INK}" '
                f'stroke-width="{1.4 if hit else 0.8}" stroke-linejoin="round"/>')
    return out


def text_block(serif):
    lines = serif.split("/")
    longest = max(len(l) for l in lines)
    x0, y0, x1, y1 = TEXT_BOX
    size = min(50, (x1 - x0) / longest, (y1 - y0) / len(lines) / 1.08)
    y = y0 + size * 0.92
    out = []
    for line in lines:
        out.append(f'<text x="{x0}" y="{y:.1f}" font-size="{size:.1f}" font-family="{FONT}" font-weight="800" '
                   f'fill="{INK}" stroke="#fff" stroke-width="{size * 0.26:.1f}" paint-order="stroke" '
                   f'stroke-linejoin="round">{html.escape(line)}</text>')
        y += size * 1.08
    return "".join(out)


def name_tag(name):
    w = 22 * len(name) + 14
    x, y = MARGIN + 4, H - MARGIN - 32
    return (f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="{INK}"/>'
            f'<text x="{x + w / 2}" y="{y + 22}" font-size="21" text-anchor="middle" font-family="{FONT}" '
            f'font-weight="800" fill="#fff">{html.escape(name)}</text>')


def face_layer(face_name, mode, cx, cy, k):
    if mode == "none":
        return ""
    if mode == "guide":
        # 自動配置の顔が占めていた範囲（顔の座標系で x ±105、y -70〜+110）
        return (f'<ellipse cx="{cx:.1f}" cy="{cy + 20 * k:.1f}" rx="{105 * k:.1f}" ry="{92 * k:.1f}" '
                f'fill="none" stroke="#6F6670" stroke-width="2" stroke-dasharray="5 5" opacity=".7"/>')
    return f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face(face_name)}</g>'


def stamp_svg(i, code, serif, face_name, mono, with_map=True, face_mode="face"):
    """face_mode: "face" 劇画の顔 ／ "none" 顔なし（手描き用） ／ "guide" 顔の位置にうすい点線の丸"""
    uid = f"{code}{'m' if mono else 'c'}"
    u = DATA[code]
    rings = fit_shape([[tuple(p) for p in r] for r in u["rings"]], with_map)
    main = max(rings, key=area)
    cx, cy, r = pole(main)
    # 本体が細い区（此花・住之江）は顔が豆粒になる。はみ出しても最低 36 は確保する
    r = max(36, min(r, 62))
    k = r * 1.7 / 210
    fill = "#FFFFFF" if mono else COLORS[i % len(COLORS)]
    d = path(rings)
    clip = f'<clipPath id="clip{uid}"><path d="{d}"/></clipPath>'
    # 影: 顔の右側から形の右端まで。B は網点、A は斜線
    shade_x = cx + r * 0.55
    shade = (f'<g clip-path="url(#clip{uid})">'
             f'<rect x="{shade_x:.1f}" y="0" width="{W}" height="{H}" fill="url(#{"tone" if mono else "hatch"}{uid})" '
             f'opacity="{0.55 if mono else 0.35}"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><style>@import url("{FONT_LINK}");</style>{defs(uid, mono)}{clip}'
            f'<clipPath id="frame{uid}"><rect x="{MARGIN + 1}" y="{MARGIN + 1}" width="{W - 2 * MARGIN - 2}" height="{H - 2 * MARGIN - 2}"/></clipPath></defs>'
            f'<g clip-path="url(#frame{uid})">{focus_lines(cx, cy, mono)}</g>'
            f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'{shade}'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'{face_layer(face_name, face_mode, cx, cy, k)}'
            f'{citymap(code) if with_map else ""}{text_block(serif)}{name_tag(u["name"])}</svg>')


# ------------------------------------------------------------------ 24区
WARDS = [
    ("27127", "梅田で/迷子/なう", "驚愕"),
    ("27128", "お城/あるけど/何か？", "ニヒル"),
    ("27109", "ごきげん/よう", "渋い笑み"),
    ("27119", "上には/上が/おるわ…", "漢泣き"),
    ("27111", "二度づけ/禁止！", "怒号"),
    ("27106", "忘れんと/いてや", "漢泣き"),
    ("27107", "ハードル/低めで/頼むわ", "疲労"),
    ("27108", "大正解！", "劇画スマイル"),
    ("27104", "ユニバ/行こ！", "劇画スマイル"),
    ("27103", "そっちの/福島/ちゃう！", "怒号"),
    ("27113", "元祖は/ウチ/やで", "ニヒル"),
    ("27123", "新大阪/着いた！", "劇画スマイル"),
    ("27114", "どの/淀川/やねん！", "怒号"),
    ("27115", "まかし/とき！", "決意"),
    ("27116", "焼肉/行こ！", "劇画スマイル"),
    ("27117", "おはよう/さん！", "劇画スマイル"),
    ("27118", "名前/だけ/やん！", "ニヒル"),
    ("27102", "住めば/都や/で", "渋い笑み"),
    ("27124", "鶴の/一声や！", "決意"),
    ("27125", "遠っ！", "驚愕"),
    ("27120", "済み/よし！", "劇画スマイル"),
    ("27121", "長居して/もうた", "疲労"),
    ("27126", "平に/ご容赦/を…", "漢泣き"),
    ("27122", "天下/取ったる！", "決意"),
]


MODES = {
    "A_color": dict(mono=False, with_map=True),
    "A_color_nomap": dict(mono=False, with_map=False),   # 2026-10-02 全体図あり／なしの比較用
    "B_mono": dict(mono=True, with_map=True),
    # 2026-10-02 ユーザーが劇画の顔を手描きで足すための下絵（全体図あり・カラー）
    "A_color_noface": dict(mono=False, with_map=True, face_mode="none"),
    "A_color_noface_guide": dict(mono=False, with_map=True, face_mode="guide"),
}


def main(only=None):
    for sub, opt in MODES.items():
        out = HERE / "build" / "osaka_24ku_v2" / sub
        out.mkdir(parents=True, exist_ok=True)
        for i, (code, serif, face_name) in enumerate(WARDS):
            if only and code not in only:
                continue
            name = f"{i + 1:02d}_{DATA[code]['name']}_{serif.replace('/', '')}.svg"
            (out / name).write_text(stamp_svg(i, code, serif, face_name, **opt), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main(sys.argv[1:] or None)

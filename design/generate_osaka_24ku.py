# -*- coding: utf-8 -*-
"""大阪市24区 試作 v1 — 区の形キャラ × 区ネタの関西弁 24個のラフ。

輪郭: design/data/osaka_72_outlines.json
  国土数値情報（行政区域）国土交通省 を smartnews-smri/japan-topography が簡素化したもの。
  CC BY 4.0（出典を書けば商用可）。

大阪府くん（generate_osaka_kun.py）との違い
  - 区ごとに形がまったく違うので、顔の位置を手で決められない。
    → 形の中で「縁からいちばん遠い点」（到達不能極）を格子探索で求め、そこに顔を置く。
      顔の大きさもその点から縁までの距離で決める。
  - 細長い区（此花・住之江など）は顔が入らない。
    → 内接円が小さすぎるときは、その向きに直交して太らせる（府くんの「横 1.22 倍」と同じ考え方）。
  - 24体を同じ黄色にすると並べたとき区別がつかない → 6色を順に回す。
  - 区名は小さな札でキャラの足もとに置く。セットの目的は「自分の区が載っている」ことなので省略しない。
"""
import html
import json
import math
import pathlib

from generate_osaka_kun import FACES, INK, CHEEK, ACCENT, SKY, stroke, sparkle, heart, drop, FONT, FONT_LINK

HERE = pathlib.Path(__file__).parent
DATA = json.loads((HERE / "data" / "osaka_72_outlines.json").read_text(encoding="utf-8"))["units"]
OUT_DIR = HERE / "build" / "osaka_24ku"

W, H, MARGIN = 370, 320, 10
TEXT_W = 140                     # 左の文字の列。150 では中央区・福島区でキャラに触れた
BOX = (178, 38, 346, 272)        # キャラを収める箱。丸めで線が外へふくらむので外周に 14px 以上逃がす
COLORS = ["#FFC65C", "#8FD3A8", "#FFB0A8", "#9CC8F0", "#C9B3F2", "#F7D98B"]


# ------------------------------------------------------------------ 形の幾何
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


def pole(p, n=60):
    """到達不能極（縁からいちばん遠い内点）と、その距離。"""
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


def catmull(p, t=0.42):     # 0.5 だと西区の先が外へふくらみ外周 10px に入った
    n = len(p)
    d = f"M{p[0][0]:.1f},{p[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = p[i - 1], p[i], p[(i + 1) % n], p[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + "Z"


def despike(p, min_deg=35):
    """細いトゲ（内角が min_deg 未満の頂点）を落とす。北区の中之島の先がムチに見えた。"""
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


def fit(pts):
    """箱に収め、顔の中心と半径を返す。顔が小さすぎるときは太らせて作り直す。"""
    p = despike([tuple(q) for q in pts])
    for _ in range(4):
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        s = min((BOX[2] - BOX[0]) / bw, (BOX[3] - BOX[1]) / bh)
        ox = BOX[0] + ((BOX[2] - BOX[0]) - bw * s) / 2 - min(xs) * s
        oy = BOX[3] - bh * s - min(ys) * s             # 下にそろえる
        q = [(x * s + ox, y * s + oy) for x, y in p]
        cx, cy, r = pole(q)
        if r >= 40:
            break
        # 細い向きに太らせる: 箱の縦横比より細長い向きを 1.25 倍
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        if bw / bh < (BOX[2] - BOX[0]) / (BOX[3] - BOX[1]):
            p = [((x - mx) * 1.25 + mx, y) for x, y in p]
        else:
            p = [(x, (y - my) * 1.25 + my) for x, y in p]
    return q, cx, cy, r


# ------------------------------------------------------------------ 小物（スタンプ座標）
def sun(x, y):
    rays = "".join(stroke(f"M{x + 22 * math.cos(a):.1f},{y + 22 * math.sin(a):.1f} "
                          f"L{x + 32 * math.cos(a):.1f},{y + 32 * math.sin(a):.1f}", 4)
                   for a in [i * math.pi / 4 for i in range(8)])
    return rays + f'<circle cx="{x}" cy="{y}" r="15" fill="#FFB347" stroke="{INK}" stroke-width="4"/>'


def small(f, x, y, s=0.45):
    return f'<g transform="translate({x},{y}) scale({s}) translate({-x},{-y})">{f(x, y)}</g>'


PROPS = {
    "sweat": lambda cx, cy, r: drop(cx + r * 1.05, cy - r * 0.6, 0.45),
    "sparkle": lambda cx, cy, r: small(sparkle, cx + r * 1.1, cy - r * 0.9) + small(sparkle, cx + r * 0.7, cy - r * 1.4, 0.3),
    "heart": lambda cx, cy, r: small(heart, cx + r * 1.1, cy - r * 0.9, 0.5),
    "sun": lambda cx, cy, r: sun(min(cx + r * 1.15, W - 46), max(cy - r * 1.2, 46)),
    "": lambda cx, cy, r: "",
}

# ------------------------------------------------------------------ 24区
# (コード, セリフ（/ で改行）, 表情, 小物, ネタの元)
WARDS = [
    ("27127", "梅田で/迷子/なう", "surprise", "sweat", "梅田ダンジョン。遅刻の連絡に"),
    ("27128", "お城/あるけど/何か？", "proud", "sparkle", "大阪城。ドヤりたいときに"),
    ("27109", "ごきげん/よう", "smile", "sparkle", "上品・文教地区のイメージ。かしこまった挨拶に"),
    ("27119", "上には/上が/おるわ…", "sad", "", "ハルカスは元日本一（2023年に麻布台ヒルズに抜かれた）"),
    ("27111", "二度づけ/禁止！", "angry", "", "新世界の串カツ。「同じこと二度言わすな」"),
    ("27106", "忘れんと/いてや", "sad", "", "24区で影が薄い。既読スルーされたときに"),
    ("27107", "ハードル/低めで/頼むわ", "tired", "sweat", "天保山（4.53m）。期待されすぎたときに"),
    ("27108", "大正解！", "smile", "sparkle", "区名のダジャレ"),
    ("27104", "ユニバ/行こ！", "wink", "heart", "USJ。遊びの誘いに"),
    ("27103", "そっちの/福島/ちゃう！", "shout", "", "福島県と間違われる。「誤解や」"),
    ("27113", "元祖は/ウチ/やで", "proud", "", "東京の佃島は西淀川の佃村の漁師が開いた"),
    ("27123", "新大阪/着いた！", "smile", "", "新大阪駅。到着の連絡に"),
    ("27114", "どの/淀川/やねん！", "shout", "", "淀川区・東淀川区・西淀川区。ツッコミ全般に"),
    ("27115", "まかし/とき！", "proud", "sparkle", "町工場の町。頼まれたときに"),
    ("27116", "焼肉/行こ！", "wink", "", "鶴橋。ごはんの誘いに"),
    ("27117", "おはよう/さん！", "smile", "sun", "旭＝朝日のダジャレ。朝の挨拶に"),
    ("27118", "名前/だけ/やん！", "sly", "", "城東区に城はない（大阪城は中央区）。名前負けへのツッコミ"),
    ("27102", "住めば/都や/で", "smile", "", "区名のダジャレ。なぐさめに"),
    ("27124", "鶴の/一声や！", "proud", "", "区名のダジャレ。決めるときに"),
    ("27125", "遠っ！", "tired", "sweat", "南港・インテックス大阪。遠いもの全般に"),
    ("27120", "済み/よし！", "wink", "sparkle", "すみよし＝済み、よし。完了の報告に"),
    ("27121", "長居して/もうた", "tired", "sweat", "長居公園。帰りぎわに"),
    ("27126", "平に/ご容赦/を…", "sad", "sweat", "区名のダジャレ。謝るときに"),
    ("27122", "天下/取ったる！", "angry", "sparkle", "天下茶屋。気合いを入れるときに"),
]


def face_group(face, cx, cy, r):
    # 顔は (408,320) 中心・幅約 180 の座標系。ほおは顔に含める。
    k = r * 1.75 / 180
    body = (f'<ellipse cx="335" cy="352" rx="22" ry="13" fill="{CHEEK}" opacity=".75"/>'
            f'<ellipse cx="482" cy="352" rx="22" ry="13" fill="{CHEEK}" opacity=".75"/>' + FACES[face])
    return f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f}) translate(-408,-325)">{body}</g>'


def text_block(serif):
    lines = serif.split("/")
    longest = max(len(l) for l in lines)
    size = min(44, TEXT_W / longest, 215 / len(lines) / 1.12)
    y = MARGIN + 12 + size * 0.95
    out = []
    for line in lines:
        out.append(f'<text x="{MARGIN + 7}" y="{y:.1f}" font-size="{size:.1f}" font-family="{FONT}" '
                   f'fill="{INK}" stroke="#fff" stroke-width="{size * 0.22:.1f}" paint-order="stroke" '
                   f'stroke-linejoin="round">{html.escape(line)}</text>')
        y += size * 1.12
    return "".join(out)


def name_tag(name, x, y):
    w = 17 * len(name) + 16
    x = min(max(x - w / 2, BOX[0] - 30), W - MARGIN - 2 - w)
    return (f'<rect x="{x:.1f}" y="{y}" width="{w}" height="24" rx="12" fill="{INK}"/>'
            f'<text x="{x + w / 2:.1f}" y="{y + 17.5}" font-size="16" text-anchor="middle" '
            f'font-family="{FONT}" fill="#fff">{html.escape(name)}</text>')


def stamp_svg(i, code, serif, face, prop):
    unit = DATA[code]
    q, cx, cy, r = fit(unit["pts"])
    color = COLORS[i % len(COLORS)]
    ward = unit["name"].replace("大阪市", "")
    xs = [p[0] for p in q]
    body = (f'<path d="{catmull(q)}" fill="{color}" stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>'
            + face_group(face, cx, cy, min(r, 60)) + PROPS[prop](cx, cy, min(r, 60)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><style>@import url("{FONT_LINK}");</style></defs>'
            f'{body}{text_block(serif)}'
            f'{name_tag(ward, (min(xs) + max(xs)) / 2, H - MARGIN - 26)}</svg>')


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, (code, serif, face, prop, _) in enumerate(WARDS):
        ward = DATA[code]["name"].replace("大阪市", "")
        name = f"{i + 1:02d}_{ward}_{serif.replace('/', '')}.svg"
        (OUT_DIR / name).write_text(stamp_svg(i, code, serif, face, prop), encoding="utf-8")
    print(f"{len(WARDS)} stamps → {OUT_DIR}")


if __name__ == "__main__":
    main()

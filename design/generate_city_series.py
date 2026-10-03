# -*- coding: utf-8 -*-
"""全国30シリーズ 叩き台の作図（2026-10-03）。

大阪市24区 v2（劇画・カラー・全体図あり）の部品をそのまま使い、シリーズごとに描く。
  セリフ: series_data.py
  輪郭:   data/series/<id>.json（build_series_geo.py で作る）
  出力:   build/series/<地方>/<順位>_<id>/NN_<名前>_<セリフ>.svg

大阪との違い
  - 区をまとめて1体にする場合（千葉県の千葉市、浜松市の新しい区）がある。
    輪郭を「線の層 → 塗りの層」の順に描き、内側の境目の線を塗りで隠す
  - 全体キャラ（市・県のすべてを合わせた形）も同じ方法で描く
  - 全体図は離島を除いた範囲で描き、その離島自体がスタンプのときだけ範囲を広げる

使い方
  python3 generate_city_series.py            # 30シリーズすべて
  python3 generate_city_series.py tokyo23    # 指定したシリーズだけ
"""
import html
import json
import math
import pathlib
import re
import sys

from generate_osaka_24ku_v2 import (
    COLORS, H, INK, MAP_BOX, MARGIN, RED, SHAPE_BOX, W, FONT_LINK,
    area, bbox, defs, face, focus_lines, name_tag, place, pole, text_block,
)
from series_data import REGIONS, SERIES

HERE = pathlib.Path(__file__).parent
OUT = HERE / "build" / "series"


def region_dir(s):
    return f"{REGIONS.index(s['region']) + 1}_{s['region']}"


def series_dir(s):
    return f"{s['rank']:02d}_{s['id']}"


# ------------------------------------------------------------------ 配置
def hits_map(rings, pad=8):
    x0, y0, x1, y1 = MAP_BOX
    return any(x0 - pad < x < x1 + pad and y0 - pad < y < y1 + pad for r in rings for x, y in r)


def place_right(rings, box):
    """place と同じ大きさで、横は右寄せ。細長い形が左のセリフにかぶるのを避ける（神戸・東灘区）。"""
    q = place(rings, box)
    x1 = max(x for r in q for x, _ in r)
    dx = box[2] - x1
    return [[(x + dx, y) for x, y in r] for r in q]


def fit_shape(rings, serif, whole=False):
    """候補の置き方から「大きく描ける」かつ「セリフにかぶらない」ものを点数で選ぶ。
    v1 は大きさだけで選んでいたため、全体図をよけた結果セリフにかぶることがあった（神戸・東灘区）。"""
    tx0, ty0, tx1, ty1 = text_rect(serif)
    boxes = [
        SHAPE_BOX,
        (SHAPE_BOX[0], ty1 + 6, SHAPE_BOX[2], SHAPE_BOX[3]),               # セリフの下
        (SHAPE_BOX[0], MAP_BOX[3] + 10, SHAPE_BOX[2], SHAPE_BOX[3]),       # 全体図の下
        (SHAPE_BOX[0], SHAPE_BOX[1], MAP_BOX[0] - 10, SHAPE_BOX[3]),       # 全体図の左
        (tx1 + 6, SHAPE_BOX[1], MAP_BOX[0] - 10, SHAPE_BOX[3]),            # セリフと全体図の間
    ]
    best, best_score = None, -1
    for b in boxes:
        if b[2] - b[0] < 60 or b[3] - b[1] < 60:
            continue
        q = place_right(rings, b)
        if hits_map(q):
            continue
        x0, y0, x1, y1 = bbox(q)
        size = (x1 - x0) * (y1 - y0)
        ox = max(0, min(x1, tx1) - max(x0, tx0)) * max(0, min(y1, ty1) - max(y0, ty0))
        score = size * max(0.05, 1 - 2.5 * ox / size)   # かぶり1割で25%減点（0.9倍では東灘区が直らなかった）
        if not whole:
            # 形はかぶらなくても顔がセリフの横に来ることがある（東灘区は北側が広い）。顔のかぶりも減点
            fx, fy, fr = face_spot(q, False, serif)
            fo = (max(0, min(fx + fr, tx1) - max(fx - fr, tx0)) *
                  max(0, min(fy + fr, ty1) - max(fy - fr, ty0))) / (4 * fr * fr)
            score *= max(0.05, 1 - 3 * fo)
        if score > best_score:
            best, best_score = q, score
    return best or place(rings, SHAPE_BOX)


def inside_any(x, y, rings):
    for p in rings:
        c = False
        for i in range(len(p)):
            (x1, y1), (x2, y2) = p[i - 1], p[i]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        if c:
            return True
    return False


def landmass(rings):
    """いちばん大きい輪と、それに地続き（外接枠が接する）の輪だけを残す。"""
    rings = sorted(rings, key=area, reverse=True)
    x0, y0, x1, y1 = bbox(rings)
    pad = max(x1 - x0, y1 - y0) * 0.004
    keep, rest = [rings[0]], rings[1:]
    grown = True
    while grown:
        grown = False
        for r in list(rest):
            rx0, ry0, rx1, ry1 = bbox([r])
            for k in keep:
                kx0, ky0, kx1, ky1 = bbox([k])
                if rx0 - pad <= kx1 and kx0 - pad <= rx1 and ry0 - pad <= ky1 and ky0 - pad <= ry1:
                    if any(min(abs(px - qx) + abs(py - qy) for qx, qy in k) < pad * 3 for px, py in r[::3]):
                        keep.append(r)
                        rest.remove(r)
                        grown = True
                        break
    return keep


def text_rect(serif):
    """左上のセリフが占める範囲（generate_osaka_24ku_v2.text_block と同じ計算）。"""
    from generate_osaka_24ku_v2 import TEXT_BOX
    lines = serif.split("/")
    longest = max(len(l) for l in lines)
    x0, y0, x1, y1 = TEXT_BOX
    size = min(50, (x1 - x0) / longest, (y1 - y0) / len(lines) / 1.08)
    return (x0 - 4, y0 - 4, x0 + longest * size + 4, y0 + len(lines) * size * 1.08 + 4)


def pole_avoid(p, avoid, n=40):
    """到達不能極。ただし顔の円がセリフの範囲にかかる点は、半径を削って評価する。"""
    from generate_osaka_24ku_v2 import seg_dist
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    ax0, ay0, ax1, ay1 = avoid
    best = (0, 0, -1, -1)
    for i in range(n + 1):
        for j in range(n + 1):
            x = min(xs) + (max(xs) - min(xs)) * i / n
            y = min(ys) + (max(ys) - min(ys)) * j / n
            if not inside_any(x, y, [p]):
                continue
            d = min(seg_dist(x, y, p[k - 1], p[k]) for k in range(len(p)))
            # セリフの範囲までの距離（範囲の中なら 0）
            dx = max(ax0 - x, 0, x - ax1)
            dy = max(ay0 - y, 0, y - ay1)
            score = min(d, max(math.hypot(dx, dy) - 6, 0) * 1.2 + d * 0.15)
            if score > best[3]:
                best = (x, y, d, score)
    return best[0], best[1], best[2]


def face_spot(rings, whole, serif):
    """顔の中心と半径。セリフの文字と重ならない場所を選ぶ。"""
    avoid = text_rect(serif)
    if whole:
        x0, y0, x1, y1 = bbox(rings)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rr = min(58, (x1 - x0) / 3.2, (y1 - y0) / 3.2)
        clear = cx - rr > avoid[2] or cy - rr > avoid[3]
        if inside_any(cx, cy, rings) and clear:
            return cx, cy, rr
        # 細長い全体キャラ（川崎市）は、いちばん広い場所が取れる輪を選ぶ
        cands = [pole_avoid(r, avoid) for r in sorted(rings, key=area, reverse=True)[:6]]
        cx, cy, r = max(cands, key=lambda t: t[2])
        return cx, cy, max(48, min(r, 62))
    cx, cy, r = pole_avoid(max(rings, key=area), avoid)
    return cx, cy, max(36, min(r, 62))


# ------------------------------------------------------------------ 部品
def series_map(geo, highlight):
    """右上の全体図。highlight の区市町村を赤く塗る。"""
    feats = geo["map"]
    x0, y0, x1, y1 = geo["map_bbox"]
    hit = [r for c in highlight if c in feats for r in feats[c]]
    arrow = None
    if hit:
        hx0, hy0, hx1, hy1 = bbox(hit)
        ex0, ey0, ex1, ey1 = min(x0, hx0), min(y0, hy0), max(x1, hx1), max(y1, hy1)
        if (ex1 - ex0) <= (x1 - x0) * 1.6 and (ey1 - ey0) <= (y1 - y0) * 1.6:
            x0, y0, x1, y1 = ex0, ey0, ex1, ey1   # 少し広げれば入るなら広げる
        elif not (x0 <= (hx0 + hx1) / 2 <= x1 and y0 <= (hy0 + hy1) / 2 <= y1):
            arrow = ((hx0 + hx1) / 2, (hy0 + hy1) / 2)   # 遠い離島は本土の地図に矢印で示す
    bx0, by0, bx1, by1 = MAP_BOX
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
    oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
    hs = set(highlight)
    out = []
    for c, rs in feats.items():
        pts = [(x * s + ox, y * s + oy) for r in rs for x, y in r]
        if not any(bx0 - 6 <= x <= bx1 + 6 and by0 - 6 <= y <= by1 + 6 for x, y in pts):
            continue                              # 範囲外の離島は描かない
        d = "".join("M" + " L".join(f"{x * s + ox:.1f},{y * s + oy:.1f}" for x, y in r) + "Z" for r in rs)
        on = c in hs
        out.append((on, f'<path d="{d}" fill="{RED if on else "#fff"}" stroke="{INK}" '
                        f'stroke-width="{1.2 if on else 0.6}" stroke-linejoin="round"/>'))
    out.sort(key=lambda t: t[0])                  # 赤を上に
    if arrow:
        import math
        mcx, mcy = (bx0 + bx1) / 2, (by0 + by1) / 2
        tx, ty = arrow[0] * s + ox, arrow[1] * s + oy
        ang = math.atan2(ty - mcy, tx - mcx)
        # 地図の枠の上で、離島の方向にある点に矢印を置く
        rx, ry = (bx1 - bx0) / 2, (by1 - by0) / 2
        t = min(rx / abs(math.cos(ang)) if math.cos(ang) else 1e9, ry / abs(math.sin(ang)) if math.sin(ang) else 1e9)
        px, py = mcx + math.cos(ang) * (t - 9), mcy + math.sin(ang) * (t - 9)
        c, sn = math.cos(ang), math.sin(ang)
        pts = [(px + 10 * c, py + 10 * sn), (px - 6 * c - 7 * sn, py - 6 * sn + 7 * c), (px - 6 * c + 7 * sn, py - 6 * sn - 7 * c)]
        out.append((True, f'<path d="M{pts[0][0]:.1f},{pts[0][1]:.1f} L{pts[1][0]:.1f},{pts[1][1]:.1f} '
                          f'L{pts[2][0]:.1f},{pts[2][1]:.1f}Z" fill="{RED}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>'))
    clip = (f'<clipPath id="mapclip"><rect x="{bx0 - 4}" y="{by0 - 4}" '
            f'width="{bx1 - bx0 + 8}" height="{by1 - by0 + 8}"/></clipPath>')
    return f'<defs>{clip}</defs><g clip-path="url(#mapclip)">{"".join(p for _, p in out)}</g>'


def ring_path(rings):
    return "".join("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in r) + "Z" for r in rings)


def stamp_svg(i, s, geo, item, with_map=True):
    whole = item["codes"] is None
    if whole:
        # 県の全体キャラは本土だけで形を作る（長崎県で顔が対馬に乗った）
        main = set(geo.get("map_main") or [])
        parts = [r for u, g in zip(s["units"], geo["units"])
                 if not main or any(c in main for c in u["codes"]) for r in g]
        if s["kind"] == "pref":
            parts = landmass(parts)               # 五島・壱岐も外し、いちばん大きい陸地だけに
        highlight = [c for u in s["units"] for c in u["codes"]]
        label = s["name"]
    else:
        idx = next(j for j, u in enumerate(s["units"]) if u is item)
        parts = geo["units"][idx]
        highlight = item["codes"]
        label = item["label"]
    # 区をまとめた1体（埼玉県のさいたま市など）も、全体キャラと同じく全体の真ん中に顔を置く
    merged = whole or len(item["codes"]) > 1
    rings = fit_shape([[tuple(p) for p in r] for r in parts], item["serif"], merged)
    cx, cy, r = face_spot(rings, merged, item["serif"])
    k = r * 1.7 / 210
    uid = f"u{i}"
    fill = COLORS[i % len(COLORS)]
    d = ring_path(rings)
    shade_x = cx + r * 0.55
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><style>@import url("{FONT_LINK}");</style>{defs(uid, False)}'
            f'<clipPath id="clip{uid}"><path d="{d}"/></clipPath>'
            f'<clipPath id="frame{uid}"><rect x="{MARGIN + 1}" y="{MARGIN + 1}" width="{W - 2 * MARGIN - 2}" '
            f'height="{H - 2 * MARGIN - 2}"/></clipPath></defs>'
            f'<g clip-path="url(#frame{uid})">{focus_lines(cx, cy, False)}</g>'
            # 線の層 → 塗りの層。内側の境目は塗りで隠れ、外周だけ 6px の線が残る
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<g clip-path="url(#clip{uid})"><rect x="{shade_x:.1f}" y="0" width="{W}" height="{H}" '
            f'fill="url(#hatch{uid})" opacity="0.35"/></g>'
            f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face(item["face"])}</g>'
            f'{series_map(geo, highlight) if with_map else ""}'
            f'{text_block(item["serif"])}{name_tag(label)}</svg>')


def overview_svg(s, geo, w, h, label=True):
    """main.png（240x240）と tab.png（96x74）用の色分け地図。シリーズのユニットをスタンプと同じ色で塗る。"""
    feats = geo["map"]
    color = {}
    for i, u in enumerate(s["units"]):
        for c in u["codes"]:
            color[c] = COLORS[i % len(COLORS)]
    x0, y0, x1, y1 = geo["map_bbox"]
    pad = 6 if w < 120 else 12
    bottom = 34 if label else 0
    bx0, by0, bx1, by1 = pad, pad, w - pad, h - pad - bottom
    sc = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * sc) / 2 - x0 * sc
    oy = by0 + ((by1 - by0) - (y1 - y0) * sc) / 2 - y0 * sc
    sw = 0.8 if w < 120 else 1.4
    paths = []
    for c, rs in feats.items():
        pts = [(x * sc + ox, y * sc + oy) for r in rs for x, y in r]
        if not any(bx0 - 4 <= x <= bx1 + 4 and by0 - 4 <= y <= by1 + 4 for x, y in pts):
            continue
        d = "".join("M" + " L".join(f"{x * sc + ox:.1f},{y * sc + oy:.1f}" for x, y in r) + "Z" for r in rs)
        paths.append(f'<path d="{d}" fill="{color.get(c, "#FFFFFF")}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    title = ""
    if label:
        title = (f'<text x="{w / 2}" y="{h - pad - 8}" font-size="25" text-anchor="middle" font-family="\'Shippori Mincho B1\',serif" '
                 f'font-weight="800" fill="{INK}" stroke="#fff" stroke-width="6" paint-order="stroke">{html.escape(s["name"])}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><style>@import url("{FONT_LINK}");</style>'
            f'<clipPath id="ov"><rect x="{pad - 2}" y="{pad - 2}" width="{w - 2 * pad + 4}" height="{h - 2 * pad + 4}"/></clipPath></defs>'
            f'<g clip-path="url(#ov)">{"".join(paths)}</g>{title}</svg>')


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "", name)


def build(s):
    geo = json.loads((HERE / "data" / "series" / f"{s['id']}.json").read_text(encoding="utf-8"))
    out = OUT / region_dir(s) / series_dir(s)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        old.unlink()
    items = s["units"] + s.get("extras", [])
    for i, item in enumerate(items):
        label = item["label"] or s["name"]
        name = safe(f"{i + 1:02d}_{label}_{item['serif'].replace('/', '')}.svg")
        (out / name).write_text(stamp_svg(i, s, geo, item), encoding="utf-8")
    # 申請に要る一覧画像とタブ画像（全体図をここで大きく使う）
    (out / "main.svg").write_text(overview_svg(s, geo, 240, 240), encoding="utf-8")
    (out / "tab.svg").write_text(overview_svg(s, geo, 96, 74, label=False), encoding="utf-8")
    return out, len(items)


def main(ids):
    for s in SERIES:
        if ids and s["id"] not in ids:
            continue
        out, n = build(s)
        print(f"{s['name']:<8} {n:>2} → {out.relative_to(HERE)}")


if __name__ == "__main__":
    main(sys.argv[1:])

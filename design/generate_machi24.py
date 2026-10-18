# -*- coding: utf-8 -*-
"""わが街スタンプ 近畿（兵庫・滋賀・奈良・和歌山）24個の作図（2026-10-18）。

generate_kyoto24.py を県ごとの設定（machi24_data.AREAS）で動くようにしたもの。
京都編は申請済みなので generate_kyoto24.py はそのまま残す。

使い方
  python3 build_machi24_geo.py --geo <dir> --pref <dir>   # data/machi24_<id>.json（初回だけ）
  python3 generate_machi24.py [id ...]                     # build/machi24/<id>/
  node render_png.js build/machi24/<id> build/machi24_png/<id>
"""
import json
import math
import pathlib
import re
import sys

import html

import generate_city_series as cs
from generate_city_series import face_spot, fit_shape, inside_any, ring_path
from generate_osaka_24ku_v2 import (COLORS, FONT, FONT_LINK, H, INK, MAP_BOX, MARGIN, W, area, bbox, defs, face,
                                    focus_lines, name_tag)
from machi24_data import AREAS, PREF

HERE = pathlib.Path(__file__).parent
OUT = HERE / "build" / "machi24"
# セリフの文字（2026-10-18 ユーザー指示: スタンプはパッと見のインパクト。イラストにかぶってよいので大きくそろえる）
# 大阪の TEXT_BOX（横166px）だと5文字で33px、6文字で27pxまで縮んでいた。
# 箱を右上の全体図の手前まで広げ、全セリフを同じ大きさにする。1行5文字（半角は0.55）まで
TEXT_BOX = (MARGIN + 10, MARGIN + 8, MAP_BOX[0] - 4, H - MARGIN - 40)
TEXT_SIZE = 45
LAKE = "#3F9AD8"   # 琵琶湖の青。区・市町村の6色の青（#9CC8F0）と見分けられるよう濃くした（#7CC4EC では大津市で区別がつかなかった）


def _w(line):
    return sum(0.55 if ord(ch) < 128 else 1 for ch in line)


def text_size(serif):
    lines = serif.replace("！", "!").split("/")
    x0, y0, x1, y1 = TEXT_BOX
    return min(TEXT_SIZE, (x1 - x0) / max(_w(l) for l in lines), (y1 - y0) / len(lines) / 1.08)


def text_rect(serif):
    """セリフが占める範囲。顔はここをよける（形はかぶってよい）。"""
    lines = serif.replace("！", "!").split("/")
    size = text_size(serif)
    x0, y0, _, _ = TEXT_BOX
    return (x0 - 4, y0 - 4, x0 + max(_w(l) for l in lines) * size + 4, y0 + len(lines) * size * 1.08 + 4)


def text_block(serif):
    """大阪の text_block と同じ見た目（白フチの明朝）。大きさは全セリフで TEXT_SIZE にそろえる。"""
    lines = serif.replace("！", "!").split("/")   # 全角「！」は斜めに見えるデザインなので半角に（大阪と同じ）
    size = text_size(serif)
    x0, y0, _, _ = TEXT_BOX
    out, y = [], y0 + size * 0.92
    for line in lines:
        out.append(f'<text x="{x0}" y="{y:.1f}" font-size="{size:.1f}" font-family="{FONT}" font-weight="800" '
                   f'fill="{INK}" stroke="#fff" stroke-width="{size * 0.26:.1f}" paint-order="stroke" '
                   f'stroke-linejoin="round">{html.escape(line)}</text>')
        y += size * 1.08
    return "".join(out)


# 形の置き方は大阪と同じ狭いセリフ範囲で決め（形はセリフにかぶってよい）、顔の位置だけ広げた範囲をよける。
# 最初は両方とも広げた範囲でよけたが、形が小さく端へ追いやられ、滋賀県くんが画像の端に触れた
NARROW_TEXT_RECT = cs.text_rect


class Area:
    def __init__(self, a):
        self.a = a
        self.geo = json.loads((HERE / "data" / f"machi24_{a['id']}.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------ 形
    def whole_rings(self):
        """県くんの形。市町村ごとに間引いた輪は境目が少しずれるので、面積の小さい輪（島）だけ落とす（京都編と同じ）。"""
        rs = [[tuple(p) for p in r] for r in self.geo["whole"]]
        top = max(area(r) for r in rs)
        return [r for r in rs if area(r) >= top * 0.01]

    def face_point(self, raw):
        """県くんの顔の位置（元の座標）。face_at の市町村の中心、なければ外接枠の真ん中。"""
        at = self.a["face_at"]
        if at:
            big = max(self.geo["pref_map"][at], key=area)
            return sum(x for x, _ in big) / len(big), sum(y for _, y in big) / len(big)
        x0, y0, x1, y1 = bbox(raw)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def whole_face(self, raw, placed, r=44):
        rx0, ry0, rx1, _ = bbox(raw)
        px0, py0, px1, _ = bbox(placed)
        s = (px1 - px0) / (rx1 - rx0)
        mx, my = self.face_point(raw)
        cx, cy = px0 + (mx - rx0) * s, py0 + (my - ry0) * s
        # 大きい顔（滋賀県くん r=70）が形の外へ出すぎないよう、外接枠の内側に寄せる
        _, _, _, py1 = bbox(placed)
        cx = min(max(cx, px0 + r * 0.8), px1 - r * 0.8)
        cy = min(max(cy, py0 + r * 0.8), py1 - r * 0.8)
        return cx, cy, r

    @staticmethod
    def drop_holes(rings):
        """本体の内側にある小さい輪は描かない。外の島は残す。"""
        main = max(rings, key=area)
        out = [main]
        for r in rings:
            if r is main:
                continue
            cx = sum(x for x, _ in r) / len(r)
            cy = sum(y for _, y in r) / len(r)
            if not inside_any(cx, cy, [main]):
                out.append(r)
        return out

    @staticmethod
    def mapper(raw, placed):
        """元の座標 → 置いた座標。fit_shape は縦横同じ倍率で縮めて動かすだけなので、外接枠どうしで決まる。"""
        rx0, ry0, rx1, _ = bbox(raw)
        px0, py0, px1, _ = bbox(placed)
        s = (px1 - px0) / (rx1 - rx0)
        return lambda x, y: (px0 + (x - rx0) * s, py0 + (y - ry0) * s)

    def lake_path(self, f):
        """湖（滋賀の琵琶湖）の path。行政区域では湖の上もまわりの市町に含まれているので、上から塗る。"""
        lake = self.geo.get("lake")
        if not lake:
            return ""
        return "".join("M" + " L".join("{:.1f},{:.1f}".format(*f(x, y)) for x, y in r) + "Z" for r in lake)

    def map_layer(self, kind, highlight):
        out = cs.series_map({"map": self.geo[f"{kind}_map"], "map_bbox": self.geo[f"{kind}_bbox"]}, highlight)
        if kind != "pref" or not self.geo.get("lake"):
            return out
        # series_map と同じ倍率で湖を重ねる（湖の上の赤を消し、町が湖のどちら側か分かるように）
        x0, y0, x1, y1 = self.geo["pref_bbox"]
        bx0, by0, bx1, by1 = MAP_BOX
        s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
        ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
        oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
        d = self.lake_path(lambda x, y: (x * s + ox, y * s + oy))
        return out + f'<path d="{d}" fill="{LAKE}" stroke="{INK}" stroke-width="0.8" stroke-linejoin="round"/>'

    def label(self, code):
        return self.a["name"] if code == PREF else self.geo["units"][code]["name"]

    # ------------------------------------------------------------ スタンプ
    def stamp_svg(self, i, code, serif, face_name):
        whole = code == PREF
        if whole:
            parts = self.whole_rings()
            kind, highlight = "pref", list(self.geo["pref_map"])
        else:
            parts = self.drop_holes([[tuple(p) for p in r] for r in self.geo["units"][code]["rings"]])
            kind = "city" if code in self.a["city_wards"] else "pref"
            highlight = [code]
        cs.text_rect = NARROW_TEXT_RECT
        rings = fit_shape(parts, serif, whole)
        cs.text_rect = text_rect
        # 湖を描くのは県くんだけ。市町は build_machi24_geo.py で湖をくり抜いた陸だけの形になっている
        lake = self.lake_path(self.mapper(parts, rings)) if whole else ""
        cx, cy, r = face_spot(rings, whole, serif)
        if whole:
            cx, cy, r = self.whole_face(parts, rings, self.a.get("whole_face_r", 44))
        k = r * 1.7 / 210
        uid = f"m{i}"
        fill = COLORS[i % len(COLORS)]
        d = ring_path(rings)
        shade_x = cx + r * 0.55
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                f'<defs><style>@import url("{FONT_LINK}");</style>{defs(uid, False)}'
                f'<clipPath id="clip{uid}"><path d="{d}"/></clipPath>'
                f'<clipPath id="frame{uid}"><rect x="{MARGIN + 1}" y="{MARGIN + 1}" width="{W - 2 * MARGIN - 2}" '
                f'height="{H - 2 * MARGIN - 2}"/></clipPath></defs>'
                f'<g clip-path="url(#frame{uid})">{focus_lines(cx, cy, False)}</g>'
                # 線の層 → 塗りの層。県くんは市町村の境目が塗りで隠れ、外周だけ線が残る
                f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>'
                f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width="2.5" stroke-linejoin="round"/>'
                f'<g clip-path="url(#clip{uid})"><rect x="{shade_x:.1f}" y="0" width="{W}" height="{H}" '
                f'fill="url(#hatch{uid})" opacity="0.35"/></g>'
                + (f'<g clip-path="url(#clip{uid})"><path d="{lake}" fill="{LAKE}" stroke="{INK}" stroke-width="3" '
                   f'stroke-linejoin="round"/></g>' if lake else "")
                + f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face(face_name)}</g>'
                f'{self.map_layer(kind, highlight)}{text_block(serif)}{name_tag(self.label(code))}</svg>')

    # ------------------------------------------------------------ メイン・タブ（大阪 B 案の型）
    def main_svg(self):
        m = 10
        feats, (x0, y0, x1, y1) = self.geo["pref_map"], self.geo["pref_bbox"]
        bx0, by0, bx1, by1 = m + 4, m + 2, 240 - m - 4, 240 - m - 34
        s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
        ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
        oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
        col = {}
        for i, (code, *_) in enumerate(self.a["items"]):
            if code != PREF and code not in col:
                col[code] = COLORS[i % len(COLORS)]
        rest = [c for c in feats if c not in col]
        for j, c in enumerate(rest):
            col[c] = COLORS[(j * 5 + 2) % len(COLORS)]
        paths = ""
        for c, rs in feats.items():
            dd = "".join("M" + " L".join(f"{x * s + ox:.1f},{y * s + oy:.1f}" for x, y in r) + "Z" for r in rs)
            paths += f'<path d="{dd}" fill="{col[c]}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round"/>'
        if self.geo.get("lake"):
            dl = self.lake_path(lambda x, y: (x * s + ox, y * s + oy))
            paths += f'<path d="{dl}" fill="{LAKE}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
        fx, fy = self.face_point(self.whole_rings())
        if self.geo.get("lake"):
            # 琵琶湖を顔で隠さない。湖の東の端より右へ
            lx1 = max(x for ring in self.geo["lake"] for x, _ in ring)
            fx = max(fx, lx1 + 40 / s)
        cx = min(max(fx * s + ox, 70), 170)
        cy = min(max(fy * s + oy, 70), 150)
        plate = self.a["plate"]
        size = 19
        pw = size * len(plate) + 20
        glow = ('<radialGradient id="gl"><stop offset="0" stop-color="#fff" stop-opacity=".8"/>'
                '<stop offset=".55" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
                '</radialGradient>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">'
                f'<defs><style>@import url("{FONT_LINK}");</style>{glow}'
                f'<clipPath id="fr"><rect x="{m}" y="{m}" width="{240 - 2 * m}" height="{240 - 2 * m}"/></clipPath></defs>'
                f'<g clip-path="url(#fr)">{focus_rays(cx, cy)}</g>{paths}'
                f'<ellipse cx="{cx:.1f}" cy="{cy + 6:.1f}" rx="64" ry="54" fill="url(#gl)"/>'
                f'<g transform="translate({cx:.1f},{cy:.1f}) scale(0.5)">{face("劇画スマイル")}</g>'
                f'<rect x="{120 - pw / 2}" y="{240 - m - 31}" width="{pw}" height="28" fill="{INK}"/>'
                f'<text x="120" y="{240 - m - 10}" font-size="{size}" text-anchor="middle" font-family="{FONT}" '
                f'font-weight="800" fill="#fff">{plate}</text></svg>')

    def tab_svg(self):
        rs = self.whole_rings()
        x0, y0, x1, y1 = bbox(rs)
        s = min(88 / (x1 - x0), 68 / (y1 - y0))
        ox = 4 + (88 - (x1 - x0) * s) / 2 - x0 * s
        oy = 3 + (68 - (y1 - y0) * s) / 2 - y0 * s
        q = [[(x * s + ox, y * s + oy) for x, y in r] for r in rs]
        d = ring_path(q)
        fx, fy, _ = self.whole_face(rs, q, r=10)   # タブは小さいので寄せ幅も小さく（44 だと顔が形の外へ出た）
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="74" viewBox="0 0 96 74">'
                f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="{d}" fill="{COLORS[0]}" stroke="{COLORS[0]}" stroke-width="1.2" stroke-linejoin="round"/>'
                + (f'<path d="{self.lake_path(self.mapper(rs, q))}" fill="{LAKE}" stroke="{INK}" stroke-width="1.2" '
                   f'stroke-linejoin="round"/>' if self.geo.get("lake") else "")
                + f'<g transform="translate({fx:.1f},{fy:.1f}) scale(0.19)">{face("劇画スマイル")}</g></svg>')

    def build(self):
        out = OUT / self.a["id"]
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.svg"):
            old.unlink()
        for i, (code, serif, face_name, _) in enumerate(self.a["items"]):
            name = re.sub(r'[\\/:*?"<>|]', "", f"{i + 1:02d}_{self.label(code)}_{serif.replace('/', '')}.svg")
            (out / name).write_text(self.stamp_svg(i, code, serif, face_name), encoding="utf-8")
        (out / "main.svg").write_text(self.main_svg(), encoding="utf-8")
        (out / "tab.svg").write_text(self.tab_svg(), encoding="utf-8")
        print(f"{self.a['label']:<6} {len(self.a['items'])} stamps + main + tab → {out.relative_to(HERE)}")


def focus_rays(cx, cy, r0=92, r1=260, n=44):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + (0.03 if i % 2 else 0)
        ra = r0 + (i * 37 % 20)
        w = 0.025 + (i * 13 % 7) * 0.003
        p = [(cx + ra * math.cos(a), cy + ra * math.sin(a)),
             (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)),
             (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))]
        out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p) + "Z")
    return f'<path d="{"".join(out)}" fill="#3B3540" opacity=".3"/>'


def main(ids):
    for a in AREAS:
        if not ids or a["id"] in ids:
            assert len(a["items"]) == 24, f"{a['id']}: {len(a['items'])} 個"
            Area(a).build()


if __name__ == "__main__":
    main(sys.argv[1:])

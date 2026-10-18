# -*- coding: utf-8 -*-
"""わが街スタンプ 京都編 24個 試作（2026-10-18）。

ユーザー決定: 24個（16個では寂しい）。1つの区・市に1枚でなくてよい。京都編としてバランスよく。
  京都市の11区   15枚（全区1枚以上。ネタの濃い東山・伏見・左京・中京は2枚）
  京都府の市      6枚（宇治・宮津・舞鶴・亀岡・福知山・長岡京）
  京都府くん      3枚（府の形の全体キャラ。誰でも使える京言葉）
ネタの根拠と線引きは docs/11-kyoto-24.md。

作図は大阪市24区 v2・全国30シリーズと同じ部品。違いは右上の全体図が2種類あること
  区 → 京都市の地図 ／ 府の市と京都府くん → 京都府の地図

使い方
  python3 build_kyoto24_geo.py --geo <dir> --pref <dir>   # data/kyoto24.json（初回だけ）
  python3 generate_kyoto24.py                              # build/kyoto24/
"""
import html
import json
import math
import pathlib
import re

import generate_city_series as cs
from generate_city_series import face_spot, fit_shape, ring_path
from generate_osaka_24ku_v2 import (COLORS, FONT, FONT_LINK, H, INK, MARGIN, W, defs, face, focus_lines,
                                    name_tag, text_block)

HERE = pathlib.Path(__file__).parent
GEO = json.loads((HERE / "data" / "kyoto24.json").read_text(encoding="utf-8"))
OUT = HERE / "build" / "kyoto24"
PREF = "京都府"

# (コード or PREF, セリフ, 顔, ネタの元)  並びはアップロード順。ふだん使いを前に、知っている人向けを後ろに
ITEMS = [
    (PREF, "おおきに", "劇画スマイル", "京言葉の「ありがとう」"),
    ("26106", "京都駅/着き/ました", "疲労", "京都駅は下京区"),
    ("26204", "お茶/しよ！", "劇画スマイル", "宇治茶"),
    ("26109", "一杯/いこか", "決意", "伏見は酒どころ"),
    (PREF, "考えとき/ます", "渋い笑み", "京都の遠回しな断り"),
    ("26107", "弘法にも/筆の/誤り", "漢泣き", "東寺（教王護国寺）は空海＝弘法大師ゆかり。南区"),
    ("26109", "神頼み/しとこ", "疲労", "伏見稲荷大社"),
    ("26104", "謹んで/お返し/します", "決意", "二条城で大政奉還。中京区"),
    ("26105", "清水の/舞台から/飛び降りる！", "決意", "清水寺。東山区"),
    ("26103", "右も左も/わからへん", "驚愕", "左京区は地図では右側（南向きの天皇から見た左）"),
    ("26108", "どっちが/右やねん！", "怒号", "右京区は地図では左側"),
    ("26205", "見方を/変えて/みよう", "ニヒル", "天橋立の股のぞき。宮津は丹後弁（断定「だ」）なので京言葉にしない"),
    ("26206", "敵は/本能寺に/あり！", "怒号", "明智光秀は亀山城（亀岡）から本能寺へ。言葉は後世の軍記物とされる"),
    ("26105", "一見さん/お断り/どす", "ニヒル", "祇園のお茶屋。東山区"),
    (PREF, "ぶぶ漬け/どうどす？", "ニヒル", "「そろそろお帰り」の定番ネタ"),
    ("26110", "京都やで/一応", "渋い笑み", "洛中・洛外ネタ。山科が自分で言う自虐"),
    ("26104", "食べ歩き/しよか", "劇画スマイル", "錦市場。中京区"),
    ("26103", "ちょっと/哲学して/くるわ", "渋い笑み", "哲学の道。左京区"),
    ("26101", "金ピカ/やろ？", "ニヒル", "金閣寺（鹿苑寺）。北区"),
    ("26102", "上品に/いきまひょ", "渋い笑み", "京都御所・西陣。上京区"),
    ("26111", "竹を割った/ような/性格や", "決意", "大原野のたけのこ・洛西竹林公園。西京区"),
    ("26202", "今夜は/肉じゃが/や！", "劇画スマイル", "舞鶴は肉じゃが発祥の地を名乗る。舞鶴弁は断定「や」"),
    ("26201", "光秀は/ええ人/やねん", "漢泣き", "福知山城を築いた光秀は地元で名君として慕われる"),
    ("26209", "都やった/時代も/あんねん", "漢泣き", "長岡京は784〜794年の都"),
]


def whole_rings():
    """京都府くんの形。市町村ごとに間引いた輪は境目が少しずれるので、landmass（地続き判定）だと
    丹後半島まで「離れ島」として落ちた。島は小さいので面積で落とすだけにする。"""
    from generate_osaka_24ku_v2 import area
    rs = [[tuple(p) for p in r] for r in GEO["whole"]]
    top = max(area(r) for r in rs)
    return [r for r in rs if area(r) >= top * 0.01]


def whole_face(raw, placed):
    """京都府くんの顔は府のいちばん太いところ（南丹市）に置く。斜めに長い形なので、
    外接枠の真ん中や到達不能極だと顔が形の外にはみ出した。"""
    from generate_osaka_24ku_v2 import area, bbox
    rx0, ry0, rx1, _ = bbox(raw)
    px0, py0, px1, _ = bbox(placed)
    s = (px1 - px0) / (rx1 - rx0)
    nantan = max(GEO["pref_map"]["26213"], key=area)
    mx = sum(x for x, _ in nantan) / len(nantan)
    my = sum(y for _, y in nantan) / len(nantan)
    return px0 + (mx - rx0) * s, py0 + (my - ry0) * s, 44


def drop_holes(rings):
    """本体の内側にある小さい輪（舞鶴市で形の中に線が出た）は描かない。外の島は残す。"""
    from generate_city_series import inside_any
    from generate_osaka_24ku_v2 import area
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


def map_layer(kind, highlight):
    geo = {"map": GEO[f"{kind}_map"], "map_bbox": GEO[f"{kind}_bbox"]}
    return cs.series_map(geo, highlight)


def stamp_svg(i, code, serif, face_name):
    whole = code == PREF
    if whole:
        parts = whole_rings()
        kind, highlight, label = "pref", list(GEO["pref_map"]), PREF
    else:
        u = GEO["units"][code]
        parts = drop_holes([[tuple(p) for p in r] for r in u["rings"]])
        kind = "city" if code.startswith("261") else "pref"
        highlight, label = [code], u["name"]
    rings = fit_shape(parts, serif, whole)
    cx, cy, r = face_spot(rings, whole, serif)
    if whole:
        cx, cy, r = whole_face(parts, rings)
    k = r * 1.7 / 210
    uid = f"k{i}"
    fill = COLORS[i % len(COLORS)]
    d = ring_path(rings)
    shade_x = cx + r * 0.55
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><style>@import url("{FONT_LINK}");</style>{defs(uid, False)}'
            f'<clipPath id="clip{uid}"><path d="{d}"/></clipPath>'
            f'<clipPath id="frame{uid}"><rect x="{MARGIN + 1}" y="{MARGIN + 1}" width="{W - 2 * MARGIN - 2}" '
            f'height="{H - 2 * MARGIN - 2}"/></clipPath></defs>'
            f'<g clip-path="url(#frame{uid})">{focus_lines(cx, cy, False)}</g>'
            # 線の層 → 塗りの層。京都府くんは市町村の境目が塗りで隠れ、外周だけ線が残る
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<g clip-path="url(#clip{uid})"><rect x="{shade_x:.1f}" y="0" width="{W}" height="{H}" '
            f'fill="url(#hatch{uid})" opacity="0.35"/></g>'
            f'<g transform="translate({cx:.1f},{cy:.1f}) scale({k:.3f})">{face(face_name)}</g>'
            f'{map_layer(kind, highlight)}{text_block(serif)}{name_tag(label)}</svg>')


# ------------------------------------------------------------------ メイン・タブ（大阪の B 案と同じ型）
def color_of():
    """府の地図で、スタンプに出る区・市をスタンプと同じ色で塗る（最初に出た色）。"""
    out = {}
    for i, (code, _, _, _) in enumerate(ITEMS):
        if code != PREF and code not in out:
            out[code] = COLORS[i % len(COLORS)]
    return out


def main_svg():
    m = 10
    feats, (x0, y0, x1, y1) = GEO["pref_map"], GEO["pref_bbox"]
    bx0, by0, bx1, by1 = m + 4, m + 2, 240 - m - 4, 240 - m - 34
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
    oy = by0 + ((by1 - by0) - (y1 - y0) * s) / 2 - y0 * s
    col = color_of()
    # スタンプに出ない町村も色を付ける（白いままだと地図が抜けて見えた）。隣と同じ色が続かないよう順番に回す
    rest = [c for c in feats if c not in col]
    for j, c in enumerate(rest):
        col[c] = COLORS[(j * 5 + 2) % len(COLORS)]
    paths = ""
    for c, rs in feats.items():
        dd = "".join("M" + " L".join(f"{x * s + ox:.1f},{y * s + oy:.1f}" for x, y in r) + "Z" for r in rs)
        paths += (f'<path d="{dd}" fill="{col.get(c, "#FFFFFF")}" stroke="{INK}" stroke-width="1.2" '
                  f'stroke-linejoin="round"/>')
    # 顔は府の真ん中あたり（丹波）。京都市の上にかぶせると区の色が隠れる
    cx, cy, k = 118, 112, 0.5
    plate_w, plate_h, size = 150, 28, 19
    glow = ('<radialGradient id="gl"><stop offset="0" stop-color="#fff" stop-opacity=".8"/>'
            '<stop offset=".55" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
            '</radialGradient>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">'
            f'<defs><style>@import url("{FONT_LINK}");</style>{glow}'
            f'<clipPath id="fr"><rect x="{m}" y="{m}" width="{240 - 2 * m}" height="{240 - 2 * m}"/></clipPath></defs>'
            f'<g clip-path="url(#fr)">{focus_rays(cx, cy)}</g>{paths}'
            f'<ellipse cx="{cx}" cy="{cy + 6}" rx="64" ry="54" fill="url(#gl)"/>'
            f'<g transform="translate({cx},{cy}) scale({k})">{face("劇画スマイル")}</g>'
            f'<rect x="{120 - plate_w / 2}" y="{240 - m - plate_h - 3}" width="{plate_w}" height="{plate_h}" fill="{INK}"/>'
            f'<text x="120" y="{240 - m - 10}" font-size="{size}" text-anchor="middle" font-family="{FONT}" '
            f'font-weight="800" fill="#fff">京都府・京都市</text></svg>')


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


def tab_svg():
    """京都府くんの形と顔のアップ。"""
    rs = whole_rings()
    xs = [x for r in rs for x, _ in r]
    ys = [y for r in rs for _, y in r]
    s = min(88 / (max(xs) - min(xs)), 68 / (max(ys) - min(ys)))
    ox = 4 + (88 - (max(xs) - min(xs)) * s) / 2 - min(xs) * s
    oy = 3 + (68 - (max(ys) - min(ys)) * s) / 2 - min(ys) * s
    q = [[(x * s + ox, y * s + oy) for x, y in r] for r in rs]
    d = ring_path(q)
    fx, fy, _ = whole_face(rs, q)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="74" viewBox="0 0 96 74">'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="{COLORS[0]}" stroke="{COLORS[0]}" stroke-width="1.2" stroke-linejoin="round"/>'
            f'<g transform="translate({fx:.1f},{fy:.1f}) scale(0.19)">{face("劇画スマイル")}</g></svg>')


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "", name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for i, (code, serif, face_name, _) in enumerate(ITEMS):
        label = PREF if code == PREF else GEO["units"][code]["name"]
        name = safe(f"{i + 1:02d}_{label}_{serif.replace('/', '')}.svg")
        (OUT / name).write_text(stamp_svg(i, code, serif, face_name), encoding="utf-8")
    (OUT / "main.svg").write_text(main_svg(), encoding="utf-8")
    (OUT / "tab.svg").write_text(tab_svg(), encoding="utf-8")
    print(f"{len(ITEMS)} stamps + main + tab → {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()

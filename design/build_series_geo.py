# -*- coding: utf-8 -*-
"""全国30シリーズの輪郭データを作る（design/data/series/<id>.json）。

入力（ネットから取得して手元に置いたもの）
  --geo   国土数値情報（行政区域）を区市町村ごとに GeoJSON 化したもの
          https://github.com/niiyz/JapanCityGeoJson （geojson/<県>/<コード>.json）
  --pref  同じく都道府県ごとに簡素化したもの（全体図用）
          https://github.com/smartnews-smri/japan-topography （N03-21_<県>_210101.json）
どちらも CC BY 4.0。

大阪市24区 v2 で分かったことを最初から入れている
  - 島はデータ上「1つの多角形の別の輪」で入っていることがある → すべての輪を読む
  - 本体の 2% 未満の小島は捨てる（370px では点にしかならない）
  - 誤差 1%（外接の長辺比）で間引き、内角 22° 未満のトゲを落とす
  - 区をまとめて1体にする場合（千葉県の中の千葉市など）は、境目が合うよう誤差を 0.4% にする

使い方
  python3 build_series_geo.py --geo <dir> --pref <dir>
"""
import argparse
import json
import math
import pathlib

from series_data import SERIES

HERE = pathlib.Path(__file__).parent
OUT = HERE / "data" / "series"


def area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


def dp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0, 0
    for i, (x, y) in enumerate(pts[1:-1], 1):
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return dp(pts[:idx + 1], eps)[:-1] + dp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def simplify(ring, eps):
    r = ring[:-1] if ring[0] == ring[-1] else ring
    if len(r) < 4:
        return r
    far = max(range(len(r)), key=lambda i: (r[i][0] - r[0][0]) ** 2 + (r[i][1] - r[0][1]) ** 2)
    return dp(r[:far + 1], eps)[:-1] + dp(r[far:] + [r[0]], eps)[:-1]


def despike(p, min_deg=22):
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


def rings_of(geom, k):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    out = []
    for poly in polys:
        for r in poly:                      # 島が別の輪として入っていることがある
            out.append([(x * k, -y) for x, y in r])
    return out


def span(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def unit_rings(codes, geo_dir, k, keep=0.02):
    raw = []
    for c in codes:
        d = json.loads((geo_dir / f"{c}.json").read_text(encoding="utf-8"))
        for ft in d["features"]:
            raw += rings_of(ft["geometry"], k)
    raw = [r for r in raw if len(r) >= 4]
    raw.sort(key=area, reverse=True)
    big = area(raw[0])
    raw = [r for r in raw if area(r) >= big * keep]
    eps = span(raw) * (0.004 if len(codes) > 1 else 0.01)
    out = []
    for r in raw:
        s = despike(simplify(r, eps))
        if len(s) >= 4:
            out.append([[round(x, 6), round(y, 6)] for x, y in s])
    return out


def map_features(series, pref_dir, k):
    d = json.loads((pref_dir / f"N03-21_{series['pref']}_210101.json").read_text(encoding="utf-8"))
    member = {c for u in series["units"] for c in u["codes"]}
    feats = {}
    for ft in d["features"]:
        c = ft["properties"]["N03_007"]
        if not c:
            continue
        if series["kind"] == "ward" and c not in member:
            continue                        # 区のシリーズは市の中だけを描く
        feats.setdefault(c, []).extend(rings_of(ft["geometry"], k))
    # 遠く離れた島（東京の伊豆・小笠原、鹿児島の奄美など）が範囲に入ると本土が潰れる。
    # 中心からの距離が中央値の 3.5 倍を超える区市町村は「離島」として範囲の計算から外す。
    cen = {}
    for c, rs in feats.items():
        big = max(rs, key=area)
        cen[c] = (sum(p[0] for p in big) / len(big), sum(p[1] for p in big) / len(big))
    # 中央値の中心だと、離島の市町村が多い県（鹿児島は奄美だけで12）で判定が崩れた。
    # → シリーズ先頭（県庁所在地など）から測る
    head = series["units"][0]["codes"][0]
    mx, my = cen.get(head, next(iter(cen.values())))
    dist = {c: math.hypot(v[0] - mx, v[1] - my) for c, v in cen.items()}
    # 近い順に並べ、距離が 1.6 倍以上かつ 0.25 度以上跳ねたところ（海を渡る切れ目）で切る
    # 切れ目の判定はシリーズに入っている区市町村だけで行う（入っていない十島村が範囲を引っぱった）
    ds = sorted(v for c, v in dist.items() if c in member) or sorted(dist.values())
    cut = ds[-1]
    for a_, b_ in zip(ds, ds[1:]):
        if a_ > 0 and b_ > a_ * 1.6 and b_ - a_ > 0.25:
            cut = a_
            break
    main = [c for c in feats if dist[c] <= cut]
    mainr = [r for c in main for r in feats[c]]
    eps = span(mainr) * 0.004
    # 範囲は各区市町村の大きな輪だけで決める（福岡市西区の小呂島のような沖の小島で地図が縮んだ）
    bigr = []
    for c in main:
        top = max(area(r) for r in feats[c])
        bigr += [r for r in feats[c] if area(r) >= top * 0.05]
    xs = [p[0] for r in bigr for p in r]
    ys = [p[1] for r in bigr for p in r]
    main_bbox = [min(xs), min(ys), max(xs), max(ys)]
    out = {}
    for c, rs in feats.items():
        keep = []
        for r in rs:
            if len(r) < 4:
                continue
            s = simplify(r, eps)
            if len(s) >= 3:
                keep.append([[round(x, 5), round(y, 5)] for x, y in s])
        if keep:
            out[c] = keep
    return out, main_bbox, sorted(main)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--pref", required=True)
    a = ap.parse_args()
    geo_dir, pref_dir = pathlib.Path(a.geo), pathlib.Path(a.pref)
    OUT.mkdir(parents=True, exist_ok=True)
    for s in SERIES:
        # 緯度は県の代表値で十分（形の縦横比を保つため）
        sample = json.loads((geo_dir / f"{s['units'][0]['codes'][0]}.json").read_text(encoding="utf-8"))
        g = sample["features"][0]["geometry"]
        first = (g["coordinates"][0][0] if g["type"] == "Polygon" else g["coordinates"][0][0][0])
        k = math.cos(math.radians(first[1]))
        units = [unit_rings(u["codes"], geo_dir, k) for u in s["units"]]
        data = {
            "source": "国土数値情報（行政区域）国土交通省（CC BY 4.0）を niiyz/JapanCityGeoJson・smartnews-smri/japan-topography 経由で加工",
            "projection": f"x=経度×{k:.5f}, y=-緯度",
            "units": units,
        }
        # map_main: 離島を除いた「本土」の区市町村。全体キャラの形にも使う
        data["map"], data["map_bbox"], data["map_main"] = map_features(s, pref_dir, k)
        (OUT / f"{s['id']}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{s['id']:<14} units {len(units):>2}  pts {sum(len(r) for u in units for r in u):>5}  map {len(data['map'])}")


if __name__ == "__main__":
    main()

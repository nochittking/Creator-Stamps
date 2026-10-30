# -*- coding: utf-8 -*-
"""わが街スタンプ 全国編の輪郭データを作る（design/data/machi24_<id>.json）。

近畿（build_machi24_geo.py）を全国の設定（national24_data.AREAS）で動くように広げたもの。
出力の形は近畿と同じなので、作図は generate_machi24.py がそのまま使える。

近畿との違い
  ・地方編（東北編など）は「県まるごと」が1キャラ。県の形は市町村をつないで作る（shapely）
  ・セリフのキーは名前で書く（「函館市」「横浜市」「青森県」「札幌市中央区」）。ここでコードに直す
    政令市の名前（「横浜市」）は区をまとめた1キャラになる
  ・政令市が2つある県（神奈川・福岡・静岡）は、区ごとにその市の地図を右上に出す
  ・23区・多摩・横浜市・札幌市のように、県の一部だけで地図を作る（map_prefix）
  ・遠い島（東京の小笠原・鹿児島の奄美・沖縄の先島）は地図の範囲から外す。沖縄は九州の近くへずらして描く

入力
  --geo   niiyz/JapanCityGeoJson の geojson/<県>/<コード>.json を置くディレクトリ（なければ取ってくる）
  --pref  smartnews-smri/japan-topography の N03-21_<県>_210101.json を置いたディレクトリ
どちらも国土数値情報（行政区域）国土交通省、CC BY 4.0

使い方
  python3 build_national24_geo.py --geo <dir> --pref <dir> [id ...]
"""
import argparse
import json
import math
import pathlib
import subprocess

from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

from build_series_geo import map_features, unit_rings
from national24_data import AREAS, PREF

HERE = pathlib.Path(__file__).parent
NIIYZ = "https://raw.githubusercontent.com/niiyz/JapanCityGeoJson/master/geojson/{p}/{c}.json"


def load_pref(pref_dir, p):
    return json.loads((pref_dir / f"N03-21_{p}_210101.json").read_text(encoding="utf-8"))["features"]


def index(feats):
    """名前 → コードの表。区は「札幌市中央区」でも「中央区」でも引ける（県内で一つなら）。政令市名は区の全コード。"""
    by_name, short = {}, {}
    names = {}
    for ft in feats:
        p = ft["properties"]
        c = p["N03_007"]
        if not c:
            continue
        city, ward = p.get("N03_003") or "", p["N03_004"] or ""
        names[c] = ward
        if ward.endswith("区") and city.endswith("市"):
            by_name.setdefault(city + ward, set()).add(c)
            short.setdefault(ward, set()).add(c)
            by_name.setdefault(city, set()).add(c)          # 政令市名 → 区の全コード
        else:
            by_name.setdefault(ward, set()).add(c)
    for k, v in short.items():
        if k not in by_name and len(v) == 1:
            by_name[k] = v
    return by_name, names


def polys_of(geom):
    g = shape(geom).buffer(0)
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def proj(poly, k, shift=(0, 0)):
    dx, dy = shift
    return [[round(x * k + dx, 6), round(-y + dy, 6)] for x, y in list(poly.exterior.coords)[:-1]]


def keep_parts(parts, min_ratio=0.015, max_deg=1.5):
    """大きい本体から遠い島・小さい島を落とす（小笠原・奄美・先島）。"""
    parts = sorted(parts, key=lambda q: -q.area)
    top = parts[0]
    c0 = top.centroid
    return [q for q in parts if q.area >= top.area * min_ratio and q.centroid.distance(c0) <= max_deg]


def whole_shape(rings):
    """県くん・地方くんの形。市町村（県）の輪を1つに溶かし合わせる。
    そのまま重ねると県境のすき間から境目の線がのぞき（首都圏くん）、沖の小島も点で残った。"""
    polys = [Polygon(r).buffer(0) for r in rings if len(r) >= 3]
    xs = [b for q in polys for b in (q.bounds[0], q.bounds[2])]
    ys = [b for q in polys for b in (q.bounds[1], q.bounds[3])]
    eps = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.002
    u = unary_union([q.buffer(eps) for q in polys]).buffer(-eps)
    parts = list(u.geoms) if hasattr(u, "geoms") else [u]
    # 遠さの基準は 2 度（1 度では中国四国くんの四国が島あつかいで外れた）
    parts = keep_parts([q for q in parts if not q.is_empty], min_ratio=0.03, max_deg=2.0)
    return [[[round(x, 6), round(y, 6)] for x, y in list(q.exterior.coords)[:-1]] for q in parts]


def ensure_geo(geo_dir, code):
    """なければ取ってくる。この環境の Python（urllib）はプロキシ越しの TLS が切れたので curl を使う。"""
    path = geo_dir / f"{code}.json"
    for _ in range(4):
        if path.exists() and path.stat().st_size > 0:
            return path
        subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(path), NIIYZ.format(p=code[:2], c=code)])
    raise SystemExit(f"{code}.json を取得できなかった")


def build(a, geo_dir, pref_dir):
    # コードのない土地（所属未定地・境界未定の湖など）は使わない
    feats = [ft for p in a["prefs"] for ft in load_pref(pref_dir, p) if ft["properties"]["N03_007"]]
    # 地図の範囲を県の一部に絞る編（横浜市・札幌市・23区・多摩）は、その範囲の中だけで名前を引く
    # （神奈川県には横浜市南区と相模原市南区がある）
    pre = a.get("map_prefix")
    by_name, names = index([ft for ft in feats if not pre or any(ft["properties"]["N03_007"].startswith(x) for x in pre)])
    pref_names = {}
    for ft in feats:
        pref_names.setdefault(ft["properties"]["N03_001"], ft["properties"]["N03_007"][:2])
    ys = [y for ft in feats for q in polys_of(ft["geometry"]) for _, y in q.exterior.coords]
    k = math.cos(math.radians((min(ys) + max(ys)) / 2))
    shifts = {n: (dx * k, dy) for n, (dx, dy) in a.get("shift", {}).items()}

    # 県の形（地方編）: 市町村をつないで1つに
    def pref_parts(pname):
        p = pref_names[pname]
        u = unary_union([q for ft in feats if ft["properties"]["N03_007"][:2] == p for q in polys_of(ft["geometry"])])
        parts = list(u.geoms) if hasattr(u, "geoms") else [u]
        return keep_parts(parts)

    # ---------------------------------------------------------------- 右上の全体図
    out = {"source": "国土数値情報（行政区域）国土交通省（CC BY 4.0）を niiyz/JapanCityGeoJson・"
                     "smartnews-smri/japan-topography 経由で加工",
           "projection": f"x=経度×{k:.5f}, y=-緯度", "units": {}}
    if a["level"] == "pref":
        pmap = {}
        for pname in pref_names:
            parts = pref_parts(pname)
            span = max(max(q.bounds[2] for q in parts) - min(q.bounds[0] for q in parts),
                       max(q.bounds[3] for q in parts) - min(q.bounds[1] for q in parts))
            pmap[pname] = [proj(q.simplify(span * 0.004), k, shifts.get(pname, (0, 0))) for q in parts]
        out["pref_map"] = pmap
    elif len(a["prefs"]) == 1 and not a.get("map_prefix"):
        # 県1つ: 全国30シリーズと同じ作り方（遠い島は範囲から外し、矢印で示す）
        member = [c for c in names]
        series = dict(pref=a["prefs"][0], kind="pref", units=[dict(codes=[c]) for c in member])
        out["pref_map"], out["pref_bbox"], _ = map_features(series, pref_dir, k)
    else:
        pre = a.get("map_prefix")
        groups = {}
        for ft in feats:
            c = ft["properties"]["N03_007"]
            if c and (not pre or any(c.startswith(x) for x in pre)):
                groups.setdefault(c, []).extend(polys_of(ft["geometry"]))
        # 遠い島（東京の島しょ部）を外す: 中心から中央値の3倍より遠い市町村
        cen = {c: max(ps, key=lambda q: q.area).centroid for c, ps in groups.items()}
        mx = sorted(p.x for p in cen.values())[len(cen) // 2]
        my = sorted(p.y for p in cen.values())[len(cen) // 2]
        dist = {c: math.hypot(p.x - mx, p.y - my) for c, p in cen.items()}
        med = sorted(dist.values())[len(dist) // 2]
        pmap = {}
        allb = [q.bounds for ps in groups.values() for q in ps]
        span = max(max(b[2] for b in allb) - min(b[0] for b in allb), max(b[3] for b in allb) - min(b[1] for b in allb))
        for c, ps in groups.items():
            if dist[c] > max(med * 3, 0.3):
                continue
            top = max(q.area for q in ps)
            pmap[c] = [proj(q.simplify(span * 0.002), k) for q in ps if q.area >= top * 0.02]
        out["pref_map"] = pmap
    if a.get("map_south"):
        # 地図の範囲を本土側に絞る（鹿児島: 奄美まで入れると本土が豆粒になった。奄美は矢印で示す）
        pts = [p for rs in out["pref_map"].values() for r in rs for p in r if -p[1] >= a["map_south"]]
        out["pref_bbox"] = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
    if "pref_bbox" not in out:
        pts = [p for rs in out["pref_map"].values() for r in rs for p in r]
        out["pref_bbox"] = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]

    # 政令市の地図（区のスタンプの右上）
    city_of = {}
    for i, city in enumerate(a.get("cities", [])):
        wards = sorted(by_name[city])
        key = f"city{i}"
        series = dict(pref=a["prefs"][0], kind="ward", units=[dict(codes=[c]) for c in wards])
        out[f"{key}_map"], out[f"{key}_bbox"], _ = map_features(series, pref_dir, k)
        for c in wards:
            city_of[c] = key

    # ---------------------------------------------------------------- スタンプの形
    for key, *_ in a["items"]:
        if key == PREF or key in out["units"]:
            continue
        if key in a.get("groups", {}):
            codes = a["groups"][key]
            label = key.split("市")[-1] if key.endswith("区") else key
        elif a["level"] == "pref" and key in pref_names:
            # 県まるごとのキャラは本体の1割未満の島を外す（東京都が伊豆大島まで入って本土が小さくなった）
            # 本体から遠い島も外す（長崎県が対馬まで入って本土が小さくなった）
            parts = keep_parts(pref_parts(key), min_ratio=0.1, max_deg=0.8)
            span = max(max(q.bounds[2] for q in parts) - min(q.bounds[0] for q in parts),
                       max(q.bounds[3] for q in parts) - min(q.bounds[1] for q in parts))
            out["units"][key] = {"name": key, "codes": [key], "map": "pref",
                                 "rings": [proj(q.simplify(span * 0.004), k) for q in parts]}
            continue
        else:
            if key not in by_name:
                raise SystemExit(f"{a['id']}: 「{key}」が見つからない")
            codes = sorted(by_name[key])
            label = names[codes[0]] if len(codes) == 1 else key
        for c in codes:
            ensure_geo(geo_dir, c)
        kind = city_of.get(codes[0], "pref") if len(codes) == 1 or key.endswith("区") else "pref"
        out["units"][key] = {"name": label, "codes": codes, "map": kind, "rings": unit_rings(codes, geo_dir, k)}

    # ---------------------------------------------------------------- 県くん（地方くん）の形・顔の位置
    excl = set()
    for n in a.get("whole_exclude", []):
        excl.add(n)
    out["whole"] = whole_shape([r for c, rs in out["pref_map"].items() if c not in excl for r in rs])
    fa = a.get("face_at")
    if fa:
        if fa in out["pref_map"]:
            out["face_key"] = fa
        else:
            out["face_key"] = sorted(by_name[fa])[0]
    path = HERE / "data" / f"machi24_{a['id']}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{a['id']:<12} units {len(out['units']):>2}  map {len(out['pref_map']):>3}  → {path.relative_to(HERE)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--pref", required=True)
    ap.add_argument("ids", nargs="*")
    args = ap.parse_args()
    for area in AREAS:
        if not args.ids or area["id"] in args.ids:
            build(area, pathlib.Path(args.geo), pathlib.Path(args.pref))


if __name__ == "__main__":
    main()

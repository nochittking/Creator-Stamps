# -*- coding: utf-8 -*-
"""わが街スタンプ（近畿の各県）の輪郭データを作る（design/data/machi24_<id>.json）。

build_kyoto24_geo.py を県ごとの設定（machi24_data.AREAS）で動くようにしたもの。
  city_map: 政令市の区だけ（神戸市）。区のスタンプの右上
  pref_map: 県の全市町村。市町村のスタンプと県くんの右上
  units:    スタンプに描く区・市町村の輪郭（誤差1%で間引き）
  whole:    県くんの形（pref_map の全市町村）

入力は build_series_geo.py と同じ（国土数値情報 行政区域、CC BY 4.0）
湖（滋賀の琵琶湖）は data/lake_biwa_naturalearth.json（Natural Earth 10m lakes、パブリックドメイン）
使い方
  python3 build_machi24_geo.py --geo <dir> --pref <dir> [id ...]
"""
import argparse
import json
import math
import pathlib

from build_series_geo import map_features, unit_rings
from machi24_data import AREAS, PREF

HERE = pathlib.Path(__file__).parent


def chaikin(ring, n=2):
    """角を丸める（各辺を 1/4・3/4 で切る）。Natural Earth の湖は点が少なく角ばるため。"""
    for _ in range(n):
        out = []
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
            out += [(x1 * .75 + x2 * .25, y1 * .75 + y2 * .25), (x1 * .25 + x2 * .75, y1 * .25 + y2 * .75)]
        ring = out
    return ring


def lake_rings(path, k):
    """湖の輪郭。国土数値情報の行政区域では湖の上もまわりの市町に分けて含まれていて湖が出ないので、
    Natural Earth（パブリックドメイン）の湖を重ねる。滋賀の琵琶湖（2026-10-18 ユーザー要望）。"""
    g = json.loads(path.read_text(encoding="utf-8"))["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return [[[round(x * k, 6), round(-y, 6)] for x, y in chaikin(poly[0][:-1])] for poly in polys]


def build(a, geo_dir, pref_dir):
    d = json.loads((pref_dir / f"N03-21_{a['pref']}_210101.json").read_text(encoding="utf-8"))
    every = sorted({ft["properties"]["N03_007"] for ft in d["features"] if ft["properties"]["N03_007"]})
    # 横の縮め方（cos 緯度）は県の南北の真ん中で決める。
    # 最初は先頭3つの市町村の点で平均したが、島の多い市町村の点まで数えてしまい、兵庫・和歌山で形が縦に潰れた
    ys = [y for ft in d["features"] for poly in
          ([ft["geometry"]["coordinates"]] if ft["geometry"]["type"] == "Polygon" else ft["geometry"]["coordinates"])
          for _, y in poly[0]]
    k = math.cos(math.radians((min(ys) + max(ys)) / 2))
    codes = sorted({c for c, *_ in a["items"] if c != PREF})
    units = {}
    for c in codes:
        g = json.loads((geo_dir / f"{c}.json").read_text(encoding="utf-8"))
        p = g["features"][0]["properties"]
        units[c] = {"name": p["N03_004"], "rings": unit_rings([c], geo_dir, k)}
    one = lambda cs, kind: dict(pref=a["pref"], kind=kind, units=[dict(codes=[c]) for c in cs])
    out = {
        "source": "国土数値情報（行政区域）国土交通省（CC BY 4.0）を niiyz/JapanCityGeoJson・smartnews-smri/japan-topography 経由で加工",
        "projection": f"x=経度×{k:.5f}, y=-緯度",
        "units": units,
    }
    head = codes[0]
    out["pref_map"], out["pref_bbox"], _ = map_features(one([head] + every, "pref"), pref_dir, k)
    if a["city_wards"]:
        out["city_map"], out["city_bbox"], _ = map_features(one(a["city_wards"], "ward"), pref_dir, k)
    out["whole"] = [r for c in out["pref_map"] for r in out["pref_map"][c]]
    if a.get("lake"):
        out["lake"] = lake_rings(HERE / "data" / a["lake"], k)
    path = HERE / "data" / f"machi24_{a['id']}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{a['id']:<9} units {len(units):>2}  pref_map {len(out['pref_map'])}  → {path.relative_to(HERE)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--pref", required=True)
    ap.add_argument("ids", nargs="*")
    a = ap.parse_args()
    for area in AREAS:
        if not a.ids or area["id"] in a.ids:
            build(area, pathlib.Path(a.geo), pathlib.Path(a.pref))


if __name__ == "__main__":
    main()

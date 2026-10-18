# -*- coding: utf-8 -*-
"""京都編24個の輪郭データを作る（design/data/kyoto24.json）。

京都編は「京都市の区」と「府の市」がまざる（2026-10-18 ユーザー決定）。全体図が2種類いる。
  city_map: 京都市の11区だけ。区のスタンプの右上に出す
  pref_map: 京都府の26市町村。府の市のスタンプと、京都府くん（全体キャラ）の右上に出す
  units:    スタンプに描く区・市の輪郭（誤差1%で間引き）
  whole:    京都府くんの形（pref_map の全市町村をまとめたもの）

入力は build_series_geo.py と同じ（国土数値情報 行政区域、CC BY 4.0）
  --geo   niiyz/JapanCityGeoJson の geojson/26/<コード>.json を置いたディレクトリ
  --pref  smartnews-smri/japan-topography の N03-21_26_210101.json を置いたディレクトリ

使い方
  python3 build_kyoto24_geo.py --geo <dir> --pref <dir>
"""
import argparse
import json
import math
import pathlib

from build_series_geo import map_features, unit_rings

HERE = pathlib.Path(__file__).parent
WARDS = [f"261{i:02d}" for i in range(1, 12)]                 # 京都市の11区
CITIES = ["26204", "26205", "26202", "26206", "26201", "26209"]   # 宇治・宮津・舞鶴・亀岡・福知山・長岡京
ALL = WARDS + [f"262{i:02d}" for i in range(1, 15)] + [
    "26303", "26322", "26343", "26344", "26364", "26365", "26366", "26367", "26407", "26463", "26465"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--pref", required=True)
    a = ap.parse_args()
    geo_dir, pref_dir = pathlib.Path(a.geo), pathlib.Path(a.pref)
    k = math.cos(math.radians(35.0))          # 京都府のおよその緯度。形の縦横比を保つため
    units = {}
    for c in WARDS + CITIES:
        d = json.loads((geo_dir / f"{c}.json").read_text(encoding="utf-8"))
        name = d["features"][0]["properties"]["N03_004"]
        units[c] = {"name": name, "rings": unit_rings([c], geo_dir, k)}
    one = lambda codes, kind: dict(pref="26", kind=kind, units=[dict(codes=[c]) for c in codes])
    city_map, city_bbox, _ = map_features(one(WARDS, "ward"), pref_dir, k)
    pref_map, pref_bbox, _ = map_features(one(["26204"] + ALL, "pref"), pref_dir, k)
    data = {
        "source": "国土数値情報（行政区域）国土交通省（CC BY 4.0）を niiyz/JapanCityGeoJson・smartnews-smri/japan-topography 経由で加工",
        "projection": f"x=経度×{k:.5f}, y=-緯度",
        "units": units,
        "city_map": city_map, "city_bbox": city_bbox,
        "pref_map": pref_map, "pref_bbox": pref_bbox,
        # 京都府くんの形。全市町村の輪をそのまま持ち、描くときに「線の層 → 塗りの層」で境目を消す
        "whole": [r for c in pref_map for r in pref_map[c]],
    }
    out = HERE / "data" / "kyoto24.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"units {len(units)}  pts {sum(len(r) for u in units.values() for r in u['rings'])}  "
          f"city_map {len(city_map)}  pref_map {len(pref_map)}  → {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()

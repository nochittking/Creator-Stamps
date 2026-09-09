#!/usr/bin/env python3
"""白背景の手描き原稿を、LINEスタンプ入稿用の透過PNGに整える。

やること
  1. 外周とつながっている白だけを透過にする（絵の内側の白は残す）
  2. 輪郭のアンチエイリアスをアルファに変換し、色を非乗算に戻す
  3. 全カット共通の倍率で縮小し、370x320 に中央配置する
     （カットごとに拡大率を変えると線の太さが揃わなくなるため）
  4. main.png (240x240) と tab.png (96x74) を書き出す

使い方
    python3 tools/prepare_stickers.py sketches/v1 stickers/set01
    python3 tools/prepare_stickers.py sketches/v1 stickers/set01 --main ありがとう
"""
from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:
    sys.exit("Pillow が必要です:  pip install Pillow")

OUT_W, OUT_H = 370, 320
MAIN, TAB = (240, 240), (96, 74)
MARGIN = 6          # 外周に残す透過の余白（px, 出力サイズ基準）
WHITE_TH = 240      # これ以上明るい画素を「背景の白」とみなす
EDGE_DEN = 235      # アンチエイリアスのアルファ換算の分母


def outside_mask(im: Image.Image) -> bytearray:
    """外周から届く「白」を塗りつぶしで探す。絵に囲まれた白は残す。"""
    w, h = im.size
    px = im.load()
    mask = bytearray(w * h)
    q = deque()

    def near_white(x, y):
        r, g, b = px[x, y][:3]
        return min(r, g, b) >= WHITE_TH

    for x in range(w):
        for y in (0, h - 1):
            if not mask[y * w + x] and near_white(x, y):
                mask[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not mask[y * w + x] and near_white(x, y):
                mask[y * w + x] = 1
                q.append((x, y))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not mask[ny * w + nx] and near_white(nx, ny):
                mask[ny * w + nx] = 1
                q.append((nx, ny))
    return mask


def cut_background(im: Image.Image) -> Image.Image:
    """外側の白を抜き、境界の1〜2画素をアルファに変換する。"""
    im = im.convert("RGBA")
    w, h = im.size
    mask = outside_mask(im)
    src = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()

    for y in range(h):
        row = y * w
        for x in range(w):
            if mask[row + x]:
                continue
            r, g, b, _ = src[x, y]
            # 外側の白に接している画素だけ、明るさからアルファを起こす
            touching = any(
                0 <= nx < w and 0 <= ny < h and mask[ny * w + nx]
                for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1),
                               (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)))
            if not touching:
                dst[x, y] = (r, g, b, 255)
                continue
            a = min(255, round((255 - min(r, g, b)) * 255 / EDGE_DEN))
            if a <= 0:
                continue
            # 白と混ざったぶんを戻す（非乗算）
            f = lambda c: max(0, min(255, round((c * 255 - 255 * (255 - a)) / a)))
            dst[x, y] = (f(r), f(g), f(b), a)
    return out


def clear_enclosed_white(im: Image.Image) -> Image.Image:
    """絵に囲まれた白も透過にする。線画では白＝紙＝背景であることが多い。"""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 0 and min(r, g, b) >= WHITE_TH:
                px[x, y] = (r, g, b, 0)
    return im


def add_outline(im: Image.Image, width: int, color=(255, 255, 255)) -> Image.Image:
    """絵の外側に白フチを付ける。濃い壁紙のトーク画面でも黒い線と文字が読める。"""
    pad = width + 2
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    alpha = big.split()[3].point(lambda v: 255 if v > 40 else 0)
    grown = alpha.filter(ImageFilter.MaxFilter(width * 2 + 1))
    halo = Image.new("RGBA", big.size, color + (0,))
    halo.putalpha(grown)
    return Image.alpha_composite(halo, big)


def content_box(im: Image.Image):
    return im.getbbox()  # アルファ 0 を除いた外接矩形


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="手描き原稿を入稿用の透過PNGに整える")
    ap.add_argument("src", type=Path, help="原稿のディレクトリ")
    ap.add_argument("dst", type=Path, help="出力先")
    ap.add_argument("--main", default=None,
                    help="メイン画像に使うファイル名の一部（省略時は先頭のカット）")
    ap.add_argument("--clear-inner", action="store_true",
                    help="絵に囲まれた白も透過にする")
    ap.add_argument("--outline", type=int, default=0, metavar="PX",
                    help="絵の外側に白フチを付ける太さ（原稿サイズ基準）")
    args = ap.parse_args(argv)

    files = sorted(p for p in args.src.glob("*.png"))
    if not files:
        sys.exit(f"{args.src} に PNG がない")
    args.dst.mkdir(parents=True, exist_ok=True)

    # 前回の出力が残っていると枚数が合わなくなるので、先に片付ける
    stale = [q for q in args.dst.glob("*.png")
             if q.stem == "main" or q.stem == "tab" or (q.stem.isdigit() and len(q.stem) == 2)]
    for q in stale:
        q.unlink()
    if stale:
        print(f"出力先の前回分 {len(stale)} 件を削除しました")

    print(f"背景を抜いています（{len(files)} 枚）…")
    cut, boxes = [], []
    for p in files:
        c = cut_background(Image.open(p))
        if args.clear_inner:
            c = clear_enclosed_white(c)
        if args.outline:
            c = add_outline(c, args.outline)
        box = content_box(c)
        if box is None:
            print(f"  !! {p.name}: 絵が残らなかった")
            continue
        cut.append((p, c))
        boxes.append(box)
        print(f"  {p.name}: 絵の範囲 {box[2]-box[0]}x{box[3]-box[1]}")

    # 全カット共通の倍率。最大のカットが枠に収まる倍率を全体に使う
    max_w = max(b[2] - b[0] for b in boxes)
    max_h = max(b[3] - b[1] for b in boxes)
    scale = min((OUT_W - MARGIN * 2) / max_w, (OUT_H - MARGIN * 2) / max_h)
    print(f"\n最大のカット {max_w}x{max_h} → 共通倍率 {scale:.4f}"
          f"（カットごとに変えると線の太さが揃わなくなるため）")

    print(f"\n{OUT_W}x{OUT_H} に書き出しています…")
    for i, ((p, c), box) in enumerate(zip(cut, boxes), 1):
        art = c.crop(box)
        nw = max(1, round(art.width * scale))
        nh = max(1, round(art.height * scale))
        art = art.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
        canvas.paste(art, ((OUT_W - nw) // 2, (OUT_H - nh) // 2))
        canvas.save(args.dst / f"{i:02d}.png", optimize=True)
        print(f"  {i:02d}.png  ← {p.name}  ({nw}x{nh})")

    # メイン画像とタブ画像
    pick = 0
    if args.main:
        for i, (p, _) in enumerate(cut):
            if args.main in p.name:
                pick = i
                break
    _, c = cut[pick]
    art = c.crop(boxes[pick])
    for size, name in ((MAIN, "main.png"), (TAB, "tab.png")):
        s = min(size[0] / art.width, size[1] / art.height)
        r = art.resize((max(1, round(art.width * s)), max(1, round(art.height * s))), Image.LANCZOS)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        canvas.paste(r, ((size[0] - r.width) // 2, (size[1] - r.height) // 2))
        canvas.save(args.dst / name, optimize=True)
        print(f"  {name}  ← {cut[pick][0].name}  ({r.width}x{r.height})")

    print(f"\n完了: {args.dst}")
    print("次: python3 tools/check_stickers.py", args.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""LINEクリエイターズスタンプの画像を申請前に機械チェックする。

標準ライブラリのみで動作する（Pillow 不要）。PNG を自前でパースし、
サイズ・形式・透過・余白・容量・枚数、APNG のフレーム数と再生時間を検証する。

想定するディレクトリ構成:

    stickers/
      main.png        メイン画像   240 x 240
      tab.png         タブ画像      96 x  74
      01.png .. 40.png  スタンプ本体 370 x 320 以内

使い方:

    python3 tools/check_stickers.py stickers/
    python3 tools/check_stickers.py stickers/ --animation   # 動くスタンプ

終了コードは ERROR が 1件でもあれば 1、それ以外は 0。

仕様は改定されるため、申請直前に必ず公式ガイドラインを確認すること:
  https://creator.line.me/ja/guideline/sticker/
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# --- 仕様値 -------------------------------------------------------------
MAIN_SIZE = (240, 240)
TAB_SIZE = (96, 74)
STICKER_MAX = (370, 320)
ANIMATION_MAX = (320, 270)
MAX_BYTES = 1024 * 1024          # 1MB / 画像
REQUIRED_MARGIN = 10             # 周囲 10px の余白
VALID_COUNTS = (8, 16, 24, 32, 40)
ANIM_FRAMES = (5, 20)            # 5〜20 フレーム
ANIM_MAX_SECONDS = 4.0

CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}   # color type -> チャンネル数
HAS_ALPHA = {4, 6}
STICKER_NAME = re.compile(r"^(\d{2})$")


# --- 結果の入れ物 -------------------------------------------------------
@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


@dataclass
class Png:
    width: int
    height: int
    bit_depth: int
    color_type: int
    interlaced: bool
    idat: bytes
    palette_alpha: bool
    apng_frames: int | None
    apng_seconds: float | None


# --- PNG パース ---------------------------------------------------------
def parse_png(raw: bytes) -> Png:
    """PNG のチャンクを走査して必要な情報だけ取り出す。"""
    if not raw.startswith(PNG_SIGNATURE):
        raise ValueError("PNG シグネチャがない（PNG ではない可能性）")

    pos = len(PNG_SIGNATURE)
    ihdr = None
    idat = bytearray()
    palette_alpha = False
    apng_frames: int | None = None
    delays: list[float] = []

    while pos + 8 <= len(raw):
        (length,) = struct.unpack(">I", raw[pos : pos + 4])
        ctype = raw[pos + 4 : pos + 8]
        body = raw[pos + 8 : pos + 8 + length]
        if len(body) < length:
            raise ValueError(f"チャンク {ctype.decode('ascii', 'replace')} が途中で切れている")
        pos += 12 + length  # length + type + data + CRC

        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body[:13])
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"tRNS":
            palette_alpha = True
        elif ctype == b"acTL":
            apng_frames = struct.unpack(">I", body[:4])[0]
        elif ctype == b"fcTL":
            delay_num, delay_den = struct.unpack(">HH", body[20:24])
            delays.append(delay_num / (delay_den or 100))
        elif ctype == b"IEND":
            break

    if ihdr is None:
        raise ValueError("IHDR チャンクがない")

    width, height, bit_depth, color_type, _comp, _filt, interlace = ihdr
    return Png(
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
        interlaced=bool(interlace),
        idat=bytes(idat),
        palette_alpha=palette_alpha,
        apng_frames=apng_frames,
        apng_seconds=sum(delays) if delays else None,
    )


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def decode_alpha(png: Png) -> list[list[int]] | None:
    """アルファチャンネルだけを 2次元配列で返す。取得できない場合は None。"""
    if png.interlaced or png.bit_depth != 8 or png.color_type not in HAS_ALPHA:
        return None

    channels = CHANNELS[png.color_type]
    stride = png.width * channels
    try:
        raw = zlib.decompress(png.idat)
    except zlib.error:
        return None
    if len(raw) < (stride + 1) * png.height:
        return None

    alpha_index = channels - 1
    prev = bytearray(stride)
    alpha: list[list[int]] = []
    pos = 0

    for _ in range(png.height):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1 : pos + 1 + stride])
        pos += 1 + stride

        if ftype == 1:      # Sub
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif ftype == 2:    # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:    # Average
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:    # Paeth
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                upleft = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        elif ftype != 0:
            return None

        alpha.append([line[x * channels + alpha_index] for x in range(png.width)])
        prev = line

    return alpha


def margin_transparent(alpha: list[list[int]], margin: int) -> bool:
    """外周 margin px がすべて完全透過かどうか。"""
    height, width = len(alpha), len(alpha[0])
    if height <= margin * 2 or width <= margin * 2:
        return False
    for y in range(height):
        row = alpha[y]
        if y < margin or y >= height - margin:
            if any(row):
                return False
        elif any(row[:margin]) or any(row[width - margin :]):
            return False
    return True


def content_bounds(alpha: list[list[int]]) -> tuple[int, int, int, int] | None:
    """不透明ピクセルの外接矩形 (left, top, right, bottom)。"""
    top = bottom = None
    left, right = len(alpha[0]), -1
    for y, row in enumerate(alpha):
        xs = [x for x, a in enumerate(row) if a]
        if not xs:
            continue
        top = y if top is None else top
        bottom = y
        left = min(left, xs[0])
        right = max(right, xs[-1])
    if top is None:
        return None
    return left, top, right, bottom


# --- 個別ファイルの検査 -------------------------------------------------
def check_image(path: Path, kind: str, animation: bool, rep: Report) -> None:
    label = f"{path.name} [{kind}]"
    raw = path.read_bytes()

    size = len(raw)
    if size > MAX_BYTES:
        rep.error(f"{label}: 容量 {size / 1024:.0f}KB が上限 1MB を超えている")

    try:
        png = parse_png(raw)
    except ValueError as exc:
        rep.error(f"{label}: {exc}")
        return

    # 形式
    if png.color_type not in HAS_ALPHA and not (png.color_type == 3 and png.palette_alpha):
        rep.error(f"{label}: アルファチャンネルがない（背景を透過した PNG が必要）")
    if png.bit_depth != 8:
        rep.warn(f"{label}: ビット深度が {png.bit_depth}（8bit RGBA での書き出しを推奨）")
    if png.interlaced:
        rep.warn(f"{label}: インターレース PNG。非インターレースで書き出すこと")

    # 寸法
    w, h = png.width, png.height
    if kind == "main":
        if (w, h) != MAIN_SIZE:
            rep.error(f"{label}: {w}x{h} → メイン画像は {MAIN_SIZE[0]}x{MAIN_SIZE[1]} 固定")
    elif kind == "tab":
        if (w, h) != TAB_SIZE:
            rep.error(f"{label}: {w}x{h} → タブ画像は {TAB_SIZE[0]}x{TAB_SIZE[1]} 固定")
    else:
        max_w, max_h = ANIMATION_MAX if animation else STICKER_MAX
        if w > max_w or h > max_h:
            rep.error(f"{label}: {w}x{h} が上限 {max_w}x{max_h} を超えている")
        if w % 2 or h % 2:
            rep.error(f"{label}: {w}x{h} に奇数がある（縦横とも偶数px にする）")
        if w < max_w and h < max_h:
            rep.note(f"{label}: {w}x{h}（上限 {max_w}x{max_h} に対して余裕あり）")

    # APNG
    if animation:
        if png.apng_frames is None:
            rep.error(f"{label}: APNG ではない（動くスタンプはアニメーション PNG が必要）")
        else:
            lo, hi = ANIM_FRAMES
            if not lo <= png.apng_frames <= hi:
                rep.error(f"{label}: {png.apng_frames} フレーム → {lo}〜{hi} フレームに収める")
            if png.apng_seconds and png.apng_seconds > ANIM_MAX_SECONDS:
                rep.error(f"{label}: 再生 {png.apng_seconds:.2f} 秒 → {ANIM_MAX_SECONDS} 秒以内に収める")
    elif png.apng_frames is not None:
        rep.warn(f"{label}: APNG だが静止画として検査した（--animation の指定漏れ？）")

    # 透過と余白（スタンプ本体のみ）
    alpha = decode_alpha(png)
    if alpha is None:
        rep.note(f"{label}: ピクセル解析をスキップ（透過・余白は目視で確認すること）")
        return

    if all(a == 255 for row in alpha for a in row):
        rep.error(f"{label}: 全ピクセルが不透明。背景の透過処理ができていない")
        return

    if kind == "sticker" and not animation:
        if not margin_transparent(alpha, REQUIRED_MARGIN):
            rep.error(f"{label}: 外周 {REQUIRED_MARGIN}px に絵がはみ出している（余白が必要）")
        bounds = content_bounds(alpha)
        if bounds is None:
            rep.error(f"{label}: 不透明ピクセルが 1つもない（空の画像）")
        else:
            left, top, right, bottom = bounds
            cw, ch = right - left + 1, bottom - top + 1
            if cw < w * 0.5 and ch < h * 0.5:
                rep.warn(
                    f"{label}: 絵の占有が {cw}x{ch} と小さい。"
                    "トーク画面では縮小表示されるため、余白を詰めて大きく描くこと"
                )


# --- ディレクトリ全体 ---------------------------------------------------
def run(directory: Path, animation: bool) -> Report:
    rep = Report()
    if not directory.is_dir():
        rep.error(f"ディレクトリが見つからない: {directory}")
        return rep

    files = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".png")
    if not files:
        rep.error(f"{directory} に PNG がない")
        return rep

    for stray in sorted(p.name for p in directory.iterdir() if p.suffix.lower() != ".png" and p.is_file()):
        rep.warn(f"{stray}: PNG 以外のファイルが混ざっている")

    stickers: list[Path] = []
    numbers: list[int] = []
    main = tab = None

    for path in files:
        stem = path.stem
        if stem == "main":
            main = path
        elif stem == "tab":
            tab = path
        elif STICKER_NAME.match(stem):
            stickers.append(path)
            numbers.append(int(stem))
        else:
            rep.warn(f"{path.name}: 命名が想定外（01.png〜40.png / main.png / tab.png を推奨）")
            stickers.append(path)

    if main is None:
        rep.error("main.png（メイン画像 240x240）がない")
    else:
        check_image(main, "main", False, rep)

    if tab is None:
        rep.error("tab.png（タブ画像 96x74）がない")
    else:
        check_image(tab, "tab", False, rep)

    for path in stickers:
        check_image(path, "sticker", animation, rep)

    count = len(stickers)
    if count not in VALID_COUNTS:
        rep.error(
            f"スタンプ画像が {count} 個。{'/'.join(map(str, VALID_COUNTS))} 個のいずれかにする"
        )

    if numbers:
        missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
        if missing:
            rep.warn("連番に欠けがある: " + ", ".join(f"{n:02d}.png" for n in missing))
        duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
        if duplicates:
            rep.error("連番が重複している: " + ", ".join(f"{n:02d}" for n in duplicates))

    return rep


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LINEスタンプ画像を申請前にチェックする",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="例: python3 tools/check_stickers.py stickers/ --animation",
    )
    parser.add_argument("directory", type=Path, help="スタンプ画像のディレクトリ")
    parser.add_argument(
        "--animation",
        action="store_true",
        help="動くスタンプとして検査する（320x270以内 / 5〜20フレーム / 4秒以内）",
    )
    args = parser.parse_args(argv)

    rep = run(args.directory, args.animation)

    for msg in rep.errors:
        print(f"ERROR  {msg}")
    for msg in rep.warnings:
        print(f"WARN   {msg}")
    for msg in rep.notes:
        print(f"NOTE   {msg}")

    print(
        f"\n{args.directory}: ERROR {len(rep.errors)} / WARN {len(rep.warnings)} / NOTE {len(rep.notes)}"
    )
    if rep.errors:
        print("→ 申請前に ERROR をすべて解消すること。")
        return 1
    print("→ 機械チェックは通過。誤字脱字・商標・類似は目視で確認すること。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

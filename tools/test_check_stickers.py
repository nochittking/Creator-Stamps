#!/usr/bin/env python3
"""check_stickers.py のテスト。実行: python3 -m unittest discover -s tools -v"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_stickers as cs  # noqa: E402


# --- テスト用の PNG を作る ----------------------------------------------
def _chunk(ctype: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body))


def _rgba_scanlines(width: int, height: int, opaque: tuple[int, int, int, int]) -> bytes:
    """opaque の矩形を中央に置いた RGBA ラスタ（フィルタ 0）。"""
    left, top, right, bottom = opaque
    out = bytearray()
    for y in range(height):
        out.append(0)  # filter: None
        for x in range(width):
            inside = left <= x <= right and top <= y <= bottom
            out += bytes((200, 60, 60, 255)) if inside else bytes(4)
    return bytes(out)


def write_png(
    path: Path,
    width: int,
    height: int,
    *,
    margin: int = 10,
    color_type: int = 6,
    fully_opaque: bool = False,
    apng: tuple[int, float] | None = None,
) -> Path:
    """検査対象の PNG を書き出す。apng=(フレーム数, 総秒数) で APNG になる。"""
    if fully_opaque:
        opaque = (0, 0, width - 1, height - 1)
    else:
        opaque = (margin, margin, width - 1 - margin, height - 1 - margin)

    if color_type == 6:
        raw = _rgba_scanlines(width, height, opaque)
    else:  # color type 2: RGB（アルファなし）
        out = bytearray()
        for _ in range(height):
            out.append(0)
            out += bytes((200, 60, 60)) * width
        raw = bytes(out)

    data = cs.PNG_SIGNATURE
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))

    if apng is not None:
        frames, seconds = apng
        data += _chunk(b"acTL", struct.pack(">II", frames, 0))
        per_frame = seconds / frames
        delay_num = max(1, round(per_frame * 1000))
        for seq in range(frames):
            data += _chunk(
                b"fcTL",
                struct.pack(">IIIIIHHBB", seq, width, height, 0, 0, delay_num, 1000, 0, 0),
            )

    data += _chunk(b"IDAT", zlib.compress(raw))
    data += _chunk(b"IEND", b"")
    path.write_bytes(data)
    return path


def build_set(directory: Path, count: int = 8, **kwargs) -> Path:
    """main / tab / 連番スタンプが揃った正常なセットを作る。"""
    directory.mkdir(parents=True, exist_ok=True)
    write_png(directory / "main.png", 240, 240)
    write_png(directory / "tab.png", 96, 74, margin=4)
    for i in range(1, count + 1):
        write_png(directory / f"{i:02d}.png", 370, 320, **kwargs)
    return directory


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)


class TestValidSet(TempDirCase):
    def test_clean_set_has_no_errors(self) -> None:
        rep = cs.run(build_set(self.tmp / "ok", count=8), animation=False)
        self.assertEqual(rep.errors, [])

    def test_all_valid_counts_accepted(self) -> None:
        for count in cs.VALID_COUNTS:
            with self.subTest(count=count):
                rep = cs.run(build_set(self.tmp / f"n{count}", count=count), animation=False)
                self.assertEqual(rep.errors, [])


class TestDimensions(TempDirCase):
    def test_oversized_sticker_is_error(self) -> None:
        d = build_set(self.tmp / "big")
        write_png(d / "01.png", 400, 320)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("上限" in e for e in rep.errors))

    def test_odd_dimension_is_error(self) -> None:
        d = build_set(self.tmp / "odd")
        write_png(d / "01.png", 369, 320)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("偶数" in e for e in rep.errors))

    def test_wrong_main_size_is_error(self) -> None:
        d = build_set(self.tmp / "main")
        write_png(d / "main.png", 200, 200)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("メイン画像" in e for e in rep.errors))

    def test_wrong_tab_size_is_error(self) -> None:
        d = build_set(self.tmp / "tab")
        write_png(d / "tab.png", 96, 96, margin=4)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("タブ画像" in e for e in rep.errors))


class TestTransparency(TempDirCase):
    def test_missing_alpha_channel_is_error(self) -> None:
        d = build_set(self.tmp / "rgb")
        write_png(d / "01.png", 370, 320, color_type=2)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("アルファチャンネル" in e for e in rep.errors))

    def test_fully_opaque_is_error(self) -> None:
        d = build_set(self.tmp / "opaque")
        write_png(d / "01.png", 370, 320, fully_opaque=True)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("透過処理" in e for e in rep.errors))

    def test_insufficient_margin_is_error(self) -> None:
        d = build_set(self.tmp / "margin")
        write_png(d / "01.png", 370, 320, margin=3)
        rep = cs.run(d, animation=False)
        self.assertTrue(any("外周" in e for e in rep.errors))

    def test_exact_10px_margin_passes(self) -> None:
        rep = cs.run(build_set(self.tmp / "exact", margin=10), animation=False)
        self.assertEqual(rep.errors, [])


class TestFileSet(TempDirCase):
    def test_missing_main_is_error(self) -> None:
        d = build_set(self.tmp / "nomain")
        (d / "main.png").unlink()
        rep = cs.run(d, animation=False)
        self.assertTrue(any("main.png" in e for e in rep.errors))

    def test_invalid_count_is_error(self) -> None:
        rep = cs.run(build_set(self.tmp / "seven", count=7), animation=False)
        self.assertTrue(any("スタンプ画像が 7 個" in e for e in rep.errors))

    def test_gap_in_numbering_is_warning(self) -> None:
        d = build_set(self.tmp / "gap", count=8)
        (d / "03.png").rename(d / "09.png")
        rep = cs.run(d, animation=False)
        self.assertTrue(any("連番に欠け" in w for w in rep.warnings))

    def test_oversized_file_is_error(self) -> None:
        d = build_set(self.tmp / "heavy")
        target = d / "01.png"
        target.write_bytes(target.read_bytes() + b"\x00" * (cs.MAX_BYTES + 1))
        rep = cs.run(d, animation=False)
        self.assertTrue(any("上限 1MB" in e for e in rep.errors))

    def test_missing_directory_is_error(self) -> None:
        rep = cs.run(self.tmp / "nope", animation=False)
        self.assertTrue(any("見つからない" in e for e in rep.errors))


class TestAnimation(TempDirCase):
    def _anim_set(self, name: str, frames: int, seconds: float, size=(320, 270)) -> Path:
        d = self.tmp / name
        d.mkdir(parents=True, exist_ok=True)
        write_png(d / "main.png", 240, 240)
        write_png(d / "tab.png", 96, 74, margin=4)
        for i in range(1, 9):
            write_png(d / f"{i:02d}.png", *size, margin=2, apng=(frames, seconds))
        return d

    def test_valid_animation_has_no_errors(self) -> None:
        rep = cs.run(self._anim_set("anim", frames=12, seconds=3.0), animation=True)
        self.assertEqual(rep.errors, [])

    def test_too_many_frames_is_error(self) -> None:
        rep = cs.run(self._anim_set("frames", frames=24, seconds=3.0), animation=True)
        self.assertTrue(any("フレーム" in e for e in rep.errors))

    def test_too_long_is_error(self) -> None:
        rep = cs.run(self._anim_set("long", frames=10, seconds=6.0), animation=True)
        self.assertTrue(any("再生" in e for e in rep.errors))

    def test_oversized_animation_is_error(self) -> None:
        rep = cs.run(
            self._anim_set("biganim", frames=10, seconds=2.0, size=(370, 320)), animation=True
        )
        self.assertTrue(any("上限 320x270" in e for e in rep.errors))

    def test_static_png_in_animation_mode_is_error(self) -> None:
        rep = cs.run(build_set(self.tmp / "static"), animation=True)
        self.assertTrue(any("APNG ではない" in e for e in rep.errors))

    def test_apng_without_flag_is_warning(self) -> None:
        rep = cs.run(self._anim_set("noflag", frames=10, seconds=2.0), animation=False)
        self.assertTrue(any("APNG" in w for w in rep.warnings))


class TestExitCode(TempDirCase):
    def test_clean_set_returns_zero(self) -> None:
        self.assertEqual(cs.main([str(build_set(self.tmp / "ok"))]), 0)

    def test_broken_set_returns_one(self) -> None:
        d = build_set(self.tmp / "bad")
        write_png(d / "01.png", 400, 320)
        self.assertEqual(cs.main([str(d)]), 1)


if __name__ == "__main__":
    unittest.main()

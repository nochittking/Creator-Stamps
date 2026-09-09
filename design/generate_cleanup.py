# -*- coding: utf-8 -*-
"""手描き原案「ありがとう（ハザード）」の清書2案を 370x320 の SVG で組む。

案A 整地版  — 手描きの揺れを残したまま、位置・太さ・影だけ揃える
案B ベクター版 — 完全な左右対称。揺れを捨てて幾何学的に整える
"""
import pathlib

W, H = 370, 320
RED, INK, ORG = "#E8231A", "#1A1815", "#F08A24"

# ---- 三角形（外／内）。手描きの弓なりを残すため直線ではなく曲線で取る ----
TRI_OUT = ("M185,56 C233,106 289,164 320,194 C252,205 118,205 50,194 "
           "C81,164 137,106 185,56 Z")
TRI_IN  = ("M185,114 C215,145 246,177 260,189 C223,194 147,194 110,189 "
           "C124,177 155,145 185,114 Z")

# 完全対称版：同じ骨格を直線で引き直す
TRI_OUT_V = "M185,56 L320,194 L50,194 Z"
TRI_IN_V  = "M185,116 L260,190 L110,190 Z"

BLINK_L = ["M52,94 C36,102 30,116 34,128",
           "M36,130 C20,138 16,152 22,164",
           "M48,166 C34,175 30,189 36,199"]

def mirror(d):
    """x 座標を 370-x に置き換えて左右反転したパスを作る。"""
    res = ""
    parts = []
    cur = ""
    for ch in d:
        if ch.isalpha():
            parts.append(cur); parts.append(ch); cur = ""
        else:
            cur += ch
    parts.append(cur)
    for p in parts:
        if len(p) == 1 and p.isalpha():
            res += p
        elif p.strip():
            nums = p.replace(",", " ").split()
            flipped = []
            for j, n in enumerate(nums):
                v = float(n)
                flipped.append(f"{W - v:g}" if j % 2 == 0 else f"{v:g}")
            res += " " + ",".join(
                f"{flipped[k]},{flipped[k+1]}" for k in range(0, len(flipped), 2)) + " "
    return res

HEART = ("M0,9 C-11,1 -16,-8 -9,-14 C-5,-17 0,-14 0,-10 "
         "C0,-14 5,-17 9,-14 C16,-8 11,1 0,9 Z")

def sticker(mode):
    """mode: 'a' 整地版 / 'b' ベクター版"""
    hand = mode == "a"
    out, inn = (TRI_OUT, TRI_IN) if hand else (TRI_OUT_V, TRI_IN_V)
    font = "'Yusei Magic', sans-serif" if hand else "'Zen Maru Gothic', sans-serif"
    weight = 400 if hand else 900
    cap = "round" if hand else "butt"
    join = "round"

    # 整地版は赤の下に黒をわずかにずらして重ね、原案の「二度描き」の味を残す
    ghost = ""
    if hand:
        ghost = (f'<g transform="translate(-4,4)" opacity=".95">'
                 f'<path d="{out}" fill="none" stroke="{INK}" stroke-width="15" '
                 f'stroke-linejoin="{join}" stroke-linecap="{cap}"/>'
                 f'<path d="{inn}" fill="none" stroke="{INK}" stroke-width="12" '
                 f'stroke-linejoin="{join}" stroke-linecap="{cap}"/></g>')

    blinks = "".join(
        f'<path d="{d}" fill="none" stroke="{ORG}" stroke-width="{9 if hand else 8}" '
        f'stroke-linecap="round"/>' for d in BLINK_L)
    blinks += "".join(
        f'<path d="{mirror(d)}" fill="none" stroke="{ORG}" stroke-width="{9 if hand else 8}" '
        f'stroke-linecap="round"/>' for d in BLINK_L)

    tri = (f'<path d="{out}" fill="none" stroke="{RED}" stroke-width="{17 if hand else 16}" '
           f'stroke-linejoin="{join}" stroke-linecap="{cap}"/>'
           f'<path d="{inn}" fill="none" stroke="{RED}" stroke-width="{13 if hand else 13}" '
           f'stroke-linejoin="{join}" stroke-linecap="{cap}"/>')

    txt_size = 66 if hand else 62
    txt = (f'<text x="166" y="264" text-anchor="middle" dominant-baseline="central" '
           f'font-family="{font}" font-weight="{weight}" font-size="{txt_size}" '
           f'fill="{INK}">ありがとう</text>')

    heart = (f'<g transform="translate(324,258) scale(1.45)">'
             f'<path d="{HEART}" fill="{RED}"/></g>')

    return (f'<svg viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="ハザードランプのマークと「ありがとう」">'
            f'{blinks}{ghost}{tri}{txt}{heart}</svg>')

if __name__ == "__main__":
    d = pathlib.Path(__file__).parent
    (d / "build").mkdir(exist_ok=True)
    for m in ("a", "b"):
        (d / "build" / f"arigatou_{m}.svg").write_text(sticker(m), encoding="utf-8")
    print("清書2案を書き出し")

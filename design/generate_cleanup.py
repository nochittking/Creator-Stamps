# -*- coding: utf-8 -*-
"""手描き原案「ありがとう（ハザード）」の清書を 370x320 の SVG で組む。

ハザードマークの根幹は「内外 2 つの三角が全周で等間隔」であること。
ここを目分量で置くと形が壊れるため、内三角は外三角の**内心**を中心に
相似縮小して求め、等間隔であることを数値で検証してから描く。
"""
import math
import pathlib

W, H = 370, 320
RED, INK, ORG = "#E8231A", "#1A1815", "#F08A24"

# 外三角（原案の比率に合わせた 底辺282 : 高さ152 ≒ 0.54 の平たい三角）
APEX = (185.0, 62.0)
BL = (44.0, 214.0)
BR = (326.0, 214.0)

# 内外の間隔（各辺への垂線距離）。原案の実測 77px(740基準) = 38.5px を目安に 33 とした
GAP = 33.0

STROKE_OUT, STROKE_IN = 14.0, 11.0


def incenter_and_inradius(a, b, c):
    """三角形の内心と内接円半径。内心を中心に縮小すると全辺が等間隔で内側に寄る。"""
    la = math.dist(b, c)
    lb = math.dist(c, a)
    lc = math.dist(a, b)
    p = la + lb + lc
    cx = (la * a[0] + lb * b[0] + lc * c[0]) / p
    cy = (la * a[1] + lb * b[1] + lc * c[1]) / p
    area = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
    return (cx, cy), area / (p / 2)


def inner_triangle(a, b, c, gap):
    """内心を中心に相似縮小して、全辺から gap だけ内側にある三角を返す。"""
    center, r = incenter_and_inradius(a, b, c)
    k = (r - gap) / r
    shrink = lambda p: (center[0] + k * (p[0] - center[0]),
                        center[1] + k * (p[1] - center[1]))
    return shrink(a), shrink(b), shrink(c), center, r, k


def dist_to_line(p, q1, q2):
    """点 p から直線 q1q2 までの距離。等間隔かどうかの検証に使う。"""
    return (abs((q2[0] - q1[0]) * (q1[1] - p[1]) - (q1[0] - p[0]) * (q2[1] - q1[1]))
            / math.dist(q1, q2))


IN_APEX, IN_BL, IN_BR, CENTER, R, K = inner_triangle(APEX, BL, BR, GAP)


def bowed(a, b, c, sag, bulge):
    """手描きの弓なりを残した三角パス。底辺は下に、斜辺は外へふくらませる。"""
    def ctrl(p, q, amount):
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        vx, vy = mid[0] - CENTER[0], mid[1] - CENTER[1]
        n = math.hypot(vx, vy) or 1
        return (mid[0] + vx / n * amount * 2, mid[1] + vy / n * amount * 2)

    r_ctrl = ctrl(a, c, bulge)
    l_ctrl = ctrl(b, a, bulge)
    base_ctrl = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2 + sag * 2)
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    return (f"M{f(a)} Q{f(r_ctrl)} {f(c)} Q{f(base_ctrl)} {f(b)} Q{f(l_ctrl)} {f(a)} Z")


TRI_OUT = bowed(APEX, BL, BR, sag=10, bulge=6)
TRI_IN = bowed(IN_APEX, IN_BL, IN_BR, sag=6, bulge=4)
TRI_OUT_V = f"M{APEX[0]:.0f},{APEX[1]:.0f} L{BR[0]:.0f},{BR[1]:.0f} L{BL[0]:.0f},{BL[1]:.0f} Z"
TRI_IN_V = (f"M{IN_APEX[0]:.1f},{IN_APEX[1]:.1f} L{IN_BR[0]:.1f},{IN_BR[1]:.1f} "
            f"L{IN_BL[0]:.1f},{IN_BL[1]:.1f} Z")

# 点滅を表すオレンジの筆。三角の辺に当たらない位置に置く
BLINK_L = ["M76,84 C60,86 50,98 54,110",
           "M52,118 C36,122 28,136 34,148",
           "M62,158 C46,164 38,178 44,190"]


def mirror(d):
    """x 座標を W-x に置き換えて左右反転する。"""
    parts, cur = [], ""
    for ch in d:
        if ch.isalpha():
            parts += [cur, ch]
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    res = ""
    for p in parts:
        if len(p) == 1 and p.isalpha():
            res += p
        elif p.strip():
            nums = [float(n) for n in p.replace(",", " ").split()]
            flipped = [f"{W - v:g}" if i % 2 == 0 else f"{v:g}" for i, v in enumerate(nums)]
            res += " " + ",".join(f"{flipped[k]},{flipped[k+1]}"
                                  for k in range(0, len(flipped), 2)) + " "
    return res


HEART = ("M0,9 C-11,1 -16,-8 -9,-14 C-5,-17 0,-14 0,-10 "
         "C0,-14 5,-17 9,-14 C16,-8 11,1 0,9 Z")


def sticker(mode):
    """mode: 'a' 整地版（手描きの揺れを残す） / 'b' ベクター版（完全対称）"""
    hand = mode == "a"
    out, inn = (TRI_OUT, TRI_IN) if hand else (TRI_OUT_V, TRI_IN_V)
    font = "'Yusei Magic', sans-serif" if hand else "'Zen Maru Gothic', sans-serif"
    weight = 400 if hand else 900

    blinks = "".join(
        f'<path d="{d}" fill="none" stroke="{ORG}" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="{mirror(d)}" fill="none" stroke="{ORG}" stroke-width="9" stroke-linecap="round"/>'
        for d in BLINK_L)

    ghost = ""
    if hand:  # 原案の「二度描き」のズレを残す
        ghost = (f'<g transform="translate(-4,3)">'
                 f'<path d="{out}" fill="none" stroke="{INK}" stroke-width="{STROKE_OUT}" '
                 f'stroke-linejoin="round"/>'
                 f'<path d="{inn}" fill="none" stroke="{INK}" stroke-width="{STROKE_IN}" '
                 f'stroke-linejoin="round"/></g>')

    tri = (f'<path d="{out}" fill="none" stroke="{RED}" stroke-width="{STROKE_OUT}" '
           f'stroke-linejoin="round"/>'
           f'<path d="{inn}" fill="none" stroke="{RED}" stroke-width="{STROKE_IN}" '
           f'stroke-linejoin="round"/>')

    txt = (f'<text x="158" y="268" text-anchor="middle" dominant-baseline="central" '
           f'font-family="{font}" font-weight="{weight}" font-size="54" fill="{INK}">'
           f'ありがとう</text>')
    heart = f'<g transform="translate(324,262) scale(1.4)"><path d="{HEART}" fill="{RED}"/></g>'

    return (f'<svg viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="ハザードランプのマークと「ありがとう」">'
            f'{blinks}{ghost}{tri}{txt}{heart}</svg>')


def verify():
    """内三角の各頂点から外三角の各辺までの距離が等しいことを確認する。"""
    sides = [(APEX, BR), (BR, BL), (BL, APEX)]
    labels = ["右辺", "底辺", "左辺"]
    print(f"外三角 底辺{BR[0]-BL[0]:.0f} × 高さ{BL[1]-APEX[1]:.0f} "
          f"（比 {(BL[1]-APEX[1])/(BR[0]-BL[0]):.2f}）")
    print(f"内心 ({CENTER[0]:.1f}, {CENTER[1]:.1f})  内接円半径 {R:.1f}  縮小率 {K:.3f}")
    print(f"内三角 底辺{IN_BR[0]-IN_BL[0]:.0f} × 高さ{IN_BL[1]-IN_APEX[1]:.0f}")
    ok = True
    for (q1, q2), label in zip(sides, labels):
        # その辺に接していない内三角の頂点からの距離を測る
        d = min(dist_to_line(p, q1, q2) for p in (IN_APEX, IN_BL, IN_BR)
                if dist_to_line(p, q1, q2) > 1)
        gap_visible = d - STROKE_OUT / 2 - STROKE_IN / 2
        print(f"  {label}: 中心線間 {d:.1f}px / 線と線の隙間 {gap_visible:.1f}px")
        if abs(d - GAP) > 0.6:
            ok = False
    print("等間隔:", "OK" if ok else "!! 不均等")
    assert ok, "内外の三角が等間隔になっていない"
    return ok


if __name__ == "__main__":
    verify()
    d = pathlib.Path(__file__).parent
    (d / "build").mkdir(exist_ok=True)
    for m in ("a", "b"):
        (d / "build" / f"arigatou_{m}.svg").write_text(sticker(m), encoding="utf-8")
    print("清書2案を書き出し")

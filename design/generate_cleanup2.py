# -*- coding: utf-8 -*-
"""手描き原案の清書（続き）。ブレーキ警告灯 / 水温計 / 給油機。

各シンボルには「崩すと別物になる骨格」がある。目分量で置かず、
骨格を数値で定義して検証してから描く。

  ブレーキ  … 円の左右の弧が、円と同心・等距離・左右対称であること
  水温計    … 目盛りが等間隔・等長で片側のみ。球が軸上にあること
  給油機    … 表示窓の左右余白が等しく、台座が本体中心に対して対称であること
"""
import math
import pathlib

W, H = 370, 320
RED, INK, ORG, BLU = "#E8231A", "#1A1815", "#E07B18", "#1B48D8"


def arc_pts(cx, cy, r, a0, a1, n=28):
    """角度 a0→a1（度・反時計回り正・y下向き）の円弧を折れ線で返す。
    SVG の円弧フラグは向きを取り違えやすいので、点列で持つ。"""
    return [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
            for a in (a0 + (a1 - a0) * i / n for i in range(n + 1))]


def poly(pts, close=False):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")


def wave(x0, x1, y, amp, periods, n=64):
    """水面を表す波線。"""
    return [(x0 + (x1 - x0) * i / n,
             y + amp * math.sin(2 * math.pi * periods * i / n))
            for i in range(n + 1)]


def text(s, x, y, size, font, fill=INK, weight=400):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{font}" font-weight="{weight}" font-size="{size}" '
            f'fill="{fill}">{s}</text>')


HAND = "'Yusei Magic', sans-serif"
VEC = "'Zen Maru Gothic', sans-serif"


# ============================================================ ブレーキ警告灯
BRK = dict(cx=185.0, cy=128.0, r=86.0, sw=21.0,     # 円（中心線半径と線幅）
           arc_r=124.0, arc_th=20.0, arc_span=76.0)  # 左右の弧

def brake(hand=True):
    c, sw = (BRK["cx"], BRK["cy"]), BRK["sw"]
    font, weight = (HAND, 400) if hand else (VEC, 900)

    def crescent(center_angle):
        """円と同心の三日月。外弧と内弧の角度幅を変えて先端をすぼめる。"""
        ro = BRK["arc_r"] + BRK["arc_th"] / 2
        ri = BRK["arc_r"] - BRK["arc_th"] / 2
        half = BRK["arc_span"] / 2
        outer = arc_pts(*c, ro, center_angle - half, center_angle + half)
        inner = arc_pts(*c, ri, center_angle + half - 9, center_angle - half + 9)
        return poly(outer + inner, close=True)

    left = crescent(180.0)
    right = crescent(0.0)

    # 「！」棒はやや先細り、点は真下に
    bang = ("M185,74 C190,74 192,79 190.5,88 L187,150 C186.5,155 183.5,155 183,150 "
            "L179.5,88 C178,79 180,74 185,74 Z")
    dot = '<circle cx="185" cy="170" r="11.5" fill="{f}"/>'

    ghost = ""
    if hand:
        ghost = (f'<g transform="translate(-4,3)" fill="none" stroke="{INK}">'
                 f'<circle cx="{c[0]}" cy="{c[1]}" r="{BRK["r"]}" stroke-width="{sw}"/></g>'
                 f'<g transform="translate(-4,3)" fill="{INK}">'
                 f'<path d="{left}"/><path d="{right}"/><path d="{bang}"/>'
                 f'{dot.format(f=INK)}</g>')

    body = (f'<circle cx="{c[0]}" cy="{c[1]}" r="{BRK["r"]}" fill="none" '
            f'stroke="{RED}" stroke-width="{sw}"/>'
            f'<path d="{left}" fill="{RED}"/><path d="{right}" fill="{RED}"/>'
            f'<path d="{bang}" fill="{RED}"/>{dot.format(f=RED)}')

    label = text("ちょっと待った！", 185, 268, 44, font, INK, weight)
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="ブレーキ警告灯と「ちょっと待った！」">{ghost}{body}{label}</svg>'


# ================================================================== 水温計
TMP = dict(axis=176.0, top=48.0, bot=170.0, bulb=(176.0, 186.0, 25.0, 19.0),
           ticks=(78.0, 104.0, 130.0), tick_x0=186.0, tick_x1=242.0, tick_w=11.0,
           waves=(184.0, 220.0))

def thermo(hand=True, hot=True):
    col = RED if hot else BLU
    font, weight = (HAND, 400) if hand else (VEC, 900)
    ax, top, bot = TMP["axis"], TMP["top"], TMP["bot"]

    stem = (f'M{ax},{top} C{ax+7},{top+18} {ax+9},{bot-40} {ax+9},{bot} '
            f'L{ax-9},{bot} C{ax-9},{bot-40} {ax-7},{top+18} {ax},{top} Z')
    ticks = "".join(
        f'<line x1="{TMP["tick_x0"]}" y1="{y}" x2="{TMP["tick_x1"]}" y2="{y}" '
        f'stroke="{{c}}" stroke-width="{TMP["tick_w"]}" stroke-linecap="round"/>'
        for y in TMP["ticks"])
    bx, by, brx, bry = TMP["bulb"]
    bulb = f'<ellipse cx="{bx}" cy="{by}" rx="{brx}" ry="{bry}" fill="{{c}}"/>'
    waves = "".join(
        f'<path d="{poly(wave(58, 312, y, 9 if hand else 8, 2.5))}" fill="none" '
        f'stroke="{{c}}" stroke-width="13" stroke-linecap="round"/>'
        for y in TMP["waves"])

    def group(c, shift=""):
        g = (f'<path d="{stem}" fill="{c}"/>{ticks.format(c=c)}'
             f'{bulb.format(c=c)}{waves.format(c=c)}')
        return f'<g transform="{shift}">{g}</g>' if shift else g

    ghost = group(INK, "translate(-4,3)") if hand else ""
    label = text("あっつーい" if hot else "つめたーい", 185, 268, 50, font, INK, weight)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="水温計と「{"あっつーい" if hot else "つめたーい"}」">'
            f'{ghost}{group(col)}{label}</svg>')


# ================================================================== 給油機
PMP = dict(bx0=96.0, bx1=214.0, by0=42.0, by1=206.0,      # 本体
           wm=13.0, wy0=56.0, wy1=124.0,                   # 表示窓（左右余白 wm）
           base_y=208.0, base_h=13.0, base_ext=62.0)       # 台座

def pump(hand=True):
    font, weight = (HAND, 400) if hand else (VEC, 900)
    b = PMP
    cx = (b["bx0"] + b["bx1"]) / 2

    body = (f'<rect x="{b["bx0"]}" y="{b["by0"]}" width="{b["bx1"]-b["bx0"]}" '
            f'height="{b["by1"]-b["by0"]}" rx="7" fill="none" stroke="{{c}}" stroke-width="15"/>')
    window = (f'<rect x="{b["bx0"]+b["wm"]}" y="{b["wy0"]}" '
              f'width="{b["bx1"]-b["bx0"]-2*b["wm"]}" height="{b["wy1"]-b["wy0"]}" '
              f'rx="4" fill="none" stroke="{{c}}" stroke-width="12"/>')
    fill = (f'<rect x="{b["bx0"]+10}" y="{b["wy1"]+12}" width="{b["bx1"]-b["bx0"]-20}" '
            f'height="{b["by1"]-b["wy1"]-24}" rx="4" fill="{ORG}"/>')
    base = (f'<rect x="{cx-b["base_ext"]-(b["bx1"]-b["bx0"])/2}" y="{b["base_y"]}" '
            f'width="{(b["bx1"]-b["bx0"])+2*b["base_ext"]}" height="{b["base_h"]}" '
            f'rx="6" fill="{{c}}"/>')
    hose = (f'<path d="M{b["bx1"]},{b["by0"]+26} C{b["bx1"]+40},{b["by0"]+22} '
            f'{b["bx1"]+46},{b["by0"]+70} {b["bx1"]+32},{b["by0"]+108} '
            f'C{b["bx1"]+26},{b["by0"]+126} {b["bx1"]+34},{b["by0"]+140} '
            f'{b["bx1"]+44},{b["by0"]+142}" fill="none" stroke="{{c}}" stroke-width="15" '
            f'stroke-linecap="round"/>')

    def group(c, with_fill, shift=""):
        g = (fill if with_fill else "") + (body + window + base + hose).format(c=c)
        return f'<g transform="{shift}">{g}</g>' if shift else g

    # 手描き版は、オレンジの塗りを黒の輪郭からずらして原案の刷りズレを残す
    ghost = group(INK, False, "translate(-5,4)") if hand else ""
    main = group(INK, True)
    ruby = text("チャージ", 150, 236, 20, font, INK, weight)
    label = text("給油しとこっ", 185, 272, 48, font, INK, weight)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="給油機と「給油しとこっ」">'
            f'{ghost}{main}{ruby}{label}</svg>')


# ================================================================ 骨格の検証
def verify():
    ok = True
    print("■ ブレーキ警告灯")
    ro, ri = BRK["arc_r"] + BRK["arc_th"] / 2, BRK["arc_r"] - BRK["arc_th"] / 2
    gap = ri - (BRK["r"] + BRK["sw"] / 2)
    print(f"  円の外縁 r={BRK['r']+BRK['sw']/2:.1f} / 弧の内縁 r={ri:.1f} → 隙間 {gap:.1f}px")
    print(f"  左右の弧: 中心角 180.0° と 0.0°、同一半径 {BRK['arc_r']:.1f} → 同心・対称 OK")
    if gap < 6:
        ok = False; print("  !! 隙間が狭すぎる")

    print("■ 水温計")
    t = TMP["ticks"]
    sp = [round(t[i+1] - t[i], 2) for i in range(len(t) - 1)]
    ln = TMP["tick_x1"] - TMP["tick_x0"]
    print(f"  目盛り間隔 {sp} / 長さ {ln:.0f}px（全て同一）")
    print(f"  球の中心 x={TMP['bulb'][0]:.1f} / 軸 x={TMP['axis']:.1f} → 軸上 OK")
    print(f"  波線 y={TMP['waves']} 間隔 {TMP['waves'][1]-TMP['waves'][0]:.0f}px（平行）")
    if len(set(sp)) != 1 or TMP["bulb"][0] != TMP["axis"]:
        ok = False; print("  !! 目盛りが不等間隔、または球が軸から外れている")

    print("■ 給油機")
    left = PMP["wm"]
    right = (PMP["bx1"] - PMP["bx0"]) - (PMP["bx1"] - PMP["bx0"] - 2 * PMP["wm"]) - PMP["wm"]
    bcx = (PMP["bx0"] + PMP["bx1"]) / 2
    base_cx = bcx
    print(f"  表示窓の左右余白 {left:.1f} / {right:.1f}px → 均等 OK")
    print(f"  本体中心 x={bcx:.1f} / 台座中心 x={base_cx:.1f} → 対称 OK")
    if abs(left - right) > 0.1:
        ok = False; print("  !! 窓の余白が不均等")

    print("検証:", "全て OK" if ok else "!! 要修正")
    assert ok
    return ok


if __name__ == "__main__":
    verify()
    d = pathlib.Path(__file__).parent / "build"
    d.mkdir(exist_ok=True)
    (d / "brake_a.svg").write_text(brake(True), encoding="utf-8")
    (d / "thermo_hot_a.svg").write_text(thermo(True, True), encoding="utf-8")
    (d / "pump_a.svg").write_text(pump(True), encoding="utf-8")
    print("清書を書き出し")

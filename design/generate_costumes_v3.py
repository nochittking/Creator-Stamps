# -*- coding: utf-8 -*-
"""コスプレ衣装絵文字 v3。v2 の失敗を構造で潰す。

v2 が可愛くなかった決定的な理由（描いて見て特定）
  A. 袖が胴と別パーツの「横向きの輪」→ 鍋の取っ手に見えた。
     → 首→肩→袖→袖口→脇→裾 を【一本の輪郭】で描く。袖は斜め下に振る。
  B. ほっぺを付けたら、襟＋ほっぺ が【顔】に読めた。服が顔になった。
     → ほっぺ全廃。可愛さは輪郭の比率で出す。
  C. 正方形に近い比率 → 2頭身の服に見えない。
     → 首元を広く・肩を狭く・裾を大きく広げる（A ライン）。
  D. 首の穴が描かれていない → 「マネキンが着ている」感が出ない。
     → 襟ぐりを一段濃い色の楕円で必ず抜く。
  E. 裾のスカラップが大きすぎて雲になった → 振幅を半分、数を倍。
"""
import pathlib

SW = 3.4          # 外形線
SWI = 2.0         # 内側の線

# v3 初版は「同系色の薄い輪郭」にしたが、180px では線が消えて弱く見えた。
# LINE の絵文字ガイドライン（はっきり太めに濃い色でアウトライン）にも反する。
# → 外形線は濃い墨色で固定し、柔らかさは配色と曲線で出す。
INK = "#3B3540"

def dark(hex_color, k=0.42):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r*k), int(g*k), int(b*k))

def mid(hex_color, k=0.88):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r*k), int(g*k), int(b*k))

def P(d, fill="none", sw=SWI, stroke="#000", extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
            f' stroke-linejoin="round" stroke-linecap="round" {extra}/>')

def wave(x0, x1, y, n=10, amp=2.6):
    """裾の波。小さく細かく。大きくすると雲になる。"""
    step = (x1 - x0) / n
    return "".join(f"q{step/2:.2f},{amp:.2f} {step:.2f},0 " for _ in range(n))

# ----------------------------------------------------- 一本輪郭のシルエット
def body(c, ink, hem=86, half=34, sleeve="short", flare=True, wav=True):
    """首→左肩→左袖→袖口→脇→左裾→裾→右裾→脇→右袖→右肩→首 を一筆で。

    左右で袖口を 1.5 ずらす（機械的な対称をやめる）。
    """
    if sleeve == "short":
        Lc, Rc, cy = 16, 85, 47          # 袖口 x と y
        Lcy, Rcy = cy, cy - 1.5
    elif sleeve == "long":
        Lc, Rc, cy = 11, 90, 62
        Lcy, Rcy = cy, cy - 2.0
    else:                                 # ノースリーブ
        Lc, Rc = 31, 70
        Lcy = Rcy = 36
    hl, hr = 50 - half, 50 + half
    waist = 30 if flare else 34
    hemline = (wave(hl, hr, hem, 12, 2.4) if wav else f"L{hr},{hem} ")

    if sleeve == "none":
        d = (f"M38,15 C30,16 26,20 25,27 "
             f"C23,45 {hl+2},70 {hl},{hem-1} "
             f"{hemline}"
             f"C{hr},{hem-1} 77,45 75,27 "
             f"C74,20 70,16 62,15 "
             f"C58,23 42,23 38,15 Z")
    else:
        d = (f"M38,15 C31,15.5 27,18 25.5,23 "          # 左肩
             f"C22,30 {Lc+1},{Lcy-12} {Lc},{Lcy-4} "     # 左袖 外側（斜め下）
             f"C{Lc-1},{Lcy+2} {Lc+6},{Lcy+4} {Lc+11},{Lcy+1} "   # 袖口
             f"C{Lc+13},{Lcy-6} 28,40 {waist},38 "       # 袖 内側→脇
             f"C27,52 {hl+2},70 {hl},{hem-1} "           # 左脇→裾
             f"{hemline}"                                 # 裾
             f"C{hr},{hem-1} 73,52 {100-waist},38 "      # 右裾→脇
             f"C{Rc-13},{Rcy-6} {Rc-11},{Rcy+4} {Rc-11},{Rcy+1} "
             f"C{Rc-6},{Rcy+4} {Rc+1},{Rcy+2} {Rc},{Rcy-4} "
             f"C{Rc-1},{Rcy-12} 78,30 74.5,23 "
             f"C73,18 69,15.5 62,15 "
             f"C58,23 42,23 38,15 Z")
    return P(d, c, SW, ink)

def neckhole(c="#E7DED6", ink=INK):
    """首の穴。これが無いと『着ている』に見えない。"""
    return P("M38,15 C42,23 58,23 62,15 C58,11 42,11 38,15 Z", c, SWI, ink)

def cuff(c, ink, sleeve="short"):
    y = 45 if sleeve == "short" else 60
    return (P(f"M16,{y} C21,{y+5} 26,{y+5} 28,{y+1}", "none", SWI, ink)
          + P(f"M85,{y-1.5} C80,{y+3.5} 75,{y+3.5} 73,{y-0.5}", "none", SWI, ink))

# ----------------------------------------------------- パーツ
def sailor_collar(c, ink, line="#FFF"):
    # 後ろ襟（台形）＋ 前の V。板に見せないため前身頃は開ける。
    out = P("M32,17 C38,23 62,23 68,17 L65,42 C59,46 41,46 35,42 Z", c, SWI, ink)
    for dy in (0, 3.2):
        out += P(f"M38,{32+dy} C44,35 56,35 62,{31+dy}", "none", 1.5, line)
    out += P("M41,18 L50,34 L59,18", "none", SWI, ink)
    return out

def bow(x, y, c, ink, s=1.0):
    """羽根は大きく丸く、結び目は小さく。逆にするとボルトに見える（v3の失敗）。"""
    w, h = 13*s, 8*s
    k = 2.2*s
    return (P(f"M{x-1.6},{y} C{x-w},{y-h} {x-w},{y+h} {x-2.4},{y+1.6} Z", c, SWI, ink)
          + P(f"M{x+1.6},{y} C{x+w},{y-h+0.8} {x+w},{y+h} {x+2.4},{y+1.6} Z", c, SWI, ink)
          + f'<rect x="{x-k}" y="{y-k+0.4}" width="{2*k}" height="{2*k}" rx="{k*0.6}"'
            f' fill="{c}" stroke="{ink}" stroke-width="{SWI}"/>')

def necktie(x, y, c, ink):
    return P(f"M{x-3},{y} L{x+3},{y} L{x+2.4},{y+5} L{x+4},{y+17} "
             f"C{x},{y+20} {x},{y+20} {x-4},{y+17} L{x-2.4},{y+5} Z", c, SWI, ink)

def apron(c, ink):
    return (P("M39,22 C44,27 56,27 61,22 L60,46 C67,49 70,57 71,76 "
              "C60,81 40,81 29,76 C30,57 33,49 40,46 Z", c, SWI, ink)
          + P(f"M29,76 {wave(29,71,76,8,2.6)} Z", c, SWI, ink))

def hem_fur(y, c="#FFF", ink=INK, h=6, half=33):
    return P(f"M{50-half},{y} {wave(50-half,50+half,y,11,2.4)} L{50+half},{y-h} "
             f"{wave(50+half,50-half,y-h,11,-2.4)} Z", c, SWI, ink)

def belt(y, c, ink, half=27):
    return P(f"M{50-half},{y} C40,{y+4} 60,{y+4} {50+half},{y-1} "
             f"L{50+half},{y+5} C60,{y+10} 40,{y+10} {50-half},{y+6} Z", c, SWI, ink)

def skirt(c, ink, top=52, hem=84, half=34):
    """腰で本体に重ねる A ライン。帯にしないこと（v3 初版の失敗）。"""
    hl, hr = 50 - half, 50 + half
    return P(f"M28,{top} C40,{top+4} 60,{top+4} 72,{top-1} "
             f"C{hr-2},{hem-8} {hr},{hem-3} {hr},{hem-1} "
             f"{wave(hr, hl, hem, 12, -2.4)} "
             f"C{hl},{hem-3} {hl+2},{hem-8} 28,{top} Z", c, SW, ink)

def dots(c, pts):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>' for x, y, r in pts)

# ----------------------------------------------------- 配色
PAL = dict(navy="#8296CB", white="#FFFFFF", red="#EF8091", pink="#F9C4D8",
           black="#5F5A6B", gold="#EFC96E", sky="#A6D6EF", rose="#E8879E",
           cream="#FFF6E9", mint="#A6DCC7")

VB = "-2 -2 104 104"
HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360" '
        f'viewBox="{VB}">')

# ----------------------------------------------------- 6案（v2と同じ衣装）
def c_sailor():
    w, n = PAL["white"], PAL["navy"]
    iw, inv = INK, INK
    return (body(w, iw, 84, 33) + skirt(n, inv, 54, 84, 34) + cuff(w, iw)
            + sailor_collar(n, inv) + neckhole()
            + necktie(50, 32, PAL["red"], dark(PAL["red"])))

def c_nurse():
    w, s = PAL["white"], PAL["sky"]
    iw, isk = INK, dark(s)
    return (body(w, iw, 84, 32) + cuff(w, iw) + neckhole()
            + P("M38,15 C44,24 56,24 62,15 C64,22 58,28 50,28 C42,28 36,22 38,15 Z",
                s, SWI, isk)
            + belt(52, s, isk)
            + P("M62,40 v9 M57.5,44.5 h9", "none", 3.0, PAL["red"]))

def c_maid():
    bk, w = PAL["black"], PAL["white"]
    ib, iw = INK, INK
    return (body(bk, ib, 86, 34) + cuff(bk, ib) + apron(w, iw) + neckhole()
            + bow(50, 26, w, iw, 0.85))

def c_santa():
    r, w = PAL["red"], PAL["white"]
    ir, iw = INK, INK
    return (body(r, ir, 82, 33) + cuff(r, ir) + hem_fur(82, w, iw, 7, 33)
            + belt(52, PAL["black"], INK)
            + neckhole() + hem_fur(24, w, iw, 5, 22))

def c_loli():
    p, w = PAL["pink"], PAL["white"]
    ip, iw = INK, INK
    return (body(p, ip, 86, 35) + cuff(p, ip) + hem_fur(86, w, iw, 8, 35)
            + P("M38,15 C44,24 56,24 62,15 C64,23 58,29 50,29 C42,29 36,23 38,15 Z",
                w, SWI, iw)
            + neckhole() + bow(50, 33, PAL["rose"], dark(PAL["rose"]), 0.9)
            + belt(50, w, iw, 26))

def c_china():
    r, g = PAL["rose"], PAL["gold"]
    ir, ig = INK, dark(g, 0.55)
    return (body(r, ir, 88, 28, "short", False) + cuff(r, ir) + neckhole()
            + P("M36,16 C42,24 58,24 64,16 L64,25 C57,29 43,29 36,25 Z", r, SWI, ir)
            + P("M50,28 C58,33 62,42 61,52", "none", 2.2, ig)
            + dots(g, [(55, 33, 2.4), (59, 42, 2.4), (61, 51, 2.4)])
            + P("M50,60 C48,66 52,66 50,72", "none", 1.8, ig))

V3 = [("01", c_sailor), ("07", c_nurse), ("09", c_maid),
      ("21", c_santa), ("28", c_china), ("30", c_loli)]

if __name__ == "__main__":
    d = pathlib.Path(__file__).parent / "build" / "v3"
    d.mkdir(parents=True, exist_ok=True)
    for name, fn in V3:
        (d / f"{name}.svg").write_text(HEAD + fn() + "</svg>", encoding="utf-8")
    print(f"{len(V3)} 案")

# -*- coding: utf-8 -*-
"""コスプレ衣装絵文字 40案（v3骨格）。v1 の硬さを直した決定版ラフ。

v3 で確立した骨格をそのまま 40 着に適用する。
  ・首→肩→袖→袖口→脇→裾 を一本の輪郭で描く（袖を別パーツにしない）
  ・袖は真横ではなく斜め下 40度
  ・裾は A ライン。腰(y=38前後)から裾(y=84前後)へ必ず広げる
  ・襟ぐりは濃い色の楕円で必ず抜く（着ている感）
  ・外形線は濃い墨色 INK。柔らかさは配色と曲線で出す
  ・ほっぺ・顔要素は描かない（服が顔に読めてしまう）
"""
import pathlib
from generate_costumes_v3 import (
    SW, SWI, INK, dark, mid, P, wave, body, neckhole, cuff, sailor_collar,
    bow, necktie, apron, hem_fur, belt, dots, skirt, PAL, HEAD,
)

C = dict(
    navy="#8296CB", dnavy="#5C6FA8", white="#FFFFFF", red="#EF8091",
    dred="#D8566C", pink="#F9C4D8", lpink="#FCE0EA", black="#5F5A6B",
    gold="#EFC96E", sky="#A6D6EF", rose="#E8879E", cream="#FFF6E9",
    mint="#A6DCC7", green="#7FC49A", purple="#B9A3DD", lav="#DCCFF2",
    orange="#F5A45F", brown="#C49A6C", grey="#C9C6D1", beige="#EBDCC4",
    khaki="#A8B183", yellow="#F7DE8B", teal="#7FC6C6",
)

# ---------------------------------------------------------------- 追加パーツ
def legs(c, ink, hem=90, w=26, crotch=64):
    """ズボン。body(hem=60) の下に先に描いて重ねる。"""
    l, r = 50 - w, 50 + w
    return P(f"M{l},52 C{l-1},68 {l+1},{hem-6} {l+2},{hem} "
             f"C{l+2},{hem+2.5} 45,{hem+2.5} 45,{hem} "
             f"C45,{hem-10} 50,{crotch+4} 50,{crotch} "
             f"C50,{crotch+4} 55,{hem-10} 55,{hem} "
             f"C55,{hem+2.5} {r-2},{hem+2.5} {r-2},{hem} "
             f"C{r-1},{hem-6} {r+1},68 {r},52 Z", c, SW, ink)

def kimono(c, ink, hem=88, half=33):
    """和装。袖は四角く垂らす。前は合わせの V。"""
    hl, hr = 50 - half, 50 + half
    return (P(f"M38,15 C30,16 25,19 24,25 L13,30 C10,42 11,54 13,62 "
              f"C17,64 22,62 24,58 C23,70 {hl+1},78 {hl},{hem} "
              f"L{hr},{hem} C{hr-1},78 77,70 76,58 "
              f"C78,62 83,64 87,62 C89,54 90,42 87,30 L76,25 "
              f"C75,19 70,16 62,15 C58,23 42,23 38,15 Z", c, SW, ink)
          + P("M38,15 L50,40 L62,15", "none", SWI, ink))

def furisode_sleeves(c, ink):
    """振袖の袂。本体の【後】に呼ぶと隠れる。前に重ねて外へ大きく垂らす。"""
    return (P("M24,28 C16,28 8,32 6,38 C3,54 4,70 8,82 C14,84 20,82 23,76 "
              "C25,60 25,42 24,28 Z", c, SW, ink)
          + P("M76,27 C84,27 92,31 94,37 C97,53 96,69 92,81 C86,83 80,81 77,75 "
              "C75,59 75,41 76,27 Z", c, SW, ink))

def obi(c, ink, y=52, h=11):
    return P(f"M25,{y} C40,{y+4} 60,{y+4} 75,{y-1} L75,{y+h-1} "
             f"C60,{y+h+4} 40,{y+h+4} 25,{y+h} Z", c, SWI, ink)

def lapel(c, ink, inner="#FFFFFF"):
    return (P("M38,15 L50,44 L62,15 C58,23 42,23 38,15 Z", inner, SWI, ink)
          + P("M36,16 L50,44 L41,17 Z", c, SWI, ink)
          + P("M64,16 L50,44 L59,17 Z", c, SWI, ink))

def buttons(c, ink, pts):
    return "".join(f'<circle cx="{x}" cy="{y}" r="2.3" fill="{c}" '
                   f'stroke="{ink}" stroke-width="1.4"/>' for x, y in pts)

def round_collar(c, ink, w=1.0):
    return P(f"M{50-12*w},15 C{50-6*w},24 {50+6*w},24 {50+12*w},15 "
             f"C{50+13*w},23 {50+8*w},29 50,29 "
             f"C{50-8*w},29 {50-13*w},23 {50-12*w},15 Z", c, SWI, ink)

def stand_collar(c, ink):
    return P("M37,16 C42,24 58,24 63,16 L63,25 C57,29 43,29 37,25 Z", c, SWI, ink)

def hood(c, ink):
    return P("M35,17 C33,6 67,6 65,17 C58,23 42,23 35,17 Z", c, SWI, ink)

def cape(c, ink, hem=84):
    """本体より必ず外に出す。v2 は幅が足りず縁しか見えなかった。"""
    return P(f"M33,16 C22,19 10,30 4,{hem} C28,{hem+5} 72,{hem+5} 96,{hem} "
             f"C90,30 78,19 67,16 C60,23 40,23 33,16 Z", c, SW, ink)

def wings(c, ink):
    """胴より大きく描かないと翼に見えない（v2の失敗）。羽根の段も入れる。"""
    return (P("M34,30 C22,10 4,8 2,26 C0,44 10,58 26,58 C32,56 36,48 34,30 Z",
              c, SW, ink)
          + P("M66,29 C78,9 96,7 98,25 C100,43 90,57 74,57 C68,55 64,47 66,29 Z",
              c, SW, ink)
          + P("M10,22 C14,34 18,44 24,50 M6,32 C11,42 16,50 22,54", "none", 1.8, ink)
          + P("M90,21 C86,33 82,43 76,49 M94,31 C89,41 84,49 78,53", "none", 1.8, ink))

def jag_hem(y, c, ink, half=33, n=7, d=8):
    """ギザギザ裾（ゾンビ・かぼちゃ）。"""
    hl, hr = 50 - half, 50 + half
    step = (hr - hl) / n
    pts = "".join(f"L{hl+step*(i+0.5):.1f},{y+d} L{hl+step*(i+1):.1f},{y} "
                  for i in range(n))
    return P(f"M{hl},{y-10} L{hl},{y} {pts} L{hr},{y-10} Z", c, SW, ink)

def pompom(x, y, c, ink, r=11):
    """房は丸い塊＋放射の切れ込み。星形にすると蝶ネクタイに見える（v2の失敗）。"""
    import math
    out = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="{ink}" stroke-width="{SW}"/>'
    for k in range(8):
        a = math.radians(k * 45 + 12)
        out += P(f"M{x+r*0.35*math.cos(a):.1f},{y+r*0.35*math.sin(a):.1f} "
                 f"L{x+r*0.92*math.cos(a):.1f},{y+r*0.92*math.sin(a):.1f}",
                 "none", 1.6, ink)
    return out

def stripe_lines(c, pts, sw=2.6):
    return "".join(P(d, "none", sw, c) for d in pts)

def pocket(x, y, c, ink, w=9, h=8):
    """角丸の貼りポケット。"""
    return P(f"M{x-w/2},{y} h{w} v{h-2} q0,2 -2,2 h-{w-4} q-2,0 -2,-2 Z",
             c, SWI, ink)

def frill_row(y, c, ink, half=30, n=9, amp=2.4, h=5):
    return P(f"M{50-half},{y} {wave(50-half,50+half,y,n,amp)} L{50+half},{y-h} "
             f"{wave(50+half,50-half,y-h,n,-amp)} Z", c, SWI, ink)

# ================================================================ 40 案
def f01():  # セーラー服 夏
    return (body(C["white"], INK, 84, 33) + skirt(C["navy"], INK, 54, 84, 34)
            + cuff(C["white"], INK) + sailor_collar(C["navy"], INK) + neckhole()
            + necktie(50, 32, C["red"], INK))

def f02():  # セーラー服 冬
    return (body(C["dnavy"], INK, 84, 33, "long") + skirt(C["dnavy"], INK, 54, 84, 34)
            + cuff(C["dnavy"], INK, "long") + sailor_collar(C["dnavy"], INK)
            + neckhole() + necktie(50, 32, C["red"], INK))

def f03():  # セーラー服 青リボン
    return (body(C["white"], INK, 84, 33) + skirt(C["navy"], INK, 54, 84, 34)
            + cuff(C["white"], INK) + sailor_collar(C["navy"], INK) + neckhole()
            + bow(50, 33, C["sky"], INK, 0.95))

def f04():  # セーラー服 ピンク
    return (body(C["white"], INK, 84, 33) + skirt(C["pink"], INK, 54, 84, 34)
            + cuff(C["white"], INK) + sailor_collar(C["pink"], INK) + neckhole()
            + bow(50, 33, C["rose"], INK, 0.95))

def f05():  # ブレザー制服
    return (body(C["grey"], INK, 84, 33, "long") + skirt(C["dnavy"], INK, 54, 84, 34)
            + cuff(C["grey"], INK, "long") + lapel(C["grey"], INK)
            + neckhole() + necktie(50, 26, C["red"], INK)
            + buttons(C["gold"], INK, [(41, 46)]))

def f06():  # 学ラン
    return (legs(C["black"], INK, 90, 24) + body(C["black"], INK, 62, 27, "long", False, False)
            + cuff(C["black"], INK, "long") + stand_collar(C["black"], INK)
            + neckhole() + buttons(C["gold"], INK, [(50, 32), (50, 40), (50, 48)]))

def f07():  # ナース服
    return (body(C["white"], INK, 84, 32) + cuff(C["white"], INK) + neckhole()
            + round_collar(C["sky"], INK) + belt(52, C["sky"], INK)
            + P("M62,38 v9 M57.5,42.5 h9", "none", 3.2, C["red"]))

def f08():  # 白衣
    return (body(C["white"], INK, 92, 30, "long", False, False)
            + cuff(C["white"], INK, "long") + lapel(C["white"], INK, C["white"])
            + neckhole() + P("M50,44 L50,90", "none", SWI, INK)
            + pocket(32, 62, C["white"], INK) + pocket(68, 62, C["white"], INK)
            + P("M40,30 v7 M36.5,33.5 h7", "none", 2.6, C["sky"]))

def f09():  # メイド服
    return (body(C["black"], INK, 86, 34) + cuff(C["black"], INK)
            + apron(C["white"], INK) + neckhole() + bow(50, 26, C["white"], INK, 0.85))

def f10():  # 婦警制服
    return (body(C["dnavy"], INK, 84, 31, "long") + skirt(C["dnavy"], INK, 54, 84, 32)
            + cuff(C["dnavy"], INK, "long") + lapel(C["dnavy"], INK, C["sky"])
            + neckhole() + belt(52, C["black"], INK)
            + P("M33,32 l4,-4 4,4 -4,4 Z", C["gold"], SWI, INK))

def f11():  # CA制服
    return (body(C["teal"], INK, 84, 31, "long") + skirt(C["teal"], INK, 54, 84, 32)
            + cuff(C["teal"], INK, "long") + lapel(C["teal"], INK, C["white"])
            + neckhole() + P("M38,20 C46,30 54,30 62,20 C58,34 42,34 38,20 Z",
                             C["red"], SWI, INK))

def f12():  # コックコート
    return (body(C["white"], INK, 88, 30, "long", False, False)
            + cuff(C["white"], INK, "long") + stand_collar(C["white"], INK) + neckhole()
            + buttons(C["white"], INK, [(43, 34), (43, 44), (43, 54),
                                        (57, 34), (57, 44), (57, 54)])
            + P("M50,30 L50,86", "none", SWI, INK))

def f13():  # 防火服
    return (legs(C["khaki"], INK, 90, 25) + body(C["khaki"], INK, 62, 28, "long", False, False)
            + cuff(C["khaki"], INK, "long") + stand_collar(C["khaki"], INK) + neckhole()
            + belt(42, C["yellow"], INK, 27) + belt(54, C["yellow"], INK, 26)
            + P("M33,74 h9 M58,74 h9", "none", 4.5, C["yellow"]))

def f14():  # 巫女装束
    return (skirt(C["dred"], INK, 50, 90, 34) + kimono(C["white"], INK, 52, 26)
            + neckhole() + obi(C["white"], INK, 46, 6))

def f15():  # 着物
    return (kimono(C["purple"], INK, 88, 33) + neckhole()
            + obi(C["gold"], INK, 50, 12)
            + dots(C["white"], [(30, 40, 2), (68, 36, 2), (35, 70, 2), (66, 74, 2)]))

def f16():  # 振袖
    return (kimono(C["red"], INK, 88, 32) + furisode_sleeves(C["red"], INK)
            + neckhole() + obi(C["gold"], INK, 50, 12)
            + dots(C["white"], [(32, 44, 2.4), (66, 40, 2.4), (36, 74, 2.4)]))

def f17():  # 浴衣
    return (kimono(C["sky"], INK, 88, 32) + neckhole() + obi(C["dnavy"], INK, 50, 10)
            + dots(C["white"], [(30, 38, 2), (67, 42, 2), (34, 72, 2), (65, 70, 2)]))

def f18():  # 袴
    return (skirt(C["dnavy"], INK, 48, 90, 35) + kimono(C["cream"], INK, 50, 26)
            + neckhole() + obi(C["dred"], INK, 44, 6)
            + P("M50,52 L50,88", "none", SWI, INK))

def f19():  # 甚平
    return (legs(C["mint"], INK, 78, 26, 62) + body(C["mint"], INK, 58, 27, "short", False, False)
            + cuff(C["mint"], INK) + neckhole() + P("M38,15 L50,40 L62,15", "none", SWI, INK)
            + P("M40,42 C45,45 55,45 60,42", "none", SWI, INK))

def f20():  # サンタ服
    return (body(C["red"], INK, 88, 32, "long") + cuff(C["red"], INK, "long")
            + hem_fur(88, C["white"], INK, 8, 32) + belt(54, C["black"], INK)
            + neckhole() + hem_fur(24, C["white"], INK, 5, 22))

def f21():  # サンタ服 ミニ
    return (body(C["red"], INK, 82, 33) + cuff(C["red"], INK)
            + hem_fur(82, C["white"], INK, 7, 33) + belt(52, C["black"], INK)
            + neckhole() + hem_fur(24, C["white"], INK, 5, 22))

def f22():  # トナカイ
    return (body(C["brown"], INK, 84, 32, "long") + cuff(C["brown"], INK, "long")
            + neckhole() + round_collar(C["cream"], INK, 0.85)
            + frill_row(36, C["red"], INK, 20, 1, 0, 5)
            + dots(C["gold"], [(50, 36, 3.2)])
            + dots(C["cream"], [(36, 56, 2.6), (62, 62, 2.6), (44, 72, 2.2)]))

def f23():  # かぼちゃ
    return (jag_hem(84, C["orange"], INK, 33, 7, 8)
            + body(C["orange"], INK, 78, 33) + cuff(C["orange"], INK)
            + neckhole() + stand_collar(C["green"], INK)
            + P("M40,44 l5,-7 5,7 Z M55,50 l5,-7 5,7 Z", C["black"], SWI, INK)
            + stripe_lines(INK, ["M36,32 C34,50 35,66 38,78",
                                 "M64,31 C66,49 65,65 62,77"], 2.0))

def f24():  # 吸血鬼
    return (cape(C["dred"], INK, 82) + body(C["black"], INK, 80, 26, "long", False, False)
            + cuff(C["black"], INK, "long") + lapel(C["black"], INK, C["white"])
            + neckhole() + P("M38,20 C46,28 54,28 62,20 C58,30 42,30 38,20 Z",
                             C["dred"], SWI, INK))

def f25():  # 魔女
    return (cape(C["purple"], INK, 84) + body(C["black"], INK, 82, 27, "long", False, False)
            + cuff(C["black"], INK, "long") + neckhole() + stand_collar(C["purple"], INK)
            + belt(54, C["gold"], INK, 24)
            + dots(C["yellow"], [(30, 44, 2), (70, 50, 2), (36, 70, 2)]))

def f26():  # ゾンビ
    return (jag_hem(84, C["mint"], INK, 32, 8, 9)
            + body(C["mint"], INK, 78, 32, "long") + cuff(C["mint"], INK, "long")
            + neckhole()
            + stripe_lines(INK, ["M34,36 L44,46 M44,36 L34,46",
                                 "M60,56 L70,64", "M40,62 L48,70"], 2.4))

def f27():  # ミイラ
    return (body(C["beige"], INK, 86, 31, "long") + cuff(C["beige"], INK, "long")
            + neckhole()
            + stripe_lines(dark(C["beige"], 0.72),
                           ["M29,32 C40,38 60,36 71,30",
                            "M27,44 C40,50 61,48 73,42",
                            "M25,56 C40,62 61,60 75,54",
                            "M22,68 C40,74 61,72 78,66"], 2.4))

def f28():  # チャイナドレス
    return (body(C["rose"], INK, 88, 28, "short", False) + cuff(C["rose"], INK)
            + neckhole() + stand_collar(C["rose"], INK)
            + P("M50,28 C58,33 62,42 61,52", "none", 2.2, dark(C["gold"], 0.55))
            + dots(C["gold"], [(55, 33, 2.4), (59, 42, 2.4), (61, 51, 2.4)]))

def f29():  # ゴスロリ
    return (body(C["black"], INK, 88, 35) + cuff(C["black"], INK)
            + frill_row(88, C["white"], INK, 35, 11, 2.4, 7)
            + frill_row(70, C["white"], INK, 33, 10, 2.2, 5)
            + round_collar(C["white"], INK, 0.9) + neckhole()
            + bow(50, 34, C["dred"], INK, 0.9))

def f30():  # 甘ロリ
    return (body(C["pink"], INK, 86, 35) + cuff(C["pink"], INK)
            + hem_fur(86, C["white"], INK, 8, 35) + round_collar(C["white"], INK, 0.9)
            + neckhole() + bow(50, 33, C["rose"], INK, 0.9)
            + belt(50, C["white"], INK, 26))

def f31():  # チアリーダー
    return (skirt(C["white"], INK, 54, 80, 33) + body(C["red"], INK, 60, 28, "none", False, False)
            + neckhole() + stripe_lines(C["white"], ["M28,66 L72,66"], 4)
            + P("M50,34 C46,40 54,40 50,46", "none", 3, C["white"])
            + pompom(15, 58, C["gold"], INK) + pompom(85, 55, C["gold"], INK))

def f32():  # 猫耳パーカー
    return (body(C["lav"], INK, 82, 32, "long", True, False) + cuff(C["lav"], INK, "long")
            + hood(C["lav"], INK)
            + P("M36,14 L33,4 L43,10 Z M64,14 L67,4 L57,10 Z", C["lav"], SWI, INK)
            + neckhole() + P("M50,24 L50,44", "none", SWI, INK)
            + P("M32,62 C32,58 68,58 68,62 C67,70 64,74 60,75 "
                "C53,77 47,77 40,75 C36,74 33,70 32,62 Z", C["lav"], SWI, INK))

def f33():  # 天使
    return (wings("#EAF2FB", INK) + body(C["cream"], INK, 86, 32) + cuff(C["cream"], INK)
            + neckhole() + belt(50, C["gold"], INK, 24)
            + frill_row(86, C["white"], INK, 32, 10, 2.2, 5))

def f34():  # パジャマ
    return (legs(C["sky"], INK, 90, 26) + body(C["sky"], INK, 60, 28, "long", False, False)
            + cuff(C["sky"], INK, "long") + lapel(C["sky"], INK, C["sky"]) + neckhole()
            + buttons(C["white"], INK, [(50, 36), (50, 46), (50, 56)])
            + dots(C["white"], [(33, 34, 2), (66, 40, 2), (34, 52, 2),
                                (36, 74, 2), (64, 78, 2)]))

def f35():  # ジャージ
    return (legs(C["dnavy"], INK, 90, 26) + body(C["dnavy"], INK, 60, 28, "long", False, False)
            + cuff(C["dnavy"], INK, "long") + stand_collar(C["dnavy"], INK) + neckhole()
            + P("M50,28 L50,58", "none", SWI, INK)
            + stripe_lines(C["white"], ["M27,26 C25,38 25,50 27,58",
                                        "M73,26 C75,38 75,50 73,58",
                                        "M26,56 C25,70 25,82 26,88",
                                        "M74,56 C75,70 75,82 74,88"], 2.6))

def f36():  # スーツ 男性
    return (legs(C["grey"], INK, 92, 25) + body(C["grey"], INK, 66, 28, "long", False, False)
            + cuff(C["grey"], INK, "long") + lapel(C["grey"], INK, C["white"])
            + neckhole() + necktie(50, 28, C["dred"], INK)
            + buttons(C["black"], INK, [(41, 52)]))

def f37():  # スーツ 女性
    return (skirt(C["grey"], INK, 56, 84, 30) + body(C["grey"], INK, 64, 28, "long", False, False)
            + cuff(C["grey"], INK, "long") + lapel(C["grey"], INK, C["white"])
            + neckhole() + buttons(C["black"], INK, [(41, 50)]))

def f38():  # つなぎ（作業着）
    return (legs(C["khaki"], INK, 92, 26) + body(C["khaki"], INK, 62, 28, "long", False, False)
            + cuff(C["khaki"], INK, "long") + stand_collar(C["khaki"], INK) + neckhole()
            + P("M50,28 L50,60", "none", SWI, INK)
            + pocket(33, 42, C["khaki"], INK) + pocket(67, 42, C["khaki"], INK)
            + belt(58, C["brown"], INK, 26))

def f39():  # ウェディングドレス
    return (body(C["white"], INK, 92, 38, "none", True, False)
            + neckhole() + belt(48, C["white"], INK, 24)
            + frill_row(92, C["white"], INK, 38, 12, 2.4, 7)
            + frill_row(74, C["white"], INK, 35, 11, 2.2, 5)
            + bow(50, 44, C["white"], INK, 0.85))

def f40():  # タキシード
    return (legs(C["black"], INK, 92, 25) + body(C["black"], INK, 66, 28, "long", False, False)
            + cuff(C["black"], INK, "long") + lapel(C["black"], INK, C["white"])
            + neckhole() + bow(50, 26, C["black"], INK, 0.8)
            + buttons(C["grey"], INK, [(41, 52)]))

NAMES = [
 "セーラー服 夏","セーラー服 冬","セーラー服 青リボン","セーラー服 ピンク","ブレザー制服",
 "学ラン","ナース服","白衣","メイド服","婦警制服","CA制服","コックコート","防火服",
 "巫女装束","着物","振袖","浴衣","袴","甚平","サンタ服","サンタ服 ミニ","トナカイ",
 "かぼちゃ","吸血鬼","魔女","ゾンビ","ミイラ","チャイナドレス","ゴスロリ","甘ロリ",
 "チアリーダー","猫耳パーカー","天使","パジャマ","ジャージ","スーツ 男性","スーツ 女性",
 "つなぎ（作業着）","ウェディングドレス","タキシード"]

FNS = [f01,f02,f03,f04,f05,f06,f07,f08,f09,f10,f11,f12,f13,f14,f15,f16,f17,f18,
       f19,f20,f21,f22,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,
       f37,f38,f39,f40]

if __name__ == "__main__":
    assert len(NAMES) == len(FNS) == 40, (len(NAMES), len(FNS))
    d = pathlib.Path(__file__).parent / "build" / "costumes_v2"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.svg"):
        f.unlink()
    for i, (name, fn) in enumerate(zip(NAMES, FNS), 1):
        (d / f"{i:02d}_{name}.svg").write_text(HEAD + fn() + "</svg>", encoding="utf-8")
    print(f"{len(FNS)} 案を書き出し → {d}")

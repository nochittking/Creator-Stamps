# -*- coding: utf-8 -*-
"""大阪府くん 試作 v1 — 都道府県の形キャラ × 関西弁 20個のラフ。

輪郭の出典: 地球地図日本（国土地理院）を dataofjapan/land が GeoJSON 化したもの。
  非営利は出典の明記、営利は出典の明記＋国土地理院への利用報告が条件。
  → 販売するなら、この輪郭を下敷きに手で描き直すか、利用報告を出すこと（docs/08 §4-5）。

輪郭の作り方
  1. 大阪府の本土ポリゴン（984点）を経度×cos(34.6°) で正距に直す
  2. Douglas-Peucker（許容 0.012°）で 58点に間引く
  3. 大阪湾の港湾部のギザギザ・東側の細かい凹凸を手で落として 33点に
  4. 横に 1.22 倍ふくらませる（顔を入れる面積を作る。縦長のままだと顔が小さい）
  5. Catmull-Rom（張り 0.55）で角を丸める。0.9 だと能勢町がリボン状に暴れた

v0 で分かったこと（衣装ラフの教訓 A・B と同じ構図）
  - 手を別パーツで付けると鍋の取っ手に見える → 手は付けない
  - 顔が小さいと「顔のついた地図」止まり → 顔を 1.35 倍・少し下へ
  - ほっぺは有りのほうが柔らかい（衣装と違い、ここでは顔そのものなので誤読しない）

レイアウト
  大阪府は縦長、スタンプ枠（370×320）は横長。キャラを右に寄せると左上が空く。
  そこは地図でいえば大阪湾にあたるので、セリフは「大阪湾」に置く。
"""
import html
import pathlib

OUT_DIR = pathlib.Path(__file__).parent / "build" / "osaka_kun"

# 33点。座標は 800px 四方に正規化した値（north-up）。
OUTLINE = [(255, 55), (264, 87), (345, 105), (337, 141), (382, 172), (411, 164),
           (393, 151), (405, 121), (435, 121), (425, 160), (457, 159), (532, 272),
           (462, 447), (462, 505), (489, 589), (484, 628), (357, 692), (275, 697),
           (198, 725), (135, 718), (118, 743), (63, 750), (50, 712), (143, 684),
           (259, 569), (301, 516), (315, 414), (321, 335), (289, 258), (310, 187),
           (237, 127), (243, 74), (226, 65)]
WIDEN = 1.22
TENSION = 0.55

INK = "#3B3540"
BODY = "#FFC65C"
CHEEK = "#FF9E8A"
MOUTH = "#FF7B6B"
ACCENT = "#E0442E"     # 「府」の強調・ハート
SKY = "#8FD3F4"        # 汗・涙

W, H = 370, 320
MARGIN = 10


def pts():
    return [((x - 400) * WIDEN + 400, y) for x, y in OUTLINE]


def catmull(p, t=TENSION):
    n = len(p)
    d = f"M{p[0][0]:.1f},{p[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = p[i - 1], p[i], p[(i + 1) % n], p[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + "Z"


def stroke(d, w=8, color=INK):
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ------------------------------------------------------------------ 顔 10種
# 顔だけの座標系（中心 ≒ 408,320）。chara() で 1.35 倍して体に載せる。
def eye(cx, cy=300):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="15" ry="20" fill="{INK}"/>'
            f'<circle cx="{cx + 5}" cy="{cy - 8}" r="5" fill="#fff"/>')


def arc_up(cx, cy=305):     # ^ 笑い目
    return stroke(f"M{cx - 17},{cy} q17,-24 34,0", 9)


def arc_down(cx, cy=295):   # ‿ 閉じ目（満足）
    return stroke(f"M{cx - 17},{cy} q17,22 34,0", 9)


def open_mouth(cx=408, cy=338, w=28, h=40):
    return (f'<path d="M{cx - w},{cy} q{w},0 {2 * w},0 q-4,{h} -{w},{h} q-{w - 4},0 -{w},-{h}Z" fill="{INK}"/>'
            f'<path d="M{cx - 14},{cy + h - 14} q14,14 28,0 q-14,-6 -28,0Z" fill="{MOUTH}"/>')


FACES = {
    "normal": eye(365) + eye(450) + stroke("M392,345 q16,18 32,0"),
    "smile": arc_up(365) + arc_up(450) + open_mouth(),
    "wink": arc_up(365) + eye(450) + open_mouth(w=24, h=32),
    "surprise": (f'<circle cx="365" cy="298" r="19" fill="#fff" stroke="{INK}" stroke-width="7"/>'
                 f'<circle cx="365" cy="298" r="7" fill="{INK}"/>'
                 f'<circle cx="450" cy="298" r="19" fill="#fff" stroke="{INK}" stroke-width="7"/>'
                 f'<circle cx="450" cy="298" r="7" fill="{INK}"/>'
                 f'<ellipse cx="408" cy="362" rx="14" ry="19" fill="{INK}"/>'),
    # ツッコミ: ＞＜ 目と大口
    "shout": (stroke("M350,285 l28,14 l-28,14", 9) + stroke("M465,285 l-28,14 l28,14", 9)
              + open_mouth(w=34, h=48)),
    "angry": (stroke("M345,280 l38,14", 9) + stroke("M470,280 l-38,14", 9)
              + f'<ellipse cx="366" cy="310" rx="12" ry="14" fill="{INK}"/>'
              + f'<ellipse cx="449" cy="310" rx="12" ry="14" fill="{INK}"/>'
              + stroke("M388,365 q20,-16 40,0")),
    # ニヤリ: 半目＋片側だけ上がる口
    "sly": (f'<path d="M350,300 h30 a15,15 0 0 1 -30,0Z" fill="{INK}"/>'
            f'<path d="M435,300 h30 a15,15 0 0 1 -30,0Z" fill="{INK}"/>'
            + stroke("M346,298 h38", 7) + stroke("M431,298 h38", 7)
            + stroke("M390,352 q20,8 38,-8")),
    "proud": arc_down(365) + arc_down(450) + stroke("M388,342 q10,14 20,0 q10,14 20,0"),
    "sad": (eye(365, 305) + eye(450, 305)
            + stroke("M345,276 l30,-10", 7) + stroke("M470,276 l-30,-10", 7)
            + stroke("M390,362 q9,-9 18,0 q9,9 18,0", 7)),
    # お疲れ: 横一文字の目＋波の口。sly（半目）と見分けるため黒目を描かない
    "tired": (stroke("M348,302 h36", 8) + stroke("M433,302 h36", 8)
              + stroke("M390,356 q6,-7 12,0 q6,7 12,0 q6,-7 12,0", 7)),
}


def chara(face):
    s = f'<path d="{catmull(pts())}" fill="{BODY}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
    s += (f'<ellipse cx="318" cy="385" rx="24" ry="14" fill="{CHEEK}" opacity=".75"/>'
          f'<ellipse cx="500" cy="385" rx="24" ry="14" fill="{CHEEK}" opacity=".75"/>')
    s += ('<g transform="translate(405,345) scale(1.35) translate(-408,-320)">'
          + FACES[face] + "</g>")
    return s


# ------------------------------------------------------------------ 小物（体の座標系）
def sparkle(x, y, r=26):
    return (f'<path d="M{x},{y - r} Q{x},{y} {x + r},{y} Q{x},{y} {x},{y + r} '
            f'Q{x},{y} {x - r},{y} Q{x},{y} {x},{y - r}Z" fill="#FFE27A" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')


def heart(x, y, s=1.0):
    return (f'<path transform="translate({x},{y}) scale({s})" d="M0,12 C-30,-12 -18,-38 0,-22 C18,-38 30,-12 0,12Z" '
            f'fill="{ACCENT}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')


def drop(x, y, s=1.0):
    return (f'<path transform="translate({x},{y}) scale({s})" d="M0,-28 C14,-6 18,4 18,12 a18,18 0 0 1 -36,0 C-18,4 -14,-6 0,-28Z" '
            f'fill="{SKY}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')


def anger(x, y):
    return "".join(stroke(d, 8, ACCENT) for d in (
        f"M{x - 22},{y - 6} q10,0 14,-14", f"M{x + 6},{y - 22} q0,10 14,14",
        f"M{x + 22},{y + 6} q-10,0 -14,14", f"M{x - 6},{y + 22} q0,-10 -14,-14"))


def shake():
    return (stroke("M600,250 q20,30 0,60", 8) + stroke("M630,235 q26,45 0,90", 8))


def speed():
    return stroke("M590,330 h60", 8) + stroke("M600,380 h80", 8) + stroke("M590,430 h60", 8)


def tears():
    return drop(330, 470, 0.9) + drop(490, 470, 0.9)


def candy(x, y):
    return f'<g transform="translate({x},{y}) scale(1.4) translate({-x},{-y})">' + (f'<path d="M{x - 70},{y - 26} l34,26 l-34,26Z" fill="#FF9EC4" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x + 70},{y - 26} l-34,26 l34,26Z" fill="#FF9EC4" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<circle cx="{x}" cy="{y}" r="38" fill="#FF6FA8" stroke="{INK}" stroke-width="7"/>'
            f'<path d="M{x - 18},{y - 14} q10,-12 26,-8" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>') + '</g>'


def takoyaki(x, y):
    s = (f'<path d="M{x - 95},{y + 10} h190 l-22,40 h-146Z" fill="#E8C48A" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    for dx in (-58, 0, 58):
        s += (f'<circle cx="{x + dx}" cy="{y}" r="32" fill="#E09A3E" stroke="{INK}" stroke-width="7"/>'
              f'<path d="M{x + dx - 24},{y - 8} q24,-22 48,0 q-6,10 -24,6 q-18,4 -24,-6Z" fill="#6B3A1E"/>'
              f'<path d="M{x + dx - 8},{y - 18} l6,-4 M{x + dx + 8},{y - 14} l6,-6" stroke="#7BC67E" stroke-width="5" stroke-linecap="round"/>')
    return f'<g transform="translate({x},{y}) scale(1.3) translate({-x},{-y})">{s}</g>'


# ------------------------------------------------------------------ 20個
# (番号, セリフ（改行は /）, 表情, 小物, 分類)
STAMPS = [
    ("01", "おおきに！", "smile", heart(610, 200) + heart(170, 150, .7), "返事"),
    ("02", "まいど！", "wink", sparkle(610, 210) + sparkle(560, 120, 16), "返事"),
    ("03", "ほんまに？", "surprise", "", "返事"),
    ("04", "せやな", "normal", "", "返事"),
    ("05", "ええやん！", "smile", sparkle(610, 210) + sparkle(570, 110, 16), "返事"),
    ("06", "なんで/やねん！", "shout", shake(), "返事"),
    ("07", "ちゃう/ちゃう", "angry", shake(), "返事"),
    ("08", "しゃあ/ないなぁ", "tired", drop(590, 260), "返事"),
    ("09", "ほな、/またな", "wink", "", "返事"),
    ("10", "いける？", "normal", drop(590, 260, .8), "ペア A"),
    ("11", "いける/いける！", "smile", sparkle(610, 210), "ペア A"),
    ("12", "今どこ/おるん？", "normal", "", "ペア B"),
    ("13", "もう/着くで！", "smile", speed(), "ペア B"),
    ("14", "もう/かり/まっか？", "sly", "", "ペア C"),
    ("15", "ぼちぼち/でんな", "proud", "", "ペア C"),
    ("16", "知らん/けど", "sly", drop(590, 260, .8), "大阪ネタ"),
    ("17", "大阪/「府」/やで", "angry", anger(600, 220), "大阪ネタ"),
    ("18", "面積、/下から/2番目/やねん", "sad", tears(), "大阪ネタ"),
    ("19", "アメ/ちゃん/あるで", "smile", candy(-36, 480), "大阪ネタ"),
    ("20", "たこ焼き/焼けたで", "proud", takoyaki(-30, 460), "大阪ネタ"),
]

FONT = "'Yusei Magic','Hiragino Maru Gothic ProN',sans-serif"
FONT_LINK = "https://fonts.googleapis.com/css2?family=Yusei+Magic&display=swap"

# 体の座標系 → スタンプ枠。外周 10px は透過のまま。
# v1 初版は縦いっぱい（0.414）にしたら、能勢町の先端が x≈148 まで来て
# セリフと衝突した。0.38 に縮めて右下に寄せ、湾（x 14〜158）を空ける。
SCALE = 0.38
TX = W - MARGIN - 4 - 690 * SCALE              # 小物込みの右端 ≒ 690
TY = H - MARGIN - 4 - 750 * SCALE              # 岬町の先を下端に。線幅ぶん 4px 逃がす
TEXT_W = 140                                   # 湾の幅。能勢町の先端の手前まで


def text_block(serif):
    lines = serif.split("/")
    # 全角の約物（！？、「」）も1字ぶん。細く見積もると能勢町の先端に当たった
    longest = max(len(l) for l in lines)
    size = min(44, TEXT_W / longest, 200 / len(lines) / 1.12)
    out = []
    y = MARGIN + 8 + size
    for line in lines:
        esc = html.escape(line)
        esc = esc.replace("「府」", f'「<tspan fill="{ACCENT}">府</tspan>」')
        out.append(f'<text x="{MARGIN + 6}" y="{y:.1f}" font-size="{size:.1f}" font-family="{FONT}" '
                   f'fill="{INK}" stroke="#fff" stroke-width="{size * 0.22:.1f}" paint-order="stroke" '
                   f'stroke-linejoin="round">{esc}</text>')
        y += size * 1.12
    return "".join(out)


def stamp_svg(no, serif, face, prop):
    body = chara(face) + prop
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><style>@import url("{FONT_LINK}");</style></defs>'
            f'<g transform="translate({TX:.2f},{TY:.2f}) scale({SCALE:.4f})">{body}</g>'
            f'{text_block(serif)}</svg>')


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for no, serif, face, prop, _ in STAMPS:
        name = f"{no}_{serif.replace('/', '')}.svg"
        (OUT_DIR / name).write_text(stamp_svg(no, serif, face, prop), encoding="utf-8")
    print(f"{len(STAMPS)} stamps → {OUT_DIR}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""コスプレ衣装の絵文字ラフ案 40個。

キャラクターは描かず、2頭身の体が中に入っているかのような
「見えないマネキン」のシルエットで衣装だけを起こす。

全40個を共通のパーツから組むことで骨格を揃える。手描きに起こすときの下敷き。
座標系は 0..100（正方形）。実制作は 180x180px。
"""
import math
import pathlib

INK = "#2E2A28"          # 輪郭。純黒にせず少し茶を入れる
SW_OUT, SW_IN = 3.4, 2.2  # 外周と内側の線幅

# ---------------------------------------------------------------- パーツ
def g(body, **attr):
    a = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in attr.items())
    return f"<g {a}>{body}</g>"

def path(d, fill="none", sw=SW_IN, stroke=INK, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')

def mirror(d):
    """x を 100-x に置き換えて左右反転。"""
    parts, cur = [], ""
    for ch in d:
        if ch.isalpha():
            parts += [cur, ch]; cur = ""
        else:
            cur += ch
    parts.append(cur)
    out = ""
    for p in parts:
        if len(p) == 1 and p.isalpha():
            out += p
        elif p.strip():
            n = [float(v) for v in p.replace(",", " ").split()]
            f = [f"{100-v:g}" if i % 2 == 0 else f"{v:g}" for i, v in enumerate(n)]
            out += " " + ",".join(f"{f[k]},{f[k+1]}" for k in range(0, len(f), 2)) + " "
    return out

# --- 胴体 -------------------------------------------------------------
TORSO = ("M22,27 C22,22 30,20 38,20 C42,25.5 58,25.5 62,20 "
         "C70,20 78,22 78,27 L75,57 L25,57 Z")
TORSO_LONG = ("M22,27 C22,22 30,20 38,20 C42,25.5 58,25.5 62,20 "
              "C70,20 78,22 78,27 L76,64 L24,64 Z")

def torso(color, long=False):
    return path(TORSO_LONG if long else TORSO, color, SW_OUT)

# --- 袖 ---------------------------------------------------------------
SLEEVE_SHORT = "M23,27 C14,29 10,37 12,45 C16,48 24,47 26,43 L25,30 Z"
SLEEVE_LONG  = "M23,27 C13,30 8,41 9,54 C12,58 20,57 22,52 L25,31 Z"
SLEEVE_PUFF  = "M23,26 C11,27 6,36 9,44 C14,49 24,48 27,43 L25,29 Z"

def sleeves(kind, color, cuff=None):
    if kind == "none":
        return ""
    d = {"short": SLEEVE_SHORT, "long": SLEEVE_LONG, "puff": SLEEVE_PUFF}[kind]
    out = path(d, color, SW_OUT) + path(mirror(d), color, SW_OUT)
    if cuff:
        c = {"short": "M12,44 C17,47 24,46 26,42", "long": "M9,52 C12,56 20,55 22,51",
             "puff": "M9,43 C14,48 24,47 27,42"}[kind]
        out += path(c, "none", SW_IN + 1.4, cuff) + path(mirror(c), "none", SW_IN + 1.4, cuff)
    return out

# --- 下半身 -----------------------------------------------------------
SKIRT_A     = "M25,55 L75,55 L86,84 C70,88.5 30,88.5 14,84 Z"
SKIRT_MINI  = "M26,55 L74,55 L83,76 C68,80 32,80 17,76 Z"
SKIRT_LONG  = "M25,62 L75,62 L88,93 C70,97 30,97 12,93 Z"
PANTS       = ("M26,55 L74,55 C74,60 72,83 71,87 C70,90.5 58,90.5 57,87 "
               "C56,83 51,66 50,66 C49,66 44,83 43,87 C42,90.5 30,90.5 29,87 "
               "C28,83 26,60 26,55 Z")
SHORTS      = ("M26,55 L74,55 C74,58 73,72 72,75 C71,78 59,78 58,75 "
               "C57,72 51,64 50,64 C49,64 43,72 42,75 C41,78 29,78 28,75 "
               "C27,72 26,58 26,55 Z")
HAKAMA      = "M23,57 L77,57 L86,92 C68,96 32,96 14,92 Z"

def bottom(kind, color, pleats=0, accent=None):
    if kind == "none":
        return ""
    d = {"aline": SKIRT_A, "mini": SKIRT_MINI, "long": SKIRT_LONG,
         "pants": PANTS, "shorts": SHORTS, "hakama": HAKAMA}[kind]
    out = path(d, color, SW_OUT)
    if pleats:
        top_y, bot_y = (55, 86) if kind in ("aline", "mini") else (57, 93)
        if kind == "mini": bot_y = 78
        for i in range(1, pleats):
            t = i / pleats
            x0 = 27 + (73 - 27) * t
            x1 = 16 + (84 - 16) * t
            out += path(f"M{x0:.1f},{top_y} L{x1:.1f},{bot_y-2}", "none", SW_IN - 0.5,
                        accent or INK, 'opacity="0.55"')
    return out

# --- 襟・首まわり -----------------------------------------------------
def collar(kind, color="#FFFFFF", accent=None):
    if kind == "sailor":
        c = path("M28,21 L72,21 L68,44 L50,52 L32,44 Z", color, SW_IN)
        for dy in (0, 3.6, 7.2):
            c += path(f"M33,{29+dy} L67,{29+dy}", "none", 1.6, accent or "#FFFFFF")
        return c
    if kind == "round":
        return path("M38,21 C42,28 58,28 62,21 C64,25 62,29 57,31 C52,32.5 48,32.5 43,31 "
                    "C38,29 36,25 38,21 Z", color, SW_IN)
    if kind == "stand":
        return path("M37,20 L63,20 L63,27 L37,27 Z", color, SW_IN)
    if kind == "lapel":
        return (path("M38,20 L50,32 L44,44 L36,28 Z", color, SW_IN)
                + path(mirror("M38,20 L50,32 L44,44 L36,28 Z"), color, SW_IN))
    if kind == "vneck":
        return path("M38,21 L50,36 L62,21", "none", SW_IN)
    return ""

# --- 装飾 -------------------------------------------------------------
def ribbon(color, y=30):
    return path(f"M50,{y} L41,{y-4} L41,{y+4} Z M50,{y} L59,{y-4} L59,{y+4} Z", color, SW_IN) \
         + path(f"M47,{y-2.5} L53,{y-2.5} L53,{y+2.5} L47,{y+2.5} Z", color, SW_IN)

def necktie(color, y=28):
    return path(f"M50,{y} L45,{y+3} L50,{y+22} L55,{y+3} Z", color, SW_IN)

def bowtie(color, y=27):
    return path(f"M50,{y} L42,{y-4} L42,{y+4} Z M50,{y} L58,{y-4} L58,{y+4} Z", color, SW_IN) \
         + path(f"M48,{y-2} L52,{y-2} L52,{y+2} L48,{y+2} Z", color, SW_IN)

def buttons(color, n=3, y0=32, y1=54):
    ys = [y0] if n == 1 else [y0 + (y1 - y0) * i / (n - 1) for i in range(n)]
    return "".join(f'<circle cx="50" cy="{y:.1f}" r="1.9" '
                   f'fill="{color}" stroke="{INK}" stroke-width="1.1"/>' for y in ys)

def placket(y0=30, y1=56):
    return path(f"M50,{y0} L50,{y1}", "none", SW_IN - 0.6)

def belt(color, y=55, h=6):
    return path(f"M24,{y} L76,{y} L76,{y+h} L24,{y+h} Z", color, SW_IN)

def apron(color="#FFFFFF"):
    return path("M39,26 L61,26 L60,50 L66,52 L70,82 C62,85 38,85 30,82 L34,52 L40,50 Z",
                color, SW_IN)

def fur_trim(color="#FFFFFF"):
    return path("M25,53 C33,50 67,50 75,53 C75,57 25,57 25,53 Z", color, SW_IN)

def hem_fur(kind="aline", color="#FFFFFF"):
    y = {"aline": 84, "mini": 76, "pants": 84, "long": 93}[kind]
    w = {"aline": (14, 86), "mini": (17, 83), "pants": (27, 73), "long": (12, 88)}[kind]
    return path(f"M{w[0]},{y} C{(w[0]+w[1])/2},{y+5} {(w[0]+w[1])/2},{y+5} {w[1]},{y} "
                f"C{w[1]-3},{y+6} {w[0]+3},{y+6} {w[0]},{y} Z", color, SW_IN)

def frill(y=84, color="#FFFFFF", x0=14, x1=86, n=7):
    d = f"M{x0},{y} "
    step = (x1 - x0) / n
    for i in range(n):
        d += f"q{step/2:.1f},7 {step:.1f},0 "
    return path(d + "Z", color, SW_IN)

def wrap_kimono(color, under="#FFFFFF"):
    """着物の打ち合わせ。V字に重なる前身頃。"""
    return (path("M22,27 C22,22 32,20 40,20 L50,34 L50,57 L25,57 Z", color, SW_OUT)
            + path("M78,27 C78,22 68,20 60,20 L50,34 L50,57 L75,57 Z", color, SW_OUT)
            + path("M40,20 L50,34 L60,20", "none", SW_IN, under))

def obi(color, y=48, h=9):
    return path(f"M24,{y} L76,{y} L76,{y+h} L24,{y+h} Z", color, SW_IN)

def dots(color, pts):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.85"/>'
                   for x, y, r in pts)

def stripes(color, y0=28, y1=56, n=5, op=0.7):
    return "".join(path(f"M{26+i*(48/(n-1)):.1f},{y0} L{26+i*(48/(n-1)):.1f},{y1}",
                        "none", 1.6, color, f'opacity="{op}"') for i in range(n))

def pompom(cx, cy, color="#FFFFFF", r=9):
    """ふわっとした房。円の縁を波打たせる。"""
    import math as _m
    pts = []
    for i in range(12):
        a = _m.radians(i * 30)
        rr = r * (1.0 if i % 2 == 0 else 0.72)
        pts.append((cx + rr * _m.cos(a), cy - rr * _m.sin(a)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return path(d, color, SW_IN)


def shirt_panel(color="#FFFFFF"):
    """襟元から覗く白シャツ。逆台形の当て布にする。"""
    return path("M41,24 L59,24 L57,52 L43,52 Z", color, SW_IN)


def furisode_sleeves(color):
    """振袖。袖を長く垂らす。"""
    d = "M23,26 C11,29 6,42 7,60 C10,72 19,72 22,64 L26,32 Z"
    return path(d, color, SW_OUT) + path(mirror(d), color, SW_OUT)


def jag_hem(y, color, x0=25, x1=75, n=7):
    """破れた裾。三角のギザギザで切る。"""
    step = (x1 - x0) / n
    d = f"M{x0},{y-7} "
    for i in range(n):
        d += f"l{step/2:.1f},7 l{step/2:.1f},-7 "
    d += f"L{x1},{y-9} L{x0},{y-9} Z"
    return path(d, color, SW_IN)


def wings(color="#E9E9F2"):
    """肩の上に広げた羽。袖と重ならない高さに置く。"""
    d = "M32,28 C22,10 4,8 4,22 C4,34 14,40 26,38 C24,34 26,30 32,32 Z"
    return path(d, color, SW_OUT) + path(mirror(d), color, SW_OUT)

def cape(color, lining):
    """背後に広がるマント。内側に裏地の色を細く覗かせる。"""
    outer = "M34,20 C16,26 8,52 6,84 C24,89 76,89 94,84 C92,52 84,26 66,20 Z"
    inner = "M38,24 C26,32 20,56 19,80 C34,83 66,83 81,80 C80,56 74,32 62,24 Z"
    return path(outer, color, SW_OUT) + path(inner, lining, SW_IN)

def hood(color, ears=False):
    out = path("M34,24 C34,14 66,14 66,24 C66,30 58,32 50,32 C42,32 34,30 34,24 Z", color, SW_IN)
    if ears:
        out += path("M36,20 L33,10 L44,16 Z", color, SW_IN)
        out += path(mirror("M36,20 L33,10 L44,16 Z"), color, SW_IN)
    return out

def tatter(color, y=80):
    """ゾンビ用の破れた裾。"""
    d = f"M26,{y-6} "
    for i, dy in enumerate((8, 2, 10, 4, 9, 3, 7)):
        d += f"l{48/7:.1f},{dy if i%2==0 else -dy}"
    return path(d, "none", SW_IN, color)

def bandage(color="#E8DCC0"):
    out = ""
    for i, y in enumerate(range(26, 88, 7)):
        x0, x1 = (22, 78) if y < 56 else (28, 72)
        out += path(f"M{x0},{y} C{50},{y+3.5} {50},{y+3.5} {x1},{y-1}",
                    "none", 2.0, color, 'opacity="0.95"')
    return out

# ================================================================ 40案
# 描画順: 袖 → 下半身 → 胴 → 襟・装飾
C = dict  # 見やすさのため

COSTUMES = [
 # --- A 学校・制服 6 -------------------------------------------------
 C(no=1, name="セーラー服 夏", cat="A",
   build=lambda: sleeves("short", "#FFFFFF")
   + bottom("aline", "#2B4E8C", pleats=7, accent="#1C355F")
   + torso("#FFFFFF") + collar("sailor", "#2B4E8C", "#FFFFFF") + ribbon("#E03A3A")),
 C(no=2, name="セーラー服 冬", cat="A",
   build=lambda: sleeves("long", "#28406B") + bottom("aline", "#28406B", pleats=7, accent="#1A2B4A")
   + torso("#28406B") + collar("sailor", "#28406B", "#FFFFFF") + ribbon("#E03A3A")),
 C(no=3, name="セーラー服 青リボン", cat="A",
   build=lambda: sleeves("short", "#FFFFFF") + bottom("aline", "#4A6FA5", pleats=7, accent="#2F4C77")
   + torso("#FFFFFF") + collar("sailor", "#4A6FA5", "#FFFFFF") + ribbon("#2F6FD0")),
 C(no=4, name="セーラー服 ピンク", cat="A",
   build=lambda: sleeves("short", "#FFFFFF") + bottom("aline", "#8E8E96", pleats=7, accent="#6C6C75")
   + torso("#FFFFFF") + collar("sailor", "#F2A0BC", "#FFFFFF") + ribbon("#EE7FA6")),
 C(no=5, name="ブレザー制服", cat="A",
   build=lambda: sleeves("long", "#2C3A5C") + bottom("aline", "#9E4A4A", pleats=6, accent="#7A3636")
   + torso("#2C3A5C") + collar("lapel", "#FFFFFF") + necktie("#A33C3C") + buttons("#D9B551", 2, 40, 50)),
 C(no=6, name="学ラン", cat="A",
   build=lambda: sleeves("long", "#23242A") + bottom("pants", "#23242A")
   + torso("#23242A") + collar("stand", "#3A3B43") + buttons("#D9B551", 4, 32, 54)),

 # --- B 職業・ユニフォーム 8 -----------------------------------------
 C(no=7, name="ナース服", cat="B",
   build=lambda: sleeves("short", "#FFFFFF", cuff="#7FC8E8") + bottom("aline", "#FFFFFF")
   + torso("#FFFFFF") + collar("round", "#7FC8E8") + buttons("#7FC8E8", 3, 34, 52)),
 C(no=8, name="白衣", cat="B",
   build=lambda: sleeves("long", "#FFFFFF") + bottom("pants", "#D8DCE0")
   + torso("#FFFFFF", long=True) + collar("lapel", "#FFFFFF")
   + path("M60,30 C70,34 70,46 62,50", "none", 2.2, "#5FA8CF")
   + '<circle cx="61" cy="52" r="4" fill="#5FA8CF" stroke="#2E2A28" stroke-width="1.6"/>'),
 C(no=9, name="メイド服", cat="B",
   build=lambda: sleeves("puff", "#2A2A32", cuff="#FFFFFF") + bottom("long", "#2A2A32")
   + torso("#2A2A32") + apron("#FFFFFF") + collar("round", "#FFFFFF")
   + frill(92, "#FFFFFF", 13, 87) + ribbon("#FFFFFF", 30)),
 C(no=10, name="婦警制服", cat="B",
   build=lambda: sleeves("long", "#2E3D63") + bottom("aline", "#2E3D63")
   + torso("#2E3D63") + belt("#FFFFFF", 54, 6) + collar("lapel", "#2E3D63")
   + buttons("#D9B551", 2, 36, 48)
   + path("M30,30 L38,30 L38,35 L30,35 Z", "#D9B551", 1.4)),
 C(no=11, name="CA制服", cat="B",
   build=lambda: sleeves("long", "#243A66") + bottom("aline", "#243A66")
   + torso("#243A66") + collar("round", "#243A66")
   + path("M37,21 C43,33 57,33 63,21 C62,33 57,42 50,45 C43,42 38,33 37,21 Z",
          "#C8443E", SW_IN)),
 C(no=12, name="コックコート", cat="B",
   build=lambda: sleeves("long", "#FFFFFF") + bottom("pants", "#B9BDC4")
   + torso("#FFFFFF") + collar("stand", "#FFFFFF")
   + buttons("#FFFFFF", 3, 33, 50) + path("M44,30 L44,56", "none", 1.6)
   + stripes("#6E747C", 60, 86, 5, 0.85)),
 C(no=13, name="防火服", cat="B",
   build=lambda: sleeves("long", "#1F2A44", cuff="#E8D24A") + bottom("pants", "#1F2A44")
   + torso("#1F2A44") + collar("stand", "#1F2A44")
   + path("M25,44 L75,44", "none", 3.2, "#E8D24A")
   + path("M28,70 L72,70", "none", 3.2, "#E8D24A") + placket(28, 56)),
 C(no=14, name="巫女装束", cat="B",
   build=lambda: sleeves("puff", "#FFFFFF") + bottom("hakama", "#C8353F")
   + wrap_kimono("#FFFFFF") + obi("#FFFFFF", 52, 6)
   + path("M30,62 L70,62", "none", 2.0, "#9E2830")),

 # --- C 和装 5 --------------------------------------------------------
 C(no=15, name="着物", cat="C",
   build=lambda: sleeves("puff", "#31517E") + bottom("long", "#31517E")
   + wrap_kimono("#31517E") + obi("#D9A23C")
   + dots("#FFFFFF", [(34,70,1.6),(46,78,1.6),(62,72,1.6),(70,84,1.6),(40,88,1.6)])),
 C(no=16, name="振袖", cat="C",
   build=lambda: furisode_sleeves("#D0384A") + bottom("long", "#D0384A")
   + wrap_kimono("#D0384A") + obi("#E0B84E")
   + dots("#FFD9A0", [(32,72,2.2),(44,82,2.0),(60,74,2.2),(70,86,2.0),(38,92,1.8),(62,92,1.8)])
   + dots("#FFFFFF", [(36,78,1.3),(52,88,1.3),(66,80,1.3)])),
 C(no=17, name="浴衣", cat="C",
   build=lambda: sleeves("puff", "#2E4470") + bottom("long", "#2E4470")
   + wrap_kimono("#2E4470") + obi("#D8515E")
   + dots("#FFFFFF", [(34,72,2.0),(48,82,2.0),(64,74,2.0),(70,88,1.8),(36,90,1.8)])),
 C(no=18, name="袴", cat="C",
   build=lambda: sleeves("puff", "#E3D3DC") + bottom("hakama", "#7A2E44")
   + wrap_kimono("#E3D3DC") + obi("#FFFFFF", 52, 5)
   + stripes("#8E6478", 26, 50, 7, 0.8)),
 C(no=19, name="甚平", cat="C",
   build=lambda: sleeves("short", "#33518A") + bottom("shorts", "#33518A")
   + torso("#33518A") + path("M50,26 L50,56", "none", 2.0, "#FFFFFF")
   + path("M32,40 L42,40 M58,40 L68,40", "none", 1.8, "#FFFFFF")),

 # --- D 季節・イベント 8 ---------------------------------------------
 C(no=20, name="サンタ服", cat="D",
   build=lambda: sleeves("long", "#C6323C", cuff="#FFFFFF") + bottom("pants", "#C6323C")
   + torso("#C6323C") + fur_trim() + belt("#2E2A28", 52, 7)
   + path("M45,53 L55,53 L55,60 L45,60 Z", "#E0B84E", 1.6)
   + hem_fur("pants")),
 C(no=21, name="サンタ服 ミニ", cat="D",
   build=lambda: sleeves("puff", "#C6323C", cuff="#FFFFFF") + bottom("mini", "#C6323C")
   + torso("#C6323C") + belt("#2E2A28", 52, 6) + hem_fur("mini")
   + collar("round", "#FFFFFF")),
 C(no=22, name="トナカイ", cat="D",
   build=lambda: sleeves("long", "#8A6038") + bottom("pants", "#8A6038")
   + torso("#8A6038") + hood("#8A6038")
   + path("M38,16 L32,6 L40,10 M62,16 L68,6 L60,10", "none", 2.2, "#5E4026")
   + path("M38,36 C38,52 62,52 62,36 C62,56 38,56 38,36 Z", "#F0E3CE", SW_IN)),
 C(no=23, name="かぼちゃ", cat="D",
   build=lambda: path("M50,20 C26,20 16,38 16,56 C16,76 30,88 50,88 C70,88 84,76 84,56 "
                      "C84,38 74,20 50,20 Z", "#EE8A2B", SW_OUT)
   + path("M34,24 C28,42 28,66 34,84 M66,24 C72,42 72,66 66,84 M50,21 L50,88",
          "none", 2.0, "#B85F16")
   + path("M46,14 C48,8 52,8 54,14 C52,17 48,17 46,14 Z", "#4E7A32", 1.8)),
 C(no=24, name="吸血鬼", cat="D",
   build=lambda: cape("#1E1B24", "#A3232E") + bottom("pants", "#1E1B24")
   + torso("#1E1B24") + collar("vneck", "#FFFFFF")
   + path("M43,24 L50,38 L57,24", "#FFFFFF", 1.8) + bowtie("#A3232E", 30)),
 C(no=25, name="魔女", cat="D",
   build=lambda: sleeves("long", "#2C2440") + bottom("long", "#2C2440")
   + torso("#2C2440", long=True) + belt("#7C5BA6", 58, 6)
   + path("M12,93 C30,97 70,97 88,93", "none", 3.0, "#7C5BA6")
   + dots("#C9A6E8", [(30,74,1.8),(62,80,1.8),(44,88,1.6),(72,70,1.6)])),
 C(no=26, name="ゾンビ", cat="D",
   build=lambda: sleeves("long", "#7A8A7A") + bottom("pants", "#5A5F52")
   + torso("#7A8A7A") + jag_hem(57, "#7A8A7A") + jag_hem(88, "#5A5F52", 29, 71)
   + path("M38,34 L44,42 M60,30 L54,40 M46,50 L52,56", "none", 2.0, "#3E4A3E")
   + path("M26,60 L34,54 M74,62 L66,56", "none", 2.0, "#3E4A3E")),
 C(no=27, name="ミイラ", cat="D",
   build=lambda: sleeves("long", "#E8DCC0") + bottom("pants", "#E8DCC0")
   + torso("#E8DCC0") + bandage("#C9B896")),

 # --- E ファンタジー 6 -----------------------------------------------
 C(no=28, name="チャイナドレス", cat="E",
   build=lambda: sleeves("short", "#C8323C") + bottom("long", "#C8323C")
   + torso("#C8323C") + collar("stand", "#C8323C")
   + path("M50,28 C58,32 62,40 62,50", "none", 2.0, "#E0B84E")
   + '<circle cx="56" cy="34" r="2.2" fill="#E0B84E" stroke="#2E2A28" stroke-width="1.1"/>'
   + '<circle cx="61" cy="43" r="2.2" fill="#E0B84E" stroke="#2E2A28" stroke-width="1.1"/>'
   + path("M64,64 L70,93", "none", 2.0, "#8E1F27")
   + dots("#E0B84E", [(32,74,2.0),(40,88,1.8),(30,90,1.6)])),
 C(no=29, name="ゴスロリ", cat="E",
   build=lambda: sleeves("puff", "#2A2530", cuff="#FFFFFF") + bottom("long", "#2A2530")
   + torso("#2A2530") + collar("round", "#FFFFFF") + ribbon("#8E2440", 31)
   + frill(93, "#FFFFFF", 12, 88) + stripes("#5A4E66", 66, 90, 5, 0.5)),
 C(no=30, name="甘ロリ", cat="E",
   build=lambda: sleeves("puff", "#F6C3D6", cuff="#FFFFFF") + bottom("long", "#F6C3D6")
   + torso("#F6C3D6") + collar("round", "#FFFFFF") + ribbon("#FFFFFF", 31)
   + frill(93, "#FFFFFF", 12, 88) + frill(74, "#FFF0F5", 18, 82, 6)),
 C(no=31, name="チアリーダー", cat="E",
   build=lambda: bottom("mini", "#D8323C", pleats=8, accent="#9E2028")
   + torso("#D8323C") + collar("vneck", "#FFFFFF")
   + path("M26,44 L74,44", "none", 3.0, "#FFFFFF")
   + path("M40,32 L50,44 L60,32", "#FFFFFF", 1.8)
   + pompom(14, 58) + pompom(86, 58)),
 C(no=32, name="猫耳パーカー", cat="E",
   build=lambda: sleeves("long", "#9BA3AE", cuff="#7D8590") + bottom("shorts", "#5E6672")
   + torso("#9BA3AE") + hood("#9BA3AE", ears=True)
   + path("M44,32 C44,44 56,44 56,32", "none", 2.0, "#6E7680")
   + path("M44,33 L42,44 M56,33 L58,44", "none", 1.8, "#E8EAED")),
 C(no=33, name="天使", cat="E",
   build=lambda: wings() + sleeves("short", "#FFFFFF") + bottom("long", "#FFFFFF")
   + torso("#FFFFFF") + obi("#E8C86A", 52, 5) + collar("round", "#FFFFFF")
   + '<circle cx="50" cy="10" r="9" fill="none" stroke="#E8C86A" stroke-width="2.6"/>'),

 # --- F カジュアル・日常 7 -------------------------------------------
 C(no=34, name="パジャマ", cat="F",
   build=lambda: sleeves("long", "#A8D8EC") + bottom("pants", "#A8D8EC")
   + torso("#A8D8EC") + collar("lapel", "#A8D8EC")
   + stripes("#FFFFFF", 28, 56, 6, 0.9) + stripes("#FFFFFF", 60, 88, 6, 0.9)
   + buttons("#FFFFFF", 3, 34, 52)),
 C(no=35, name="ジャージ", cat="F",
   build=lambda: sleeves("long", "#27365C") + bottom("pants", "#27365C")
   + torso("#27365C") + collar("stand", "#27365C") + placket(28, 56)
   + path("M20,31 C14,36 11,45 11,53", "none", 2.6, "#FFFFFF")
   + path("M80,31 C86,36 89,45 89,53", "none", 2.6, "#FFFFFF")
   + path("M34,58 L32,88 M66,58 L68,88", "none", 2.4, "#FFFFFF")),
 C(no=36, name="スーツ 男性", cat="F",
   build=lambda: sleeves("long", "#3A3F4A") + bottom("pants", "#3A3F4A")
   + torso("#3A3F4A") + shirt_panel() + collar("lapel", "#3A3F4A") + necktie("#2F4C77", 30) + buttons("#23262C", 2, 46, 54)),
 C(no=37, name="スーツ 女性", cat="F",
   build=lambda: sleeves("long", "#2A2A30") + bottom("aline", "#2A2A30")
   + torso("#2A2A30") + shirt_panel() + collar("lapel", "#43434C")
   + buttons("#1A1A1E", 1, 48, 48)),
 C(no=38, name="つなぎ（作業着）", cat="F",
   build=lambda: sleeves("long", "#2B5FB0", cuff="#1F4885") + bottom("pants", "#2B5FB0")
   + torso("#2B5FB0") + collar("lapel", "#2B5FB0") + placket(30, 62)
   + path("M56,34 L70,34 L70,45 L56,45 Z", "#1F4885", 1.8)
   + belt("#1F4885", 54, 5)),
 C(no=39, name="ウェディングドレス", cat="F",
   build=lambda: sleeves("puff", "#FFFFFF") + bottom("long", "#FFFFFF")
   + torso("#FFFFFF") + collar("round", "#FFFFFF")
   + path("M12,93 C30,98 70,98 88,93", "none", 3.0, "#EDE3EE")
   + frill(92, "#FBF3F8", 12, 88, 8) + obi("#EFE0E8", 54, 5)
   + dots("#EFD9E4", [(34,74,1.8),(62,80,1.8),(48,88,1.6)])),
 C(no=40, name="タキシード", cat="F",
   build=lambda: sleeves("long", "#1E1E24") + bottom("pants", "#1E1E24")
   + torso("#1E1E24") + shirt_panel() + collar("lapel", "#3A3A44") + bowtie("#43434C", 29)
   + path("M30,57 L26,86 M70,57 L74,86", "none", 2.2, "#3A3A44")),
]

# ================================================================ 出力
VIEWBOX = "-1 -2 102 104"

def svg(c, size=None):
    wh = f'width="{size}" height="{size}" ' if size else ""
    return (f'<svg {wh}viewBox="{VIEWBOX}" role="img" aria-label="{c["name"]}の衣装">'
            f'{c["build"]()}</svg>')

CATS = {"A": "学校・制服", "B": "職業・ユニフォーム", "C": "和装",
        "D": "季節・イベント", "E": "ファンタジー", "F": "カジュアル・日常"}

def write_svgs(outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    for c in COSTUMES:
        (outdir / f"{c['no']:02d}_{c['name']}.svg").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360" '
            f'viewBox="{VIEWBOX}">{c["build"]()}</svg>', encoding="utf-8")
    return len(COSTUMES)

if __name__ == "__main__":
    n = write_svgs(pathlib.Path(__file__).parent / "build" / "costumes")
    assert len(COSTUMES) == 40, len(COSTUMES)
    assert [c["no"] for c in COSTUMES] == list(range(1, 41))
    print(f"{n} 案を書き出し / 連番 OK")

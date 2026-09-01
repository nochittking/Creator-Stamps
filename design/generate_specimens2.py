# -*- coding: utf-8 -*-
"""見本帳 vol.2 — 書体カタログ／枠なしレタリング／工具・車モチーフ／組み合わせ。

各スタンプは 370x320 の SVG。実際の入稿サイズと同じ座標系で組んでいる。
実行すると design/build/ に断片を書き出し、text-sticker-specimens2.html を生成する。
"""
import html, pathlib, math

W, H, CX, CY = 370, 320, 185, 160
INK = "#1A1815"

# ---------------------------------------------------------------- 文字組み
def fit(lines, max_w=300, max_h=200, cap=132):
    return round(min(cap, max_w / max(len(l) for l in lines), max_h / (len(lines) * 1.14)), 1)

def rows(lines, size, cy=CY, lh=1.14):
    top = cy - (len(lines) - 1) * size * lh / 2
    return [(round(top + i * size * lh, 1), l) for i, l in enumerate(lines)]

def T(x, y, s, font, weight, size, fill, extra=""):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{font}" font-weight="{weight}" font-size="{size}" fill="{fill}" {extra}>'
            f'{html.escape(s)}</text>')

def outlined(lines, font, weight=400, fill="#FFFFFF", outer=INK, inner="#FFFFFF",
             size=None, cy=CY, cap=132, ow=22, iw=11):
    """外側の濃い縁 → 内側の白縁 → 本体、の三重で文字単体を成立させる。"""
    size = size or fit(lines, cap=cap)
    out = []
    for y, s in rows(lines, size, cy):
        out.append(T(CX, y, s, font, weight, size, "none",
                     f'stroke="{outer}" stroke-width="{ow}" stroke-linejoin="round"'))
    for y, s in rows(lines, size, cy):
        out.append(T(CX, y, s, font, weight, size, "none",
                     f'stroke="{inner}" stroke-width="{iw}" stroke-linejoin="round"'))
    for y, s in rows(lines, size, cy):
        out.append(T(CX, y, s, font, weight, size, fill))
    return "\n      ".join(out), size

def extruded(lines, font, weight=400, top="#FFD400", side="#8A5A10", edge=INK,
             depth=9, dx=1.0, dy=1.0, size=None, cy=CY, cap=124):
    """奥行きぶんテキストを重ねて押し出す。"""
    size = size or fit(lines, cap=cap)
    out = []
    for d in range(depth, 0, -1):
        for y, s in rows(lines, size, cy):
            out.append(T(CX + d * dx, y + d * dy, s, font, weight, size, side,
                         f'stroke="{side}" stroke-width="6" stroke-linejoin="round"'))
    for y, s in rows(lines, size, cy):
        out.append(T(CX, y, s, font, weight, size, "none",
                     f'stroke="{edge}" stroke-width="16" stroke-linejoin="round"'))
    for y, s in rows(lines, size, cy):
        out.append(T(CX, y, s, font, weight, size, top))
    return "\n      ".join(out), size

def arched(text, font, weight, size, uid, fill="#FFFFFF", outer=INK, sag=76, y0=228):
    """円弧に沿わせた文字組み。"""
    d = f"M36,{y0} Q{CX},{y0-sag*2} 334,{y0}"
    body = ""
    for st, sw in ((outer, 22), ("#FFFFFF", 11), (None, 0)):
        f = fill if st is None else "none"
        stroke = "" if st is None else f'stroke="{st}" stroke-width="{sw}" stroke-linejoin="round"'
        body += (f'<text font-family="{font}" font-weight="{weight}" font-size="{size}" fill="{f}" {stroke}>'
                 f'<textPath href="#{uid}" startOffset="50%" text-anchor="middle">{html.escape(text)}</textPath></text>')
    return f'<defs><path id="{uid}" d="{d}" fill="none"/></defs>{body}'

def vert(chars, font, weight, size, x=CX, cy=CY, fill="#FFFFFF", outer=INK, ow=20):
    lh = size * 1.02
    top = cy - (len(chars) - 1) * lh / 2
    out = []
    for pas, (st, sw) in enumerate(((outer, ow), ("#FFFFFF", 10), (None, 0))):
        for i, c in enumerate(chars):
            f = fill if st is None else "none"
            stroke = "" if st is None else f'stroke="{st}" stroke-width="{sw}" stroke-linejoin="round"'
            out.append(T(x, round(top + i * lh, 1), c, font, weight, size, f, stroke))
    return "\n      ".join(out)

# ---------------------------------------------------------------- 工具・車
def tool(name, color=INK, sw=9):
    """工具のデフォルメ。すべて 0..100 の座標系。線は太く、細部は捨てる。"""
    g = f'stroke="{color}" fill="none" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    if name == "spanner":   # コンビネーションレンチ：片側メガネ／片側スパナ
        return (f'<g {g}><circle cx="26" cy="74" r="14"/>'
                f'<line x1="35" y1="65" x2="65" y2="35" stroke-width="{sw+4}"/>'
                f'<circle cx="74" cy="26" r="14" stroke-dasharray="60 28"/></g>')
    if name == "driver":    # ドライバー
        return (f'<g transform="rotate(-32 50 50)"><g {g} stroke-linecap="butt">'
                f'<rect x="37" y="8" width="26" height="36" rx="11" fill="{color}"/>'
                f'<rect x="44" y="44" width="12" height="7" rx="2" fill="{color}" stroke-width="3"/>'
                f'<line x1="50" y1="52" x2="50" y2="80" stroke-width="{sw}"/>'
                f'<path d="M44,80 h12 l-3,12 h-6 z" fill="{color}" stroke-width="4"/></g></g>')
    if name == "hex":       # 六角レンチ
        return f'<g {g}><path d="M30,16 L30,72 L74,72" stroke-width="{sw+3}"/></g>'
    if name == "bolt":      # ボルト・ナット
        return (f'<g {g}><polygon points="80,50 65,76 35,76 20,50 35,24 65,24"/>'
                f'<circle cx="50" cy="50" r="13"/></g>')
    if name == "tire":      # タイヤ
        return (f'<g {g}><circle cx="50" cy="50" r="30" stroke-width="{sw+3}"/>'
                f'<circle cx="50" cy="50" r="12" stroke-width="{sw-2}"/>'
                f'<circle cx="50" cy="50" r="40" stroke-width="7" stroke-dasharray="7 11"/></g>')
    if name == "gear":      # 歯車
        return (f'<g {g}><circle cx="50" cy="50" r="26" stroke-width="{sw+2}"/>'
                f'<circle cx="50" cy="50" r="10"/>'
                f'<circle cx="50" cy="50" r="36" stroke-width="14" stroke-dasharray="11 12"/></g>')
    if name == "oilcan":    # オイル缶
        return (f'<g {g}><rect x="16" y="44" width="48" height="38" rx="8"/>'
                f'<path d="M64,54 C78,52 86,42 88,30"/>'
                f'<path d="M28,44 C28,31 54,31 54,44"/>'
                f'<path d="M88,22 c6,8 6,14 0,16 c-6,-2 -6,-8 0,-16z" fill="{color}" stroke-width="4"/></g>')
    if name == "jack":      # パンタグラフジャッキ
        return (f'<g {g}><path d="M50,20 L78,50 L50,80 L22,50 Z"/>'
                f'<line x1="30" y1="14" x2="70" y2="14" stroke-width="{sw+2}"/>'
                f'<line x1="30" y1="86" x2="70" y2="86" stroke-width="{sw+2}"/></g>')
    raise ValueError(name)

def car(kind, body="#1A1815", accent="#FFD400", eyes=False):
    """抽象化した車。実在車種と特定できない輪郭にする。"""
    if kind == "cool":      # 低く・長い。0..140 x 0..58
        return (f'<g><path d="M6,42 C6,34 11,30 21,28 L39,15 C45,11 60,9 74,11 L97,16 '
                f'C113,19 127,25 131,32 L132,42 Z" fill="{body}"/>'
                f'<path d="M44,17 C50,14 60,13 70,14 L86,19 L44,20 Z" fill="{accent}" opacity=".9"/>'
                f'<circle cx="36" cy="43" r="11" fill="{body}"/><circle cx="36" cy="43" r="4.5" fill="{accent}"/>'
                f'<circle cx="105" cy="43" r="11" fill="{body}"/><circle cx="105" cy="43" r="4.5" fill="{accent}"/></g>')
    # cute: 丸く・背が高い。0..120 x 0..78
    eye = ""
    if eyes:
        eye = ('<circle cx="90" cy="38" r="9" fill="#FFFFFF"/><circle cx="92" cy="39" r="4.5" fill="#1A1815"/>'
               '<circle cx="30" cy="38" r="9" fill="#FFFFFF"/><circle cx="32" cy="39" r="4.5" fill="#1A1815"/>')
    return (f'<g><path d="M14,56 C12,32 23,19 42,16 C57,13 72,13 86,18 C103,24 108,37 106,56 Z" fill="{body}"/>'
            f'<path d="M34,30 C40,23 52,21 60,22 L60,36 L34,36 Z" fill="{accent}"/>'
            f'<path d="M68,23 C78,25 86,30 90,36 L68,36 Z" fill="{accent}"/>'
            f'{eye}'
            f'<circle cx="34" cy="57" r="13" fill="{body}"/><circle cx="34" cy="57" r="5" fill="{accent}"/>'
            f'<circle cx="86" cy="57" r="13" fill="{body}"/><circle cx="86" cy="57" r="5" fill="{accent}"/></g>')

def place(inner, x, y, scale, rot=0, opacity=1):
    r = f' rotate({rot})' if rot else ''
    o = f' opacity="{opacity}"' if opacity != 1 else ''
    return f'<g transform="translate({x},{y}) scale({scale}){r}"{o}>{inner}</g>'

def svg(inner, extra=""):
    return f'<svg viewBox="0 0 {W} {H}" {extra} role="img" aria-hidden="true">{inner}</svg>'

# ================================================================ 見本の定義
FONTS = [
 ("Rampart One", 400, ["無理"], "立体的に彫られた輪郭。それ自体が看板になる", "叫び・拒否"),
 ("Train One", 400, ["納期", "未定"], "字の中を白い線が走る工業書体。標識の質感", "断定・警告"),
 ("DotGothic16", 400, ["故障コード", "出ました"], "ドット表示。診断機の画面そのもの", "症状・診断"),
 ("Reggae One", 400, ["まじか"], "極太に強い癖。うるさいくらいの主張", "驚き・リアクション"),
 ("Dela Gothic One", 400, ["入庫", "しました"], "癖のない極太。読ませることに徹する", "業務連絡"),
 ("Potta One", 400, ["助かる"], "ぽってり丸い。角がなく人当たりが良い", "感謝・軽い依頼"),
 ("Mochiy Pop One", 400, ["ありがとう"], "太い丸ゴシック。明るく素直", "挨拶・汎用"),
 ("Kaisei Decol", 700, ["お疲れさま"], "装飾的で柔らかい。丁寧さが出る", "労い・接客"),
 ("Yuji Syuku", 400, ["完了"], "筆。職人の手つきをそのまま持ち込む", "完了報告・硬派"),
 ("Shippori Mincho B1", 800, ["原因", "不明"], "重い明朝。皮肉とシリアスに効く", "皮肉・重い話"),
 ("Hachi Maru Pop", 400, ["わからん"], "ゆるい手書き。力の抜けた自虐", "自虐・共感"),
 ("New Tegomin", 400, ["残業確定"], "古風で癖のある骨格。昭和の工場の匂い", "疲弊・自虐"),
]

def font_card(font, weight, lines):
    body, _ = outlined(lines, f"'{font}', sans-serif", weight, fill="#F7F5EE",
                       outer=INK, inner="#FFFFFF", cap=118, ow=24, iw=12)
    return svg(body)

# ---------------------------------------------------------------- 枠なしの形
def free_triple():
    body, _ = outlined(["まだ", "帰れない"], "'Dela Gothic One', sans-serif", 400,
                       fill="#FFD400", outer=INK, inner="#FFFFFF", cap=112, ow=26, iw=13)
    shadow, _ = outlined(["まだ", "帰れない"], "'Dela Gothic One', sans-serif", 400,
                         fill=INK, outer=INK, inner=INK, cap=112, ow=26, iw=13)
    return svg(f'<g opacity=".22" transform="translate(9,10)">{shadow}</g>{body}')

def free_extrude():
    body, _ = extruded(["無理"], "'Reggae One', sans-serif", 400,
                       top="#FFD400", side="#8C4A0E", edge=INK, depth=10, cap=132)
    return svg(body)

def free_arch():
    return svg(arched("おつかれさま", "'Mochiy Pop One', sans-serif", 400, 62, "arch1",
                      fill="#FF6B35", outer=INK)
               + place(tool("spanner", INK, 9), 152, 190, 0.62, rot=-12))

def free_vertical():
    seal = ('<g transform="translate(276,236) rotate(-12)">'
            '<circle cx="0" cy="0" r="34" fill="none" stroke="#C0392B" stroke-width="5"/>'
            '<text x="0" y="1" text-anchor="middle" dominant-baseline="central" '
            'font-family="\'Shippori Mincho B1\', serif" font-weight="800" font-size="30" fill="#C0392B">済</text></g>')
    return svg(vert("車検完了", "'Yuji Syuku', serif", 400, 66, x=150) + seal)

def free_dotmatrix():
    """診断機の表示器。枠ではなく「機器そのもの」の形にする。"""
    dot = "'DotGothic16', monospace"
    scan = "".join(f'<rect x="34" y="{y}" width="302" height="2" fill="#000" opacity=".22"/>'
                   for y in range(96, 226, 8))
    code = T(CX, 138, "P0301", dot, 400, 52, "#57F27A")
    msg = T(CX, 190, "故障コード出た", dot, 400, 38, "#57F27A")
    tag = T(196, 252, "DIAGNOSIS", dot, 400, 20, INK)
    return svg(
        f'<rect x="26" y="84" width="318" height="152" rx="16" fill="#12160F"/>'
        f'<rect x="26" y="84" width="318" height="152" rx="16" fill="none" stroke="{INK}" stroke-width="9"/>'
        f'<rect x="38" y="96" width="294" height="128" rx="6" fill="#0A2A12"/>'
        f'{scan}{code}{msg}'
        f'<circle cx="52" cy="252" r="7" fill="#57F27A"/>{tag}')

def free_slant():
    lines = ["エンジン", "かからん"]
    burst = "".join(
        f'<line x1="{CX+math.cos(math.radians(a))*118:.1f}" y1="{CY+math.sin(math.radians(a))*104:.1f}" '
        f'x2="{CX+math.cos(math.radians(a))*172:.1f}" y2="{CY+math.sin(math.radians(a))*152:.1f}" '
        f'stroke="{INK}" stroke-width="{6 if i%2 else 10}" stroke-linecap="round"/>'
        for i, a in enumerate(range(0, 360, 22)))
    body, _ = outlined(lines, "'Train One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#E8402A", cap=104, ow=26, iw=14)
    return svg(f'{burst}<g transform="rotate(-7 {CX} {CY})">{body}</g>')

FREE = [
 ("三重の縁取り＋落ち影", "FREE 01", free_triple,
  "白フチと濃フチを重ね、影を落とすだけで枠がいらなくなる。最も潰しが効く基本形"),
 ("立体押し出し", "FREE 02", free_extrude,
  "文字を奥行きぶん重ねて彫り込む。短い語ほど強い"),
 ("アーチ組み＋工具", "FREE 03", free_arch,
  "弧に沿わせると硬さが取れる。空いた足元に工具を落とす"),
 ("縦組み＋朱印", "FREE 04", free_vertical,
  "筆＋縦組み＋判子。完了報告と相性がよく、他業種と一切かぶらない"),
 ("ドットの表示器", "FREE 05", free_dotmatrix,
  "診断機の画面そのものを持ち込む。この業界にしか作れない形"),
 ("斜め＋集中線", "FREE 06", free_slant,
  "傾きと放射線で勢いを出す。緊急・トラブル系の定番"),
]

# ---------------------------------------------------------------- 工具・車
TOOLS = [("spanner","コンビネーションレンチ"),("driver","ドライバー"),("hex","六角レンチ"),
         ("bolt","ボルト・ナット"),("tire","タイヤ"),("gear","歯車"),
         ("oilcan","オイル缶"),("jack","ジャッキ")]

def tool_card(name):
    return f'<svg viewBox="0 0 100 100" role="img" aria-hidden="true">{tool(name, INK, 9)}</svg>'

def combo_corner():
    body, _ = outlined(["部品", "まだ来ない"], "'Potta One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#FFD400", cap=104, ow=24, iw=12, cy=146)
    return svg(body + place(tool("oilcan", INK, 9), 268, 234, 0.66, rot=8))

def combo_through():
    body, _ = outlined(["工具どこ"], "'Dela Gothic One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#17A2A2", cap=104, ow=26, iw=13)
    return svg(place(tool("spanner", INK, 11), 66, 74, 2.0, rot=0, opacity=.9) + body)

def combo_replace():
    """文字の一部を工具に置き換える。O をナットに。"""
    dela = "'Dela Gothic One', sans-serif"
    k = T(252, CY, "K", dela, 400, 150, "none",
          f'stroke="{INK}" stroke-width="26" stroke-linejoin="round"')
    k2 = T(252, CY, "K", dela, 400, 150, "#FFD400")
    return svg(place(tool("bolt", INK, 13), 48, 95, 1.30) + k + k2)

def combo_backdrop():
    body, _ = outlined(["トルク", "管理して"], "'Train One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#FFD400", cap=100, ow=26, iw=13)
    return svg(place(tool("gear", INK, 11), 60, 30, 2.6, opacity=.14) + body)

def combo_flank():
    body, _ = outlined(["交代して"], "'Mochiy Pop One', sans-serif", 400, fill="#FF6B35",
                       outer=INK, inner="#FFFFFF", cap=88, ow=24, iw=12)
    return svg(place(tool("driver", INK, 9), 12, 108, 0.78, rot=-8)
               + place(tool("hex", INK, 9), 282, 108, 0.78, rot=8) + body)

def combo_ontop():
    body, _ = outlined(["タイヤ", "終わってる"], "'Hachi Maru Pop', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#E8402A", cap=96, ow=24, iw=12, cy=192)
    return svg(place(tool("tire", INK, 10), 138, 14, 0.92, rot=-14) + body)

COMBO = [
 ("角にちょこっと", "TOOL 01", combo_corner, "空いた隅に小さく落とす。いちばん邪魔をしない置き方"),
 ("文字を貫く", "TOOL 02", combo_through, "工具を大きく背面に通す。文字と一体の絵になる"),
 ("文字の一部を置換", "TOOL 03", combo_replace, "O をナットに差し替える。短い語ほど成立しやすい"),
 ("背景に大きく薄く", "TOOL 04", combo_backdrop, "薄く敷いて地紋にする。40個で使い回しが効く"),
 ("両側から挟む", "TOOL 05", combo_flank, "左右対称に置く。文字が短いときの間延びを埋める"),
 ("上に載せる", "TOOL 06", combo_ontop, "文字の上に転がす。動きが出て縦の間が持つ"),
]

def car_small():
    body, _ = outlined(["出庫", "します"], "'Dela Gothic One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#17A2A2", cap=104, ow=26, iw=13, cy=142)
    return svg(body + place(car("cool", INK, "#17A2A2"), 118, 236, 1.0))

def car_backdrop():
    body, _ = outlined(["納車", "しますっ"], "'Reggae One', sans-serif", 400, fill="#FFD400",
                       outer=INK, inner="#FFFFFF", cap=100, ow=26, iw=13)
    return svg(place(car("cool", INK, INK), 22, 96, 2.3, opacity=.13) + body)

def car_cute():
    body, _ = outlined(["ありがとう"], "'Mochiy Pop One', sans-serif", 400, fill="#FF6B35",
                       outer=INK, inner="#FFFFFF", cap=84, ow=24, iw=12, cy=128)
    return svg(body + place(car("cute", INK, "#FFD400", eyes=True), 122, 212, 1.05))

def car_carry():
    body, _ = outlined(["レッカー", "呼びます"], "'Potta One', sans-serif", 400, fill="#FFFFFF",
                       outer=INK, inner="#E8402A", cap=96, ow=24, iw=12, cy=124)
    return svg(body
               + place(car("cool", INK, "#E8402A"), 34, 216, 0.86)
               + place(car("cute", INK, "#FFFFFF"), 206, 210, 0.78)
               + f'<line x1="150" y1="248" x2="214" y2="248" stroke="{INK}" stroke-width="9" stroke-linecap="round" stroke-dasharray="14 10"/>')

CARS = [
 ("小さく添える", "CAR 01", car_small, "文字の下に低いシルエットを置く。硬派な方向に振れる"),
 ("背景に薄く大きく", "CAR 02", car_backdrop, "地紋にする。車種が特定できない抽象度が安全でもある"),
 ("かわいい車", "CAR 03", car_cute, "背を高く丸く、ライトを目に。挨拶・感謝と相性がよい"),
 ("2台で状況を作る", "CAR 04", car_carry, "牽引や入庫など、車を2台置くと状況そのものが絵になる"),
]

SIZE_TEST = [("FREE 05 ドットの表示器", free_dotmatrix), ("FREE 02 立体押し出し", free_extrude),
             ("TOOL 04 背景に薄く", combo_backdrop)]

# ================================================================ HTML 組み立て
FONT_URL = ("https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700"
            "&family=IBM+Plex+Mono:wght@400;500"
            "&family=Dela+Gothic+One&family=DotGothic16&family=Hachi+Maru+Pop"
            "&family=Kaisei+Decol:wght@700&family=Mochiy+Pop+One&family=New+Tegomin"
            "&family=Potta+One&family=Rampart+One&family=Reggae+One"
            "&family=Shippori+Mincho+B1:wght@800&family=Train+One&family=Yuji+Syuku"
            "&display=swap")

def plate(code, title, en, note, inner):
    return f'''
<section class="plate">
  <header><span class="code">{code}</span><h2>{title}<span class="en">{en}</span></h2></header>
  <div class="inner">
    <p class="note">{note}</p>
    {inner}
  </div>
</section>'''

def cardgrid(items, cls="grid"):
    return f'<div class="{cls}">' + "".join(items) + "</div>"

def build():
    # PART 1
    fcards = []
    for font, weight, lines, desc, use in FONTS:
        fcards.append(f'''<figure class="card">
        <div class="st free">{font_card(font, weight, lines)}</div>
        <figcaption><b class="fname">{font}</b><span class="d">{desc}</span>
        <span class="u">{use}</span></figcaption></figure>''')
    p1 = cardgrid(fcards)

    # PART 2 / 4 / 5 は共通の作り
    def treat(items):
        out = []
        for title, code, fn, desc in items:
            out.append(f'''<figure class="card">
            <div class="st free">{fn()}</div>
            <figcaption><b class="fname">{code} — {title}</b><span class="d">{desc}</span></figcaption></figure>''')
        return cardgrid(out)

    p2, p4, p5 = treat(FREE), treat(COMBO), treat(CARS)

    # PART 3 工具
    ticons = "".join(f'<figure class="tool"><div class="ti">{tool_card(n)}</div>'
                     f'<figcaption>{label}</figcaption></figure>' for n, label in TOOLS)
    p3 = f'<div class="tools">{ticons}</div>'

    # 実寸
    rows_html = ""
    for label, fn in SIZE_TEST:
        s = fn()
        rows_html += (f'<div class="row"><div class="rowlabel">{label}</div><div class="sizes">'
                      + "".join(f'<figure><div style="width:{w}px;max-width:100%">{s}</div>'
                                f'<figcaption>{cap}</figcaption></figure>'
                                for w, cap in ((370, "370 px 入稿"), (92, "92 px トーク"), (58, "58 px 一覧")))
                      + '</div></div>')

    page = f'''<title>整備士スタンプ 造形見本</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONT_URL}">
<style>
:root{{--paper:#F0F0EE;--surface:#FAFAF8;--sunk:#E5E5E1;--ink:#191918;--body:#333331;
 --muted:#6D6D68;--rule:#D2D2CC;--rule-soft:#E1E1DB;--chk1:#E9E9E4;--chk2:#F6F6F3;}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
 --paper:#111111;--surface:#1A1A19;--sunk:#0C0C0C;--ink:#ECECE8;--body:#C5C5BF;
 --muted:#8E8E88;--rule:#2B2B29;--rule-soft:#222221;--chk1:#232322;--chk2:#1C1C1B;}}}}
:root[data-theme="dark"]{{--paper:#111111;--surface:#1A1A19;--sunk:#0C0C0C;--ink:#ECECE8;
 --body:#C5C5BF;--muted:#8E8E88;--rule:#2B2B29;--rule-soft:#222221;--chk1:#232322;--chk2:#1C1C1B;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--body);
 font-family:"BIZ UDPGothic","Hiragino Sans",sans-serif;font-size:15px;line-height:1.85;
 -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1060px;margin:0 auto;padding:0 20px 96px}}
.masthead{{padding:56px 0 26px;border-bottom:2px solid var(--ink)}}
.eyebrow{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.22em;
 text-transform:uppercase;color:var(--muted)}}
h1{{font-size:clamp(32px,5.5vw,50px);line-height:1.12;letter-spacing:.04em;font-weight:700;
 margin:.3em 0 .2em;color:var(--ink)}}
.sub{{color:var(--muted);max-width:66ch;margin:0}}
.plate{{margin-top:40px;border:1px solid var(--rule);background:var(--surface)}}
.plate>header{{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;padding:14px 20px;
 border-bottom:1px solid var(--rule);background:var(--sunk)}}
.code{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;
 background:var(--ink);color:var(--surface);padding:3px 9px;white-space:nowrap}}
.plate h2{{font-size:19px;margin:0;color:var(--ink);letter-spacing:.03em}}
.plate h2 .en{{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:400;
 color:var(--muted);letter-spacing:.13em;margin-left:11px}}
.inner{{padding:22px 20px}}
.note{{margin:0 0 20px;color:var(--body);max-width:72ch;font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:16px}}
.card{{margin:0;border:1px solid var(--rule-soft);background:var(--sunk)}}
.st{{border-bottom:1px solid var(--rule-soft)}}
.st.free{{background-image:
 linear-gradient(45deg,var(--chk1) 25%,transparent 25%,transparent 75%,var(--chk1) 75%),
 linear-gradient(45deg,var(--chk1) 25%,transparent 25%,transparent 75%,var(--chk1) 75%);
 background-size:20px 20px;background-position:0 0,10px 10px;background-color:var(--chk2)}}
.st svg{{display:block;width:100%;height:auto}}
.card figcaption{{padding:9px 11px;background:var(--surface);display:flex;flex-direction:column;gap:2px}}
.fname{{color:var(--ink);font-size:12.5px;font-family:"IBM Plex Mono",monospace;letter-spacing:.02em}}
.d{{font-size:12.5px;color:var(--body);line-height:1.55}}
.u{{font-size:11px;color:var(--muted);font-family:"IBM Plex Mono",monospace;letter-spacing:.05em}}
.tools{{display:grid;grid-template-columns:repeat(auto-fill,minmax(108px,1fr));gap:14px}}
.tool{{margin:0;text-align:center}}
.ti{{border:1px solid var(--rule-soft);background:var(--sunk);padding:10px}}
.ti svg{{display:block;width:100%;height:auto}}
.tool figcaption{{margin-top:7px;font-size:11.5px;color:var(--muted);line-height:1.45}}
.row{{padding:18px 0;border-bottom:1px solid var(--rule-soft)}}
.row:last-child{{border-bottom:0}}
.rowlabel{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;
 color:var(--muted);margin-bottom:12px}}
.sizes{{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-end}}
.sizes figure{{margin:0}}
.sizes figcaption{{margin-top:8px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;
 color:var(--muted)}}
.sizes svg{{display:block;width:100%;height:auto;border:1px solid var(--rule)}}
.tablewrap{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;min-width:520px;font-size:13.5px}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--rule-soft);vertical-align:top}}
thead th{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.13em;
 text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--rule);font-weight:500;
 white-space:nowrap}}
td b{{color:var(--ink)}}
.mono{{font-family:"IBM Plex Mono",monospace;font-size:12.5px}}
.warn{{border-left:3px solid var(--ink);padding:2px 0 2px 18px;margin:20px 0 0}}
.warn p{{margin:0 0 8px;font-size:13.5px}} .warn p:last-child{{margin:0}}
footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--muted)}}
footer a{{color:var(--ink)}}
a:focus-visible{{outline:2px solid var(--ink);outline-offset:3px}}
</style>
<div class="wrap">
<header class="masthead">
  <div class="eyebrow">Type &amp; Form Specimen vol.2</div>
  <h1>整備士スタンプ 造形見本</h1>
  <p class="sub">四角い枠に文字を流し込むのをやめ、<b>文字そのものを形にする</b>方向で組み直した。癖のある書体 12 種、枠を使わないレタリング 6 種、工具と車のモチーフ、そしてその添え方。市松模様は透過部分を示している。</p>
</header>
{plate("PART 1", "書体カタログ", "TYPEFACES",
   "同じ扱い（三重の縁取り・枠なし）で 12 書体を並べた。ここでの選択が、そのままシリーズの性格になる。すべて Google Fonts の日本語書体で、原則 SIL OFL のため商用利用・改変とも可。", p1)}
{plate("PART 2", "枠を使わない形", "FREE FORM",
   "背景を透過させ、文字の輪郭そのものをスタンプの形にする。市松模様が透けている部分。<b>枠がないぶんトーク画面に馴染み、他のスタンプに埋もれない。</b>", p2)}
{plate("PART 3", "工具モチーフ", "TOOL MARKS",
   "線を太く、細部を捨てたデフォルメ。<b>実在ブランドの意匠を避けるため、一般化した形だけで構成している。</b>単色なので、どの配色にも載せられる。", p3)}
{plate("PART 4", "文字 × 工具 の添え方", "COMBINATION",
   "同じ工具でも、置き方で役割が変わる。40 個を作るときは<b>この 6 通りを配分する</b>と、単調にならずに統一感が保てる。", p4)}
{plate("PART 5", "車モチーフ", "CAR MARKS",
   "実在車種と特定できない抽象度に留める。<b>これは権利対策であると同時に、可愛さ・格好よさを自由に振れるという利点でもある。</b>低く長い輪郭は硬派に、背が高く丸い輪郭は可愛い方向に振れる。", p5)}
{plate("TEST", "実寸での可読性", "LEGIBILITY", "右端の 58px で意味が判別できなければ不採用。装飾を増やすほどここが厳しくなる。", rows_html)}

<section class="plate">
  <header><span class="code">SUMMARY</span><h2>組み立ての指針<span class="en">HOW TO BUILD 40</span></h2></header>
  <div class="inner">
    <p class="note">40 個すべてを凝った造形にすると、かえって単調で読みにくくなる。<b>骨格は 1 つに決め、装飾は配分する。</b></p>
    <div class="tablewrap">
      <table>
        <thead><tr><th>要素</th><th>配分の目安</th><th>考え方</th></tr></thead>
        <tbody>
          <tr><td><b>書体</b></td><td>主 1 ＋ 従 2〜3</td><td>主書体で 25 個前後。残りを感情に応じて振る</td></tr>
          <tr><td><b>枠なし（FREE 01）</b></td><td>25 個前後</td><td>三重の縁取りを基本形に据える。最も潰しが効く</td></tr>
          <tr><td><b>凝った造形</b></td><td>8〜10 個</td><td>立体・アーチ・縦組み・ドット表示。多用すると散らかる</td></tr>
          <tr><td><b>工具を添える</b></td><td>12〜15 個</td><td>角・貫通・置換・地紋を配分。全部には付けない</td></tr>
          <tr><td><b>車を添える</b></td><td>4〜6 個</td><td>入庫・出庫・納車・レッカーなど、車が要る文言だけ</td></tr>
          <tr><td><b>装飾なし</b></td><td>10 個前後</td><td>短い汎用語は文字だけで強い。<b>余白が全体を締める</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="warn">
      <p><b>権利。</b>工具・車はすべて一般化した形に留めてある。実在ブランドのロゴや意匠、特定できる車種の外観は入れないこと。<b>抽象化は表現の選択であると同時に、審査を通すための条件でもある。</b></p>
      <p><b>余白。</b>枠なしの形は縁取りが外側に膨らむ。外周 10px の完全透過を必ず残すこと。<span class="mono">tools/check_stickers.py</span> が自動で判定する。</p>
    </div>
  </div>
</section>

<footer>
  文言は <span class="mono">content/04-text-only-candidates.md</span> の候補 161 個から採用。
  この見本の各図は <span class="mono">design/generate_specimens2.py</span> が生成している。
  書体のライセンスは改定されるため、使用前に各配布ページで原文を確認し、その時点の規約を保存すること。
  制作ガイドラインは <a href="https://creator.line.me/ja/guideline/sticker/">LINE Creators Market 公式</a>で再確認。
</footer>
</div>
'''
    pathlib.Path(__file__).parent.joinpath('text-sticker-specimens2.html').write_text(page, encoding='utf-8')
    print("書き出し:", len(page), "bytes /", page.count('viewBox="0 0 370 320"'), "枚のスタンプ")

if __name__ == "__main__":
    build()

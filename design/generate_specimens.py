# -*- coding: utf-8 -*-
"""見本帳のHTMLを生成する。各スタンプは 370x320 のSVGとして書き出す。"""
import html, pathlib, sys

W, H = 370, 320

def fit(lines, max_w=298, max_h=196, cap=124):
    n = len(lines)
    longest = max(len(l) for l in lines)
    size = min(cap, max_w / longest, max_h / (n * 1.14))
    return round(size, 1)

def text_block(lines, family, weight, fill, cy=None, cap=124, extra="", lsp=0):
    """中央寄せの複数行テキストを返す。"""
    size = fit(lines, cap=cap)
    lh = size * 1.14
    cy = cy if cy is not None else 160
    top = cy - (len(lines) - 1) * lh / 2
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="185" y="{round(top + i*lh, 1)}" text-anchor="middle" '
            f'dominant-baseline="central" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" letter-spacing="{lsp}" {extra}>{html.escape(line)}</text>'
        )
    return "\n      ".join(out), size

def vertical(chars, family, weight, fill, x=185, cy=160, size=86, extra=""):
    lh = size * 1.06
    top = cy - (len(chars) - 1) * lh / 2
    return "\n      ".join(
        f'<text x="{x}" y="{round(top + i*lh,1)}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{family}" font-weight="{weight}" font-size="{size}" fill="{fill}" {extra}>{html.escape(c)}</text>'
        for i, c in enumerate(chars))

# ---------- パターンごとの描画 ----------
def pat_A(lines, accent=None):
    """現場の黒板：黒地に白抜き極太。強調語だけ黄色。"""
    body, size = text_block(lines, "'Dela Gothic One', sans-serif", 400, "#F7F5EE", cap=112)
    if accent is not None:
        body = body.replace(f'fill="#F7F5EE"', 'fill="#FFD400"', 1) if accent == 0 else body
        if accent != 0:
            parts = body.split("\n      ")
            parts[accent] = parts[accent].replace('fill="#F7F5EE"', 'fill="#FFD400"')
            body = "\n      ".join(parts)
    return f'''<rect x="10" y="18" width="350" height="284" rx="20" fill="#1A1A1A"/>
      <rect x="24" y="32" width="322" height="256" rx="10" fill="none" stroke="#55534C" stroke-width="2.5" stroke-dasharray="7 7"/>
      {body}'''

def pat_B(lines):
    """安全標識：黄地＋黒縁＋斜めストライプ帯。"""
    body, size = text_block(lines, "'Noto Sans JP', sans-serif", 900, "#141210", cap=100)
    return f'''<rect x="10" y="22" width="350" height="276" rx="10" fill="#FFD200" stroke="#141210" stroke-width="11"/>
      <rect x="22" y="34" width="326" height="26" fill="url(#hazard)"/>
      <rect x="22" y="260" width="326" height="26" fill="url(#hazard)"/>
      {body}'''

def pat_C(lines):
    """油染み・かすれ：生成り地に手書き。染みは不定形。"""
    body, size = text_block(lines, "'Yusei Magic', sans-serif", 400, "#2B2622", cap=112)
    return f'''<rect x="8" y="16" width="354" height="288" rx="26" fill="#EDE7DC"/>
      <ellipse cx="86" cy="72" rx="52" ry="34" fill="#2B2622" opacity=".075" transform="rotate(-18 86 72)"/>
      <ellipse cx="296" cy="248" rx="60" ry="38" fill="#2B2622" opacity=".07" transform="rotate(12 296 248)"/>
      <ellipse cx="304" cy="70" rx="22" ry="15" fill="#2B2622" opacity=".06" transform="rotate(-30 304 70)"/>
      <ellipse cx="70" cy="252" rx="26" ry="17" fill="#2B2622" opacity=".055" transform="rotate(24 70 252)"/>
      {body}'''

def pat_D(lines, stamp=None):
    """整備伝票：紙・罫線・パンチ穴・判子。"""
    body, size = text_block(lines, "'BIZ UDPGothic', sans-serif", 700, "#22201C", cy=172, cap=96)
    seal = ""
    if stamp:
        seal = f'''<g transform="rotate(-13 300 76)" opacity=".88">
        <circle cx="300" cy="76" r="34" fill="none" stroke="#C0392B" stroke-width="4"/>
        <text x="300" y="77" text-anchor="middle" dominant-baseline="central" font-family="'Noto Serif JP', serif" font-weight="900" font-size="26" fill="#C0392B">{html.escape(stamp)}</text>
      </g>'''
    return f'''<rect x="14" y="14" width="342" height="292" rx="5" fill="#FBFAF5" stroke="#BFBAAA" stroke-width="3"/>
      <rect x="14" y="14" width="342" height="34" fill="#E9E5D8"/>
      <text x="30" y="32" dominant-baseline="central" font-family="'BIZ UDPGothic', sans-serif" font-size="15" fill="#7A7566" letter-spacing="3">作業指示書</text>
      <circle cx="330" cy="31" r="5.5" fill="#D8D3C2"/><circle cx="312" cy="31" r="5.5" fill="#D8D3C2"/>
      <g stroke="#DAD5C4" stroke-width="2">
        <path d="M30 232 h310"/><path d="M30 258 h310"/><path d="M30 284 h310"/>
      </g>
      {seal}
      {body}'''

def pat_E(lines, bg="#FF6B35"):
    """ポップガレージ：カラフルな丸角＋丸ゴシック白抜き。"""
    body, size = text_block(
        lines, "'Zen Maru Gothic', sans-serif", 900, "#FFFFFF", cap=110,
        extra=f'paint-order="stroke fill" stroke="#25211E" stroke-width="{round(fit(lines,cap=110)*0.13,1)}" stroke-linejoin="round"')
    return f'''<rect x="12" y="20" width="346" height="280" rx="60" fill="{bg}"/>
      <rect x="12" y="20" width="346" height="280" rx="60" fill="none" stroke="#25211E" stroke-width="9"/>
      <circle cx="60" cy="66" r="9" fill="#FFFFFF" opacity=".45"/>
      <circle cx="86" cy="52" r="5" fill="#FFFFFF" opacity=".35"/>
      {body}'''

def svg(inner, cls=""):
    return f'<svg viewBox="0 0 {W} {H}" class="{cls}" role="img" aria-hidden="true">{inner}</svg>'

# ---------- 見本の中身 ----------
PATTERNS = [
  dict(code="PATTERN A", name="現場の黒板", en="GENBA BLACK",
       pitch="黒地に白抜きの極太。トーク画面（白地）で最も目立ち、最小サイズでも潰れない。",
       font="Dela Gothic One（極太ディスプレイ）", color="鉄板黒 #1A1A1A ／ 白 #F7F5EE ／ 注意黄 #FFD400",
       fits="断定・叫び・業務連絡 — 無理 / 納期未定 / 入庫しました",
       target="男性整備士。職場グループでの業務連絡が主戦場",
       note="5案中で<b>可読性が最強</b>。ただし全40個を黒にすると重い印象になる",
       cells=[(pat_A, (["無理"],), None), (pat_A, (["納期","未定"], 1), None),
              (pat_A, (["入庫","しました"],), None), (pat_A, (["了解"],), None)]),
  dict(code="PATTERN B", name="安全標識", en="SAFETY SIGN",
       pitch="工場の注意喚起サインを借りる。業界の記号なので、読む前に意味が伝わる。",
       font="Noto Sans JP 900（角の立ったゴシック）", color="標識黄 #FFD200 ／ 黒 #141210",
       fits="注意喚起・強い断り — 締めすぎ / タイヤ終わってる / 車検通りません",
       target="工場全般。整備士以外の現場職にも通じる",
       note="強いぶん<b>多用すると疲れる</b>。40個中 3〜5個の差し色として使うのが合う",
       cells=[(pat_B, (["締めすぎ"],), None), (pat_B, (["タイヤ","終わってる"],), None),
              (pat_B, (["車検","通りません"],), None), (pat_B, (["危険"],), None)]),
  dict(code="PATTERN C", name="油染み・かすれ", en="OIL STAIN",
       pitch="くたびれた手書きと油の染み。共感と自虐の温度をそのまま版面にする。",
       font="Yusei Magic（手書きマーカー）", color="生成り #EDE7DC ／ 油墨 #2B2622",
       fits="疲弊・自虐・共感 — 今日残業確定 / 手が油まみれ / わからん",
       target="整備士本人。<b>購買のトリガーになるカテゴリ G と完全に対応</b>",
       note="SNSで最も拡散しやすい。ただし<b>最小サイズでの可読性は5案中で最弱</b>",
       cells=[(pat_C, (["今日","残業確定"],), None), (pat_C, (["手が油","まみれ"],), None),
              (pat_C, (["わからん"],), None), (pat_C, (["まだ帰れない"],), None)]),
  dict(code="PATTERN D", name="整備伝票", en="WORK ORDER",
       pitch="作業指示書の紙をそのまま持ち込む。業界のリアルな道具立てで、他業種に模倣されにくい。",
       font="BIZ UDPGothic 700 ／ 判子は Noto Serif JP", color="紙 #FBFAF5 ／ 罫 #DAD5C4 ／ 朱 #C0392B",
       fits="事務・進捗・接客 — 見積出します / 部品発注しました / 承認",
       target="フロント・事務。<b>整備士以外の社内メンバーにも売れる</b>",
       note="5案で<b>最もオリジナリティが高い</b>。文字が小さくなりがちなのが弱点",
       cells=[(pat_D, (["見積","出します"],), "承認"), (pat_D, (["部品","発注しました"],), None),
              (pat_D, (["車検","完了"],), "済"), (pat_D, (["確認します"],), None)]),
  dict(code="PATTERN E", name="ポップガレージ", en="POP GARAGE",
       pitch="明るい丸ゴシックと原色。挨拶とリアクションを軽く投げられる。",
       font="Zen Maru Gothic 900（丸ゴシック）", color="橙 #FF6B35 ／ 青緑 #17A2A2 ／ 黄 #F5B301 ／ 縁 #25211E",
       fits="挨拶・リアクション・軽い依頼 — ありがとう / OK / お疲れさま",
       target="若手・フロント。年齢層と性別を広く取れる",
       note="<b>汎用リアクション13個の受け皿に最適</b>。単体では整備士感が薄い",
       cells=[(pat_E, (["ありがとう"],), None), (pat_E, (["OK"], "#17A2A2"), None),
              (pat_E, (["お疲れ","さま"], "#F5B301"), None), (pat_E, (["助かる"], "#17A2A2"), None)]),
]

def render_cell(spec):
    fn, args, extra = spec
    if fn is pat_D:
        return svg(fn(*args, stamp=extra))
    return svg(fn(*args))

cards = []
for p in PATTERNS:
    samples = "\n        ".join(f'<div class="st">{render_cell(c)}</div>' for c in p["cells"])
    cards.append(f'''
<section class="plate">
  <header>
    <span class="code">{p["code"]}</span>
    <h2>{p["name"]}<span class="en">{p["en"]}</span></h2>
  </header>
  <div class="inner">
    <p class="pitch">{p["pitch"]}</p>
    <div class="samples">
        {samples}
    </div>
    <dl class="spec">
      <dt>書体</dt><dd>{p["font"]}</dd>
      <dt>配色</dt><dd class="mono">{p["color"]}</dd>
      <dt>向く文言</dt><dd>{p["fits"]}</dd>
      <dt>ターゲット</dt><dd>{p["target"]}</dd>
      <dt>評価</dt><dd>{p["note"]}</dd>
    </dl>
  </div>
</section>''')

pathlib.Path('build/cards.html').write_text("\n".join(cards), encoding='utf-8')

# 可読性テスト用（A と C を3サイズで）
tests = {
  "A": svg(pat_A(["納期","未定"], 1)),
  "C": svg(pat_C(["今日","残業確定"])),
  "D": svg(pat_D(["見積","出します"], stamp="承認")),
}
pathlib.Path('build/tests.py.json').write_text(repr(tests), encoding='utf-8')

# トーク画面用
talk = {
  "a1": svg(pat_A(["入庫","しました"])),
  "e1": svg(pat_E(["OK"], "#17A2A2")),
  "c1": svg(pat_C(["まだ帰れない"])),
  "e2": svg(pat_E(["お疲れ","さま"], "#F5B301")),
}
pathlib.Path('build/talk.py.json').write_text(repr(talk), encoding='utf-8')
print("カード", len(cards), "件を生成")

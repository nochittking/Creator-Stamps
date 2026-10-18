// SVG を透過 PNG に書き出す。大きさは各 SVG の width/height のまま（370x320・240x240・96x74）。
//
// 2026-10-18 の不具合: Google Fonts の読み込みに失敗すると、ブラウザは黙って別のフォントで描いた。
// この環境で選ばれたのは中国語フォント（WenQuanYi Zen Hei）で、「今」の一画目が点、「誤」の右が「吴」、
// 「駅」「返」「割」も中国の字形になった。
//   → フォントは design/fonts/ の手元のファイルを @font-face で読む（ネットに頼らない）
//   → 読み込めなかったら書き出さずに止める
//   → lang="ja" を付け、万一のときも日本語の字形を選ばせる
//
// フォントの用意（初回だけ。15MB あるのでリポジトリには入れない。OFL）
//   curl -L -o design/fonts/ShipporiMinchoB1-ExtraBold.ttf \
//     https://raw.githubusercontent.com/google/fonts/main/ofl/shipporiminchob1/ShipporiMinchoB1-ExtraBold.ttf
//
// 使い方: node render_png.js <SVGのディレクトリ> <PNGのディレクトリ> [倍率]（手描き用の下絵は 2）
const { execSync } = require('child_process');
const { chromium } = require(execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), os = require('os'), path = require('path');

const FONT_FILE = path.join(__dirname, 'fonts', 'ShipporiMinchoB1-ExtraBold.ttf');
const FAMILY = 'Shippori Mincho B1';

(async () => {
  const [, , dir, out, scale = '1'] = process.argv;
  if (!dir || !out) { console.error('使い方: node render_png.js <svgdir> <pngdir>'); process.exit(2); }
  if (!fs.existsSync(FONT_FILE)) { console.error(`フォントがない: ${FONT_FILE}（先頭のコメントの手順で用意する）`); process.exit(1); }
  fs.mkdirSync(out, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'render-'));
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: +scale });
  let n = 0;
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort()) {
    // SVG 内の Google Fonts の @import は外す（失敗したときに別フォントへ逃げる原因）
    const svg = fs.readFileSync(path.join(dir, f), 'utf8').replace(/@import url\([^)]*\);?/g, '');
    const w = +svg.match(/width="(\d+)"/)[1], h = +svg.match(/height="(\d+)"/)[1];
    const page = path.join(tmp, 'page.html');
    fs.writeFileSync(page, `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>
      @font-face{font-family:'${FAMILY}';font-weight:800;src:url('file://${FONT_FILE}') format('truetype')}
      body{margin:0;background:transparent}</style></head><body>${svg}</body></html>`);
    await p.setViewportSize({ width: w, height: h });
    await p.goto('file://' + page);
    const loaded = await p.evaluate(async fam => {
      const faces = await document.fonts.load(`800 40px "${fam}"`, '今駅返誤割');
      return faces.length > 0 && document.fonts.check(`800 40px "${fam}"`, '今駅返誤割');
    }, FAMILY);
    if (!loaded) { console.error(`${f}: ${FAMILY} を読み込めなかったので止めた`); await b.close(); process.exit(1); }
    await p.screenshot({ path: path.join(out, f.replace(/\.svg$/, '.png')), omitBackground: true,
                         clip: { x: 0, y: 0, width: w, height: h } });
    n++;
  }
  await b.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`${n} 枚 → ${out}`);
})();

// 全国30シリーズの書き出し。
//   PNG: build/series_png/<地方>/<シリーズ>/NN_*.png（370x320 透過・申請用。リポジトリには入れない）
//   SHEETS_ONLY=1 で PNG を作り直さず一覧だけ作る
//   一覧: build/series_sheets/<シリーズ>.jpg（確認用。4列・半分の大きさ）
// 使い方: node export_series.js [シリーズのディレクトリ名の一部 ...]
// Playwright はグローバルに入っているものを使う（PLAYWRIGHT_BROWSERS_PATH 設定済みの環境）
const { execSync } = require('child_process');
const { chromium } = require(execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, 'build');
const FONT = 'https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@800&display=swap';
const want = process.argv.slice(2);

function seriesDirs() {
  const out = [];
  const base = path.join(ROOT, 'series');
  for (const r of fs.readdirSync(base).sort())
    for (const s of fs.readdirSync(path.join(base, r)).sort())
      if (!want.length || want.some(w => s.includes(w))) out.push([r, s]);
  return out;
}

(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 370, height: 320 } });
  const sheet = await b.newPage({ viewport: { width: 760, height: 400 } });
  for (const [r, s] of seriesDirs()) {
    const dir = path.join(ROOT, 'series', r, s);
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort();
    const stamps = files.filter(f => f !== 'main.svg' && f !== 'tab.svg');
    const pngDir = path.join(ROOT, 'series_png', r, s);
    fs.mkdirSync(pngDir, { recursive: true });
    for (const f of (process.env.SHEETS_ONLY ? [] : files)) {
      const svg = fs.readFileSync(path.join(dir, f), 'utf8');
      // main（240x240）と tab（96x74）は大きさが違う
      const size = f === 'main.svg' ? [240, 240] : f === 'tab.svg' ? [96, 74] : [370, 320];
      await page.setViewportSize({ width: size[0], height: size[1] });
      await page.setContent(`<html><head><link rel="stylesheet" href="${FONT}"></head><body style="margin:0;background:transparent">${svg}</body></html>`);
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: path.join(pngDir, f.replace('.svg', '.png')), omitBackground: true,
                              clip: { x: 0, y: 0, width: size[0], height: size[1] }, timeout: 60000 });
    }
    // file:// の画像は about:blank から読めないので data URI で埋め込む
    const cells = stamps.map(f => {
      const b64 = fs.readFileSync(path.join(pngDir, f.replace('.svg', '.png'))).toString('base64');
      return `<div class="c"><img src="data:image/png;base64,${b64}"></div>`;
    }).join('');
    await sheet.setContent(`<html><body style="margin:0;background:#9bb4c9;width:760px">
      <div style="font:bold 18px sans-serif;color:#1e1a1d;padding:8px 10px;background:#fff">${s}（${stamps.length}）</div>
      <div style="display:grid;grid-template-columns:repeat(4,185px);gap:4px;padding:4px">${cells}</div>
      <style>.c img{width:185px;height:160px;display:block}</style></body></html>`);
    await sheet.waitForTimeout(200);
    fs.mkdirSync(path.join(ROOT, 'series_sheets'), { recursive: true });
    await sheet.screenshot({ path: path.join(ROOT, 'series_sheets', `${s}.jpg`), type: 'jpeg', quality: 82, fullPage: true });
    console.log(`${s} ${stamps.length}`);
  }
  await b.close();
})();

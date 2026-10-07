// Exporta el deck a PDF (una lámina por página, 1920x1080) y, opcionalmente, capturas PNG.
// Uso:  node deck/tools/export-pdf.cjs            -> deck/Serendipity_x_Zamna_2027.pdf
//       node deck/tools/export-pdf.cjs --png       -> además deck/capturas/slide-NN.png
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const deck = path.resolve(__dirname, '..');
const html = 'file://' + path.join(deck, 'index.html') + '?render';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(html, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  if (process.argv.includes('--png')) {
    const out = path.join(deck, 'capturas');
    fs.mkdirSync(out, { recursive: true });
    const slides = page.locator('section.slide');
    const n = await slides.count();
    for (let i = 0; i < n; i++) await slides.nth(i).screenshot({ path: path.join(out, `slide-${String(i + 1).padStart(2, '0')}.png`) });
    console.log(`${n} capturas -> ${out}`);
  }
  const pdf = path.join(deck, 'Serendipity_x_Zamna_2027.pdf');
  await page.pdf({ path: pdf, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true });
  console.log('PDF -> ' + pdf);
  await browser.close();
})();

// Exporta el deck a un PDF ligero: una lámina por página a 1920x1080.
// Cada página lleva el fondo (fotos, luz, grano, líneas) como UNA sola imagen JPEG
// y el texto encima como texto real (nítido, seleccionable y buscable).
// Así el PDF pesa pocos MB y abre rápido, sin las capas de transparencia que
// Chrome genera a 300 dpi para cada desenfoque o degradado.
//
// Uso:  node deck/tools/export-pdf.cjs            -> deck/Serendipity_x_Zamna_2027.pdf
//       node deck/tools/export-pdf.cjs --png      -> además deck/capturas/slide-NN.png
//       node deck/tools/export-pdf.cjs --q=80     -> calidad JPEG del fondo (por defecto 82)
const path = require('path');
const fs = require('fs');
const os = require('os');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const deck = path.resolve(__dirname, '..');
const html = 'file://' + path.join(deck, 'index.html') + '?render';
const qArg = process.argv.find(a => a.startsWith('--q='));
const quality = qArg ? parseInt(qArg.slice(4), 10) : 82;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(html, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  const slides = page.locator('section.slide');
  const n = await slides.count();

  if (process.argv.includes('--png')) {
    const out = path.join(deck, 'capturas');
    fs.mkdirSync(out, { recursive: true });
    for (let i = 0; i < n; i++) await slides.nth(i).screenshot({ path: path.join(out, `slide-${String(i + 1).padStart(2, '0')}.png`) });
    console.log(`${n} capturas -> ${out}`);
  }

  // 1) Fondo de cada lámina sin texto (solo se vuelve transparente el relleno de las letras).
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'deck-pdf-'));
  const hideText = await page.addStyleTag({ content:
    'section.slide, section.slide *{-webkit-text-fill-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important}' });
  await page.waitForTimeout(100);
  const bgs = [];
  for (let i = 0; i < n; i++) {
    const file = path.join(tmp, `bg-${String(i + 1).padStart(2, '0')}.jpg`);
    await slides.nth(i).screenshot({ path: file, type: 'jpeg', quality });
    bgs.push('file://' + file);
  }
  await hideText.evaluate(el => el.remove());

  // 2) Deja visible solo el texto y pone la imagen de fondo en cada lámina.
  await page.evaluate(bgs => {
    const slides = [...document.querySelectorAll('section.slide')];
    slides.forEach((s, i) => {
      s.style.setProperty('background', `url("${bgs[i]}") 0 0 / 1920px 1080px no-repeat`, 'important');
      const walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (node.textContent.trim() && node.parentElement) node.parentElement.classList.add('pdf-t');
      }
    });
  }, bgs);
  await page.addStyleTag({ content: [
    'section.slide *{visibility:hidden!important;filter:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;mix-blend-mode:normal!important;box-shadow:none!important}',
    'section.slide *::before, section.slide *::after{visibility:hidden!important}',
    'section.slide .pdf-t{visibility:visible!important;background:none!important;border-color:transparent!important;outline:none!important}',
  ].join('\n') });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);

  const pdf = path.join(deck, 'Serendipity_x_Zamna_2027.pdf');
  await page.pdf({ path: pdf, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true });
  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`PDF -> ${pdf} (${(fs.statSync(pdf).size / 1048576).toFixed(1)} MB, ${n} páginas)`);
})();

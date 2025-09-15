// File: generate-keith-resume.js (fixed)
// Usage:
//   npm i puppeteer handlebars
//   node generate-keith-resume.js
//
// Expects these files side-by-side:
//   - ./keith-resume-template.html
//   - ./keith_etiometry_resume_json.json

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

// ---------- Handlebars helpers ----------
// FIX: Guard against Handlebars passing the "options" hash as the 2nd arg.
// Previously sep became an object -> items.join('[object Object]').
handlebars.registerHelper('formatList', function (items, sep) {
  const hasOptionsAsSep = typeof sep === 'object' && sep !== null;
  const actualSep = hasOptionsAsSep ? ', ' : (sep ?? ', ');
  if (!Array.isArray(items) || items.length === 0) return '';
  return items.join(actualSep);
});

handlebars.registerHelper('ensureProtocol', function (maybeUrl) {
  if (!maybeUrl) return '';
  const s = String(maybeUrl).trim();
  if (s.startsWith('http://') || s.startsWith('https://') || s.startsWith('mailto:') || s.startsWith('tel:')) return s;
  return 'https://' + s;
});

handlebars.registerHelper('doiUrl', function (doi) {
  if (!doi) return '';
  const clean = String(doi).replace(/^https?:\/\/doi\.org\//i, '').trim();
  return 'https://doi.org/' + clean;
});

// ---------- Generator ----------
async function loadJson(jsonPath) {
  const raw = await fs.readFile(jsonPath, 'utf-8');
  return JSON.parse(raw);
}

function preprocess(data) {
  const out = { ...data };

  // Sort publications by year desc if present
  if (Array.isArray(out.publications)) {
    out.publications = [...out.publications].sort((a, b) => (b.year || 0) - (a.year || 0));
  }

  return out;
}

async function generatePDF({
  data,
  templatePath = './keith-resume-template.html',
  outputPath = './keith-krenek-resume.pdf',
  format = 'Letter',
  margin = { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' },
  printBackground = true,
  saveHtml = true,
  screenshot = false
} = {}) {
  // Compile template
  const tmplSrc = await fs.readFile(templatePath, 'utf-8');
  const template = handlebars.compile(tmplSrc);

  const html = template(preprocess(data));
  if (saveHtml) {
    await fs.writeFile('keith-resume-generated.html', html, 'utf-8');
  }

  // Render with Puppeteer
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: ['domcontentloaded', 'networkidle0'] });
    await page.evaluateHandle('document.fonts && document.fonts.ready');

    if (screenshot) {
      await page.screenshot({ path: 'keith-resume-preview.png', fullPage: true });
    }

    await page.pdf({ path: outputPath, format, printBackground, margin, preferCSSPageSize: false });
    return outputPath;
  } finally {
    await browser.close();
  }
}

// ---------- CLI ----------
(async function main() {
  try {
    const dataPath = path.resolve('./keith_etiometry_resume_json.json');
    const data = await loadJson(dataPath);

    const pdfPath = await generatePDF({
      data,
      templatePath: path.resolve('./keith-resume-template.html'),
      outputPath: path.resolve('./keith-krenek-resume.pdf'),
      saveHtml: true,
      screenshot: true
    });

    console.log(`✅ PDF written to: ${pdfPath}`);
    console.log('💾 Also saved: keith-resume-generated.html and keith-resume-preview.png');
  } catch (err) {
    console.error('❌ Failed to generate resume:', err);
    process.exit(1);
  }
})();

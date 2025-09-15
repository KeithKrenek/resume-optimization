// File: generate-keith-resume.js
// Usage:
//   npm i puppeteer handlebars
//   node generate-keith-resume.js
//
// Expects:
//   - ./keith-resume-template.html
//   - ./keith_etiometry_resume_json.json  (or replace below)

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

/* ---------------- Handlebars helpers ---------------- */
handlebars.registerHelper('formatList', function (items, sep) {
  const hasOptionsAsSep = typeof sep === 'object' && sep !== null;
  const actualSep = hasOptionsAsSep ? ', ' : (sep ?? ', ');
  if (!Array.isArray(items) || items.length === 0) return '';
  return items.join(actualSep);
});
handlebars.registerHelper('formatMaybeList', function (value, sep) {
  const hasOptionsAsSep = typeof sep === 'object' && sep !== null;
  const actualSep = hasOptionsAsSep ? ' | ' : (sep ?? ' | ');
  if (Array.isArray(value)) return value.join(actualSep);
  if (value == null) return '';
  return String(value);
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

/* ---------------- Utility ---------------- */
async function loadJson(jsonPath) {
  const raw = await fs.readFile(jsonPath, 'utf-8');
  return JSON.parse(raw);
}

function mergeArraysUnique(a = [], b = []) {
  const set = new Set([...(a || []), ...(b || [])].map(String));
  return Array.from(set);
}
function mergeMapOfArrays(a = {}, b = {}) {
  const keys = new Set([...Object.keys(a || {}), ...Object.keys(b || {})]);
  const out = {};
  for (const k of keys) {
    const av = Array.isArray(a?.[k]) ? a[k] : [];
    const bv = Array.isArray(b?.[k]) ? b[k] : [];
    out[k] = mergeArraysUnique(av, bv);
  }
  return out;
}

/* ---- RAO/IMPACT sections for projects ---- */
function buildProjectSections(project) {
  const titleCase = (s) => String(s || '').replace(/\b\w/g, c => c.toUpperCase());
  const normalizeVal = (v) => {
    if (Array.isArray(v)) return v.join('; ');
    if (v && typeof v === 'object') {
      return Object.entries(v).map(([k, val]) => `${titleCase(k)}: ${normalizeVal(val)}`).join('; ');
    }
    return String(v ?? '');
  };
  const lower = (s) => String(s || '').toLowerCase();
  const dict = Object.keys(project || {}).reduce((acc, k) => { acc[lower(k)] = k; return acc; }, {});
  const getVal = (names) => {
    for (const n of names) {
      const real = dict[lower(n)];
      if (real && project[real] != null && String(project[real]).trim() !== '') return project[real];
    }
    return null;
  };

  const groups = [
    { title: 'Challenge', keys: ['challenge','problem','context'] },
    { title: 'Role', keys: ['role','responsibility','responsibilities'] },
    { title: 'Approach', keys: ['approach','action','actions','solution','method','methods'] },
    { title: 'Impact', keys: ['impact_section','impact','outcome','results','result','metrics'] },
  ];

  const sections = [];
  for (const g of groups) {
    const val = getVal(g.keys);
    if (val != null && String(normalizeVal(val)).trim() !== '') {
      sections.push({ title: g.title, content: normalizeVal(val) });
    }
  }
  const hasImpactSection = sections.some(s => s.title === 'Impact');
  return { sections, hasImpactSection };
}

/* ---------------- Preprocess (union normalizer) ---------------- */
function preprocess(input) {
  const d = { ...input };

  // Core skills: merge core_skills + core_competencies into one map
  const mergedCore = mergeMapOfArrays(d.core_skills, d.core_competencies);
  d.core_skills_all = Object.keys(mergedCore).length ? mergedCore : undefined;

  // Projects: merge "projects" and "selected_projects", normalize fields
  const proj = Array.isArray(d.projects) ? d.projects : [];
  const sel = Array.isArray(d.selected_projects) ? d.selected_projects : [];
  const combined = [...proj, ...sel].map(p => {
    const title = p.title || p.name || '';
    const { sections, hasImpactSection } = buildProjectSections(p);
    return {
      ...p,
      title,
      sections,
      hasImpactSection
    };
  });
  d.projects_all = combined.length ? combined : undefined;
  d.projects_title = d.selected_projects && d.selected_projects.length ? 'Selected Projects' : 'Projects';

  // Publications: sort desc by year if present
  if (Array.isArray(d.publications)) {
    d.publications = [...d.publications].sort((a, b) => (b.year || 0) - (a.year || 0));
  }

  return d;
}

/* ---------------- PDF render ---------------- */
async function generatePDF({
  data,
  templatePath = './resume-template.html',
  outputPath = './keith-krenek-resume.pdf',
  format = 'Letter',
  margin = { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' },
  printBackground = true,
  saveHtml = true,
  screenshot = false
} = {}) {
  const tmplSrc = await fs.readFile(templatePath, 'utf-8');
  const template = handlebars.compile(tmplSrc);
  const html = template(preprocess(data));

  if (saveHtml) await fs.writeFile('keith-resume-generated.html', html, 'utf-8');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: ['domcontentloaded', 'networkidle0'] });
    await page.evaluateHandle('document.fonts && document.fonts.ready');

    if (screenshot) await page.screenshot({ path: 'keith-resume-preview.png', fullPage: true });
    await page.pdf({ path: outputPath, format, printBackground, margin, preferCSSPageSize: false });
    return outputPath;
  } finally {
    await browser.close();
  }
}

/* ---------------- CLI ---------------- */
(async function main() {
  try {
    const dataPath = path.resolve('./resume.json');
    const data = await loadJson(dataPath);

    const pdfPath = await generatePDF({
      data,
      templatePath: path.resolve('./resume-template.html'),
      outputPath: path.resolve('./keith-krenek-resume.pdf'),
      saveHtml: false,
      screenshot: false
    });

    console.log(`✅ PDF written to: ${pdfPath}`);
    // console.log('💾 Also saved: keith-resume-generated.html and keith-resume-preview.png');
  } catch (err) {
    console.error('❌ Failed to generate resume:', err);
    process.exit(1);
  }
})();

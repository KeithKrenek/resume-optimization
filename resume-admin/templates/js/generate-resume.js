// File: generate-keith-resume.js
// Description: A smart PDF generator that automatically finds the latest job
//              application folder and its corresponding files.
// Usage:
//   1. Configure BASE_APPLICATIONS_DIR below.
//   2. Run `npm i puppeteer handlebars` once in this folder.
//   3. Run `node generate-resume.js` from this folder (`templates/js`).

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

// --- USER CONFIGURATION ---
// IMPORTANT: Set this to the same path as "save_path" in your app.py defaults.
// Use forward slashes, e.g., "C:/Users/YourName/Documents/Job Applications"
const BASE_APPLICATIONS_DIR = "C:/Users/keith/Dropbox/Resume";
// --------------------------

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
  templatePath = './resume-template3.html',
  outputPath = './keith-krenek-resume.pdf',
  format = 'Letter',
  margin = { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' },
  printBackground = true,
  saveHtml = false,
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

/* ---------------- NEW: Dynamic File Discovery ---------------- */
/**
 * Finds the most recently modified subdirectory in a base directory.
 * @param {string} baseDir The directory to search in.
 * @returns {Promise<string|null>} The path to the latest directory or null.
 */
async function findLatestJobFolder(baseDir) {
  try {
    const entries = await fs.readdir(baseDir, { withFileTypes: true });
    const subdirs = entries
      .filter(entry => entry.isDirectory())
      .map(entry => path.join(baseDir, entry.name));

    if (subdirs.length === 0) return null;

    const dirsWithStats = await Promise.all(
      subdirs.map(async (dir) => ({
        path: dir,
        mtime: (await fs.stat(dir)).mtime,
      }))
    );

    dirsWithStats.sort((a, b) => b.mtime - a.mtime);
    return dirsWithStats[0].path;
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.error(`❌ Error: The base directory does not exist: "${baseDir}"`);
      console.error('Please update the BASE_APPLICATIONS_DIR variable in this script.');
      return null;
    }
    throw error;
  }
}

/**
 * Finds a file in a directory based on a regex pattern.
 * @param {string} dir The directory to search.
 * @param {RegExp} pattern The regex pattern to match.
 * @param {string} fileType A human-readable name for the file type for errors.
 * @returns {Promise<string|null>} The full path to the first matching file or null.
 */
async function findFileByPattern(dir, pattern, fileType) {
  const files = await fs.readdir(dir);
  const match = files.find(file => pattern.test(file));
  if (!match) {
    console.error(`❌ Could not find a ${fileType} file in "${dir}"`);
    return null;
  }
  return path.join(dir, match);
}

/* ---------------- REVISED: CLI ---------------- */
(async function main() {
  try {
    console.log('🔍 Finding latest job application folder...');
    const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);

    if (!targetDir) {
      throw new Error("No application folders found to process.");
    }
    console.log(`📂 Using folder: "${path.basename(targetDir)}"`);

    // Dynamically find the necessary files within the target directory
    const dataPath = await findFileByPattern(targetDir, /^resume.*\.json$/, 'Resume JSON');
    const templatePath = await findFileByPattern(targetDir, /\.html$/, 'HTML template');
    
    if (!dataPath || !templatePath) {
        throw new Error("Missing necessary files in the target directory.");
    }

    // Generate a clean output filename
    const companyName = path.basename(targetDir).split('_')[0] || 'resume';
    const outputPath = path.join(targetDir, `${companyName}_KKrenek_Resume.pdf`);

    // Load data and generate the PDF
    const data = await loadJson(dataPath);
    const pdfPath = await generatePDF({
      data,
      templatePath,
      outputPath
    });

    console.log(`\n✅ PDF successfully generated: ${pdfPath}`);
  } catch (err) {
    console.error(`\n❌ Failed to generate resume: ${err.message}`);
    process.exit(1);
  }
})();

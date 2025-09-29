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
const { exec } = require('child_process');

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

// ADD YOUR NEW HELPERS HERE
handlebars.registerHelper('displayUrl', function(url) {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '');
});

handlebars.registerHelper('skillLevel', function(level) {
  const icons = {
    'expert': 'â—â—â—â—â—',
    'advanced': 'â—â—â—â—â—‹',
    'intermediate': 'â—â—â—â—‹â—‹',
    'learning': 'â—â—â—‹â—‹â—‹'
  };
  return icons[level] || '';
});

// Helper to automatically determine optimal section placement
function optimizeLayout(data) {
  const processed = preprocessEnhanced(data);
  
  // Calculate "weight" of each section
  const sectionWeights = {
    experience: (processed.experience?.length || 0) * 100,
    projects: (processed.projects_all?.length || 0) * 80,
    education: (processed.education?.length || 0) * 30,
    publications: (processed.publications?.length || 0) * 25,
    work_samples: (processed.work_samples?.length || 0) * 40,
    leadership: (processed.leadership_mentoring?.length || 0) * 20,
  };
  
  // Determine if we need 2 or 3 pages based on content volume
  const totalWeight = Object.values(sectionWeights).reduce((a, b) => a + b, 0);
  processed.targetPages = totalWeight > 800 ? 3 : 2;
  
  // Smart truncation for 2-page limit
  if (processed.targetPages === 2) {
    // Keep only top 3 projects
    if (processed.projects_all?.length > 3) {
      processed.projects_all = processed.projects_all.slice(0, 3);
      processed.projects_title = "Selected Projects";
    }
    
    // Limit experience bullets to 4 each for older positions
    if (processed.experience?.length > 3) {
      processed.experience = processed.experience.map((exp, idx) => ({
        ...exp,
        highlights: idx < 2 ? exp.highlights : exp.highlights?.slice(0, 4)
      }));
    }
    
    // Keep only top 3 publications
    if (processed.publications?.length > 3) {
      processed.publications = processed.publications.slice(0, 3);
    }
  }
  
  return processed;
}

// Helper to intelligently shorten URLs for display
handlebars.registerHelper('smartUrl', function(url) {
  if (!url) return '';
  
  // Remove protocol
  let display = url.replace(/^https?:\/\//, '');
  
  // Special handling for common domains
  const shorteners = {
    'linkedin.com/in/': 'LinkedIn',
    'github.com/': 'GitHub',
    'scholar.google.com': 'Google Scholar',
    'arxiv.org': 'arXiv',
  };
  
  for (const [pattern, replacement] of Object.entries(shorteners)) {
    if (display.includes(pattern)) {
      return replacement;
    }
  }
  
  // For other URLs, truncate if too long
  if (display.length > 30) {
    const parts = display.split('/');
    if (parts.length > 2) {
      return parts[0] + '/.../' + parts[parts.length - 1];
    }
  }
  
  return display.replace(/\/$/, '');
});

// Helper to format date ranges more compactly
handlebars.registerHelper('dateRange', function(start, end) {
  // Convert "January 2024" to "Jan 2024"
  const shortMonths = {
    'January': 'Jan', 'February': 'Feb', 'March': 'Mar',
    'April': 'Apr', 'May': 'May', 'June': 'Jun',
    'July': 'Jul', 'August': 'Aug', 'September': 'Sep',
    'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
  };
  
  const shorten = (date) => {
    if (!date) return '';
    for (const [long, short] of Object.entries(shortMonths)) {
      date = date.replace(long, short);
    }
    return date;
  };
  
  const shortStart = shorten(start);
  const shortEnd = end === 'Present' ? 'Present' : shorten(end);
  
  return `${shortStart} â€“ ${shortEnd}`;
});

// Update PDF generation settings for tighter layout
async function generateCompactPDF(options) {
  return generatePDF({
    ...options,
    margin: { 
      top: '0.3in', 
      right: '0.3in', 
      bottom: '0.3in', 
      left: '0.3in' 
    },
    // Use optimized layout preprocessing
    data: optimizeLayout(options.data)
  });
}

/* ============================================
   SECTION 2: UTILITY FUNCTIONS
   Place data manipulation utilities here
   ============================================ */

// EXISTING UTILITIES (keep these)
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

// Add this to your generate-resume.js file

/**
 * Intelligent Layout Manager for Resume Sections
 * Automatically detects and aligns sections for optimal readability
 */

// Helper to analyze section sizes and determine optimal layout
function analyzeLayoutBalance(data) {
  const sectionSizes = {
    education: {
      items: data.education?.length || 0,
      estimatedLines: (data.education?.length || 0) * 3, // ~3 lines per degree
      preferredColumn: 'flexible'
    },
    publications: {
      items: data.publications?.length || 0,
      estimatedLines: (data.publications?.length || 0) * 2, // ~2 lines per pub
      preferredColumn: 'flexible'
    },
    projects: {
      items: data.projects_all?.length || 0,
      estimatedLines: (data.projects_all?.length || 0) * 6, // ~6 lines per project
      preferredColumn: 'left' // Projects usually need more space
    },
    work_samples: {
      items: data.work_samples?.length || 0,
      estimatedLines: Math.ceil((data.work_samples?.length || 0) / 2) * 4, // 2-column grid
      preferredColumn: 'flexible'
    },
    leadership: {
      items: data.leadership_mentoring?.length || 0,
      estimatedLines: (data.leadership_mentoring?.length || 0) * 1.5,
      preferredColumn: 'flexible'
    },
    certifications: {
      items: data.certifications?.length || 0,
      estimatedLines: data.certifications?.length || 0,
      preferredColumn: 'flexible'
    }
  };

  return sectionSizes;
}

// Determine optimal column placement for balanced layout
function optimizeColumnPlacement(data) {
  const sizes = analyzeLayoutBalance(data);
  
  // Calculate which sections should go in which column
  let leftColumnLines = 0;
  let rightColumnLines = 0;
  let leftSections = [];
  let rightSections = [];
  
  // Priority order for section placement
  const sectionOrder = ['projects', 'work_samples', 'education', 'publications', 'leadership', 'certifications'];
  
  for (const sectionName of sectionOrder) {
    if (!data[sectionName] && !data[sectionName + '_all']) continue;
    
    const sectionInfo = sizes[sectionName];
    
    // Place section in the column with fewer lines for balance
    if (leftColumnLines <= rightColumnLines) {
      leftSections.push(sectionName);
      leftColumnLines += sectionInfo.estimatedLines;
    } else {
      rightSections.push(sectionName);
      rightColumnLines += sectionInfo.estimatedLines;
    }
  }
  
  // Check if sections should be vertically aligned
  const shouldAlign = Math.abs(leftColumnLines - rightColumnLines) < 5; // Within 5 lines
  
  return {
    leftSections,
    rightSections,
    shouldAlign,
    leftHeight: leftColumnLines,
    rightHeight: rightColumnLines
  };
}

// Enhanced preprocessing with layout optimization
function preprocessWithLayout(input) {
  const data = preprocessEnhanced(input); // Your existing preprocessing
  
  // Add layout hints
  const layout = optimizeColumnPlacement(data);
  
  // Mark sections with their intended column
  data._layout = {
    ...layout,
    // Add CSS classes for alignment
    gridClass: layout.shouldAlign ? 'resume-grid aligned' : 'resume-grid',
    leftClass: layout.shouldAlign ? 'section-left align-start' : 'section-left',
    rightClass: layout.shouldAlign ? 'section-right align-start' : 'section-right'
  };
  
  // Reorganize sections for optimal display
  data._leftColumnSections = layout.leftSections.map(name => ({
    name,
    data: data[name] || data[name + '_all']
  }));
  
  data._rightColumnSections = layout.rightSections.map(name => ({
    name,
    data: data[name] || data[name + '_all']
  }));
  
  return data;
}

// CSS additions for automatic alignment
const alignmentStyles = `
  /* Automatic Section Alignment */
  .resume-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 16px;
    align-items: start; /* Default: each column starts at top */
  }
  
  .resume-grid.aligned {
    align-items: stretch; /* When balanced, stretch to fill */
  }
  
  /* Ensure sections in aligned grid start at same height */
  .align-start {
    align-self: start;
  }
  
  /* Smart vertical alignment for adjacent sections */
  .section-left.balanced,
  .section-right.balanced {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  /* Detect and fix orphaned sections */
  .section:only-child {
    grid-column: 1 / -1; /* Span full width if alone */
  }
  
  /* Auto-balance short adjacent sections */
  @supports (display: grid) {
    .resume-grid:has(.section-left:nth-child(1)) {
      .section-left:first-child,
      .section-right:first-child {
        align-self: start;
      }
    }
  }
`;

// Handlebars helper for smart layout
handlebars.registerHelper('smartLayout', function(sections, column, options) {
  if (!sections || !Array.isArray(sections)) return '';
  
  let html = '';
  for (const section of sections) {
    // Render appropriate section based on type
    const sectionHtml = renderSection(section.name, section.data, options);
    html += `<div class="section section-${column}">${sectionHtml}</div>`;
  }
  return new handlebars.SafeString(html);
});

// Helper to render individual sections
function renderSection(name, data, options) {
  const templates = {
    education: (items) => `
      <div class="title">Education</div>
      ${items.map(edu => `
        <div class="edu">
          <div style="display: flex; justify-content: space-between;">
            <span class="edu-degree">${edu.degree}</span>
            <span class="edu-dates">${edu.graduation}</span>
          </div>
          <div class="edu-inst">${edu.institution}</div>
          ${edu.gpa ? `<div style="font-size: 8.5pt; color: #666;">GPA: ${edu.gpa}</div>` : ''}
        </div>
      `).join('')}
    `,
    
    publications: (items) => `
      <div class="title">Publications</div>
      ${items.map(pub => `
        <div class="pub">
          <div class="pub-title">${pub.title}</div>
          <div class="pub-venue">
            ${pub.url || pub.doi ? 
              `<a href="${pub.url || 'https://doi.org/' + pub.doi}">${pub.journal} (${pub.year})</a>` :
              `${pub.journal} (${pub.year})`
            }
          </div>
        </div>
      `).join('')}
    `,
    
    // Add other section templates...
  };
  
  const template = templates[name];
  return template ? template(data) : '';
}

// Enhanced PDF generation with smart layout
async function generateSmartPDF(options) {
  // Use enhanced preprocessing with layout optimization
  const processedData = preprocessWithLayout(options.data);
  
  // Inject alignment styles
  const templateSrc = await fs.readFile(options.templatePath, 'utf-8');
  const enhancedTemplate = templateSrc.replace(
    '</style>',
    alignmentStyles + '</style>'
  );
  
  // Save enhanced template temporarily
  const tempTemplatePath = options.templatePath.replace('.html', '-enhanced.html');
  await fs.writeFile(tempTemplatePath, enhancedTemplate);
  
  try {
    return await generatePDF({
      ...options,
      data: processedData,
      templatePath: tempTemplatePath
    });
  } finally {
    // Clean up temp file
    await fs.unlink(tempTemplatePath).catch(() => {});
  }
}

// Helper: Convert traditional skills list to contextual expertise
function convertCoreSkillsToExpertise(coreSkills) {
  const expertise = {};
  for (const [category, skills] of Object.entries(coreSkills)) {
    expertise[category] = {
      skills: Array.isArray(skills) ? skills.join(', ') : skills,
      context: null // Would need manual addition or AI enhancement
    };
  }
  return expertise;
}

// Helper: Extract most important skills for badges
function extractTopSkills(techArray, limit) {
  if (!techArray) return [];
  
  // Priority skills that should appear if present
  // CUSTOMIZE THIS LIST based on your domain/industry
  const prioritySkills = [
    'Python', 'Machine Learning', 'Team Leadership',
    'React', 'TypeScript', 'MLOps', 'Production Systems',
    'MATLAB', 'Computer Vision', 'LLMs', 'RAG Systems',
    'Cross-functional', 'System Architecture', 'AI/ML'
  ];
  
  const matches = techArray.filter(t =>
    prioritySkills.some(p =>
      t.toLowerCase().includes(p.toLowerCase())
    )
  );
  
  return matches.slice(0, limit);
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
function preprocessEnhanced(input) {
  const d = { ...input };

  // Convert old core_skills to new technical_expertise if needed
  if (d.core_skills && !d.technical_expertise) {
    d.technical_expertise = convertCoreSkillsToExpertise(d.core_skills);
  }
  
  // Keep existing core_skills processing for backward compatibility
  const mergedCore = mergeMapOfArrays(d.core_skills, d.core_competencies);
  d.core_skills_all = Object.keys(mergedCore).length ? mergedCore : undefined;

  // Auto-generate demonstrated_skills for experiences if not present
  d.experience = d.experience?.map(exp => ({
    ...exp,
    demonstrated_skills: exp.demonstrated_skills ||
      extractTopSkills(exp.technologies, 4)
  }));
  
  // Process projects (both "projects" and "selected_projects")
  const proj = Array.isArray(d.projects) ? d.projects : [];
  const sel = Array.isArray(d.selected_projects) ? d.selected_projects : [];
  const combined = [...proj, ...sel].map(p => {
    const title = p.title || p.name || '';
    const { sections, hasImpactSection } = buildProjectSections(p);
    return {
      ...p,
      title,
      sections,
      hasImpactSection,
      // Add demonstrated_skills to projects
      demonstrated_skills: p.demonstrated_skills ||
        extractTopSkills(p.technologies || p.tech_stack, 3)
    };
  });
  d.projects_all = combined.length ? combined : undefined;
  d.projects_title = d.selected_projects && d.selected_projects.length ? 
    'Selected Projects' : 'Projects';
  
  // Process work_samples if present
  if (d.work_samples && Array.isArray(d.work_samples)) {
    d.work_samples = d.work_samples.map(sample => ({
      ...sample,
      // Ensure URL is properly formatted
      display_url: sample.url ? 
        sample.url.replace(/^https?:\/\//, '').replace(/\/$/, '') : ''
    }));
  }

  // Publications: sort desc by year if present
  if (Array.isArray(d.publications)) {
    d.publications = [...d.publications].sort((a, b) => (b.year || 0) - (a.year || 0));
  }

  return d;
}

// Keep the old preprocess function name for backward compatibility
// but use the enhanced version
const preprocess = preprocessEnhanced;

/* ============================================
   SECTION 5: PDF GENERATION (keep existing)
   ============================================ */

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
  
  // USE THE ENHANCED PREPROCESSING HERE
  const html = template(preprocessEnhanced(data));

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

/* ---------------- NEW: Open PDF in System Viewer ---------------- */
/**
 * Opens a file using the system's default application.
 * @param {string} filePath The absolute path to the file to open.
 */
function openFile(filePath) {
  let command;
  switch (process.platform) {
    case 'darwin': // macOS
      command = `open "${filePath}"`;
      break;
    case 'win32': // Windows
      command = `start "" "${filePath}"`;
      break;
    default: // Linux
      command = `xdg-open "${filePath}"`;
      break;
  }

  exec(command, (error) => {
    if (error) {
      console.error(`\nâš ï¸  Could not open the PDF automatically: ${error.message}`);
    }
  });
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
      console.error(`âŒ Error: The base directory does not exist: "${baseDir}"`);
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
    console.error(`âŒ Could not find a ${fileType} file in "${dir}"`);
    return null;
  }
  return path.join(dir, match);
}

/* ---------------- REVISED: CLI ---------------- */
(async function main() {
  try {
    console.log('ðŸ” Finding latest job application folder...');
    const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);

    if (!targetDir) {
      throw new Error("No application folders found to process.");
    }
    console.log(`ðŸ“‚ Using folder: "${path.basename(targetDir)}"`);

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

    console.log(`\nâœ… PDF successfully generated: ${pdfPath}`);
    openFile(pdfPath);
  } catch (err) {
    console.error(`\nâŒ Failed to generate resume: ${err.message}`);
    process.exit(1);
  }
})();
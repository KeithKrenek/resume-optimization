// ============================================================================
// ENHANCED RESUME PDF GENERATOR - Schema-Compatible v7.0
// ============================================================================
// Compatible with multi-agent pipeline JSON output
// Flexible section ordering via configuration
// Unicode character support
// ============================================================================

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

// ============================================================================
// CONFIGURATION
// ============================================================================

// Default configuration - can be overridden by resume_config.json in job folder
const DEFAULT_CONFIG = {
  section_order: [
    'professional_summary',
    'technical_expertise',
    'experience',
    'projects',
    'education',
    'publications',
    'work_samples'
  ],
  section_visibility: {
    professional_summary: true,
    technical_expertise: true,
    experience: true,
    projects: true,
    education: true,
    publications: true,
    work_samples: false
  },
  skills_columns: 2,  // Number of columns for skills grid
  max_pages: 2
};

// ============================================================================
// SCHEMA MAPPING
// ============================================================================

/**
 * Map new schema field names to expected names for HTML generation
 */
function normalizeResumeData(data) {
  const normalized = { ...data };
  
  // Map technical_expertise to technical_skills format if needed
  if (data.technical_expertise && !data.technical_skills) {
    normalized.technical_skills = {};
    for (const [key, value] of Object.entries(data.technical_expertise)) {
      normalized.technical_skills[key] = {
        skills: value.skills || [],
        years: value.years || '',
        proficiency: value.proficiency || '',
        context: value.context || ''
      };
    }
  }
  
  // Ensure professional_summary is a string
  if (typeof data.professional_summary === 'object' && data.professional_summary.text) {
    normalized.professional_summary = data.professional_summary.text;
  }
  
  // Normalize experience achievements format
  if (data.experience) {
    normalized.experience = data.experience.map(exp => {
      const normalizedExp = { ...exp };
      
      // Extract text from achievement objects if needed
      if (exp.achievements) {
        normalizedExp.achievements = exp.achievements.map(ach => {
          if (typeof ach === 'object' && ach.text) {
            return ach.text;
          }
          return ach;
        });
      }
      
      return normalizedExp;
    });
  }
  
  // Map bulleted_projects to projects if needed
  if (data.bulleted_projects && !data.projects) {
    normalized.projects = data.bulleted_projects;
  }
  
  return normalized;
}

// ============================================================================
// ENHANCED PROFESSIONAL STYLING
// ============================================================================

const STYLES = `
  * { 
    box-sizing: border-box; 
    margin: 0; 
    padding: 0; 
  }
  
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif;
    color: #1a1a1a;
    background: #ffffff;
    line-height: 1.45;
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.3in 0.3in;
    font-size: 9.5pt;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    letter-spacing: -0.011em;
  }

  /* ========== COLOR SYSTEM ========== */
  :root {
    --primary: #0f172a;
    --primary-light: #334155;
    --accent: #0ea5e9;
    --accent-dark: #0284c7;
    --title-color: #b45309;
    --accent-light: #e0f2fe;
    --accent-subtle: #f0f9ff;
    --success: #10b981;
    --success-light: #d1fae5;
    --warning: #f59e0b;
    --warning-light: #fef3c7;
    --surface: #f8fafc;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --text-muted: #64748b;
  }

  /* ========== HEADER ========== */
  .header {
    position: relative;
    margin-bottom: 16px;
    padding-bottom: 12px;
  }
  
  .header::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent) 30%, transparent 100%);
  }
  
  .header-main {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }
  
  .name {
    font-size: 24pt;
    font-weight: 800;
    letter-spacing: -1px;
    color: var(--primary);
    line-height: 1;
  }
  
  .tagline {
    font-size: 11pt;
    color: var(--accent-dark);
    font-weight: 600;
    letter-spacing: -0.02em;
    margin-left: 16px;
  }
  
  .contact {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    font-size: 8.5pt;
    color: var(--text-muted);
    font-weight: 500;
    gap: 2px 10px;
  }
  
  .contact a {
    color: var(--primary);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all 0.2s ease;
  }
  
  .contact a:hover {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }
  
  .contact > span:not(:last-child)::after {
    content: "   •   ";
    color: var(--border-strong);
    margin-left: 10px;
    font-weight: 200;
    opacity: 0.5;
  }

  .summary {
    margin-bottom: 18px; 
  }

  /* ========== SECTION HEADERS ========== */
  .section {
    margin-bottom: 18px;
    break-inside: avoid;
  }
  
  .section-title {
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--title-color);
    padding-bottom: 4px;
    margin-bottom: 4px;
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-strong) 0%, transparent 100%);
  }

  /* ========== SKILLS SECTION ========== */
  .skills-grid {
    display: grid;
    row-gap: 4px;
    column-gap: 18px;
    margin-bottom: -4px;
  }
  
  .skills-grid.cols-1 { grid-template-columns: 1fr; }
  .skills-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
  .skills-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
  
  .skill-category {
    padding: 10px 12px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 4px;
    position: relative;
    overflow: hidden;
  }
  
  .skill-category::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: var(--accent);
  }
  
  .skill-category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  
  .skill-category-title {
    font-weight: 700;
    font-size: 9pt;
    color: var(--primary);
    flex: 1;
  }
  
  .skill-years {
    font-size: 7pt;
    color: var(--accent-dark);
    font-weight: 600;
    background: var(--accent-light);
    padding: 2px 6px;
    border-radius: 8px;
    white-space: nowrap;
    margin-left: 8px;
  }
  
  .skill-context {
    font-size: 7.5pt;
    color: var(--primary-light);
    line-height: 1.4;
    margin-bottom: 6px;
    font-style: italic;
  }
  
  .skill-items {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .skill-tag {
    font-size: 7.5pt;
    color: var(--primary);
    padding: 2px 7px;
    background: var(--surface);
    border-radius: 3px;
    font-weight: 500;
    border: 1px solid var(--border);
  }

  /* ========== EXPERIENCE ========== */
  .experience-item {
    margin-bottom: 18px;
    position: relative;
    padding-left: 16px;
  }
  
  .experience-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 7px;
    width: 7px;
    height: 7px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 0 2px white, 0 0 0 3px var(--accent-light);
  }
  
  .experience-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 2px;
  }
  
  .experience-title {
    font-weight: 700;
    font-size: 10pt;
    color: var(--primary);
  }
  
  .experience-company {
    font-weight: 600;
    font-size: 9.5pt;
    color: var(--accent-dark);
  }
  
  .experience-meta {
    font-size: 8pt;
    color: var(--text-muted);
    font-weight: 500;
  }
  
  .experience-achievements {
    margin-top: 6px;
    padding-left: 0;
    list-style: none;
  }
  
  .experience-achievements li {
    position: relative;
    padding-left: 16px;
    margin-bottom: 4px;
    line-height: 1.5;
    font-size: 9pt;
  }
  
  .experience-achievements li::before {
    content: '▸';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
  }

  /* ========== PROJECTS ========== */
  .project-card {
    margin-bottom: 16px;
    padding: 12px;
    background: var(--surface);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
  }
  
  .project-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
  }
  
  .project-title {
    font-weight: 700;
    font-size: 10pt;
    color: var(--primary);
  }
  
  .project-org {
    font-size: 8.5pt;
    color: var(--text-muted);
    font-style: italic;
  }
  
  .project-achievements {
    padding-left: 0;
    list-style: none;
  }
  
  .project-achievements li {
    position: relative;
    padding-left: 16px;
    margin-bottom: 4px;
    line-height: 1.5;
    font-size: 9pt;
  }
  
  .project-achievements li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
  }
  
  .project-tech {
    margin-top: 6px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .project-tech-tag {
    font-size: 7pt;
    padding: 2px 6px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--primary-light);
    font-weight: 600;
  }

  /* ========== EDUCATION ========== */
  .education-item {
    margin-bottom: 12px;
  }
  
  .education-degree {
    font-weight: 700;
    font-size: 9.5pt;
    color: var(--primary);
  }
  
  .education-institution {
    font-weight: 600;
    font-size: 9pt;
    color: var(--accent-dark);
  }
  
  .education-meta {
    font-size: 8pt;
    color: var(--text-muted);
  }

  /* ========== PUBLICATIONS ========== */
  .publication-item {
    margin-bottom: 10px;
    padding-left: 12px;
    border-left: 2px solid var(--accent-light);
  }
  
  .publication-title {
    font-weight: 600;
    font-size: 9pt;
    color: var(--primary);
  }
  
  .publication-meta {
    font-size: 8pt;
    color: var(--text-muted);
    font-style: italic;
  }

  /* ========== UTILITY CLASSES ========== */
  .text-muted {
    color: var(--text-muted);
  }
  
  .font-bold {
    font-weight: 700;
  }
  
  .allow-break {
    break-inside: auto;
  }

  /* ========== PRINT OPTIMIZATIONS ========== */
  @media print {
    body {
      padding: 0;
    }
    
    .section {
      break-inside: avoid;
    }
  }
`;

// ============================================================================
// TEXT FORMATTING
// ============================================================================

function processTextFormatting(text) {
  if (!text) return '';
  
  // Convert markdown-style formatting
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>');
  
  // Ensure proper Unicode characters (no escapes)
  formatted = formatted
    .replace(/\\u2013/g, '–')
    .replace(/\\u2014/g, '—')
    .replace(/\\u2019/g, "'")
    .replace(/\\u201c/g, '"')
    .replace(/\\u201d/g, '"')
    .replace(/\\u2022/g, '•')
    .replace(/\\u00d7/g, '×')
    .replace(/\\u221d/g, '∝')
    .replace(/\\u2192/g, '→')
    .replace(/\\u2264/g, '≤')
    .replace(/\\u2265/g, '≥');
  
  return formatted;
}

// ============================================================================
// HTML SECTION GENERATORS
// ============================================================================

function generateHeader(data) {
  const contact = data.contact || {};
  
  let contactParts = [];
  if (contact.email) contactParts.push(`<a href="mailto:${contact.email}">${contact.email}</a>`);
  if (contact.phone) contactParts.push(`<span>${contact.phone}</span>`);
  if (contact.location) contactParts.push(`<span>${contact.location}</span>`);
  if (contact.linkedin) contactParts.push(`<a href="${contact.linkedin}">LinkedIn</a>`);
  if (contact.github) contactParts.push(`<a href="${contact.github}">GitHub</a>`);
  
  const tagline = contact.tagline || '';
  
  return `
    <div class="header">
      <div class="header-main">
        <h1 class="name">${contact.name || 'Name'}</h1>
        ${tagline ? `<div class="tagline">${tagline}</div>` : ''}
      </div>
      <div class="contact">
        ${contactParts.map(part => `<span>${part}</span>`).join('\n        ')}
      </div>
    </div>
  `;
}

function generateSummary(data) {
  let summary = data.professional_summary || data.summary || '';
  
  // Handle different summary formats
  if (typeof summary === 'object') {
    summary = summary.text || '';
  }
  
  if (!summary) return '';
  
  const formatted = processTextFormatting(summary);
  
  return `
    <div class="section summary">
      <p>${formatted}</p>
    </div>
  `;
}

function generateTechnicalExpertise(data, config) {
  const skills = data.technical_skills || data.technical_expertise || {};
  
  if (Object.keys(skills).length === 0) return '';
  
  const columns = config.skills_columns || 2;
  
  let html = `
    <div class="section">
      <div class="section-title">Technical Expertise</div>
      <div class="skills-grid cols-${columns}">
  `;
  
  for (const [category, details] of Object.entries(skills)) {
    const skillsList = Array.isArray(details.skills) ? details.skills : 
                      (typeof details.skills === 'string' ? details.skills.split(',').map(s => s.trim()) : []);
    
    const years = details.years || '';
    const context = details.context || '';
    
    html += `
      <div class="skill-category">
        <div class="skill-category-header">
          <div class="skill-category-title">${category}</div>
          ${years ? `<div class="skill-years">${years}</div>` : ''}
        </div>
        ${context ? `<div class="skill-context">${processTextFormatting(context)}</div>` : ''}
        <div class="skill-items">
          ${skillsList.map(skill => `<span class="skill-tag">${skill}</span>`).join('\n          ')}
        </div>
      </div>
    `;
  }
  
  html += `
      </div>
    </div>
  `;
  
  return html;
}

function generateExperience(data) {
  const experiences = data.experience || [];
  
  if (experiences.length === 0) return '';
  
  let html = `
    <div class="section">
      <div class="section-title">Professional Experience</div>
  `;
  
  for (const exp of experiences) {
    const achievements = exp.achievements || [];
    const achievementsList = achievements.map(ach => {
      const text = typeof ach === 'string' ? ach : ach.text || ach;
      return `<li>${processTextFormatting(text)}</li>`;
    }).join('\n          ');
    
    html += `
      <div class="experience-item">
        <div class="experience-header">
          <div>
            <div class="experience-title">${exp.title || 'Position'}</div>
            <div class="experience-company">${exp.company || 'Company'}</div>
          </div>
          <div class="experience-meta">
            ${exp.dates || 'Dates'} • ${exp.location || 'Location'}
          </div>
        </div>
        <ul class="experience-achievements">
          ${achievementsList}
        </ul>
      </div>
    `;
  }
  
  html += `</div>`;
  return html;
}

function generateProjects(data) {
  const projects = data.projects || data.bulleted_projects || [];
  
  if (projects.length === 0) return '';
  
  let html = `
    <div class="section">
      <div class="section-title">Key Projects</div>
  `;
  
  for (const proj of projects) {
    // Handle different project formats
    const achievements = [];
    if (proj.achievement1) achievements.push(proj.achievement1);
    if (proj.achievement2) achievements.push(proj.achievement2);
    if (proj.achievement3) achievements.push(proj.achievement3);
    if (proj.achievement4) achievements.push(proj.achievement4);
    if (proj.achievements) achievements.push(...proj.achievements);
    
    const achievementsList = achievements.map(ach => 
      `<li>${processTextFormatting(ach)}</li>`
    ).join('\n          ');
    
    const technologies = proj.technologies || proj.tech_stack || [];
    const techTags = technologies.map(tech => 
      `<span class="project-tech-tag">${tech}</span>`
    ).join('\n          ');
    
    html += `
      <div class="project-card">
        <div class="project-header">
          <div class="project-title">${proj.title || 'Project'}</div>
          ${proj.org_context || proj.org ? `<div class="project-org">${proj.org_context || proj.org}</div>` : ''}
        </div>
        <ul class="project-achievements">
          ${achievementsList}
        </ul>
        ${technologies.length > 0 ? `
        <div class="project-tech">
          ${techTags}
        </div>
        ` : ''}
      </div>
    `;
  }
  
  html += `</div>`;
  return html;
}

function generateEducation(data) {
  const education = data.education || [];
  
  if (education.length === 0) return '';
  
  let html = `
    <div class="section">
      <div class="section-title">Education</div>
  `;
  
  for (const edu of education) {
    html += `
      <div class="education-item">
        <div class="education-degree">${edu.degree || 'Degree'}</div>
        <div class="education-institution">${edu.institution || 'Institution'}</div>
        <div class="education-meta">
          ${edu.graduation || edu.graduation_date || 'Year'}
          ${edu.location ? ` • ${edu.location}` : ''}
        </div>
      </div>
    `;
  }
  
  html += `</div>`;
  return html;
}

function generatePublications(data) {
  const publications = data.publications || [];
  
  if (publications.length === 0) return '';
  
  let html = `
    <div class="section">
      <div class="section-title">Publications</div>
  `;
  
  for (const pub of publications) {
    html += `
      <div class="publication-item">
        <div class="publication-title">${pub.title || 'Title'}</div>
        <div class="publication-meta">
          ${pub.journal || pub.venue || 'Venue'} • ${pub.year || 'Year'}
        </div>
      </div>
    `;
  }
  
  html += `</div>`;
  return html;
}

function generateWorkSamples(data) {
  const samples = data.work_samples || [];
  
  if (samples.length === 0) return '';
  
  let html = `
    <div class="section">
      <div class="section-title">Work Samples & Portfolio</div>
  `;
  
  for (const sample of samples) {
    html += `
      <div class="project-card">
        <div class="project-header">
          <div class="project-title">${sample.title || 'Sample'}</div>
          ${sample.type ? `<div class="project-org">${sample.type}</div>` : ''}
        </div>
        ${sample.description ? `<p style="margin: 6px 0; font-size: 9pt;">${processTextFormatting(sample.description)}</p>` : ''}
        ${sample.url ? `<p style="font-size: 8pt; color: var(--text-muted);"><a href="${sample.url}">${sample.url}</a></p>` : ''}
      </div>
    `;
  }
  
  html += `</div>`;
  return html;
}

// ============================================================================
// MAIN HTML GENERATION
// ============================================================================

function generateHTML(data, config = DEFAULT_CONFIG) {
  // Normalize the data to handle schema differences
  const normalizedData = normalizeResumeData(data);
  
  // Section generators map
  const sectionGenerators = {
    'professional_summary': () => generateSummary(normalizedData),
    'technical_expertise': () => generateTechnicalExpertise(normalizedData, config),
    'experience': () => generateExperience(normalizedData),
    'projects': () => generateProjects(normalizedData),
    'education': () => generateEducation(normalizedData),
    'publications': () => generatePublications(normalizedData),
    'work_samples': () => generateWorkSamples(normalizedData)
  };
  
  // Generate sections in configured order
  let sectionsHTML = '';
  for (const sectionName of config.section_order) {
    if (config.section_visibility[sectionName] !== false && sectionGenerators[sectionName]) {
      const sectionHTML = sectionGenerators[sectionName]();
      if (sectionHTML) {
        sectionsHTML += sectionHTML + '\n';
      }
    }
  }
  
  // Build complete HTML
  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resume - ${normalizedData.contact?.name || 'Candidate'}</title>
  <style>${STYLES}</style>
</head>
<body>
  ${generateHeader(normalizedData)}
  ${sectionsHTML}
</body>
</html>
  `;
}

// ============================================================================
// PDF GENERATION
// ============================================================================

async function generatePDF(html, outputPath) {
  const browser = await puppeteer.launch({ 
    headless: 'new', 
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ 
      width: 1200, 
      height: 1600, 
      deviceScaleFactor: 2 
    });
    
    await page.setContent(html, { 
      waitUntil: ['domcontentloaded', 'networkidle0'] 
    });
    
    await page.evaluateHandle('document.fonts && document.fonts.ready');
    
    const metrics = await page.evaluate(() => {
      const pageHeight = 11 * 96;
      const sections = Array.from(document.querySelectorAll('.section, .experience-item, .project-card'));
      const totalContentHeight = sections.reduce((sum, s) => sum + s.offsetHeight, 0);
      const bottomMost = Math.max(...sections.map(s => s.getBoundingClientRect().bottom));
      const totalPages = Math.ceil(bottomMost / pageHeight);
      const totalAvailableHeight = totalPages * pageHeight * 0.85;
      const whitespacePercent = ((totalAvailableHeight - totalContentHeight) / totalAvailableHeight * 100).toFixed(1);
      
      return { 
        totalPages, 
        whitespacePercent: parseFloat(whitespacePercent) 
      };
    });
    
    await page.pdf({
      path: outputPath,
      format: 'Letter',
      printBackground: true,
      margin: { 
        top: '0.45in', 
        right: '0.5in', 
        bottom: '0.45in', 
        left: '0.5in' 
      }
    });
    
    return metrics;
  } finally {
    await browser.close();
  }
}

// ============================================================================
// FILE UTILITIES
// ============================================================================

async function loadConfig(jobFolder) {
  try {
    const configPath = path.join(jobFolder, 'resume_config.json');
    const configData = await fs.readFile(configPath, 'utf-8');
    const userConfig = JSON.parse(configData);
    
    // Merge with defaults
    return {
      ...DEFAULT_CONFIG,
      ...userConfig,
      section_visibility: {
        ...DEFAULT_CONFIG.section_visibility,
        ...(userConfig.section_visibility || {})
      }
    };
  } catch (error) {
    // Config file not found or invalid, use defaults
    return DEFAULT_CONFIG;
  }
}

async function findLatestJobFolder(baseDir) {
  try {
    const entries = await fs.readdir(baseDir, { withFileTypes: true });
    const subdirs = entries
      .filter(e => e.isDirectory())
      .map(e => path.join(baseDir, e.name));
    
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
    console.error(`Error: ${error.message}`);
    return null;
  }
}

async function findResumeFile(dir) {
  const patterns = [
    /^resume_final\.json$/,
    /^resume_validated\.json$/,
    /^resume.*\.json$/
  ];
  
  const files = await fs.readdir(dir);
  
  for (const pattern of patterns) {
    const match = files.find(file => pattern.test(file));
    if (match) {
      return path.join(dir, match);
    }
  }
  
  console.error(`Could not find resume JSON file in "${dir}"`);
  return null;
}

function openFile(filePath) {
  const command = process.platform === 'win32' ? 'start ""' :
                  process.platform === 'darwin' ? 'open' : 'xdg-open';
  exec(`${command} "${filePath}"`);
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  console.log('Enhanced Resume PDF Generator v7.0 - Schema-Compatible\n');
  
  // Get job folder from argument or find latest
  let targetDir;
  if (process.argv[2]) {
    targetDir = process.argv[2];
    console.log(`Using specified folder: ${path.basename(targetDir)}`);
  } else {
    const baseDir = process.env.APPLICATIONS_FOLDER || "C:/Users/keith/Dropbox/Resume";
    targetDir = await findLatestJobFolder(baseDir);
    if (!targetDir) {
      console.error('No application folders found');
      return;
    }
    console.log(`Using latest folder: ${path.basename(targetDir)}`);
  }
  
  // Load configuration
  const config = await loadConfig(targetDir);
  console.log(`Loaded configuration (${config.skills_columns} skill columns)`);
  
  // Find resume JSON file
  const dataPath = await findResumeFile(targetDir);
  if (!dataPath) return;
  
  console.log(`Reading: ${path.basename(dataPath)}`);
  
  // Read and parse JSON
  const fileContent = await fs.readFile(dataPath, 'utf-8');
  const data = JSON.parse(fileContent);
  
  console.log('Generating HTML...');
  const html = generateHTML(data, config);
  
  // Create output filename
  const today = new Date();
  const dateStamp = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
  
  let taglineForFilename = 'Resume';
  if (data.contact && data.contact.tagline) {
    const firstTagline = Array.isArray(data.contact.tagline) 
      ? data.contact.tagline[0] 
      : String(data.contact.tagline);
    taglineForFilename = firstTagline
      .split('|')[0]
      .trim()
      .replace(/\s+/g, '')
      .replace(/\//g, '');
  }
  
  const lastName = data.contact?.name?.split(' ').pop() || 'Resume';
  const outputPath = path.join(targetDir, `${dateStamp}_${taglineForFilename}_${lastName}.pdf`);
  
  console.log('Generating PDF...');
  const metrics = await generatePDF(html, outputPath);
  
  console.log(`\n✓ Generated: ${path.basename(outputPath)}`);
  console.log(`  Pages: ${metrics.totalPages}`);
  console.log(`  Whitespace: ${metrics.whitespacePercent}%`);
  console.log(`  Design: Schema-Compatible v7.0`);
  
  openFile(outputPath);
}

main().catch(err => {
  console.error(`\nError: ${err.message}`);
  process.exit(1);
});

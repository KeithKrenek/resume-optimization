// Interactive Layout Generator with Approval Workflow
// Generates layouts one at a time, you approve/reject each
// Usage: node generate-interactive-layouts.js

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');
const { exec } = require('child_process');

const BASE_APPLICATIONS_DIR = "C:/Users/keith/Dropbox/Resume";

// EXPANDED LAYOUT CONFIGURATIONS
// Each layout can now specify:
// - width: 'full' or 'half'
// - columns: number of columns within the section
// - order: explicit ordering of all sections
const LAYOUT_CONFIGS = [
  {
    name: 'compact-header',
    description: 'Technical Expertise half-width with 2 columns, Education next to it',
    sections: [
      { type: 'header', width: 'full' },
      { type: 'summary', width: 'full' },
      { 
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'technical_expertise', columns: 2 }],
          [{ type: 'education' }]
        ]
      },
      { type: 'experience', width: 'full' },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', count: 2 }],
          [{ type: 'work_samples' }, { type: 'publications' }]
        ]
      },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', startFrom: 2 }],
          [{ type: 'leadership' }]
        ]
      }
    ]
  },
  
  {
    name: 'education-prominent',
    description: 'Education first after summary, full-width work samples',
    sections: [
      { type: 'header', width: 'full' },
      { type: 'summary', width: 'full' },
      { type: 'education', width: 'half' },
      { type: 'technical_expertise', width: 'half', columns: 2 },
      { type: 'experience', width: 'full' },
      { type: 'work_samples', width: 'full' },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects' }],
          [{ type: 'publications' }, { type: 'leadership' }]
        ]
      }
    ]
  },
  
  {
    name: 'three-column-projects',
    description: 'Projects in 3 columns on one page, rest balanced',
    sections: [
      { type: 'header', width: 'full' },
      { type: 'summary', width: 'full' },
      { type: 'technical_expertise', width: 'full', columns: 4 },
      { type: 'experience', width: 'full' },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', count: 1 }],
          [{ type: 'projects', startFrom: 1, count: 1 }],
          [{ type: 'projects', startFrom: 2, count: 1 }]
        ]
      },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'work_samples' }, { type: 'education' }],
          [{ type: 'publications' }, { type: 'leadership' }]
        ]
      }
    ]
  },
  
  {
    name: 'balanced-split',
    description: 'Standard two-column with projects split across pages',
    sections: [
      { type: 'header', width: 'full' },
      { type: 'summary', width: 'full' },
      { type: 'technical_expertise', width: 'full', columns: 3 },
      { type: 'experience', width: 'full' },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', count: 2 }],
          [{ type: 'work_samples' }, { type: 'publications' }]
        ]
      },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', startFrom: 2 }, { type: 'leadership' }],
          [{ type: 'education' }]
        ]
      }
    ]
  },
  
  {
    name: 'skills-showcase',
    description: 'Full-width Technical Expertise with 4 columns, compact below',
    sections: [
      { type: 'header', width: 'full' },
      { type: 'summary', width: 'full' },
      { type: 'technical_expertise', width: 'full', columns: 4 },
      { type: 'experience', width: 'full' },
      {
        type: 'grid',
        width: 'full',
        columns: [
          [{ type: 'projects', count: 2 }, { type: 'publications' }],
          [{ type: 'work_samples' }, { type: 'education' }, { type: 'leadership' }]
        ]
      },
      { type: 'projects', startFrom: 2, width: 'full' }
    ]
  }
];

// Handlebars helpers
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
  if (s.startsWith('http://') || s.startsWith('https://') || 
      s.startsWith('mailto:') || s.startsWith('tel:')) return s;
  return 'https://' + s;
});

handlebars.registerHelper('doiUrl', function (doi) {
  if (!doi) return '';
  const clean = String(doi).replace(/^https?:\/\/doi\.org\//i, '').trim();
  return 'https://doi.org/' + clean;
});

handlebars.registerHelper('displayUrl', function(url) {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '');
});

// Generate HTML from layout config
function generateHTML(data, layoutConfig) {
  let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${data.contact.name} Resume</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1a1a1a; 
      background: #fff; 
      line-height: 1.4;
      max-width: 8.5in; 
      margin: 0 auto; 
      padding: 0.35in;
      font-size: 10pt;
    }
    .header { border-bottom: 2px solid #0d3775; padding-bottom: 8px; margin-bottom: 12px; }
    .name { font-size: 20pt; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 2px; }
    .tagline { font-size: 10.5pt; color: #0d3775; font-weight: 600; margin-bottom: 3px; }
    .contact { display: flex; flex-wrap: wrap; align-items: center; font-size: 9pt; color: #444; gap: 0 12px; }
    .contact a { color: #0d3775; text-decoration: none; }
    .contact span { white-space: nowrap; }
    .contact span:not(:last-child)::after { content: "•"; color: #999; margin-left: 12px; }
    .summary { font-size: 9.5pt; color: #333; line-height: 1.45; margin-bottom: 10px; }
    
    .section { margin-bottom: 10px; break-inside: avoid; }
    .section-full { width: 100%; }
    .section-half { width: 48%; display: inline-block; vertical-align: top; }
    
    .grid { display: grid; gap: 12px 16px; margin-bottom: 10px; }
    .grid-2 { grid-template-columns: 1fr 1fr; }
    .grid-3 { grid-template-columns: 1fr 1fr 1fr; }
    .grid-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
    
    .title { font-size: 11pt; font-weight: 700; letter-spacing: 0.3px; text-transform: uppercase;
             color: #0d3775; border-bottom: 1px solid #d0d5dd; padding-bottom: 2px; margin-bottom: 6px; }
    
    .expertise-grid { display: grid; gap: 8px; }
    .expertise-grid.cols-2 { grid-template-columns: 1fr 1fr; }
    .expertise-grid.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
    .expertise-grid.cols-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
    .expertise-area { padding: 6px 8px; background: #f8f9fb; border: 0.5px solid #e0e5eb;
                     border-left: 2px solid #0d3775; border-radius: 5px; }
    .expertise-title { font-weight: 700; font-size: 8.5pt; color: #0d3775; margin-bottom: 2px; }
    .expertise-items { font-size: 8.5pt; color: #333; line-height: 1.3; }
    .expertise-context { font-size: 7.5pt; color: #666; font-style: italic; margin-top: 1px; }
    
    .xp, .proj { margin-bottom: 8px; padding: 6px 8px; border: 0.5px solid #e0e5eb;
                border-left: 2px solid #0d3775; background: #fafbfc; border-radius: 5px; break-inside: avoid; }
    .xp-head, .proj-head { display: flex; justify-content: space-between; align-items: baseline;
                          flex-wrap: wrap; gap: 4px 10px; margin-bottom: 3px; }
    .xp-role, .proj-name { font-weight: 700; font-size: 9.5pt; color: #1a1a1a; }
    .xp-company { color: #0d3775; font-weight: 600; }
    .xp-dates { font-size: 8.5pt; color: #666; white-space: nowrap; margin-left: auto; }
    .bullets { margin: 3px 0 3px 16px; font-size: 9pt; line-height: 1.35; }
    .bullets li { margin-bottom: 2px; }
    .proj-sections { font-size: 9pt; line-height: 1.35; margin: 3px 0; }
    .proj-section { margin-bottom: 2px; }
    .proj-section-title { font-weight: 600; color: #0d3775; }
    
    .skill-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
    .skill-tag { padding: 1px 6px; border-radius: 10px; font-size: 7.5pt; background: #e8f0fe;
                color: #1967d2; white-space: nowrap; }
    .skill-tag-proven { background: #e6f4ea; color: #137333; }
    
    .samples-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
    .sample-card { padding: 6px; border: 0.5px solid #e0e5eb; border-radius: 5px;
                  background: #fafbfc; font-size: 8.5pt; break-inside: avoid; }
    .sample-type { font-size: 7pt; color: #666; text-transform: uppercase; letter-spacing: 0.3px; }
    .sample-title { font-weight: 700; font-size: 8.5pt; color: #0d3775; margin: 1px 0; }
    .sample-desc { font-size: 8pt; color: #444; line-height: 1.3; margin-bottom: 2px; }
    .sample-link a { color: #0d3775; font-size: 8pt; text-decoration: none; }
    
    .edu, .pub { margin-bottom: 6px; font-size: 9pt; break-inside: avoid; }
    .edu-degree, .pub-title { font-weight: 700; font-size: 9pt; }
    .edu-inst, .pub-venue { color: #0d3775; font-size: 8.5pt; }
    .edu-dates, .pub-year { color: #666; font-size: 8.5pt; }
    .pub a { color: #0d3775; text-decoration: none; font-size: 8pt; }
    
    .list { margin-left: 16px; font-size: 9pt; line-height: 1.3; }
    .list li { margin-bottom: 2px; }
    
    @media print {
      body { padding: 0.25in; }
      .section, .xp, .proj, .edu, .pub, .sample-card { page-break-inside: avoid; }
    }
  </style>
</head>
<body>`;

  for (const section of layoutConfig.sections) {
    html += renderSection(section, data);
  }

  html += `</body></html>`;
  return html;
}

function renderSection(section, data) {
  if (section.type === 'header') {
    return `<header class="header">
      <div class="name">${data.contact.name}</div>
      <div class="tagline">${Array.isArray(data.contact.tagline) ? data.contact.tagline.join(' | ') : data.contact.tagline}</div>
      <div class="contact">
        ${data.contact.email ? `<span><a href="mailto:${data.contact.email}">${data.contact.email}</a></span>` : ''}
        ${data.contact.phone ? `<span><a href="tel:${data.contact.phone}">${data.contact.phone}</a></span>` : ''}
        ${data.contact.location ? `<span>${data.contact.location}</span>` : ''}
        ${data.contact.linkedin ? `<span><a href="https://${data.contact.linkedin}">LinkedIn</a></span>` : ''}
        ${data.contact.github ? `<span><a href="https://${data.contact.github}">GitHub</a></span>` : ''}
        ${data.contact.portfolio ? `<span><a href="https://${data.contact.portfolio}">Portfolio</a></span>` : ''}
      </div>
    </header>`;
  }
  
  if (section.type === 'summary') {
    return `<div class="summary">${data.professional_summary}</div>`;
  }
  
  if (section.type === 'technical_expertise') {
    const cols = section.columns || 3;
    let html = `<section class="section section-${section.width || 'full'}">
      <div class="title">Technical Expertise</div>
      <div class="expertise-grid cols-${cols}">`;
    for (const [key, value] of Object.entries(data.technical_expertise)) {
      html += `<div class="expertise-area">
        <div class="expertise-title">${key}</div>
        <div class="expertise-items">${value.skills}</div>
        ${value.context ? `<div class="expertise-context">${value.context}</div>` : ''}
      </div>`;
    }
    html += `</div></section>`;
    return html;
  }
  
  if (section.type === 'experience') {
    let html = `<section class="section section-full">
      <div class="title">Professional Experience</div>`;
    for (const exp of data.experience) {
      html += `<div class="xp">
        <div class="xp-head">
          <div><span class="xp-role">${exp.title}</span> <span class="xp-company">@ ${exp.company}</span></div>
          <span class="xp-dates">${exp.dates}</span>
        </div>
        <ul class="bullets">
          ${exp.highlights.map(h => `<li>${h}</li>`).join('')}
        </ul>
        ${exp.demonstrated_skills ? `<div class="skill-tags">${exp.demonstrated_skills.map(s => `<span class="skill-tag skill-tag-proven">${s}</span>`).join('')}</div>` : ''}
      </div>`;
    }
    html += `</section>`;
    return html;
  }
  
  if (section.type === 'projects') {
    const projects = data.projects_all || [];
    const startFrom = section.startFrom || 0;
    const count = section.count || projects.length - startFrom;
    const subset = projects.slice(startFrom, startFrom + count);
    
    if (subset.length === 0) return '';
    
    let html = `<div class="section">
      <div class="title">${startFrom > 0 ? 'Projects (continued)' : 'Projects'}</div>`;
    for (const proj of subset) {
      html += `<div class="proj">
        <div class="proj-head"><div class="proj-name">${proj.title}</div></div>
        ${proj.description ? `<div style="font-size: 8.5pt; color: #555; margin-bottom: 2px;">${proj.description}</div>` : ''}
        ${proj.sections ? `<div class="proj-sections">${proj.sections.map(s => `<div class="proj-section"><span class="proj-section-title">${s.title}:</span> ${s.content}</div>`).join('')}</div>` : ''}
        ${proj.demonstrated_skills ? `<div class="skill-tags">${proj.demonstrated_skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>` : ''}
      </div>`;
    }
    html += `</div>`;
    return html;
  }
  
  if (section.type === 'education') {
    let html = `<div class="section">
      <div class="title">Education</div>`;
    for (const edu of data.education) {
      html += `<div class="edu">
        <div style="display: flex; justify-content: space-between;">
          <span class="edu-degree">${edu.degree}</span>
          <span class="edu-dates">${edu.graduation}</span>
        </div>
        <div class="edu-inst">${edu.institution}</div>
        ${edu.gpa ? `<div style="font-size: 8.5pt; color: #666;">GPA: ${edu.gpa}</div>` : ''}
      </div>`;
    }
    html += `</div>`;
    return html;
  }
  
  if (section.type === 'publications') {
    let html = `<div class="section">
      <div class="title">Publications</div>`;
    for (const pub of data.publications) {
      const link = pub.url || (pub.doi ? `https://doi.org/${pub.doi}` : null);
      html += `<div class="pub">
        <div class="pub-title">${pub.title}</div>
        <div class="pub-venue">${link ? `<a href="${link}">${pub.journal} (${pub.year})</a>` : `${pub.journal} (${pub.year})`}</div>
      </div>`;
    }
    html += `</div>`;
    return html;
  }
  
  if (section.type === 'work_samples') {
    let html = `<div class="section">
      <div class="title">Work Samples</div>
      <div class="samples-grid">`;
    for (const sample of data.work_samples) {
      html += `<div class="sample-card">
        <div class="sample-type">${sample.type}</div>
        <div class="sample-title">${sample.title}</div>
        <div class="sample-desc">${sample.description}</div>
        <div class="sample-link"><a href="${sample.url}">${sample.url.replace(/^https?:\/\//, '').replace(/\/$/, '')}</a></div>
      </div>`;
    }
    html += `</div></div>`;
    return html;
  }
  
  if (section.type === 'leadership') {
    let html = `<div class="section">
      <div class="title">Leadership</div>
      <ul class="list">`;
    for (const item of data.leadership_mentoring) {
      html += `<li>${item}</li>`;
    }
    html += `</ul></div>`;
    return html;
  }
  
  if (section.type === 'grid') {
    const numCols = section.columns.length;
    let html = `<div class="grid grid-${numCols}">`;
    for (const column of section.columns) {
      html += `<div>`;
      for (const subsection of column) {
        html += renderSection(subsection, data);
      }
      html += `</div>`;
    }
    html += `</div>`;
    return html;
  }
  
  return '';
}

// Generate PDF and measure
async function generatePDF(html, outputPath) {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: ['domcontentloaded', 'networkidle0'] });
    await page.evaluateHandle('document.fonts && document.fonts.ready');
    
    const metrics = await page.evaluate(() => {
      const pageHeight = 11 * 96;
      const sections = Array.from(document.querySelectorAll('.section, .xp, .proj'));
      const totalContentHeight = sections.reduce((sum, s) => sum + s.offsetHeight, 0);
      const totalPages = Math.ceil(
        Math.max(...sections.map(s => s.getBoundingClientRect().bottom)) / pageHeight
      );
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
      margin: { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' }
    });
    
    const previewPath = outputPath.replace('.pdf', '-preview.png');
    await page.screenshot({ path: previewPath, fullPage: true, deviceScaleFactor: 1 });
    
    return { metrics, previewPath };
  } finally {
    await browser.close();
  }
}

// Interactive CLI
function createInterface() {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

function prompt(rl, question) {
  return new Promise(resolve => rl.question(question, resolve));
}

// Main interactive loop
async function main() {
  console.log('Interactive Resume Layout Generator\n');
  
  const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);
  if (!targetDir) {
    console.error('No application folders found');
    return;
  }
  
  console.log(`Using: ${path.basename(targetDir)}\n`);
  
  const dataPath = await findFileByPattern(targetDir, /^resume.*\.json$/, 'JSON');
  if (!dataPath) return;
  
  const data = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
  
  // Preprocess data (add demonstrated_skills, etc.)
  if (data.experience) {
    data.experience = data.experience.map(exp => ({
      ...exp,
      demonstrated_skills: exp.demonstrated_skills || (exp.technologies ? exp.technologies.slice(0, 4) : [])
    }));
  }
  
  // Process projects
  const proj = Array.isArray(data.projects) ? data.projects : [];
  const sel = Array.isArray(data.selected_projects) ? data.selected_projects : [];
  data.projects_all = [...proj, ...sel].map(p => {
    const sections = [];
    if (p.challenge) sections.push({ title: 'Challenge', content: p.challenge });
    if (p.approach) sections.push({ title: 'Approach', content: p.approach });
    if (p.impact) sections.push({ title: 'Impact', content: p.impact });
    return { ...p, sections };
  });
  
  const companyName = path.basename(targetDir).split('_')[0];
  const rl = createInterface();
  const approved = [];
  
  console.log(`Will generate ${LAYOUT_CONFIGS.length} layout options.\n`);
  console.log('For each layout:');
  console.log('  - PDF and preview will be generated');
  console.log('  - You can view them');
  console.log('  - Type "keep" to save it, "skip" to discard\n');
  
  for (let i = 0; i < LAYOUT_CONFIGS.length; i++) {
    const config = LAYOUT_CONFIGS[i];
    console.log(`\n[${i + 1}/${LAYOUT_CONFIGS.length}] Generating: ${config.name}`);
    console.log(`    ${config.description}`);
    
    const html = generateHTML(data, config);
    const tempPath = path.join(targetDir, `temp_${config.name}.pdf`);
    
    const { metrics, previewPath } = await generatePDF(html, tempPath);
    console.log(`    Pages: ${metrics.totalPages} | Whitespace: ${metrics.whitespacePercent}%`);
    console.log(`    Preview: ${previewPath}`);
    
    // Open the PDF
    const command = process.platform === 'win32' ? 'start ""' :
                    process.platform === 'darwin' ? 'open' : 'xdg-open';
    exec(`${command} "${tempPath}"`);
    
    const answer = await prompt(rl, '\n    Keep this layout? (keep/skip/quit): ');
    
    if (answer.toLowerCase() === 'quit' || answer.toLowerCase() === 'q') {
      console.log('\nStopping...');
      break;
    }
    
    if (answer.toLowerCase() === 'keep' || answer.toLowerCase() === 'k') {
      const finalPath = path.join(targetDir, `${companyName}_Resume_${config.name}.pdf`);
      await fs.rename(tempPath, finalPath);
      approved.push({ name: config.name, path: finalPath, metrics });
      console.log(`    ✓ Saved as: ${path.basename(finalPath)}`);
    } else {
      await fs.unlink(tempPath).catch(() => {});
      await fs.unlink(previewPath).catch(() => {});
      console.log(`    ✗ Skipped`);
    }
  }
  
  rl.close();
  
  console.log(`\n✅ Done! Kept ${approved.length} layout(s):`);
  approved.forEach(a => console.log(`   - ${a.name}: ${a.metrics.whitespacePercent}% whitespace, ${a.metrics.totalPages} pages`));
}

async function findLatestJobFolder(baseDir) {
  try {
    const entries = await fs.readdir(baseDir, { withFileTypes: true });
    const subdirs = entries.filter(e => e.isDirectory()).map(e => path.join(baseDir, e.name));
    if (subdirs.length === 0) return null;
    const dirsWithStats = await Promise.all(subdirs.map(async (dir) => ({
      path: dir, mtime: (await fs.stat(dir)).mtime,
    })));
    dirsWithStats.sort((a, b) => b.mtime - a.mtime);
    return dirsWithStats[0].path;
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return null;
  }
}

async function findFileByPattern(dir, pattern, fileType) {
  const files = await fs.readdir(dir);
  const match = files.find(file => pattern.test(file));
  if (!match) {
    console.error(`Could not find ${fileType} in "${dir}"`);
    return null;
  }
  return path.join(dir, match);
}

main().catch(err => {
  console.error(`\nError: ${err.message}`);
  process.exit(1);
});
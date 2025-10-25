// ============================================================================
// PREMIUM RESUME GENERATOR - Enhanced Visual Design v6.0
// ============================================================================
// Improvements: Optimized header, cleaner skills section, better hierarchy
// Strategic emphasis, improved readability, maintained ATS compatibility
// ============================================================================

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

// ============================================================================
// CONFIGURATION
// ============================================================================

const BASE_APPLICATIONS_DIR = "C:/Users/keith/Dropbox/Resume";

// ============================================================================
// ENHANCED PROFESSIONAL STYLING - Cutting-Edge Design v6.0
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

  /* ========== ENHANCED COLOR SYSTEM ========== */
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
    --emphasis-subtle: #fef9e7;
    --emphasis-border: #f59e0b;
  }

  /* ========== OPTIMIZED COMPACT HEADER ========== */
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
    /* MODIFICATION 2: Make contact info full-width and evenly spaced */
    /* justify-content: space-between; */
    gap: 2px 10px; /* Use gap for spacing */
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
  
  /* MODIFICATION: Removed the separator dot as space-between handles spacing */
  /* .contact > span:not(:last-child)::after { ... } */
  /* Restores the dot separator */
  .contact > span:not(:last-child)::after {
    content: "   •   ";
    color: var(--border-strong);
    margin-left: 10px;
    font-weight: 200;
    opacity: 0.5;
  }


  /* MODIFICATION 1: Increase space after summary text */
  .summary {
    margin-bottom: 18px; 
  }

  /* ========== MODERN SECTION HEADERS ========== */
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

  /* ========== REDESIGNED CLEAN SKILLS SECTION ========== */
  .skills-grid {
    display: grid;
    row-gap: 4px;
    column-gap: 18px;
    margin-bottom: -4px;
  }
  
  .skills-grid.cols-1 { 
    grid-template-columns: 1fr; 
  }
  
  .skills-grid.cols-2 { 
    grid-template-columns: repeat(2, 1fr); 
  }
  
  .skills-grid.cols-3 { 
    grid-template-columns: repeat(3, 1fr); 
  }
  
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

  /* ========== ENHANCED EXPERIENCE WITH VISUAL TIMELINE ========== */
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
  
  .experience-item::after {
    content: '';
    position: absolute;
    left: 3px;
    top: 18px;
    bottom: -18px;
    width: 1.5px;
    background: linear-gradient(to bottom, var(--border-strong), transparent);
  }
  
  .experience-item:last-child::after {
    display: none;
  }
  
  .experience-header {
    margin-bottom: 10px;
  }
  
  .experience-title {
    font-weight: 700;
    font-size: 10.5pt;
    color: var(--primary);
    letter-spacing: -0.02em;
    line-height: 1.3;
  }
  
  .experience-subtitle {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-top: 2px;
    flex-wrap: wrap;
  }
  
  .experience-company {
    font-size: 9.5pt;
    color: var(--accent-dark);
    font-weight: 600;
  }
  
  .experience-dates {
    font-size: 8.5pt;
    color: var(--text-muted);
    font-weight: 500;
  }
  
  .achievement {
    margin-bottom: 8px;
    position: relative;
    padding-left: 14px;
  }
  
  .achievement::before {
    content: "▸";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
    font-size: 8pt;
    top: 1px;
  }
  
  .achievement-text {
    font-size: 9pt;
    line-height: 1.6;
    color: var(--primary);
  }
  
  /* ========== REFINED EMPHASIS SYSTEM ========== */
  
  /* Subtle emphasis for key terms - minimal highlighting */
  .achievement-text em,
  .achievement-text .em,
  .project-content em,
  .project-content .em,
  .leadership-list li em {
    font-style: normal;
    font-weight: 600;
    color: var(--primary);
    background: var(--emphasis-subtle);
    padding: 0px 3px;
    border-radius: 2px;
    border-bottom: 1px solid var(--emphasis-border);
  }
  
  /* Metrics - bold with subtle underline, no background */
  .achievement-text .metric,
  .project-content .metric,
  .leadership-list li .metric {
    font-style: normal;
    font-weight: 700;
    color: var(--primary);
    /* border-bottom: 2px solid var(--accent); */
    padding-bottom: 1px;
  }
  
  /* Strong emphasis - bold only, clean */
  .achievement-text strong,
  .achievement-text .strong,
  .project-content strong,
  .project-content .strong {
    font-weight: 700;
    color: var(--primary);
  }
  
  /* Impact - bold with subtle green accent */
  .achievement-text .impact,
  .project-content .impact {
    font-style: normal;
    font-weight: 700;
    color: var(--success);
  }

  /* ========== ENHANCED PROJECT CARDS ========== */
  .projects-grid {
    display: grid;
    row-gap: 4px;
    column-gap: 18px;
  }
  
  .projects-grid.cols-1 { 
    grid-template-columns: 1fr; 
  }
  
  .projects-grid.cols-2 { 
    grid-template-columns: repeat(2, 1fr); 
  }
  
  .project-card {
    padding: 14px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
    position: relative;
    break-inside: avoid;
  }
  
  .project-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(to bottom, var(--accent), var(--accent-dark));
    border-radius: 6px 0 0 6px;
  }
  
  .project-header {
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  
  .project-title {
    font-weight: 700;
    font-size: 9.5pt;
    color: var(--primary);
    margin-bottom: 4px;
  }
  
  .project-meta {
    display: flex;
    gap: 10px;
    font-size: 7.5pt;
    color: var(--text-muted);
    font-weight: 500;
  }
  
  .project-content {
    font-size: 8.5pt;
    line-height: 1.55;
    color: var(--primary);
  }
  
  .project-section {
    margin-bottom: 7px;
  }
  
  .project-label {
    font-weight: 600;
    color: var(--accent-dark);
    display: inline-block;
    margin-right: 4px;
    font-size: 8pt;
  }
  
  .tech-stack {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    /* MODIFICATION 3: Center-align technology pills */
    justify-content: center;
  }
  
  .tech-pill {
    font-size: 7pt;
    padding: 2px 7px;
    background: var(--surface);
    color: var(--primary-light);
    border-radius: 10px;
    font-weight: 500;
    border: 1px solid var(--border);
  }

  /* ========== ROW/COLUMN LAYOUT SYSTEM ========== */
  .row {
    display: grid;
    row-gap: 4px;
    column-gap: 18px;
    margin-bottom: -8px;
    align-items: start;
  }
  
  .row.cols-2 {
    grid-template-columns: 1fr 1fr;
  }
  
  .row.cols-3 {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .column-group {
    display: flex;
    flex-direction: column;
    /* gap: 14px; */
  }

  .column-group > .section:not(:last-child) {
    margin-bottom: 8px; /* Reduces space between stacked sections */
  }

  /* ========== PORTFOLIO SHOWCASE ========== */
  .portfolio-grid {
    display: grid;
    row-gap: 4px;
    column-gap: 18px;
  }
  
  .portfolio-grid.cols-1 { 
    grid-template-columns: 1fr; 
  }
  
  .portfolio-grid.cols-2 { 
    grid-template-columns: repeat(2, 1fr); 
  }
  
  .portfolio-item {
    padding: 12px;
    border-radius: 5px;
    background: var(--surface);
    border: 1px solid var(--border);
    position: relative;
  }
  
  .portfolio-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, transparent 100%);
    border-radius: 5px 5px 0 0;
  }
  
  .portfolio-type {
    font-size: 6.5pt;
    color: var(--accent-dark);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 700;
    margin-bottom: 5px;
  }
  
  .portfolio-title {
    font-weight: 600;
    font-size: 8.5pt;
    color: var(--primary);
    margin-bottom: 4px;
  }
  
  .portfolio-desc {
    font-size: 7.5pt;
    color: var(--primary-light);
    line-height: 1.5;
    margin-bottom: 6px;
  }
  
  .portfolio-link {
    font-size: 7pt;
  }
  
  .portfolio-link a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }

  /* ========== COMPACT EDUCATION & PUBLICATIONS ========== */
  /* MODIFICATION 4: Update education section styling */
  .education-item {
    margin-bottom: 10px;
    line-height: 1.4;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }
  
  .publication-item {
    margin-bottom: 8px;
    padding-left: 12px;
    position: relative;
    line-height: 1.4;
  }
  
  .publication-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 6px;
    width: 3px;
    height: 3px;
    background: var(--accent);
    border-radius: 50%;
  }
  
  .education-degree,
  .publication-title {
    font-weight: 600;
    font-size: 9pt;
    color: var(--primary);
  }
  
  .education-main {
    display: flex;
    flex-direction: column;
  }
  
  .education-date {
    font-size: 8.5pt;
    color: var(--text-muted);
    font-weight: 500;
    white-space: nowrap;
    margin-top: 1px;
  }
  
  .education-institution,
  .publication-venue {
    color: var(--accent-dark);
    font-size: 8.5pt;
  }
  
  .education-details,
  .publication-meta {
    font-size: 7.5pt;
    color: var(--text-muted);
    margin-top: 2px;
  }

  /* ========== LEADERSHIP & ACHIEVEMENTS ========== */
  .leadership-list {
    list-style: none;
    padding: 0;
  }
  
  .leadership-list li {
    margin-bottom: 8px;
    position: relative;
    padding-left: 14px;
    font-size: 9pt;
    line-height: 1.55;
    color: var(--primary);
  }
  
  .leadership-list li::before {
    content: "▸";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
    font-size: 8pt;
    top: 1px;
  }

  /* ========== PRINT OPTIMIZATION ========== */
  @media print {
    body {
      padding: 0.3in 0.4in;
      font-size: 9pt;
    }
    
    .section,
    .experience-item,
    .project-card {
      page-break-inside: avoid;
    }

    .section.allow-break {
      page-break-inside: auto;
    }
    
    .header::after,
    .section-title::after {
      background: var(--border-strong) !important;
    }
    
    a {
      color: var(--primary) !important;
      border-bottom: none !important;
    }
    
    em, .em, .metric, .impact, strong {
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
  }
`;

// ============================================================================
// ENHANCED TEXT FORMATTING FUNCTIONS
// ============================================================================

/**
 * Process text with refined emphasis markers
 * Supports: {text} for metrics, **text** for strong, {{text}} for impact
 */
function processTextFormatting(text) {
  if (!text) return '';
  
  let processed = text;
  
  // Convert {{text}} to <span class="impact">text</span> (green impact emphasis)
  processed = processed.replace(/\{\{([^}]+)\}\}/g, '<span class="impact">$1</span>');
  
  // Convert {text} to <span class="metric">text</span> (underlined metric)
  processed = processed.replace(/\{([^}]+)\}/g, '<span class="metric">$1</span>');
  
  // Convert **text** to <strong>text</strong>
  processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  return processed;
}

// ============================================================================
// HTML GENERATION FUNCTIONS
// ============================================================================

function generateHTML(data) {
  let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${data.contact.name} Resume</title>
  <style>${STYLES}</style>
</head>
<body>`;

  const layout = data.layout || getDefaultLayout();
  
  for (const section of layout.sections) {
    html += renderSection(section, data, layout.options || {});
  }

  html += `</body></html>`;
  return html;
}

function getDefaultLayout() {
  return {
    sections: [
      { section: 'header' },
      { section: 'summary' },
      { section: 'technical_skills' },
      { section: 'experience' },
      { section: 'projects' },
      { section: 'education' },
      { section: 'publications' },
      { section: 'portfolio' },
      { section: 'leadership' }
    ],
    options: {}
  };
}

function renderSection(config, data, options) {
  const type = config.section;
  
  if (config.enabled === false) return '';
  
  if (type === 'row') {
    return renderRow(config, data, options);
  }
  
  switch (type) {
    case 'header':
      return renderHeader(data);
    case 'summary':
      return renderSummary(data);
    case 'technical_skills':
      return renderTechnicalSkills(data, config);
    case 'experience':
      return renderExperience(data, config, options);
    case 'projects':
      return renderProjects(data, config);
    case 'portfolio':
      return renderPortfolio(data, config);
    case 'education':
      return renderEducation(data, config);
    case 'publications':
      return renderPublications(data, config);
    case 'leadership':
      return renderLeadership(data, config);
    default:
      return '';
  }
}

function renderRow(config, data, options) {
  const numCols = config.columns.length;
  let html = `<div class="row cols-${numCols}">`;
  
  for (const column of config.columns) {
    if (Array.isArray(column)) {
      html += `<div class="column-group">`;
      for (const subsection of column) {
        html += renderSection(subsection, data, options);
      }
      html += `</div>`;
    } else {
      html += renderSection(column, data, options);
    }
  }
  
  html += `</div>`;
  return html;
}

function renderHeader(data) {
  const contact = data.contact;
  const tagline = Array.isArray(contact.tagline) 
    ? contact.tagline.join(' | ') 
    : contact.tagline;
  
  return `<header class="header">
    <div class="header-main">
      <div>
        <span class="name">${contact.name}</span>
        <span class="tagline">${tagline}</span>
      </div>
    </div>
    <div class="contact">
      ${contact.email ? `<span><a href="mailto:${contact.email}">${contact.email}</a></span>` : ''}
      ${contact.phone ? `<span><a href="tel:${contact.phone}">${contact.phone}</a></span>` : ''}
      ${contact.location ? `<span>${contact.location}</span>` : ''}
      ${contact.linkedin ? `<span><a href="https://${contact.linkedin}">LinkedIn</a></span>` : ''}
      ${contact.github ? `<span><a href="https://${contact.github}">GitHub</a></span>` : ''}
      ${contact.scholar ? `<span><a href="https://${contact.scholar}">Scholar</a></span>` : ''}
      ${contact.portfolio ? `<span><a href="https://${contact.portfolio}">Portfolio</a></span>` : ''}
    </div>
  </header>`;
}

function renderSummary(data) {
  if (!data.summary || !data.summary.text) return '';
  if (data.summary.enabled === false) return '';
  
  const formatted = processTextFormatting(data.summary.text);
  return `<div class="summary">${formatted}</div>`;
}

function renderTechnicalSkills(data, config) {
  const skills = data.technical_skills || data.technical_expertise;
  if (!skills || Object.keys(skills).length === 0) return '';
  
  const cols = config.grid_columns || 2;
  const breakClass = config.keep_together === false ? 'allow-break' : '';
  
  let html = `<div class="section ${breakClass}">
    <div class="section-title">Technical Expertise</div>
    <div class="skills-grid cols-${cols}">`;
  
  for (const [category, details] of Object.entries(skills)) {
    const skillList = Array.isArray(details.skills) ? details.skills : details.skills.split(',').map(s => s.trim());
    
    html += `<div class="skill-category">
      <div class="skill-category-header">
        <span class="skill-category-title">${category}</span>
        ${details.years ? `<span class="skill-years">${details.years} years</span>` : ''}
      </div>`;
    
    if (details.context) {
      html += `<div class="skill-context">${details.context}</div>`;
    }
    
    html += `<div class="skill-items">`;
    
    for (const skill of skillList) {
      html += `<span class="skill-tag">${skill}</span>`;
    }
    
    html += `</div></div>`;
  }
  
  html += `</div></div>`;
  return html;
}

function renderExperience(data, config, options) {
  if (!data.experience || data.experience.length === 0) return '';
  const breakClass = config.allow_break === true ? 'allow-break' : '';
  let html = `<div class="section ${breakClass}">
    <div class="section-title">Professional Experience</div>`;
  
  for (const exp of data.experience) {
    html += `<div class="experience-item">
      <div class="experience-header">
        <div class="experience-title">${exp.title}</div>
        <div class="experience-subtitle">
          <span class="experience-company">${exp.company}</span>
          <span class="experience-dates">${exp.dates}</span>
        </div>
      </div>`;
    
    const achievements = exp.achievements || exp.highlights;
    if (achievements && achievements.length > 0) {
      for (const achievement of achievements) {
        const text = typeof achievement === 'string' ? achievement : achievement.text;
        const formatted = processTextFormatting(text);
        
        html += `<div class="achievement">
          <div class="achievement-text">${formatted}</div>
        </div>`;
      }
    }
    
    html += `</div>`;
  }
  
  html += `</div>`;
  return html;
}

function renderProjects(data, config) {
  if (!data.projects || data.projects.length === 0) return '';
  
  const projects = data.projects.slice(0, config.limit || data.projects.length);
  const cols = config.grid_columns || 1;
  const breakClass = config.keep_together === false ? 'allow-break' : '';

  let html = `<div class="section ${breakClass}">
    <div class="section-title">Key Projects</div>
    <div class="projects-grid cols-${cols}">`;
  
  for (const project of projects) {
    html += `<div class="project-card">
      <div class="project-header">
        <div class="project-title">${project.title}</div>
        <div class="project-meta">`;
    
    if (project.organization) {
      html += `<span>${project.organization}</span>`;
    }
    if (project.dates) {
      html += `<span>${project.dates}</span>`;
    }
    
    html += `</div></div><div class="project-content">`;
    
    if (project.format === 'impact') {
      if (project.challenge) {
        html += `<div class="project-section">
          <span class="project-label">Challenge:</span> ${processTextFormatting(project.challenge)}
        </div>`;
      }
      if (project.approach) {
        html += `<div class="project-section">
          <span class="project-label">Solution:</span> ${processTextFormatting(project.approach)}
        </div>`;
      }
      if (project.impact) {
        html += `<div class="project-section">
          <span class="project-label">Impact:</span> ${processTextFormatting(project.impact)}
        </div>`;
      }
    }
    
    html += `</div>`;
    
    if (project.technologies && project.technologies.length > 0) {
      html += `<div class="tech-stack">`;
      for (const tech of project.technologies) {
        html += `<span class="tech-pill">${tech}</span>`;
      }
      html += `</div>`;
    }
    
    html += `</div>`;
  }
  
  html += `</div></div>`;
  return html;
}

function renderPortfolio(data, config) {
  if (!data.portfolio || data.portfolio.length === 0) {
    if (!data.work_samples || data.work_samples.length === 0) return '';
    data.portfolio = data.work_samples;
  }
  
  const cols = config.grid_columns || 1;
  const breakClass = config.keep_together === false ? 'allow-break' : '';
  
  let html = `<div class="section ${breakClass}">
    <div class="section-title">Example Projects</div>
    <div class="portfolio-grid cols-${cols}">`;
  
  for (const item of data.portfolio) {
    html += `<div class="portfolio-item">
      <div class="portfolio-type">${item.type}</div>
      <div class="portfolio-title">${item.title}</div>
      <div class="portfolio-desc">${processTextFormatting(item.description)}</div>`;
    
    if (item.url) {
      const cleanUrl = item.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
      const fullUrl = item.url.startsWith('http') ? item.url : `https://${item.url}`;
      html += `<div class="portfolio-link"><a href="${fullUrl}">${cleanUrl}</a></div>`;
    }
    
    if (item.demo_url) {
      const cleanDemoUrl = item.demo_url.replace(/^https?:\/\//, '').replace(/\/$/, '');
      const fullDemoUrl = item.demo_url.startsWith('http') ? item.demo_url : `https://${item.demo_url}`;
      html += `<div class="portfolio-link"><a href="${fullDemoUrl}">${cleanDemoUrl}</a></div>`;
    }
    
    html += `</div>`;
  }
  
  html += `</div></div>`;
  return html;
}

// MODIFICATION 4: Update the renderEducation function for a better layout
function renderEducation(data, config) {
  if (!data.education || data.education.length === 0) return '';

  const breakClass = config.keep_together === false ? 'allow-break' : '';

  let html = `<div class="section ${breakClass}">
    <div class="section-title">Education</div>`;

  for (const edu of data.education) {
    html += `<div class="education-item">
      <div class="education-main">
        <div class="education-degree">${edu.degree}</div>
        <div class="education-institution">${edu.institution}</div>`;

    const details = [];
    if (edu.gpa) details.push(`GPA: ${edu.gpa}`);
    if (edu.honors) {
      const honorsText = Array.isArray(edu.honors) ? edu.honors.join(', ') : edu.honors;
      details.push(honorsText);
    }

    if (details.length > 0) {
      html += `<div class="education-details">${details.join(' • ')}</div>`;
    }

    html += `</div>
      <div class="education-date">${edu.graduation}</div>
    </div>`;
  }

  html += `</div>`;
  return html;
}


function renderPublications(data, config) {
  if (!data.publications || data.publications.length === 0) return '';
  
  const breakClass = config.keep_together === false ? 'allow-break' : '';
  
  let html = `<div class="section ${breakClass}">
    <div class="section-title">Publications</div>`;
  
  for (const pub of data.publications) {
    const venue = pub.venue || pub.journal;
    const link = pub.url || (pub.doi ? `https://doi.org/${pub.doi}` : null);
    
    html += `<div class="publication-item">
      <div class="publication-title">${pub.title}</div>
      <div class="publication-venue">`;
    
    if (link) {
      html += `<a href="${link}">${venue} (${pub.year})</a>`;
    } else {
      html += `${venue} (${pub.year})`;
    }
    
    html += `</div></div>`;
  }
  
  html += `</div>`;
  return html;
}

function renderLeadership(data, config) {
  const items = data.leadership || data.leadership_mentoring || data.achievements;
  if (!items || items.length === 0) return '';
  
  const breakClass = config.keep_together === false ? 'allow-break' : '';
  
  let html = `<div class="section ${breakClass}">
    <div class="section-title">Leadership & Mentoring</div>
    <ul class="leadership-list">`;
  
  for (const item of items) {
    const formatted = processTextFormatting(item);
    html += `<li>${formatted}</li>`;
  }
  
  html += `</ul></div>`;
  return html;
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

async function findFileByPattern(dir, pattern, fileType) {
  const files = await fs.readdir(dir);
  const match = files.find(file => pattern.test(file));
  
  if (!match) {
    console.error(`Could not find ${fileType} in "${dir}"`);
    return null;
  }
  
  return path.join(dir, match);
}

function openFile(filePath) {
  const command = process.platform === 'win32' ? 'start ""' :
                  process.platform === 'darwin' ? 'open' : 'xdg-open';
  exec(`${command} "${filePath}"`);
}

function validateContent(data) {
  const issues = [];
  const warnings = [];
  
  const forbiddenPhrases = [
    'spearheaded', 'leveraged', 'utilized', 'harnessed',
    'cutting-edge', 'state-of-the-art', 'best-in-class',
    'robust', 'seamless', 'innovative solution',
    'passion for', 'excited about', 'thought leader'
  ];
  
  const checkText = (text, location) => {
    if (!text) return;
    const lowerText = text.toLowerCase();
    
    forbiddenPhrases.forEach(phrase => {
      if (lowerText.includes(phrase)) {
        warnings.push(`Corporate speak detected in ${location}: "${phrase}"`);
      }
    });
    
    if (/^(achieved|reached|attained)\s+\d+/.test(lowerText)) {
      warnings.push(`Metric-first pattern in ${location} - consider adding context first`);
    }
    
    const wordCount = text.split(/\s+/).length;
    if (wordCount > 25) {
      warnings.push(`Bullet too long in ${location} (${wordCount} words) - target 12-18 words`);
    }
  };
  
  if (data.experience) {
    data.experience.forEach((exp, i) => {
      const location = `${exp.company}`;
      
      if (!exp.achievements || exp.achievements.length === 0) {
        issues.push(`No achievements for ${location}`);
      }
      
      exp.achievements?.forEach((ach, j) => {
        const text = typeof ach === 'string' ? ach : ach.text;
        checkText(text, `${location}, bullet ${j + 1}`);
        
        if (ach.metrics && ach.metrics.length > 0 && text.split(' ').length < 10) {
          warnings.push(`${location}, bullet ${j + 1}: Metrics present but bullet may lack context`);
        }
      });
    });
  }
  
  if (data.summary && data.summary.text) {
    checkText(data.summary.text, 'Summary');
  }
  
  if (issues.length > 0) {
    console.log('\n⚠️  CONTENT ISSUES FOUND:');
    issues.forEach(issue => console.log(`   ${issue}`));
  }
  
  if (warnings.length > 0) {
    console.log('\n💡 CONTENT WARNINGS:');
    warnings.forEach(warning => console.log(`   ${warning}`));
  }
  
  if (issues.length === 0 && warnings.length === 0) {
    console.log('✅ Content validation passed');
  }
  
  return { issues, warnings };
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  console.log('Premium Resume Generator v6.0 - Optimized Design\n');
  
  const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);
  if (!targetDir) {
    console.error('No application folders found');
    return;
  }
  
  console.log(`Using: ${path.basename(targetDir)}`);
  
  const dataPath = await findFileByPattern(targetDir, /^resume.*\.json$/, 'JSON');
  if (!dataPath) return;

  console.log('--- Attempting to read file at path:', dataPath);

  // Read the file content as a raw string
  const fileContent = await fs.readFile(dataPath, 'utf-8');

  // --- ADD THIS BLOCK FOR DEBUGGING ---
  console.log('--- RAW FILE CONTENT AS READ FROM DISK ---');
  console.log(fileContent);
  console.log('--- END OF RAW FILE CONTENT ---');
  // ------------------------------------

  // Now, parse the content
  const data = JSON.parse(fileContent);

  console.log('\nValidating content quality...');
  const validation = validateContent(data);
  
  if (validation.issues.length > 0) {
    console.log('\n❌ Please fix content issues before generating PDF');
    return;
  }
  
  // if (data.technical_expertise && !data.technical_skills) {
  //   data.technical_skills = {};
  //   for (const [key, value] of Object.entries(data.technical_expertise)) {
  //     const skills = typeof value.skills === 'string' 
  //       ? value.skills.split(',').map(s => s.trim())
  //       : value.skills;
  //     data.technical_skills[key] = {
  //       skills,
  //       highlight: [],
  //       years: value.years,
  //       proficiency: value.proficiency,
  //       context: value.context
  //     };
  //   }
  // }
  
  console.log('Generating Optimized Resume...');
  const html = generateHTML(data);
  
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
  
  const outputPath = path.join(targetDir, `${dateStamp}_${taglineForFilename}_KKrenek.pdf`);
  
  const metrics = await generatePDF(html, outputPath);
  
  console.log(`\n✓ Generated: ${path.basename(outputPath)}`);
  console.log(`  Pages: ${metrics.totalPages}`);
  console.log(`  Whitespace: ${metrics.whitespacePercent}%`);
  console.log(`  Design: Optimized v6.0`);
  console.log(`  Features: Compact header, clean skills, refined emphasis`);
  
  openFile(outputPath);
}

main().catch(err => {
  console.error(`\nError: ${err.message}`);
  process.exit(1);
});
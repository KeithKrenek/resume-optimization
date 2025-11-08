// ============================================================================
// RESUME PDF GENERATOR v11.0 - COMPREHENSIVE FORMATTING IMPROVEMENTS
// ============================================================================
// Major improvements:
// - Contact section: Display "LinkedIn", "GitHub", "Scholar" instead of URLs
// - Name + tagline combined on same line option
// - Technical skills: Pill-style boxes, removed dots, added "years"/"yrs"
// - Technical skills: Card-style groups with borders
// - Experience: Combined company/role/location/dates all on same line with even spacing
// - Projects: Inline bold keywords (Challenge/Approach/Impact) instead of labels, blue accent
// - Work Samples: Portfolio-style formatting with URL display
// - Enhanced visual hierarchy with improved spacing and differentiation
// - Smarter highlighting logic for better scannability and ATS compatibility
// ============================================================================

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

// ============================================================================
// ENHANCED DEFAULT CONFIGURATION
// ============================================================================

const DEFAULT_CONFIG = {
  version: '11.0',
  page_settings: {
    format: 'Letter',
    margins: {
      top: '0.45in',
      right: '0.5in',
      bottom: '0.45in',
      left: '0.5in'
    },
    target_pages: 2
  },
  typography: {
    font_family: 'Inter',
    base_size: '9.5pt',
    line_height: 1.45,
    scale_factor: 1.0
  },
  colors: {
    primary: '#0f172a',
    accent: '#0ea5e9',
    accent_dark: '#0284c7',
    title: '#b45309',
    muted: '#64748b',
    border: '#e2e8f0',
    pill_bg: '#f1f5f9',
    pill_border: '#cbd5e1',
    card_bg: '#fafbfc',
    surface: '#f8fafc'
  },
  spacing: {
    section_margin_bottom: '16px',
    subsection_margin_bottom: '10px',
    paragraph_margin_bottom: '5px',
    compact_mode: false
  },
  header: {
    style: 'professional',
    show_tagline: true,
    tagline_position: 'inline', // 'inline' or 'below'
    enable_hyperlinks: true,
    friendly_link_names: true // Show "LinkedIn" instead of full URL
  },
  sections: {
    professional_summary: {
      enabled: true,
      order: 1,
      style: 'paragraph',
      visual_treatment: 'accent_border',
      max_length: 0
    },
    technical_expertise: {
      enabled: true,
      order: 2,
      layout: 'columns',
      columns: 2,
      show_years: true,
      show_proficiency: false,
      center_align: false,
      pill_style: true,
      card_style: true
    },
    experience: {
      enabled: true,
      order: 3,
      header_style: 'company_first',
      compact_header: 'ultra', // true/'compact' = 2 lines, 'ultra' = 1 line, false = 3+ lines
      enable_highlighting: true,
      max_highlights_per_bullet: 4,
      show_company_logo: false,
      card_style: true
    },
    projects: {
      enabled: true,
      order: 4,
      structure: 'challenge_approach_impact',
      show_org_context: false,
      org_context_position: 'subtitle',
      enable_highlighting: true,
      card_style: true,
      hide_labels: true,
      inline_keywords: true
    },
    bulleted_projects: {
      enabled: true,
      order: 4,
      structure: 'challenge_approach_impact',
      show_org_context: false,
      org_context_position: 'subtitle',
      enable_highlighting: true,
      card_style: true,
      hide_labels: true,
      inline_keywords: true
    },
    education: {
      enabled: true,
      order: 5,
      style: 'detailed',
      show_gpa: true
    },
    publications: {
      enabled: true,
      order: 6,
      enable_hyperlinks: true,
      style: 'full'
    },
    work_samples: {
      enabled: true,
      order: 7,
      enable_hyperlinks: true,
      portfolio_style: true,
      show_tech: false,
      show_impact: false,
      show_url: true,
      columns: 2
    }
  },
  layout: {
    rows: [
      {
        type: 'single',
        sections: ['professional_summary'],
        allow_page_break: false
      },
      {
        type: 'single',
        sections: ['technical_expertise'],
        allow_page_break: false
      },
      {
        type: 'single',
        sections: ['experience'],
        allow_page_break: true
      },
      {
        type: 'single',
        sections: ['projects'],
        allow_page_break: true
      },
      {
        type: 'side_by_side',
        sections: ['education', 'publications'],
        widths: ['50%', '50%'],
        column_gap: '20px',
        allow_page_break: false
      }
    ],
    auto_layout: false
  },
  highlighting: {
    enabled: true,
    metrics: {
      enabled: true,
      style: 'bold'
    },
    technologies: {
      enabled: true,
      style: 'subtle', // 'accent_color', 'background', or 'subtle'
      max_per_bullet: 4
    },
    ats_friendly: true // Ensure highlighting doesn't break ATS parsing
  },
  advanced: {
    enable_orphan_control: true,
    enable_smart_compression: false,
    debug_mode: false
  }
};

// ============================================================================
// CONFIGURATION UTILITIES
// ============================================================================

async function loadConfig(jobFolder) {
  try {
    const configPath = path.join(jobFolder, 'resume_layout_config.json');
    const configData = await fs.readFile(configPath, 'utf-8');
    const userConfig = JSON.parse(configData);
    return deepMerge(DEFAULT_CONFIG, userConfig);
  } catch (error) {
    console.log('Using default configuration');
    return DEFAULT_CONFIG;
  }
}

function deepMerge(target, source) {
  const output = { ...target };
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          Object.assign(output, { [key]: source[key] });
        } else {
          output[key] = deepMerge(target[key], source[key]);
        }
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  return output;
}

function isObject(item) {
  return item && typeof item === 'object' && !Array.isArray(item);
}

function applySpacingMultiplier(config) {
  if (config.spacing.compact_mode) {
    const multiplier = 0.8;
    config.spacing.section_margin_bottom = multiplySize(config.spacing.section_margin_bottom, multiplier);
    config.spacing.subsection_margin_bottom = multiplySize(config.spacing.subsection_margin_bottom, multiplier);
    config.spacing.paragraph_margin_bottom = multiplySize(config.spacing.paragraph_margin_bottom, multiplier);
  }
  return config;
}

function multiplySize(sizeStr, multiplier) {
  const value = parseFloat(sizeStr);
  const unit = sizeStr.replace(/[0-9.]/g, '');
  return `${(value * multiplier).toFixed(1)}${unit}`;
}

// ============================================================================
// ENHANCED STYLING SYSTEM
// ============================================================================

function generateStyles(config) {
  const colors = config.colors;
  const typography = config.typography;
  const spacing = config.spacing;
  const baseSize = parseFloat(typography.base_size) * typography.scale_factor;
  
  return `
    * { 
      box-sizing: border-box; 
      margin: 0; 
      padding: 0; 
    }
    
    @import url('https://fonts.googleapis.com/css2?family=${typography.font_family}:wght@400;500;600;700;800;900&display=swap');
    
    body {
      font-family: '${typography.font_family}', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: ${colors.primary};
      background: #ffffff;
      line-height: ${typography.line_height};
      max-width: 8.5in;
      margin: 0 auto;
      padding: 0.3in 0.3in;
      font-size: ${baseSize}pt;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      letter-spacing: -0.011em;
    }

    /* ========== HEADER (IMPROVED) ========== */
    .header {
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 2px solid ${colors.accent};
    }
    
    .name-tagline-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 4px;
    }
    
    .name {
      font-size: ${baseSize * 2.5}pt;
      font-weight: 800;
      letter-spacing: -1px;
      color: ${colors.primary};
      line-height: 1.1;
    }
    
    .tagline {
      font-size: ${baseSize * 1.05}pt;
      color: ${colors.accent};
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    
    .tagline.below {
      display: block;
      margin-bottom: 8px;
    }
    
    .contact {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      font-size: ${baseSize * 0.9}pt;
      color: ${colors.muted};
      font-weight: 500;
      gap: 8px 0;
      width: 100%;
    }
    
    .contact a {
      color: ${colors.primary};
      text-decoration: none;
      transition: color 0.2s ease;
    }
    
    .contact a:hover {
      color: ${colors.accent};
    }
    
    .contact > span {
      flex: 0 1 auto;
      white-space: nowrap;
    }
    
    .contact > span:not(:last-child)::after {
      content: " ";
      color: #cbd5e1;
      margin-left: 10px;
      margin-right: 10px;
      font-weight: 200;
      opacity: 0.5;
    }

    /* ========== SECTION LAYOUT SYSTEM ========== */
    .section {
      margin-bottom: ${spacing.section_margin_bottom};
      page-break-inside: avoid;
    }
    
    .section.allow-break {
      page-break-inside: auto;
    }
    
    .section-row {
      display: flex;
      gap: 20px;
      margin-bottom: ${spacing.section_margin_bottom};
      page-break-inside: avoid;
    }
    
    .section-row.allow-break {
      page-break-inside: auto;
    }
    
    .section-row > div {
      flex: 1;
    }
    
    .section-title {
      font-size: ${baseSize * 1.3}pt;
      font-weight: 700;
      color: ${colors.title};
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      border-bottom: 1.5px solid ${colors.border};
      padding-bottom: 4px;
    }

    /* ========== PROFESSIONAL SUMMARY ========== */
    .summary {
      margin-bottom: ${spacing.section_margin_bottom};
    }
    
    .summary.accent-border {
      border-left: 3px solid ${colors.accent};
      padding-left: 14px;
      background: linear-gradient(90deg, ${colors.accent}06 0%, transparent 100%);
      padding-top: 10px;
      padding-bottom: 10px;
    }
    
    .summary-paragraph {
      font-size: ${baseSize * 1.05}pt;
      line-height: 1.55;
      color: ${colors.primary};
      font-weight: 400;
    }
    
    .summary-paragraph strong {
      font-weight: 700;
      color: ${colors.accent};
    }

    /* ========== TECHNICAL EXPERTISE (IMPROVED WITH PILLS & CARDS) ========== */
    .tech-expertise {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 14px 20px;
    }
    
    .tech-expertise.columns-1 {
      grid-template-columns: 1fr;
    }
    
    .tech-expertise.columns-2 {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .tech-expertise.columns-3 {
      grid-template-columns: repeat(3, 1fr);
    }
    
    .tech-expertise.columns-4 {
      grid-template-columns: repeat(4, 1fr);
    }
    
    .tech-category {
      margin-bottom: 0;
    }
    
    .tech-category.card {
      background: ${colors.card_bg};
      border: 1px solid ${colors.border};
      border-radius: 6px;
      padding: 10px 12px;
    }
    
    .tech-category-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 7px;
      flex-wrap: wrap;
    }
    
    .tech-category-name {
      font-size: ${baseSize * 1.05}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .tech-years-pill {
      font-size: ${baseSize * 0.82}pt;
      color: ${colors.accent};
      font-weight: 700;
      padding: 3px 9px;
      background: ${colors.accent}15;
      border: 1px solid ${colors.accent}30;
      border-radius: 12px;
      white-space: nowrap;
    }
    
    .tech-skills {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      font-size: ${baseSize * 0.92}pt;
      color: ${colors.primary};
    }
    
    .tech-skills.center {
      justify-content: center;
    }
    
    .tech-skill-pill {
      padding: 3px 8px;
      background: ${colors.pill_bg};
      border: 1px solid ${colors.pill_border};
      border-radius: 4px;
      font-weight: 500;
      white-space: nowrap;
    }

    /* ========== EXPERIENCE (CARD STYLE WITH COMPACT HEADER) ========== */
    .experience-item {
      margin-bottom: ${spacing.subsection_margin_bottom};
      page-break-inside: avoid;
    }
    
    .experience-item.card {
      background: ${colors.card_bg};
      border: 1px solid ${colors.border};
      border-left: 3px solid ${colors.accent};
      border-radius: 6px;
      padding: 12px 14px;
      margin-bottom: 12px;
    }
    
    .experience-header {
      margin-bottom: 8px;
    }
    
    .experience-header.compact {
      margin-bottom: 6px;
    }
    
    .experience-company-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 3px;
    }
    
    .experience-company {
      font-size: ${baseSize * 1.15}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .experience-dates {
      font-size: ${baseSize * 0.88}pt;
      color: ${colors.muted};
      font-weight: 600;
      white-space: nowrap;
    }
    
    .experience-role-location {
      display: flex;
      align-items: baseline;
      gap: 8px;
      flex-wrap: wrap;
    }
    
    .experience-title {
      font-size: ${baseSize * 1.0}pt;
      font-weight: 600;
      color: ${colors.accent};
    }
    
    .experience-location {
      font-size: ${baseSize * 0.88}pt;
      color: ${colors.muted};
      font-weight: 500;
    }
    
    .experience-location::before {
      content: "•";
      margin-right: 8px;
      color: ${colors.border};
    }
    
    /* Ultra-compact: everything on one line */
    .experience-single-line {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px 12px;
      margin-bottom: 8px;
    }
    
    .experience-single-line-left {
      display: flex;
      align-items: baseline;
      gap: 10px;
      flex-wrap: wrap;
    }
    
    .experience-single-line .experience-company {
      font-size: ${baseSize * 1.1}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .experience-single-line .experience-title {
      font-size: ${baseSize * 0.98}pt;
      font-weight: 600;
      color: ${colors.accent};
    }
    
    .experience-single-line .experience-location {
      font-size: ${baseSize * 0.88}pt;
      color: ${colors.muted};
      font-weight: 500;
    }
    
    .experience-single-line .experience-dates {
      font-size: ${baseSize * 0.88}pt;
      color: ${colors.muted};
      font-weight: 600;
      white-space: nowrap;
    }
    
    .experience-separator {
      color: ${colors.border};
      margin: 0 4px;
      font-weight: 300;
    }
    
    .experience-achievements {
      list-style: none;
      padding-left: 0;
    }
    
    .experience-achievements li {
      position: relative;
      padding-left: 16px;
      margin-bottom: 6px;
      line-height: 1.5;
      font-size: ${baseSize}pt;
    }
    
    .experience-achievements li::before {
      content: "▸";
      position: absolute;
      left: 0;
      color: ${colors.accent};
      font-weight: 700;
    }

    /* ========== PROJECTS (ENHANCED CARD STYLE) ========== */
    .project-card {
      margin-bottom: 12px;
      page-break-inside: avoid;
    }
    
    .project-card.card {
      background: ${colors.card_bg};
      border: 1px solid ${colors.border};
      border-left: 3px solid ${colors.accent};
      border-radius: 6px;
      padding: 12px 14px;
    }
    
    .project-header {
      margin-bottom: 8px;
    }
    
    .project-title-line {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 2px;
    }
    
    .project-title {
      font-size: ${baseSize * 1.1}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .project-dates {
      font-size: ${baseSize * 0.88}pt;
      color: ${colors.muted};
      font-weight: 600;
      white-space: nowrap;
    }
    
    .project-org {
      font-size: ${baseSize * 0.95}pt;
      color: ${colors.title};
      font-weight: 600;
      font-style: italic;
      margin-bottom: 6px;
    }
    
    .project-section {
      margin-bottom: 6px;
    }
    
    .project-section:last-child {
      margin-bottom: 0;
    }
    
    .project-section-label {
      font-size: ${baseSize * 0.82}pt;
      font-weight: 700;
      color: ${colors.title};
      text-transform: uppercase;
      letter-spacing: 0.3px;
      margin-bottom: 2px;
    }
    
    .project-section-content {
      line-height: 1.5;
      font-size: ${baseSize}pt;
    }

    /* ========== EDUCATION ========== */
    .education-item {
      margin-bottom: ${spacing.subsection_margin_bottom};
    }
    
    .education-degree-line {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 2px;
    }
    
    .education-degree {
      font-size: ${baseSize * 1.0}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .education-graduation {
      font-size: ${baseSize * 0.9}pt;
      color: ${colors.muted};
      font-weight: 600;
    }
    
    .education-institution {
      font-size: ${baseSize * 0.95}pt;
      color: ${colors.accent_dark};
      font-weight: 600;
      margin-bottom: 2px;
    }
    
    .education-details {
      font-size: ${baseSize * 0.9}pt;
      color: ${colors.muted};
    }

    /* ========== PUBLICATIONS ========== */
    .publication-item {
      margin-bottom: ${spacing.subsection_margin_bottom};
      line-height: 1.5;
    }
    
    .publication-title {
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .publication-title a {
      color: ${colors.primary};
      text-decoration: none;
    }
    
    .publication-title a:hover {
      color: ${colors.accent};
      text-decoration: underline;
    }
    
    .publication-authors {
      font-size: ${baseSize * 0.95}pt;
      color: ${colors.muted};
      font-style: italic;
      margin-top: 2px;
    }
    
    .publication-meta {
      font-size: ${baseSize * 0.9}pt;
      color: ${colors.muted};
      margin-top: 2px;
    }

    /* ========== PORTFOLIO SHOWCASE (WORK SAMPLES) ========== */
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

    /* ========== WORK SAMPLES ========== */
    .work-sample-item {
      margin-bottom: ${spacing.subsection_margin_bottom};
      page-break-inside: avoid;
    }
    
    .work-sample-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 4px;
    }
    
    .work-sample-title {
      font-size: ${baseSize * 1.05}pt;
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .work-sample-type {
      font-size: ${baseSize * 0.85}pt;
      color: ${colors.muted};
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .work-sample-description {
      line-height: 1.5;
      margin-bottom: 4px;
    }
    
    .work-sample-tech {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-bottom: 4px;
    }
    
    .work-sample-tech .tech-badge {
      padding: 2px 7px;
      background: ${colors.pill_bg};
      border: 1px solid ${colors.pill_border};
      border-radius: 4px;
      font-size: ${baseSize * 0.85}pt;
      font-weight: 500;
      white-space: nowrap;
    }
    
    .work-sample-impact {
      font-size: ${baseSize * 0.95}pt;
      color: ${colors.muted};
      line-height: 1.5;
      margin-top: 4px;
    }
    
    .work-sample-title a {
      color: ${colors.primary};
      text-decoration: none;
    }
    
    .work-sample-title a:hover {
      color: ${colors.accent};
      text-decoration: underline;
    }
    
    .work-sample-url {
      font-size: ${baseSize * 0.9}pt;
      color: ${colors.accent};
      word-break: break-all;
    }

    /* ========== HIGHLIGHTING STYLES (ATS-FRIENDLY) ========== */
    .highlight-metric {
      font-weight: 700;
      color: ${colors.primary};
    }
    
    .highlight-metric.accent {
      color: ${colors.accent};
      font-weight: 700;
    }
    
    .highlight-tech {
      font-weight: 600;
      color: ${colors.accent};
    }
    
    .highlight-tech.subtle {
      font-weight: 600;
      color: ${colors.primary};
    }
    
    .highlight-tech.background {
      background: ${colors.accent}12;
      padding: 1px 4px;
      border-radius: 3px;
      font-weight: 600;
    }
    
    /* ========== UTILITY CLASSES ========== */
    .no-break {
      page-break-inside: avoid;
    }
    
    .allow-break {
      page-break-inside: auto;
    }
    
    .no-page-break {
      page-break-inside: avoid;
    }
    
    ${config.advanced.debug_mode ? `
    .section {
      border: 1px dashed red;
      position: relative;
    }
    .section::before {
      content: attr(data-section);
      position: absolute;
      top: 0;
      right: 0;
      background: red;
      color: white;
      font-size: 8pt;
      padding: 2px 4px;
    }
    ` : ''}
  `;
}

// ============================================================================
// HEADER GENERATOR (IMPROVED)
// ============================================================================

function generateHeader(data, config) {
  const contact = data.contact || {};
  const headerConfig = config.header;
  
  let html = '<div class="header">';
  
  // Name and tagline - inline or stacked
  if (headerConfig.tagline_position === 'inline' && headerConfig.show_tagline && contact.tagline) {
    html += '<div class="name-tagline-row">';
    html += `<div class="name">${escapeHtml(contact.name || 'Name')}</div>`;
    const tagline = Array.isArray(contact.tagline) ? contact.tagline[0] : contact.tagline;
    html += `<div class="tagline">${escapeHtml(tagline)}</div>`;
    html += '</div>';
  } else {
    html += `<div class="name">${escapeHtml(contact.name || 'Name')}</div>`;
    if (headerConfig.show_tagline && contact.tagline) {
      const tagline = Array.isArray(contact.tagline) ? contact.tagline[0] : contact.tagline;
      html += `<div class="tagline below">${escapeHtml(tagline)}</div>`;
    }
  }
  
  // Contact info
  html += '<div class="contact">';
  
  const contactItems = [];
  
  if (contact.email) {
    if (headerConfig.enable_hyperlinks) {
      contactItems.push(`<a href="mailto:${contact.email}">${escapeHtml(contact.email)}</a>`);
    } else {
      contactItems.push(escapeHtml(contact.email));
    }
  }
  
  if (contact.phone) {
    contactItems.push(escapeHtml(contact.phone));
  }
  
  if (contact.location) {
    contactItems.push(escapeHtml(contact.location));
  }
  
  // LinkedIn - show "LinkedIn" instead of URL
  if (contact.linkedin) {
    const linkText = headerConfig.friendly_link_names ? 'LinkedIn' : 
                     contact.linkedin.replace(/https?:\/\/(www\.)?/, '').replace(/\/$/, '');
    if (headerConfig.enable_hyperlinks) {
      contactItems.push(`<a href="${contact.linkedin}">${escapeHtml(linkText)}</a>`);
    } else {
      contactItems.push(escapeHtml(linkText));
    }
  }
  
  // GitHub - show "GitHub" instead of URL
  if (contact.github) {
    const linkText = headerConfig.friendly_link_names ? 'GitHub' : 
                     contact.github.replace(/https?:\/\/(www\.)?/, '').replace(/\/$/, '');
    if (headerConfig.enable_hyperlinks) {
      contactItems.push(`<a href="${contact.github}">${escapeHtml(linkText)}</a>`);
    } else {
      contactItems.push(escapeHtml(linkText));
    }
  }
  
  // Portfolio - show "Scholar" or "Portfolio"
  if (contact.portfolio) {
    const linkText = headerConfig.friendly_link_names && contact.portfolio.includes('scholar.google') 
                     ? 'Scholar' 
                     : (headerConfig.friendly_link_names ? 'Portfolio' : 
                        contact.portfolio.replace(/https?:\/\/(www\.)?/, '').replace(/\/$/, ''));
    if (headerConfig.enable_hyperlinks) {
      contactItems.push(`<a href="${contact.portfolio}">${linkText}</a>`);
    } else {
      contactItems.push(linkText);
    }
  }
  
  html += contactItems.map(item => `<span>${item}</span>`).join('');
  html += '</div>';
  html += '</div>';
  
  return html;
}

// ============================================================================
// PROFESSIONAL SUMMARY GENERATOR
// ============================================================================

function generateSummary(data, config) {
  const sectionConfig = config.sections.professional_summary;
  if (!sectionConfig.enabled || !data.professional_summary) return '';
  
  let html = '<div class="section';
  if (sectionConfig.visual_treatment === 'accent_border') {
    html += ' summary accent-border';
  }
  html += '" data-section="summary">';
  
  const summary = typeof data.professional_summary === 'string' 
    ? data.professional_summary 
    : data.professional_summary.text || '';
  
  const highlighted = highlightText(summary, config);
  html += `<div class="summary-paragraph">${highlighted}</div>`;
  
  html += '</div>';
  return html;
}

// ============================================================================
// TECHNICAL EXPERTISE GENERATOR (WITH PILLS & CARDS)
// ============================================================================

function generateTechnicalExpertise(data, config) {
  const sectionConfig = config.sections.technical_expertise;
  if (!sectionConfig.enabled || !data.technical_expertise) return '';
  
  let html = '<div class="section" data-section="technical">';
  html += '<div class="section-title">Technical Expertise</div>';
  
  const columns = sectionConfig.columns || 2;
  const centerAlign = sectionConfig.center_align;
  const pillStyle = sectionConfig.pill_style !== false;
  const cardStyle = sectionConfig.card_style !== false;
  
  html += `<div class="tech-expertise columns-${columns}">`;
  
  const categories = Object.entries(data.technical_expertise);
  
  for (const [categoryName, categoryData] of categories) {
    html += `<div class="tech-category${cardStyle ? ' card' : ''}">`;
    
    // Header with category name and years (with "years" or "yrs" suffix)
    html += '<div class="tech-category-header">';
    html += `<span class="tech-category-name">${escapeHtml(categoryName)}</span>`;
    
    if (sectionConfig.show_years && categoryData.years) {
      const yearsText = categoryData.years + (categoryData.years.includes('year') || categoryData.years.includes('yr') ? '' : ' yrs');
      html += `<span class="tech-years-pill">${escapeHtml(yearsText)}</span>`;
    }
    
    html += '</div>';
    
    // Skills list with pill styling
    if (categoryData.skills && Array.isArray(categoryData.skills)) {
      html += `<div class="tech-skills${centerAlign ? ' center' : ''}">`;
      categoryData.skills.forEach(skill => {
        if (pillStyle) {
          html += `<span class="tech-skill-pill">${escapeHtml(skill)}</span>`;
        } else {
          html += `<span class="tech-skill">${escapeHtml(skill)}</span>`;
        }
      });
      html += '</div>';
    }
    
    html += '</div>';
  }
  
  html += '</div></div>';
  return html;
}

// ============================================================================
// EXPERIENCE GENERATOR (COMPACT HEADER & CARD STYLE)
// ============================================================================

function generateExperience(data, config) {
  const sectionConfig = config.sections.experience;
  if (!sectionConfig.enabled || !data.experience || data.experience.length === 0) return '';
  
  let html = '<div class="section allow-break" data-section="experience">';
  html += '<div class="section-title">Professional Experience</div>';
  
  const compactHeader = sectionConfig.compact_header;
  const cardStyle = sectionConfig.card_style !== false;
  
  for (const exp of data.experience) {
    html += `<div class="experience-item${cardStyle ? ' card' : ''}">`;
    
    // Header - Three options: ultra-compact (1 line), compact (2 lines), or standard (3+ lines)
    if (compactHeader === 'ultra') {
      // Ultra-compact: Everything on one line with separators
      html += '<div class="experience-single-line">';
      html += '<div class="experience-single-line-left">';
      html += `<span class="experience-company">${escapeHtml(exp.company || 'Company')}</span>`;
      html += '<span class="experience-separator">|</span>';
      html += `<span class="experience-title">${escapeHtml(exp.title || 'Title')}</span>`;
      if (exp.location) {
        html += '<span class="experience-separator">|</span>';
        html += `<span class="experience-location">${escapeHtml(exp.location)}</span>`;
      }
      html += '</div>';
      if (exp.dates) {
        html += `<span class="experience-dates">${escapeHtml(exp.dates)}</span>`;
      }
      html += '</div>';
    } else if (compactHeader === true || compactHeader === 'compact') {
      // Compact: Company and dates on line 1, role and location on line 2
      html += `<div class="experience-header compact">`;
      html += '<div class="experience-company-row">';
      html += `<div class="experience-company">${escapeHtml(exp.company || 'Company')}</div>`;
      if (exp.dates) {
        html += `<div class="experience-dates">${escapeHtml(exp.dates)}</div>`;
      }
      html += '</div>';
      
      html += '<div class="experience-role-location">';
      html += `<div class="experience-title">${escapeHtml(exp.title || 'Title')}</div>`;
      if (exp.location) {
        html += `<div class="experience-location">${escapeHtml(exp.location)}</div>`;
      }
      html += '</div>';
      html += '</div>';
    } else {
      // Original non-compact style
      html += `<div class="experience-header">`;
      html += `<div class="experience-company">${escapeHtml(exp.company || 'Company')}</div>`;
      html += '<div class="experience-role-line">';
      html += `<div class="experience-title">${escapeHtml(exp.title || 'Title')}</div>`;
      html += '<div class="experience-meta">';
      if (exp.location) html += `${escapeHtml(exp.location)} • `;
      if (exp.dates) html += escapeHtml(exp.dates);
      html += '</div>';
      html += '</div>';
      html += '</div>';
    }
    
    // Achievements
    if (exp.achievements && Array.isArray(exp.achievements)) {
      html += '<ul class="experience-achievements">';
      for (const achievement of exp.achievements) {
        const text = typeof achievement === 'string' ? achievement : achievement.text;
        const highlighted = highlightText(text, config);
        html += `<li>${highlighted}</li>`;
      }
      html += '</ul>';
    }
    
    html += '</div>'; // experience-item
  }
  
  html += '</div>'; // section
  return html;
}

// ============================================================================
// PROJECTS GENERATOR (ENHANCED CARD STYLE, NO REPEATED LABELS)
// ============================================================================

function generateProjects(data, config) {
  // Support both 'projects' and 'bulleted_projects' config names
  const sectionConfig = config.sections.projects || config.sections.bulleted_projects;
  if (!sectionConfig.enabled) return '';
  
  // Support both 'projects' and 'bulleted_projects' field names
  const projectsData = data.projects || data.bulleted_projects;
  if (!projectsData || projectsData.length === 0) return '';
  
  let html = '<div class="section allow-break" data-section="projects">';
  html += '<div class="section-title">Key Projects</div>';
  
  const cardStyle = sectionConfig.card_style !== false;
  const hideLabels = sectionConfig.hide_labels === true;
  
  for (const project of projectsData) {
    html += `<div class="project-card${cardStyle ? ' card' : ''}">`;
    
    // Header
    html += '<div class="project-header">';
    
    // Title and dates
    html += '<div class="project-title-line">';
    html += `<div class="project-title">${escapeHtml(project.title || 'Project')}</div>`;
    if (project.dates) {
      html += `<div class="project-dates">${escapeHtml(project.dates)}</div>`;
    }
    html += '</div>';
    
    // Organization context (as subtitle)
    if (sectionConfig.show_org_context && project.org_context && sectionConfig.org_context_position === 'subtitle') {
      html += `<div class="project-org">${escapeHtml(project.org_context)}</div>`;
    }
    
    html += '</div>'; // header
    
    // Challenge/Approach/Impact structure - no repeated labels
    if (sectionConfig.structure === 'challenge_approach_impact') {
      if (project.achievement1) {
        html += '<div class="project-section">';
        if (!hideLabels) {
          html += '<div class="project-section-label">Challenge</div>';
        }
        const highlighted = highlightText(project.achievement1, config);
        html += `<div class="project-section-content">${highlighted}</div>`;
        html += '</div>';
      }
      
      if (project.achievement2) {
        html += '<div class="project-section">';
        if (!hideLabels) {
          html += '<div class="project-section-label">Approach</div>';
        }
        const highlighted = highlightText(project.achievement2, config);
        html += `<div class="project-section-content">${highlighted}</div>`;
        html += '</div>';
      }
      
      if (project.achievement3) {
        html += '<div class="project-section">';
        if (!hideLabels) {
          html += '<div class="project-section-label">Impact</div>';
        }
        const highlighted = highlightText(project.achievement3, config);
        html += `<div class="project-section-content">${highlighted}</div>`;
        html += '</div>';
      }
    }
    
    html += '</div>'; // project-card
  }
  
  html += '</div>'; // section
  return html;
}

// ============================================================================
// EDUCATION GENERATOR
// ============================================================================

function generateEducation(data, config) {
  const sectionConfig = config.sections.education;
  if (!sectionConfig.enabled || !data.education || data.education.length === 0) return '';
  
  let html = '<div class="section" data-section="education">';
  html += '<div class="section-title">Education</div>';
  
  for (const edu of data.education) {
    html += '<div class="education-item">';
    
    // Degree and graduation date
    html += '<div class="education-degree-line">';
    html += `<div class="education-degree">${escapeHtml(edu.degree || 'Degree')}</div>`;
    if (edu.graduation) {
      html += `<div class="education-graduation">${escapeHtml(edu.graduation)}</div>`;
    }
    html += '</div>';
    
    // Institution
    if (edu.institution) {
      html += `<div class="education-institution">${escapeHtml(edu.institution)}`;
      if (edu.location && sectionConfig.style === 'detailed') {
        html += `, ${escapeHtml(edu.location)}`;
      }
      html += '</div>';
    }
    
    // Details (GPA, honors, etc.)
    if (edu.details && sectionConfig.show_gpa) {
      html += `<div class="education-details">${escapeHtml(edu.details)}</div>`;
    }
    
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

// ============================================================================
// PUBLICATIONS GENERATOR
// ============================================================================

function generatePublications(data, config) {
  const sectionConfig = config.sections.publications;
  if (!sectionConfig.enabled || !data.publications || data.publications.length === 0) return '';
  
  let html = '<div class="section" data-section="publications">';
  html += '<div class="section-title">Publications</div>';
  
  for (const pub of data.publications) {
    html += '<div class="publication-item">';
    
    // Title with optional link
    if (pub.url && sectionConfig.enable_hyperlinks) {
      html += `<div class="publication-title"><a href="${pub.url}">${escapeHtml(pub.title)}</a></div>`;
    } else {
      html += `<div class="publication-title">${escapeHtml(pub.title || 'Publication')}</div>`;
    }
    
    // Authors
    if (pub.authors) {
      html += `<div class="publication-authors">${escapeHtml(pub.authors)}</div>`;
    }
    
    // Meta (journal, year)
    const meta = [];
    if (pub.journal) meta.push(pub.journal);
    if (pub.year) meta.push(pub.year);
    if (meta.length > 0) {
      html += `<div class="publication-meta">${escapeHtml(meta.join(', '))}</div>`;
    }
    
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

// ============================================================================
// WORK SAMPLES GENERATOR
// ============================================================================

function generateWorkSamples(data, config) {
  const sectionConfig = config.sections.work_samples;
  if (!sectionConfig.enabled || !data.work_samples || data.work_samples.length === 0) return '';
  
  let html = '<div class="section" data-section="work_samples">';
  html += '<div class="section-title">Example Projects</div>';
  
  const columns = sectionConfig.columns || 1;
  const showTech = sectionConfig.show_tech !== false;
  const showImpact = sectionConfig.show_impact !== false;
  const showUrl = sectionConfig.show_url !== false;
  
  html += `<div class="portfolio-grid cols-${columns}">`;
  
  for (const sample of data.work_samples) {
    html += '<div class="portfolio-item">';
    
    // Type
    if (sample.type) {
      html += `<div class="portfolio-type">${escapeHtml(sample.type)}</div>`;
    }
    
    // Title
    html += `<div class="portfolio-title">${escapeHtml(sample.title || 'Work Sample')}</div>`;
    
    // Description
    if (sample.description) {
      html += `<div class="portfolio-desc">${escapeHtml(sample.description)}</div>`;
    }
    
    // URL - show if enabled
    if (showUrl && sample.url && sectionConfig.enable_hyperlinks) {
      const cleanDemoUrl = sample.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
      const fullDemoUrl = sample.url.startsWith('http') ? sample.url : `https://${sample.url}`;
      html += `<div class="portfolio-link"><a href="${fullDemoUrl}">${cleanDemoUrl}</a></div>`;
      // html += `<div class="portfolio-link"><a href="${sample.url}" target="_blank">${escapeHtml(sample.url)}</a></div>`;
    }
    
    html += '</div>';
  }
  
  html += '</div>';
  html += '</div>';
  return html;
}

// ============================================================================
// HIGHLIGHTING SYSTEM (IMPROVED & ATS-FRIENDLY)
// ============================================================================

function highlightText(text, config) {
  if (!config.highlighting.enabled || !text) return escapeHtml(text);
  
  let result = escapeHtml(text);
  
  // Highlight metrics (numbers with context)
  if (config.highlighting.metrics.enabled) {
    const metricPatterns = [
      // Percentages and multipliers
      /\b\d+[×xX]\b/g,
      /\b\d+%\b/g,
      /\b>\s*\d+%\b/g,
      /\b<\s*\d+%\b/g,
      /\b\d+\s*-\s*\d+%\b/g,
      
      // Currency
      /\$\d+[KMB]?\+?/g,
      
      // Decimal numbers
      /\b\d+\.\d+x?\b/g,
      
      // Years (already formatted)
      /\b\d+\+?\s*(?:years?|yrs?)\b/gi,
      
      // Counts with + or context
      /\b\d+\+\s+\w+/g,
      /\b100s?\b/gi,
      /\b1000s?\b/gi
    ];
    
    metricPatterns.forEach(pattern => {
      result = result.replace(pattern, match => {
        const style = config.highlighting.metrics.style;
        if (style === 'bold_accent') {
          return `<span class="highlight-metric accent">${match}</span>`;
        }
        return `<strong class="highlight-metric">${match}</strong>`;
      });
    });
  }
  
  // Highlight technologies (smarter, limited per bullet)
  if (config.highlighting.technologies.enabled) {
    const techKeywords = [
      // Languages
      'Python', 'JavaScript', 'TypeScript', 'Java', 'C\\+\\+', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin',
      // Frameworks/Libraries
      'React', 'Vue', 'Angular', 'Django', 'Flask', 'Spring', 'Express', 'Next\\.js', 'Node\\.js',
      'PyTorch', 'TensorFlow', 'Keras', 'scikit-learn', 'XGBoost', 'Pandas', 'NumPy',
      // Cloud/DevOps
      'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'K8s', 'Jenkins', 'GitLab', 'GitHub Actions',
      // Databases
      'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
      // AI/ML Terms
      'RAG', 'LLM', 'LLMs', 'GPT', 'BERT', 'Transformer',
      // Methodologies/Practices
      'CI\/CD', 'MLOps', 'DevOps', 'Agile', 'Scrum',
      // Domains
      'NLP', 'Computer Vision', 'Deep Learning', 'Machine Learning', 'Neural Networks',
      // Tools
      'Git', 'JIRA', 'Terraform', 'Ansible',
      // Specialized
      'FAISS', 'Pinecone', 'Chroma', 'LangChain', 'OpenAI API', 'Anthropic API',
      'SHAP', 'Matplotlib', 'Plotly', 'D3\\.js'
    ];
    
    const style = config.highlighting.technologies.style || 'subtle';
    const className = style === 'background' ? 'highlight-tech background' : 
                     style === 'accent_color' ? 'highlight-tech' : 
                     'highlight-tech subtle';
    
    // Create a pattern that matches whole words/phrases
    const pattern = new RegExp(`\\b(${techKeywords.join('|')})\\b`, 'g');
    
    // Track highlights to limit per bullet (ATS-friendly)
    let highlightCount = 0;
    const maxHighlights = config.highlighting.technologies.max_per_bullet || 4;
    
    result = result.replace(pattern, match => {
      if (highlightCount >= maxHighlights) return match;
      highlightCount++;
      return `<span class="${className}">${match}</span>`;
    });
  }
  
  return result;
}

// ============================================================================
// LAYOUT ENGINE
// ============================================================================

function generateHTML(data, config) {
  config = applySpacingMultiplier(config);
  
  const sectionGenerators = {
    'professional_summary': () => generateSummary(data, config),
    'technical_expertise': () => generateTechnicalExpertise(data, config),
    'experience': () => generateExperience(data, config),
    'projects': () => generateProjects(data, config),
    'bulleted_projects': () => generateProjects(data, config), // Alias for projects
    'education': () => generateEducation(data, config),
    'publications': () => generatePublications(data, config),
    'work_samples': () => generateWorkSamples(data, config)
  };
  
  let bodyHTML = generateHeader(data, config);
  
  // Use layout rows configuration
  if (config.layout && config.layout.rows) {
    for (const row of config.layout.rows) {
      const enabledSections = row.sections.filter(s => config.sections[s]?.enabled);
      
      if (enabledSections.length === 0) continue;
      
      if (row.type === 'single' && enabledSections.length === 1) {
        // Single section, full width
        const sectionHTML = sectionGenerators[enabledSections[0]]?.();
        if (sectionHTML) {
          bodyHTML += sectionHTML + '\n';
        }
      } else if (row.type === 'side_by_side' || row.type === 'multi_column') {
        // Multiple sections in a row
        const sectionHTMLs = enabledSections
          .map(s => sectionGenerators[s]?.())
          .filter(Boolean);
        
        if (sectionHTMLs.length > 0) {
          const rowClass = row.allow_page_break ? 'section-row allow-break' : 'section-row';
          const gap = row.column_gap || '20px';
          
          bodyHTML += `<div class="${rowClass}" style="gap: ${gap};">`;
          
          sectionHTMLs.forEach((html, index) => {
            const width = row.widths?.[index] || `${100 / sectionHTMLs.length}%`;
            bodyHTML += `<div style="flex: 0 0 ${width};">${html}</div>`;
          });
          
          bodyHTML += '</div>\n';
        }
      }
    }
  } else {
    // Fallback: render all enabled sections in order
    const orderedSections = Object.entries(config.sections)
      .filter(([_, cfg]) => cfg.enabled)
      .sort((a, b) => a[1].order - b[1].order)
      .map(([name, _]) => name);
    
    for (const sectionName of orderedSections) {
      const sectionHTML = sectionGenerators[sectionName]?.();
      if (sectionHTML) {
        bodyHTML += sectionHTML + '\n';
      }
    }
  }
  
  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resume - ${data.contact?.name || 'Candidate'}</title>
  <style>${generateStyles(config)}</style>
</head>
<body>
  ${bodyHTML}
</body>
</html>
  `.trim();
}

// ============================================================================
// PDF GENERATION
// ============================================================================

async function generatePDF(html, outputPath, config) {
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
      format: config.page_settings?.format || 'Letter',
      printBackground: true,
      margin: config.page_settings?.margins || {
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
// UTILITIES
// ============================================================================

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
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
    /^resume_edited\.json$/,
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
  console.log('Resume PDF Generator v10.0 - Comprehensive Formatting Improvements\n');
  
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
  
  const config = await loadConfig(targetDir);
  console.log('Configuration loaded');
  
  const dataPath = await findResumeFile(targetDir);
  if (!dataPath) return;
  
  console.log(`Reading: ${path.basename(dataPath)}`);
  
  const fileContent = await fs.readFile(dataPath, 'utf-8');
  const data = JSON.parse(fileContent);
  
  console.log('Generating HTML...');
  const html = generateHTML(data, config);
  
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
  const metrics = await generatePDF(html, outputPath, config);
  
  console.log(`\n✓ Generated: ${path.basename(outputPath)}`);
  console.log(`  Pages: ${metrics.totalPages}`);
  console.log(`  Whitespace: ${metrics.whitespacePercent}%`);
  console.log(`  Version: v10.0 Comprehensive Formatting Improvements`);
  
  openFile(outputPath);
}

main().catch(err => {
  console.error(`\nError: ${err.message}`);
  process.exit(1);
});
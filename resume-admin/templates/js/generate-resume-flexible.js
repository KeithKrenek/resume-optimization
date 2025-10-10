// ============================================================================
// FLEXIBLE RESUME GENERATOR - Production Ready
// ============================================================================
// This script generates resumes with fully customizable layouts.
// See LAYOUT_CONFIG below for how to adjust your resume layout.
// ============================================================================

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

// ============================================================================
// CONFIGURATION - EDIT THIS SECTION
// ============================================================================

const BASE_APPLICATIONS_DIR = "C:/Users/keith/Dropbox/Resume";

// ============================================================================
// LAYOUT CONFIGURATION
// ============================================================================
// This is where you define how your resume sections are arranged.
//
// SECTION TYPES:
// - 'header'              : Contact info (always full-width)
// - 'summary'             : Professional summary (always full-width)
// - 'technical_expertise' : Skills grid
// - 'experience'          : Work history (always full-width)
// - 'projects'            : Project descriptions
// - 'education'           : Degrees
// - 'publications'        : Papers/articles
// - 'work_samples'        : Portfolio links
// - 'leadership'          : Leadership bullet points
//
// SECTION PROPERTIES:
//
// width: 'full' | 'half'
//   - 'full' = spans entire page width
//   - 'half' = takes up half the page (use with another half-width section)
//
// columns: 1 | 2 | 3 | 4
//   - Number of columns WITHIN the section
//   - Only applies to: technical_expertise, projects (when multiple)
//
// startFrom: number
//   - For projects: which project index to start from (0-based)
//   - Example: startFrom: 2 means start from 3rd project
//
// count: number
//   - For projects: how many projects to show
//   - Example: count: 2 means show only 2 projects
//
// keepTogether: true | false
//   - true = prevent section from breaking across pages (uses page-break-inside: avoid)
//   - false = allow section to break across pages if needed (default)
//   - Useful for: keeping all projects together, or ensuring education stays on one page
//   - Example: { type: 'projects', keepTogether: true }
//
// GRID LAYOUT:
//   Use { type: 'row', sections: [...] } to place multiple sections side-by-side
//   All sections in a row automatically become half-width (or 1/3 if 3 sections)
//
// ============================================================================

const LAYOUT_CONFIG = {
  sections: [
    // Page 1: Header and Summary (always at top)
    { type: 'header' },
    { type: 'summary' },
    
    // ========================================================================
    // EXAMPLE 1: Technical Expertise side-by-side with Education
    // ========================================================================
    // This creates two columns: Technical Expertise (with 2 internal columns)
    // and Education next to it
    {
      type: 'row',
      sections: [
        { type: 'technical_expertise', columns: 2 },  // Left half, 2-column grid inside
        { type: 'education' }                         // Right half
      ]
    },
    
    // ========================================================================
    // ALTERNATIVE: Full-width Technical Expertise with 4 columns
    // ========================================================================
    // Uncomment this and comment out the row above if you prefer:
    // { type: 'technical_expertise', width: 'full', columns: 4 },
    // { type: 'education', width: 'full' },
    
    // Experience always full-width
    { type: 'experience' },
    
    // ========================================================================
    // EXAMPLE 2: Projects and Work Samples side-by-side
    // ========================================================================
    // First 2 projects on left, work samples + publications on right
    {
      type: 'row',
      sections: [
        { type: 'projects', count: 2 },               // First 2 projects only
        [                                             // Right column has multiple sections
          { type: 'work_samples' },
          { type: 'publications' }
        ]
      ]
    },
    
    // ========================================================================
    // EXAMPLE 3: Third project with leadership
    // ========================================================================
    // Remaining project on left, leadership on right
    {
      type: 'row',
      sections: [
        { type: 'projects', startFrom: 2, keepTogether: true },  // Keep on one page
        { type: 'leadership' }
      ]
    }
    
    // ========================================================================
    // EXAMPLE 4: Using keepTogether to control page breaks
    // ========================================================================
    // keepTogether: true prevents a section from breaking across pages
    // keepTogether: false (or omitted) allows natural page breaks
    
    // Keep all projects together on one page:
    // { type: 'projects', keepTogether: true }
    
    // Allow projects to break across pages (default):
    // { type: 'projects', keepTogether: false }
    
    // Mixed approach:
    // {
    //   type: 'row',
    //   sections: [
    //     { type: 'projects', count: 2, keepTogether: true },  // First 2 stay together
    //     { type: 'projects', startFrom: 2 }                   // 3rd can break
    //   ]
    // }
    
    // ========================================================================
    // MORE EXAMPLES - Uncomment to try different layouts:
    // ========================================================================
    
    // All projects in one column, everything else on the right:
    // {
    //   type: 'row',
    //   sections: [
    //     { type: 'projects' },
    //     [
    //       { type: 'work_samples' },
    //       { type: 'publications' },
    //       { type: 'education' },
    //       { type: 'leadership' }
    //     ]
    //   ]
    // },
    
    // Three columns of projects:
    // {
    //   type: 'row',
    //   sections: [
    //     { type: 'projects', count: 1 },
    //     { type: 'projects', startFrom: 1, count: 1 },
    //     { type: 'projects', startFrom: 2, count: 1 }
    //   ]
    // },
    
    // Work samples full-width:
    // { type: 'work_samples', width: 'full' },
    // {
    //   type: 'row',
    //   sections: [
    //     { type: 'projects' },
    //     [
    //       { type: 'education' },
    //       { type: 'publications' },
    //       { type: 'leadership' }
    //     ]
    //   ]
    // },
  ]
};

// ============================================================================
// QUICK LAYOUT PRESETS
// ============================================================================
// Uncomment one of these to quickly try different layouts.
// These replace the LAYOUT_CONFIG.sections above.
// ============================================================================

// PRESET 1: Compact header, balanced columns
// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' },
//   { type: 'row', sections: [
//     { type: 'technical_expertise', columns: 2 },
//     { type: 'education' }
//   ]},
//   { type: 'experience' },
//   { type: 'row', sections: [
//     { type: 'projects', count: 2 },
//     [{ type: 'work_samples' }, { type: 'publications' }]
//   ]},
//   { type: 'row', sections: [
//     { type: 'projects', startFrom: 2 },
//     { type: 'leadership' }
//   ]}
// ];

// PRESET 2: Full-width skills showcase
// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' },
//   { type: 'technical_expertise', width: 'full', columns: 4 },
//   { type: 'experience', keepTogether: false  },
//   { type: 'row', keepTogether: false, sections: [
//     [{ type: 'projects' }, { type: 'education' }],
//     [{ type: 'publications' }, { type: 'leadership' }, { type: 'work_samples', columns: 3 }]
//   ]}
// ];

// Recommended Layout: Denser two-column structure for Page 2
// LAYOUT_CONFIG.sections = [
//   // Page 1 Content (remains the same)
//   { type: 'header' },
//   { type: 'summary' },
//   { type: 'technical_expertise', width: 'full', columns: 4 },
//   { type: 'experience', keepTogether: false  },

//   // Page 2 Content: Restructured into a main content column and a sidebar
//   {
//     type: 'row',
//     keepTogether: false, // Allow this entire row to break if needed
//     sections: [
//       // --- LEFT COLUMN (main content) ---
//       [{ type: 'projects', width: 'full', columns: 1 }], // All projects stack here
//       // --- RIGHT COLUMN (sidebar with multiple smaller sections) ---
//       [ // This array groups sections vertically within the right column
//         { type: 'education' },
//         { type: 'publications' },
//         { type: 'leadership' }, // This section uses the 'achievements' data
//         { type: 'work_samples' }
//       ]
//     ]
//   }
// ];

// PRESET 3: Education prominent
// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' },
//   { type: 'education', width: 'full' },
//   { type: 'technical_expertise', width: 'full', columns: 3 },
//   { type: 'experience' },
//   { type: 'row', sections: [
//     { type: 'projects' },
//     [{ type: 'work_samples' }, { type: 'publications' }, { type: 'leadership' }]
//   ]}
// ];

// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' }, // Shorten this significantly
//   { type: 'technical_expertise', width: 'full', columns: 2 }, // Not 4
//   { type: 'experience', keepTogether: false },
//   { type: 'projects', width: 'full' }, // Full width, not columns
//   { type: 'row', sections: [
//     { type: 'education' },
//     { type: 'publications' }
//   ]},
//   { type: 'work_samples', width: 'full' }, // More prominent
//   { type: 'leadership' }
// ];

// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' },  // Now only 3-4 lines
//   { type: 'technical_expertise', width: 'full', columns: 3 },  // No context lines
//   { type: 'experience', keepTogether: false },
  
//   // Page 2/3: Projects prominent
//   { type: 'projects', width: 'full', keepTogether: false },
  
//   // Supporting sections in compact grid
//   { type: 'row', sections: [
//     [
//       { type: 'education' },
//       { type: 'publications' }
//     ],
//     { type: 'work_samples' }
//   ]},
  
//   // Only if space remains
//   // { type: 'leadership' }  // Consider removing entirely
// ];

// LAYOUT_CONFIG.sections = [
//   { type: 'header' },
//   { type: 'summary' },
  
//   // Page 1: Skills + Proof of work side-by-side
//   { type: 'technical_expertise', width: 'full', columns: 2 },
//   { type: 'work_samples', width: 'full', columns: 2 }, 
//   { type: 'experience', keepTogether: false },
//   // Page 3: Credentials
//   { type: 'row', sections: [
//     { type: 'education' },
//     { type: 'publications' }
//   ]},
  
//   { type: 'projects', width: 'full', keepTogether: false },
  
  
// ];

LAYOUT_CONFIG.sections = [
  { type: 'header' },
  // { type: 'summary' },
  
  // Page 1: Skills + Proof of work side-by-side
  { type: 'technical_expertise', width: 'full', columns: 2 },
  { type: 'experience', keepTogether: false },
  // Page 3: Credentials
  { type: 'row', sections: [
    { type: 'education' },
    { type: 'publications' }
  ]},
  // { type: 'row', sections: [
  //   { type: 'work_samples' },
  //   { type: 'leadership' }
  // ]},
  { type: 'work_samples', width: 'full', columns: 2 }, 
  { type: 'projects', width: 'full', keepTogether: false },
  
  
];

// ============================================================================
// END OF CONFIGURATION
// ============================================================================
// Don't modify below this line unless you need to change styling or logic
// ============================================================================

// HTML/CSS generation
function generateHTML(data, config) {
  const styles = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1a1a1a; background: #fff; line-height: 1.4;
      max-width: 8.5in; margin: 0 auto; padding: 0.35in; font-size: 10pt;
    }
    .header { border-bottom: 2px solid #0d3775; padding-bottom: 8px; margin-bottom: 12px; }
    .name { font-size: 20pt; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 2px; }
    .tagline { font-size: 10.5pt; color: #0d3775; font-weight: 600; margin-bottom: 3px; }
    .contact { display: flex; flex-wrap: wrap; align-items: center; font-size: 9pt; color: #444; gap: 0 12px; }
    .contact a { color: #0d3775; text-decoration: none; }
    .contact span { white-space: nowrap; }
    .contact span:not(:last-child)::after { content: "•"; color: #999; margin-left: 12px; }
    .summary { font-size: 10pt; color: #333; line-height: 1.45; margin-bottom: 12px; }
    
    .section { margin-bottom: 10px; break-inside: avoid; }
    .section.allow-break { break-inside: auto; }
    .row { display: grid; gap: 16px; margin-bottom: -5px; align-items: start; }
    .row.cols-2 { grid-template-columns: 1fr 1fr; }
    .row.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
    .column-group { display: flex; flex-direction: column; gap: 10px; }
    
    .title { font-size: 11pt; font-weight: 700; letter-spacing: 0.3px; text-transform: uppercase;
             color: #0d3775; border-bottom: 1px solid #d0d5dd; padding-bottom: 2px; margin-bottom: 6px; }
    
    .expertise-grid { display: grid; gap: 8px; }
    .expertise-grid.cols-1 { grid-template-columns: 1fr; }
    .expertise-grid.cols-2 { grid-template-columns: 1fr 1fr; }
    .expertise-grid.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
    .expertise-grid.cols-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }

    .projects-grid { display: grid; } /* The 'gap' property is removed */
    .projects-grid.cols-1 { grid-template-columns: 1fr; }
    .projects-grid.cols-2 { grid-template-columns: 1fr 1fr; gap: 8px; } /* Gap is kept for horizontal spacing in multi-column layouts */
    .projects-grid.cols-3 { grid-template-columns: 1fr 1fr 1fr; gap: 8px; }

    .expertise-area { padding: 6px 8px; background: #f8f9fb; border: 0.5px solid #e0e5eb;
                     border-left: 2px solid #0d3775; border-radius: 5px; }
    .expertise-title { font-weight: 700; font-size: 8.5pt; color: #0d3775; margin-bottom: 2px; }
    .expertise-items { font-size: 8.5pt; color: #333; line-height: 1.3; }
    .expertise-context { font-size: 7.5pt; color: #666; font-style: italic; margin-top: 1px; }
    
    // .xp, .proj { margin-bottom: 8px; padding: 6px 8px; border: 0.5px solid #e0e5eb;
    //             border-left: 2px solid #0d3775; background: #fafbfc; border-radius: 5px; break-inside: avoid; }
    .xp, .proj { margin-bottom: 6px; padding: 6px 8px; border: 0.5px solid #e0e5eb;
                background: #fafbfc; border-radius: 5px; break-inside: avoid; }
    .xp-head, .proj-head { display: flex; justify-content: space-between; align-items: baseline;
                          flex-wrap: wrap; gap: 4px 10px; margin-bottom: 3px; }
    .xp-role, .proj-name { font-weight: 700; font-size: 10pt; color: #0d3775; }
    .xp-company { font-size: 10pt; color: #0d3775; font-weight: 700; }
    .xp-dates { font-size: 8.5pt; color: #666; white-space: nowrap; margin-left: auto; }
    .bullets { margin: 3px 0 3px 16px; font-size: 9.5pt; line-height: 1.35; color: #444; }
    .bullets li { margin-bottom: 2px; }
    .proj-sections { font-size: 9pt; line-height: 1.35; margin: 3px 0; }
    .proj-section { margin-bottom: 2px; }
    .proj-section-title { font-weight: 600; color: #0d3775; }

    /* --- MODIFICATION START: New styles for bulleted projects --- */
    .proj-subhead { display: flex; justify-content: space-between; flex-wrap: wrap;
                    font-size: 8.5pt; color: #444; font-weight: 600; margin-bottom: 4px; gap: 4px 10px; }
    .proj-link { margin-top: 4px; font-size: 8pt; }
    .proj-link a { color: #0d3775; text-decoration: none; }
    /* --- MODIFICATION END --- */
    
    .skill-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
    .skill-tag { padding: 1px 6px; border-radius: 10px; font-size: 7.5pt; background: #e8f0fe;
                color: #1967d2; white-space: nowrap; }
    .skill-tag-proven { background: #e6f4ea; color: #137333; }
    
    .samples-grid { display: grid; gap: 8px; }
    .samples-grid.cols-1 { grid-template-columns: 1fr; }
    .samples-grid.cols-2 { grid-template-columns: 1fr 1fr; }
    .samples-grid.cols-3 { grid-template-columns: 1fr 1fr 1fr; }
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
  `;
  
  let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${data.contact.name} Resume</title>
  <style>${styles}</style>
</head>
<body>`;

  for (const section of config.sections) {
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
        ${data.contact.scholar ? `<span><a href="https://${data.contact.scholar}">Scholar</a></span>` : ''}
        ${data.contact.portfolio ? `<span><a href="https://${data.contact.portfolio}">Portfolio</a></span>` : ''}
      </div>
    </header>`;
  }
  
  if (section.type === 'summary') {
    return `<div class="summary">${data.professional_summary}</div>`; 
  }
  
  if (section.type === 'technical_expertise') {
    const cols = section.columns || 3;
    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
      <div class="title">Technical Expertise</div>
      <div class="expertise-grid cols-${cols}">`;
    for (const [key, value] of Object.entries(data.technical_expertise)) {
      html += `<div class="expertise-area">
        <div class="expertise-title">${key}</div>
        <div class="expertise-items">${value.skills}</div>
        ${value.context ? `<div class="expertise-context">${value.context}</div>` : ''}
      </div>`;
    }
    html += `</div></div>`;
    return html;
  }

  if (section.type === 'experience') {
    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
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
      </div>`;
    }
    html += `</div>`;
    return html;
  }
  
  // if (section.type === 'experience') {
  //   const breakClass = section.keepTogether === false ? 'allow-break' : '';
  //   let html = `<div class="section ${breakClass}">
  //     <div class="title">Professional Experience</div>`;
  //   for (const exp of data.experience) {
  //     html += `<div class="xp">
  //       <div class="xp-head">
  //         <div><span class="xp-role">${exp.title}</span> <span class="xp-company">@ ${exp.company}</span></div>
  //         <span class="xp-dates">${exp.dates}</span>
  //       </div>
  //       <ul class="bullets">
  //         ${exp.highlights.map(h => `<li>${h}</li>`).join('')}
  //       </ul>
  //       ${exp.demonstrated_skills ? `<div class="skill-tags">${exp.demonstrated_skills.map(s => `<span class="skill-tag skill-tag-proven">${s}</span>`).join('')}</div>` : ''}
  //     </div>`;
  //   }
  //   html += `</div>`;
  //   return html;
  // }
  
  if (section.type === 'projects') {
  const projects = data.projects_all || [];
  const startFrom = section.startFrom || 0;
  const count = section.count || projects.length - startFrom;
  const subset = projects.slice(startFrom, startFrom + count);
  if (subset.length === 0) return '';
  const cols = section.columns || 1;
  const breakClass = section.keepTogether === false ? '' : 'avoid-break';
  
  let html = `<div class="section ${breakClass}">
    <div class="title">${startFrom > 0 ? 'Projects (continued)' : 'Projects'}</div>
    <div class="projects-grid cols-${cols}">`;
  
  for (const proj of subset) {
    const skillsHTML = (proj.demonstrated_skills && proj.demonstrated_skills.length > 0)
      ? `<div class="skill-tags">${proj.demonstrated_skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>`
      : '';
    
    const urlHTML = proj.url
      ? `<div class="proj-link"><a href="https://${proj.url.replace(/^https?:\/\//, '')}">${proj.url.replace(/^https?:\/\//, '')}</a></div>`
      : '';
    
    if (proj.project_type === 'condensed') {
      // Render condensed impact format with Problem/Solution/Impact
      const sectionsHTML = proj.sections && proj.sections.length > 0
        ? proj.sections.map(s => 
            `<div class="proj-section">
              <span class="proj-section-title">${s.title}:</span> ${s.content}
            </div>`
          ).join('')
        : '';
      
      html += `<div class="proj">
        <div class="proj-head"><div class="proj-name">${proj.title}</div></div>
        ${(proj.org_context || proj.dates) ? `
          <div class="proj-subhead">
            ${proj.org_context ? `<span>${proj.org_context}</span>` : ''}
            ${proj.dates ? `<span>${proj.dates}</span>` : ''}
          </div>` : ''}
        ${sectionsHTML ? `<div class="proj-sections">${sectionsHTML}</div>` : ''}
        ${skillsHTML}
        ${urlHTML}
      </div>`;
    } else if (proj.project_type === 'bulleted') {
      // Render bulleted project card
      html += `<div class="proj">
        <div class="proj-head"><div class="proj-name">${proj.title}</div></div>
        ${(proj.org_context || proj.dates) ? `
          <div class="proj-subhead">
            ${proj.org_context ? `<span>${proj.org_context}</span>` : ''}
            ${proj.dates ? `<span>${proj.dates}</span>` : ''}
          </div>` : ''}
        ${proj.achievements && proj.achievements.length > 0 ? `
          <ul class="bullets">
            ${proj.achievements.map(a => `<li>${a}</li>`).join('')}
          </ul>` : ''}
        ${skillsHTML}
        ${urlHTML}
      </div>`;
    } else {
      // Render original/impact project card (fallback)
      html += `<div class="proj">
        <div class="proj-head"><div class="proj-name">${proj.title}</div></div>
        ${proj.description ? `<div style="font-size: 8.5pt; color: #555; margin-bottom: 2px;">${proj.description}</div>` : ''}
        ${proj.sections && proj.sections.length > 0 ? `<div class="proj-sections">${proj.sections.map(s => `<div class="proj-section"><span class="proj-section-title">${s.title}:</span> ${s.content}</div>`).join('')}</div>` : ''}
        ${skillsHTML}
        ${urlHTML}
      </div>`;
    }
  }
  html += `</div></div>`;
  return html;
}
  
  if (section.type === 'education') {
    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
      <div class="title">Education</div>`;
    for (const edu of data.education) {
      html += `<div class="edu">
        <div style="display: flex; justify-content: space-between;">
          <span class="edu-degree">${edu.degree}</span>
          <span class="edu-dates">${edu.graduation}</span>
        </div>
        <div class="edu-inst">${edu.institution}</div>
        ${edu.note ? `<div style="font-size: 8.5pt; color: #666;">${edu.note}</div>` : ''}
        ${edu.gpa ? `<div style="font-size: 8.5pt; color: #666;">GPA: ${edu.gpa}</div>` : ''}
        ${edu.honors ? `<div style="font-size: 8.5pt; color: #666;">Honors: ${edu.honors}</div>` : ''}
      </div>`;
    }
    html += `</div>`;
    return html;
  }
  
  if (section.type === 'publications') {
    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
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
    // AI Safety & Evaluation Research OR Work Samples
    const cols = section.columns || 1;
    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
      <div class="title">AI Safety & Evaluation Research</div>
      <div class="samples-grid cols-${cols}">`;
    for (const sample of data.work_samples) {
      // Safely create the link HTML only if a URL exists
      let linkHTML = '';
      if (sample.url) {
        const fullUrl = sample.url.startsWith('http') ? sample.url : `https://${sample.url}`;
        const displayUrl = sample.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
        linkHTML = `<div class="sample-link"><a href="${fullUrl}">${displayUrl}</a></div>`;
      }
      let linkHTML2 = '';
      if (sample.demo_url) {
        const fullDemoUrl = sample.demo_url.startsWith('http') ? sample.demo_url : `https://${sample.demo_url}`;
        const displayUrl2 = sample.demo_url.replace(/^https?:\/\//, '').replace(/\/$/, '');
        linkHTML2 = `<div class="sample-link"><a href="${fullDemoUrl}">${displayUrl2}</a></div>`;
      }

      html += `<div class="sample-card">
        <div class="sample-type">${sample.type}</div>
        <div class="sample-title">${sample.title}</div>
        <div class="sample-desc">${sample.description}</div>
        ${linkHTML}
        ${linkHTML2}
      </div>`;
    }
    html += `</div></div>`;
    return html;
  }
  
  if (section.type === 'leadership') {
    // Prioritize 'leadership_mentoring' but fall back to 'achievements' for compatibility.
    const items = data.leadership_mentoring || data.achievements || []; 
    if (items.length === 0) return ''; // Don't render if the section would be empty.

    // Determine the title based on which data source was found and used.
    const title = data.leadership_mentoring ? "Leadership & Mentoring" : "Achievements";

    const breakClass = section.keepTogether === false ? 'allow-break' : '';
    let html = `<div class="section ${breakClass}">
      <div class="title">${title}</div>
      <ul class="list">`;
    for (const item of items) {
      html += `<li>${item}</li>`;
    }
    html += `</ul></div>`;
    return html;
  }
  
  if (section.type === 'row') {
    const numCols = section.sections.length;
    let html = `<div class="row cols-${numCols}">`;
    for (const subsection of section.sections) {
      if (Array.isArray(subsection)) {
        html += `<div class="column-group">`;
        for (const item of subsection) {
          html += renderSection(item, data);
        }
        html += `</div>`;
      } else {
        html += renderSection(subsection, data);
      }
    }
    html += `</div>`;
    return html;
  }
  
  return '';
}

// PDF generation
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
      
      return { totalPages, whitespacePercent: parseFloat(whitespacePercent) };
    });
    
    await page.pdf({
      path: outputPath,
      format: 'Letter',
      printBackground: true,
      margin: { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' }
    });
    
    return metrics;
  } finally {
    await browser.close();
  }
}

// File utilities
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

function openFile(filePath) {
  const command = process.platform === 'win32' ? 'start ""' :
                  process.platform === 'darwin' ? 'open' : 'xdg-open';
  exec(`${command} "${filePath}"`);
}

// Main
async function main() {
  console.log('Flexible Resume Generator\n');
  
  const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);
  if (!targetDir) {
    console.error('No application folders found');
    return;
  }
  
  console.log(`Using: ${path.basename(targetDir)}`);
  
  const dataPath = await findFileByPattern(targetDir, /^resume.*\.json$/, 'JSON');
  if (!dataPath) return;
  
  const data = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
  
  // Preprocess experience data
  if (data.experience) {
    data.experience = data.experience.map(exp => ({
      ...exp,
      demonstrated_skills: exp.demonstrated_skills || (exp.technologies ? exp.technologies.slice(0, 4) : [])
    }));
  }
  
  // --- MODIFICATION START: Preprocess all project types into a single list ---
  const allProjects = [];

  // Process impact-style projects (includes backward compatibility for 'projects' and 'selected_projects')
  const impactSources = ['projects', 'selected_projects', 'impact_projects'];
  for (const key of impactSources) {
      if (Array.isArray(data[key])) {
          for (const p of data[key]) {
              const sections = [];
              if (p.role) sections.push({ title: 'Role', content: p.role });
              if (p.challenge) sections.push({ title: 'Challenge', content: p.challenge });
              if (p.approach) sections.push({ title: 'Approach', content: p.approach });
              if (p.impact) sections.push({ title: 'Impact', content: p.impact });
              if (p.outcome) sections.push({ title: 'Outcome', content: p.outcome });
              
              allProjects.push({
                  ...p,
                  project_type: 'impact', // Add type flag
                  title: p.title || p.name, // Normalize title field
                  sections: sections,
                  demonstrated_skills: p.demonstrated_skills || p.technologies || []
              });
          }
      }
  }

  // Process bulleted-style projects
  if (Array.isArray(data.bulleted_projects)) {
      for (const p of data.bulleted_projects) {
          const achievements = [];
          // Dynamically collect all 'achievement#' fields
          for (let i = 1; i < 10; i++) {
              if (p[`achievement${i}`]) {
                  achievements.push(p[`achievement${i}`]);
              } else {
                  break; // Stop when the sequence is broken
              }
          }
          allProjects.push({
              ...p,
              project_type: 'bulleted', // Add type flag
              title: p.title || p.name, // Normalize title field
              achievements: achievements, // Store collected achievements
              demonstrated_skills: p.technologies || [] // Normalize skills field
          });
      }
  }

  data.projects_all = allProjects;
  // --- MODIFICATION END ---
  
  console.log('Generating PDF...');
  const html = generateHTML(data, LAYOUT_CONFIG);
  
  // Create the filename based on the format: YYYYMMDD_FirstTagline_KKrenek.pdf
  const today = new Date();
  const dateStamp = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
  
  // Safely get the first tagline item and format it (e.g., "Machine Learning Engineer" -> "MachineLearningEngineer")
  let taglineForFilename = 'Resume'; // Default fallback
  if (data.contact && data.contact.tagline) {
      const firstTagline = Array.isArray(data.contact.tagline) ? data.contact.tagline[0] : String(data.contact.tagline);
      taglineForFilename = firstTagline.split('|')[0].trim().replace(/\s+/g, '');
  }
  taglineForFilename = taglineForFilename.replace(/\//g, "");
  
  const outputPath = path.join(targetDir, `${dateStamp}_${taglineForFilename}_KKrenek.pdf`);
  
  const metrics = await generatePDF(html, outputPath);
  
  console.log(`\n✓ Generated: ${path.basename(outputPath)}`);
  console.log(`  Pages: ${metrics.totalPages}`);
  console.log(`  Whitespace: ${metrics.whitespacePercent}%`);
  
  openFile(outputPath);
}

main().catch(err => {
  console.error(`\nError: ${err.message}`);
  process.exit(1);
});
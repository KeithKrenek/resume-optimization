// Automatic Layout Optimizer
// Generates multiple layout variations and compares them visually
// Usage: node generate-with-layout-options.js

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

const BASE_APPLICATIONS_DIR = "C:/Users/keith/Dropbox/Resume";

// Define layout variations to try
// Each layout specifies how to arrange sections on pages 3+
const LAYOUT_VARIANTS = {
  'current': {
    description: 'Current layout (projects left, samples+pubs right)',
    page3_4: {
      leftCol: ['projects_all'],  // All projects in left column
      rightCol: ['work_samples', 'publications']
    },
    page4: {
      leftCol: [],
      rightCol: ['education', 'leadership_mentoring']
    }
  },
  
  'balanced-split': {
    description: 'Split projects across pages, balance columns',
    page3: {
      leftCol: ['projects_all:0-1'],  // First 2 projects
      rightCol: ['work_samples', 'publications']
    },
    page4: {
      leftCol: ['projects_all:2', 'leadership_mentoring'],  // 3rd project + leadership
      rightCol: ['education']
    }
  },
  
  'compact-projects': {
    description: 'All projects together, tight layout below',
    page3: {
      leftCol: ['projects_all'],  // All 3 projects
      rightCol: ['work_samples']
    },
    page4: {
      leftCol: ['publications', 'leadership_mentoring'],
      rightCol: ['education']
    }
  },
  
  'full-width-samples': {
    description: 'Work samples full width, everything else balanced',
    page3: {
      fullWidth: ['work_samples'],
      leftCol: ['projects_all:0-1'],
      rightCol: ['publications', 'education']
    },
    page4: {
      leftCol: ['projects_all:2'],
      rightCol: ['leadership_mentoring']
    }
  },
  
  'education-first': {
    description: 'Education prominent on page 3',
    page3: {
      leftCol: ['projects_all:0-1', 'education'],
      rightCol: ['work_samples', 'publications']
    },
    page4: {
      leftCol: ['projects_all:2'],
      rightCol: ['leadership_mentoring']
    }
  }
};

// Handlebars helpers
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

handlebars.registerHelper('eq', function(a, b) {
  return a === b;
});

// Parse slice notation (e.g., "projects_all:0-1" means items 0 and 1)
function sliceData(data, spec) {
  if (!spec.includes(':')) {
    return data[spec];
  }
  
  const [key, range] = spec.split(':');
  const items = data[key];
  if (!Array.isArray(items)) return items;
  
  if (range.includes('-')) {
    const [start, end] = range.split('-').map(Number);
    return items.slice(start, end + 1);
  } else {
    return [items[Number(range)]];
  }
}

// Apply layout configuration to data
function applyLayoutConfig(baseData, layoutConfig) {
  const data = JSON.parse(JSON.stringify(baseData)); // Deep clone
  
  // Add layout metadata
  data._layoutConfig = layoutConfig;
  
  // Process page 3
  if (layoutConfig.page3) {
    data._page3 = {
      fullWidth: layoutConfig.page3.fullWidth?.map(spec => ({
        key: spec.split(':')[0],
        data: sliceData(data, spec)
      })) || [],
      leftCol: layoutConfig.page3.leftCol?.map(spec => ({
        key: spec.split(':')[0],
        data: sliceData(data, spec)
      })) || [],
      rightCol: layoutConfig.page3.rightCol?.map(spec => ({
        key: spec.split(':')[0],
        data: sliceData(data, spec)
      })) || []
    };
  }
  
  // Process page 4
  if (layoutConfig.page4) {
    data._page4 = {
      leftCol: layoutConfig.page4.leftCol?.map(spec => ({
        key: spec.split(':')[0],
        data: sliceData(data, spec)
      })) || [],
      rightCol: layoutConfig.page4.rightCol?.map(spec => ({
        key: spec.split(':')[0],
        data: sliceData(data, spec)
      })) || []
    };
  }
  
  return data;
}

// Measure whitespace and get metrics
async function measureLayout(page) {
  return await page.evaluate(() => {
    const pageHeight = 11 * 96; // Letter page height in pixels at 96 DPI
    const pageWidth = 8.5 * 96;
    
    // Get all major sections
    const sections = Array.from(document.querySelectorAll('.section, .xp, .proj, .edu, .pub'));
    
    let totalContentHeight = 0;
    let pageBreaks = 0;
    const pageDistribution = {};
    
    sections.forEach(section => {
      const rect = section.getBoundingClientRect();
      const pageNum = Math.floor(rect.top / pageHeight) + 1;
      
      totalContentHeight += rect.height;
      
      if (!pageDistribution[pageNum]) {
        pageDistribution[pageNum] = { height: 0, sections: 0 };
      }
      pageDistribution[pageNum].height += rect.height;
      pageDistribution[pageNum].sections++;
      
      // Check if section crosses page boundary
      const pageBottom = pageNum * pageHeight;
      if (rect.bottom > pageBottom && rect.top < pageBottom - 50) {
        pageBreaks++;
      }
    });
    
    const totalPages = Math.ceil(
      Math.max(...sections.map(s => s.getBoundingClientRect().bottom)) / pageHeight
    );
    
    const totalAvailableHeight = totalPages * pageHeight * 0.85; // 85% usable (margins)
    const whitespacePercent = ((totalAvailableHeight - totalContentHeight) / totalAvailableHeight * 100).toFixed(1);
    
    // Calculate column balance on last page
    const lastPageNum = totalPages;
    const lastPageSections = sections.filter(s => {
      const rect = s.getBoundingClientRect();
      const pageNum = Math.floor(rect.top / pageHeight) + 1;
      return pageNum === lastPageNum;
    });
    
    const leftColHeight = lastPageSections
      .filter(s => s.getBoundingClientRect().left < pageWidth / 2)
      .reduce((sum, s) => sum + s.getBoundingClientRect().height, 0);
    
    const rightColHeight = lastPageSections
      .filter(s => s.getBoundingClientRect().left >= pageWidth / 2)
      .reduce((sum, s) => sum + s.getBoundingClientRect().height, 0);
    
    const columnImbalance = Math.abs(leftColHeight - rightColHeight).toFixed(0);
    
    return {
      totalPages,
      whitespacePercent: parseFloat(whitespacePercent),
      pageBreaks,
      columnImbalance: parseFloat(columnImbalance),
      pageDistribution,
      lastPageBalance: {
        left: leftColHeight.toFixed(0),
        right: rightColHeight.toFixed(0)
      }
    };
  });
}

// Generate PDF with layout
async function generateLayoutPDF(data, templatePath, outputPath, layoutName) {
  const tmplSrc = await fs.readFile(templatePath, 'utf-8');
  const template = handlebars.compile(tmplSrc);
  const html = template(data);
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: ['domcontentloaded', 'networkidle0'] });
    await page.evaluateHandle('document.fonts && document.fonts.ready');
    
    // Measure before generating PDF
    const metrics = await measureLayout(page);
    
    // Generate PDF
    await page.pdf({
      path: outputPath,
      format: 'Letter',
      printBackground: true,
      margin: { top: '0.35in', right: '0.35in', bottom: '0.35in', left: '0.35in' }
    });
    
    // Generate preview image
    const previewPath = outputPath.replace('.pdf', '-preview.png');
    await page.screenshot({ 
      path: previewPath, 
      fullPage: true,
      deviceScaleFactor: 1
    });
    
    return { metrics, previewPath };
  } finally {
    await browser.close();
  }
}

// Generate comparison HTML
async function generateComparisonPage(results, outputDir) {
  const companyName = path.basename(outputDir).split('_')[0];
  
  // Sort by quality score (lower whitespace + lower imbalance = better)
  const scored = results.map(r => ({
    ...r,
    score: r.metrics.whitespacePercent + (r.metrics.columnImbalance / 10)
  })).sort((a, b) => a.score - b.score);
  
  const bestLayout = scored[0].name;
  
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Resume Layout Comparison - ${companyName}</title>
  <style>
    * { box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f5f5f5;
      padding: 20px;
      margin: 0;
    }
    h1 { color: #0d3775; margin-bottom: 10px; }
    .subtitle { color: #666; margin-bottom: 30px; }
    .grid { 
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background: white;
      border: 3px solid #ddd;
      border-radius: 8px;
      padding: 20px;
      transition: all 0.2s;
      cursor: pointer;
      position: relative;
    }
    .card:hover {
      border-color: #0d3775;
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .card.best {
      border-color: #4caf50;
      background: #f1f8f4;
    }
    .best-badge {
      position: absolute;
      top: -12px;
      right: 20px;
      background: #4caf50;
      color: white;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: bold;
    }
    .layout-name {
      font-size: 20px;
      font-weight: bold;
      color: #0d3775;
      margin-bottom: 5px;
    }
    .layout-desc {
      font-size: 13px;
      color: #666;
      margin-bottom: 15px;
      font-style: italic;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin-bottom: 15px;
    }
    .metric {
      background: #f8f9fa;
      padding: 12px;
      border-radius: 6px;
      text-align: center;
    }
    .metric-label {
      font-size: 11px;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }
    .metric-value {
      font-size: 24px;
      font-weight: bold;
      color: #0d3775;
    }
    .metric-value.good { color: #4caf50; }
    .metric-value.warning { color: #ff9800; }
    .metric-value.bad { color: #f44336; }
    .preview {
      width: 100%;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-top: 10px;
    }
    .actions {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }
    .btn {
      flex: 1;
      padding: 10px;
      background: #0d3775;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: background 0.2s;
    }
    .btn:hover {
      background: #0a2855;
    }
    .btn-secondary {
      background: #6c757d;
    }
    .btn-secondary:hover {
      background: #545b62;
    }
    .summary {
      background: white;
      padding: 20px;
      border-radius: 8px;
      border-left: 4px solid #0d3775;
      margin-bottom: 30px;
    }
    .summary h2 {
      margin-top: 0;
      color: #0d3775;
    }
  </style>
</head>
<body>
  <h1>Resume Layout Comparison</h1>
  <p class="subtitle">Generated ${scored.length} layout variations. Click any card to open the full PDF.</p>
  
  <div class="summary">
    <h2>Recommendation</h2>
    <p><strong>${LAYOUT_VARIANTS[bestLayout].description}</strong> has the best balance of minimal whitespace (${scored[0].metrics.whitespacePercent}%) and column balance (${scored[0].metrics.columnImbalance}px difference).</p>
    <p>All layouts preserve 100% of your content. Choose based on visual preference and section flow.</p>
  </div>
  
  <div class="grid">
    ${scored.map((result, index) => {
      const isBest = index === 0;
      const whitespaceClass = result.metrics.whitespacePercent < 15 ? 'good' : 
                             result.metrics.whitespacePercent < 25 ? 'warning' : 'bad';
      const balanceClass = result.metrics.columnImbalance < 100 ? 'good' :
                          result.metrics.columnImbalance < 200 ? 'warning' : 'bad';
      
      return `
        <div class="card ${isBest ? 'best' : ''}" onclick="window.open('${result.path}')">
          ${isBest ? '<div class="best-badge">RECOMMENDED</div>' : ''}
          <div class="layout-name">${result.name}</div>
          <div class="layout-desc">${result.description}</div>
          
          <div class="metrics">
            <div class="metric">
              <div class="metric-label">Whitespace</div>
              <div class="metric-value ${whitespaceClass}">${result.metrics.whitespacePercent}%</div>
            </div>
            <div class="metric">
              <div class="metric-label">Column Balance</div>
              <div class="metric-value ${balanceClass}">${result.metrics.columnImbalance}px</div>
            </div>
            <div class="metric">
              <div class="metric-label">Total Pages</div>
              <div class="metric-value">${result.metrics.totalPages}</div>
            </div>
            <div class="metric">
              <div class="metric-label">Page Breaks</div>
              <div class="metric-value ${result.metrics.pageBreaks === 0 ? 'good' : 'warning'}">${result.metrics.pageBreaks}</div>
            </div>
          </div>
          
          <img src="${path.basename(result.previewPath)}" class="preview" alt="${result.name} preview">
          
          <div class="actions">
            <button class="btn" onclick="event.stopPropagation(); window.open('${result.path}')">
              Open PDF
            </button>
            <button class="btn btn-secondary" onclick="event.stopPropagation(); window.open('${result.previewPath}')">
              View Full Image
            </button>
          </div>
        </div>
      `;
    }).join('')}
  </div>
  
  <div class="summary">
    <h2>Next Steps</h2>
    <ol>
      <li>Review the layouts above and pick your favorite</li>
      <li>If none are perfect, note which comes closest</li>
      <li>We can create custom variations based on your preference</li>
    </ol>
  </div>
</body>
</html>`;
  
  const comparisonPath = path.join(outputDir, `${companyName}_Layout_Comparison.html`);
  await fs.writeFile(comparisonPath, html);
  return comparisonPath;
}

// Main execution
async function main() {
  console.log('Finding latest application folder...');
  const targetDir = await findLatestJobFolder(BASE_APPLICATIONS_DIR);
  
  if (!targetDir) {
    console.error('No application folders found');
    return;
  }
  
  console.log(`Using: ${path.basename(targetDir)}\n`);
  
  const dataPath = await findFileByPattern(targetDir, /^resume.*\.json$/, 'JSON');
  const templatePath = await findFileByPattern(targetDir, /resume-template.*\.html$/, 'template');
  
  if (!dataPath || !templatePath) {
    console.error('Missing required files');
    return;
  }
  
  const baseData = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
  const companyName = path.basename(targetDir).split('_')[0];
  const results = [];
  
  console.log(`Generating ${Object.keys(LAYOUT_VARIANTS).length} layout variations...\n`);
  
  for (const [name, config] of Object.entries(LAYOUT_VARIANTS)) {
    console.log(`  Generating: ${name}`);
    console.log(`    ${config.description}`);
    
    const layoutData = applyLayoutConfig(baseData, config);
    const outputPath = path.join(targetDir, `${companyName}_Resume_${name}.pdf`);
    
    const { metrics, previewPath } = await generateLayoutPDF(
      layoutData,
      templatePath,
      outputPath,
      name
    );
    
    console.log(`    ✓ Whitespace: ${metrics.whitespacePercent}% | Balance: ${metrics.columnImbalance}px\n`);
    
    results.push({
      name,
      description: config.description,
      path: outputPath,
      previewPath,
      metrics
    });
  }
  
  console.log('Creating comparison page...');
  const comparisonPath = await generateComparisonPage(results, targetDir);
  console.log(`\n✅ Done! Opening comparison page...\n`);
  
  // Open comparison page
  const command = process.platform === 'win32' ? 'start ""' :
                  process.platform === 'darwin' ? 'open' : 'xdg-open';
  exec(`${command} "${comparisonPath}"`);
}

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
// technical-excellence.generate.js
// Technical-focused resume generator emphasizing projects and skills
// Usage: node technical-excellence.generate.js

const puppeteer = require('puppeteer').default;
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
  dataFile: 'technical-excellence.resume.json',
  templateFile: 'technical-excellence.template.html',
  outputPdf: 'technical-excellence.resume.pdf',
  outputHtml: 'technical-excellence.resume.html',
  outputDocx: 'technical-excellence.resume.docx',
  generateScreenshot: true,
  verbose: true
};

// Register all required Handlebars helpers
function registerHelpers() {
  // Format list with custom separator
  handlebars.registerHelper('formatList', function(items, separator) {
    const sep = (typeof separator === 'string') ? separator : ', ';
    if (!Array.isArray(items) || items.length === 0) return '';
    return items.join(sep);
  });

  // Ensure URL has protocol
  handlebars.registerHelper('ensureProtocol', function(url) {
    if (!url) return '';
    const s = String(url).trim();
    if (s.match(/^https?:\/\//)) return s;
    if (s.includes('@')) return `mailto:${s}`;
    return `https://${s}`;
  });

  // Format date nicely
  handlebars.registerHelper('formatDate', function(dateString) {
    if (!dateString) return 'Present';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const [year, month, day] = dateString.split('-');
    if (month) {
      return `${months[parseInt(month) - 1]} ${year}`;
    }
    return year;
  });

  // Calculate years of experience
  handlebars.registerHelper('yearsExperience', function(startDate) {
    if (!startDate) return '0';
    const start = new Date(startDate);
    const now = new Date();
    const years = Math.floor((now - start) / (365.25 * 24 * 60 * 60 * 1000));
    return years.toString();
  });

  // Truncate text to specified length
  handlebars.registerHelper('truncate', function(text, length) {
    const maxLength = length || 100;
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  });
}

// Main generation function
async function generateResume() {
  const startTime = Date.now();
  
  try {
    if (CONFIG.verbose) {
      console.log('🚀 Technical Excellence Resume Generator v2.0');
      console.log('============================================\n');
    }
    
    // Register helpers
    registerHelpers();
    
    // Load data and template
    const dataPath = path.resolve(`./${CONFIG.dataFile}`);
    const templatePath = path.resolve(`./${CONFIG.templateFile}`);
    const outputPdfPath = path.resolve(`./${CONFIG.outputPdf}`);
    const outputHtmlPath = path.resolve(`./${CONFIG.outputHtml}`);
    
    console.log('📂 Loading resume data...');
    const resumeData = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
    
    // Enhance data with computed properties
    enhanceResumeData(resumeData);
    
    console.log('📄 Loading HTML template...');
    const templateSource = await fs.readFile(templatePath, 'utf-8');
    
    // Validate technical resume data
    validateTechnicalResume(resumeData);
    
    // Compile template
    console.log('🔨 Compiling template with Handlebars...');
    const template = handlebars.compile(templateSource);
    const html = template(resumeData);
    
    // Save HTML
    await fs.writeFile(outputHtmlPath, html, 'utf-8');
    console.log(`💾 HTML saved to: ${CONFIG.outputHtml}`);
    
    // Generate PDF with advanced options
    console.log('🖨️ Generating PDF with optimized settings...');
    const browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--font-render-hinting=max',
        '--enable-font-antialiasing'
      ]
    });
    
    const page = await browser.newPage();
    
    // Set high-quality viewport
    await page.setViewport({
      width: 1200,
      height: 1600,
      deviceScaleFactor: 2
    });
    
    // Inject custom fonts if needed
    await page.evaluateHandle(() => {
      const style = document.createElement('style');
      style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      `;
      document.head.appendChild(style);
    });
    
    // Load HTML content
    await page.setContent(html, {
      waitUntil: ['domcontentloaded', 'networkidle0']
    });
    
    // Wait for fonts (robust across Puppeteer versions)
    await page.evaluate(() => (document.fonts ? document.fonts.ready : Promise.resolve()));
    // Small extra delay to ensure final layout
    await new Promise((r) => setTimeout(r, 200));
    
    // Generate screenshot if requested
    if (CONFIG.generateScreenshot) {
      const screenshotPath = outputPdfPath.replace('.pdf', '.png');
      await page.screenshot({
        path: screenshotPath,
        fullPage: true,
        type: 'png'
      });
      console.log(`📸 Screenshot saved to: ${path.basename(screenshotPath)}`);
    }
    
    // Generate PDF with technical-friendly settings
    await page.pdf({
      path: outputPdfPath,
      format: 'Letter',
      printBackground: true,
      margin: {
        top: '0.3in',
        right: '0.3in',
        bottom: '0.3in',
        left: '0.3in'
      },
      displayHeaderFooter: false,
      preferCSSPageSize: false
    });
    
    await browser.close();
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`\n✅ PDF successfully generated: ${CONFIG.outputPdf}`);
    console.log(`⏱️ Total generation time: ${duration} seconds`);
    
    // Display technical resume features
    displayTechnicalFeatures(resumeData);
    
    // Perform technical analysis
    analyzeTechnicalResume(resumeData);
    
  } catch (error) {
    console.error('❌ Error generating resume:', error.message);
    if (CONFIG.verbose) {
      console.error('\nStack trace:', error.stack);
    }
    process.exit(1);
  }
}

// Enhance resume data with computed properties
function enhanceResumeData(data) {
  // Calculate total years of experience
  if (data.experience && data.experience.length > 0) {
    const firstJob = data.experience[data.experience.length - 1];
    if (firstJob.dates) {
      const match = firstJob.dates.match(/(\w+)\s+(\d{4})/);
      if (match) {
        const startYear = parseInt(match[2]);
        const currentYear = new Date().getFullYear();
        data.totalExperience = currentYear - startYear;
      }
    }
  }
  
  // Count total projects
  if (data.featured_projects) {
    data.projectCount = data.featured_projects.length;
  }
  
  // Count total skills
  let skillCount = 0;
  if (data.technical_proficiencies) {
    for (const category of Object.values(data.technical_proficiencies)) {
      if (category.items && Array.isArray(category.items)) {
        skillCount += category.items.length;
      }
    }
  }
  data.totalSkills = skillCount;
}

// Validate technical resume structure
function validateTechnicalResume(data) {
  console.log('\n🔍 Validating technical resume structure...');
  
  const issues = [];
  
  // Check for required sections
  if (!data.contact || !data.contact.name) {
    issues.push('Missing contact name');
  }
  
  if (!data.contact || !data.contact.email) {
    issues.push('Missing contact email');
  }
  
  if (!data.technical_proficiencies || Object.keys(data.technical_proficiencies).length === 0) {
    issues.push('No technical skills defined');
  }
  
  if (!data.featured_projects || data.featured_projects.length === 0) {
    issues.push('No featured projects (critical for technical resume)');
  }
  
  // Check project quality
  if (data.featured_projects) {
    data.featured_projects.forEach((project, index) => {
      if (!project.impact || project.impact.length === 0) {
        issues.push(`Project ${index + 1} missing impact metrics`);
      }
      if (!project.technologies || project.technologies.length === 0) {
        issues.push(`Project ${index + 1} missing technology stack`);
      }
    });
  }
  
  if (issues.length > 0) {
    console.log('   ⚠️ Issues found:');
    issues.forEach(issue => console.log(`      - ${issue}`));
  } else {
    console.log('   ✅ All validations passed');
  }
  
  return issues.length === 0;
}

// Display technical resume features
function displayTechnicalFeatures(data) {
  console.log('\n🎯 Technical Resume Features:');
  console.log('   ✓ Projects-first layout emphasizing hands-on experience');
  console.log('   ✓ Detailed technical proficiency matrix with skill levels');
  console.log('   ✓ Challenge-Solution-Impact format for projects');
  console.log('   ✓ Technology stack visualization with chips');
  console.log('   ✓ Open source contributions section');
  console.log('   ✓ Speaking engagements and community involvement');
  console.log('   ✓ GitHub links for portfolio verification');
}

// Analyze technical resume quality
function analyzeTechnicalResume(data) {
  console.log('\n📊 Technical Resume Analysis:');
  
  // Skills analysis
  let totalSkills = 0;
  let expertSkills = 0;
  
  if (data.technical_proficiencies) {
    for (const [category, details] of Object.entries(data.technical_proficiencies)) {
      if (details.items) {
        totalSkills += details.items.length;
        if (details.level === 'Expert') {
          expertSkills += details.items.length;
        }
      }
    }
  }
  
  console.log(`   • Technical Skills: ${totalSkills} total (${expertSkills} at expert level)`);
  
  // Projects analysis
  if (data.featured_projects) {
    let totalImpactMetrics = 0;
    let projectsWithGithub = 0;
    
    data.featured_projects.forEach(project => {
      if (project.impact) totalImpactMetrics += project.impact.length;
      if (project.github) projectsWithGithub++;
    });
    
    console.log(`   • Featured Projects: ${data.featured_projects.length}`);
    console.log(`   • Impact Metrics: ${totalImpactMetrics} total`);
    console.log(`   • Projects with GitHub: ${projectsWithGithub}/${data.featured_projects.length}`);
  }
  
  // Experience metrics
  if (data.experience) {
    let totalHighlights = 0;
    let quantifiedHighlights = 0;
    const quantifiers = /\d+[%$MKBk]?|\b(increased|decreased|reduced|improved)\b/i;
    
    data.experience.forEach(job => {
      if (job.highlights) {
        totalHighlights += job.highlights.length;
        job.highlights.forEach(highlight => {
          if (quantifiers.test(highlight)) {
            quantifiedHighlights++;
          }
        });
      }
    });
    
    const quantificationRate = totalHighlights > 0 
      ? Math.round((quantifiedHighlights / totalHighlights) * 100)
      : 0;
    
    console.log(`   • Work Experience: ${data.experience.length} positions`);
    console.log(`   • Quantification Rate: ${quantificationRate}% of achievements`);
  }
  
  // Open source contributions
  if (data.open_source) {
    console.log(`   • Open Source Contributions: ${data.open_source.length}`);
  }
  
  // Calculate technical depth score
  const techScore = calculateTechnicalScore(data);
  console.log(`\n🏆 Technical Depth Score: ${techScore}/100`);
  
  if (techScore >= 85) {
    console.log('   ⭐ Exceptional technical resume!');
  } else if (techScore >= 70) {
    console.log('   ✅ Strong technical resume');
  } else if (techScore >= 50) {
    console.log('   ⚠️ Good foundation, consider adding more technical depth');
  } else {
    console.log('   ❌ Needs significant technical content improvement');
  }
}

// Calculate technical depth score
function calculateTechnicalScore(data) {
  let score = 0;
  
  // Technical skills (25 points)
  if (data.technical_proficiencies) {
    const categories = Object.keys(data.technical_proficiencies).length;
    score += Math.min(categories * 5, 25);
  }
  
  // Featured projects (30 points)
  if (data.featured_projects) {
    const projectScore = Math.min(data.featured_projects.length * 7, 21);
    const impactScore = data.featured_projects.some(p => p.impact) ? 9 : 0;
    score += projectScore + impactScore;
  }
  
  // Open source (15 points)
  if (data.open_source && data.open_source.length > 0) {
    score += Math.min(data.open_source.length * 5, 15);
  }
  
  // Certifications (10 points)
  if (data.certifications && data.certifications.length > 0) {
    score += Math.min(data.certifications.length * 5, 10);
  }
  
  // Speaking/Community (10 points)
  if (data.speaking && data.speaking.length > 0) {
    score += Math.min(data.speaking.length * 3, 10);
  }
  
  // Quantified achievements (10 points)
  if (data.experience) {
    const hasMetrics = data.experience.some(job => 
      job.highlights && job.highlights.some(h => /\d+[%$MKk]/.test(h))
    );
    if (hasMetrics) score += 10;
  }
  
  return Math.min(score, 100);
}

// Run the generator
if (require.main === module) {
  generateResume();
}

module.exports = { 
  generateResume, 
  validateTechnicalResume, 
  calculateTechnicalScore,
  enhanceResumeData 
};
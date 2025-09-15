// ats-maximum.generate.js
// ATS-optimized resume generator with maximum compatibility
// Usage: node ats-maximum.generate.js

const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

// Register Handlebars helpers
handlebars.registerHelper('formatList', function(items, separator) {
  const sep = (typeof separator === 'string') ? separator : ', ';
  if (!Array.isArray(items) || items.length === 0) return '';
  return items.join(sep);
});

handlebars.registerHelper('ensureProtocol', function(url) {
  if (!url) return '';
  const s = String(url).trim();
  if (s.match(/^https?:\/\//)) return s;
  if (s.includes('@')) return `mailto:${s}`;
  return `https://${s}`;
});

// Main generation function
async function generateResume() {
  try {
    console.log('🔄 Starting ATS-Maximum resume generation...');
    
    // Load data and template
    const dataPath = path.resolve('./ats-maximum.resume.json');
    const templatePath = path.resolve('./ats-maximum.template.html');
    const outputPath = path.resolve('./ats-maximum.resume.pdf');
    
    console.log('📂 Loading resume data...');
    const resumeData = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
    
    console.log('📄 Loading HTML template...');
    const templateSource = await fs.readFile(templatePath, 'utf-8');
    
    // Compile template with data
    console.log('🔨 Compiling template...');
    const template = handlebars.compile(templateSource);
    const html = template(resumeData);
    
    // Save intermediate HTML for debugging
    const htmlPath = path.resolve('./ats-maximum.resume.html');
    await fs.writeFile(htmlPath, html, 'utf-8');
    console.log(`💾 Intermediate HTML saved to: ${htmlPath}`);
    
    // Generate PDF
    console.log('🖨️ Generating PDF...');
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Set viewport for Letter size
    await page.setViewport({
      width: 1200,
      height: 1600,
      deviceScaleFactor: 2
    });
    
    // Load HTML content
    await page.setContent(html, {
      waitUntil: ['domcontentloaded', 'networkidle0']
    });
    
    // Wait for fonts to load
    await page.evaluateHandle('document.fonts.ready');
    
    // Generate PDF with ATS-friendly settings
    await page.pdf({
      path: outputPath,
      format: 'Letter',
      printBackground: false, // ATS-friendly: no background colors
      margin: {
        top: '0.5in',
        right: '0.5in',
        bottom: '0.5in',
        left: '0.5in'
      }
    });
    
    await browser.close();
    
    console.log(`✅ PDF successfully generated: ${outputPath}`);
    console.log('📊 ATS Optimization Features:');
    console.log('   - Single column layout');
    console.log('   - Standard section headers');
    console.log('   - No graphics or tables');
    console.log('   - Black text on white background');
    console.log('   - Standard fonts (Arial)');
    console.log('   - Simple bullet points');
    
    // Validate ATS compatibility
    validateATSCompatibility(resumeData);
    
  } catch (error) {
    console.error('❌ Error generating resume:', error);
    process.exit(1);
  }
}

// ATS compatibility validator
function validateATSCompatibility(data) {
  console.log('\n🔍 ATS Compatibility Check:');
  
  const checks = {
    'Contact Information': !!data.contact && !!data.contact.email && !!data.contact.phone,
    'Professional Summary': !!data.professional_summary && data.professional_summary.length > 50,
    'Skills Section': !!data.core_skills && Object.keys(data.core_skills).length > 0,
    'Work Experience': !!data.experience && data.experience.length > 0,
    'Education': !!data.education && data.education.length > 0,
    'Quantified Achievements': checkQuantifiedAchievements(data.experience),
    'Keywords Present': checkKeywords(data)
  };
  
  let passCount = 0;
  for (const [check, passed] of Object.entries(checks)) {
    console.log(`   ${passed ? '✅' : '⚠️'} ${check}`);
    if (passed) passCount++;
  }
  
  const score = Math.round((passCount / Object.keys(checks).length) * 100);
  console.log(`\n📈 ATS Compatibility Score: ${score}%`);
  
  if (score < 80) {
    console.log('⚠️ Warning: Consider improving ATS compatibility');
  }
}

// Check for quantified achievements
function checkQuantifiedAchievements(experience) {
  if (!experience || experience.length === 0) return false;
  
  const quantifiers = /\d+[%$MKk]?|\b(increased|decreased|reduced|improved|saved|generated)\b/i;
  let quantifiedCount = 0;
  let totalHighlights = 0;
  
  for (const job of experience) {
    if (job.highlights) {
      for (const highlight of job.highlights) {
        totalHighlights++;
        if (quantifiers.test(highlight)) {
          quantifiedCount++;
        }
      }
    }
  }
  
  return totalHighlights > 0 && (quantifiedCount / totalHighlights) > 0.5;
}

// Check for relevant keywords
function checkKeywords(data) {
  const commonKeywords = [
    'Python', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
    'Machine Learning', 'Data Analysis', 'Project Management',
    'Agile', 'Git', 'REST API', 'Database', 'Cloud'
  ];
  
  const resumeText = JSON.stringify(data).toLowerCase();
  let keywordCount = 0;
  
  for (const keyword of commonKeywords) {
    if (resumeText.includes(keyword.toLowerCase())) {
      keywordCount++;
    }
  }
  
  return keywordCount >= 5;
}

// Run the generator
if (require.main === module) {
  generateResume();
}

module.exports = { generateResume };
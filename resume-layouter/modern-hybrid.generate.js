// modern-hybrid.generate.js
// Modern hybrid resume generator with visual appeal and ATS compatibility
// Usage: node modern-hybrid.generate.js

const puppeteer = require('puppeteer').default;
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
  dataFile: 'modern-hybrid.resume.json',
  templateFile: 'modern-hybrid.template.html',
  outputPdf: 'modern-hybrid.resume.pdf',
  outputHtml: 'modern-hybrid.resume.html',
  debugMode: true
};

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

handlebars.registerHelper('formatDate', function(dateString) {
  if (!dateString) return 'Present';
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const [year, month] = dateString.split('-');
  if (month) {
    return `${months[parseInt(month) - 1]} ${year}`;
  }
  return year;
});

// Main generation function
async function generateResume() {
  const startTime = Date.now();
  
  try {
    console.log('🎨 Starting Modern Hybrid resume generation...\n');
    
    // Load data and template
    const dataPath = path.resolve(`./${CONFIG.dataFile}`);
    const templatePath = path.resolve(`./${CONFIG.templateFile}`);
    const outputPdfPath = path.resolve(`./${CONFIG.outputPdf}`);
    const outputHtmlPath = path.resolve(`./${CONFIG.outputHtml}`);
    
    console.log('📂 Loading resume data from:', CONFIG.dataFile);
    const resumeData = JSON.parse(await fs.readFile(dataPath, 'utf-8'));
    
    console.log('📄 Loading HTML template from:', CONFIG.templateFile);
    const templateSource = await fs.readFile(templatePath, 'utf-8');
    
    // Validate data
    validateResumeData(resumeData);
    
    // Compile template with data
    console.log('🔨 Compiling template with Handlebars...');
    const template = handlebars.compile(templateSource);
    const html = template(resumeData);
    
    // Save HTML if debug mode
    if (CONFIG.debugMode) {
      await fs.writeFile(outputHtmlPath, html, 'utf-8');
      console.log(`💾 Debug HTML saved to: ${CONFIG.outputHtml}`);
    }
    
    // Generate PDF
    console.log('🖨️ Generating PDF with Puppeteer...');
    const browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--font-render-hinting=none'
      ]
    });
    
    const page = await browser.newPage();
    
    // Set viewport for high quality rendering
    await page.setViewport({
      width: 1200,
      height: 1600,
      deviceScaleFactor: 2
    });
    
    // Load HTML with modern fonts
    await page.setContent(html, {
      waitUntil: ['domcontentloaded', 'networkidle0']
    });
    
    // Wait for fonts (robust across Puppeteer versions)
    await page.evaluate(() => (document.fonts ? document.fonts.ready : Promise.resolve()));
    // Small extra delay to ensure final layout
    await new Promise((r) => setTimeout(r, 200));
    
    // Generate PDF with hybrid-friendly settings
    await page.pdf({
      path: outputPdfPath,
      format: 'Letter',
      printBackground: true, // Include background colors for visual appeal
      margin: {
        top: '0.4in',
        right: '0.4in',
        bottom: '0.4in',
        left: '0.4in'
      },
      displayHeaderFooter: false,
      preferCSSPageSize: true
    });
    
    await browser.close();
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`\n✅ PDF successfully generated: ${CONFIG.outputPdf}`);
    console.log(`⏱️ Generation completed in ${duration} seconds`);
    
    // Display optimization features
    console.log('\n🎯 Hybrid Optimization Features:');
    console.log('   ✓ Visual CSS Grid layout (renders as single column for ATS)');
    console.log('   ✓ Professional color scheme with print fallbacks');
    console.log('   ✓ Icon-enhanced contact section');
    console.log('   ✓ Tech tags for visual scanning');
    console.log('   ✓ Standard section headers for ATS');
    console.log('   ✓ Semantic HTML structure');
    
    // Calculate statistics
    displayStatistics(resumeData);
    
  } catch (error) {
    console.error('❌ Error generating resume:', error.message);
    if (CONFIG.debugMode) {
      console.error('Stack trace:', error.stack);
    }
    process.exit(1);
  }
}

// Validate resume data structure
function validateResumeData(data) {
  console.log('\n🔍 Validating resume data...');
  
  const required = ['contact', 'professional_summary', 'experience', 'education'];
  const missing = required.filter(field => !data[field]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(', ')}`);
  }
  
  // Validate contact info
  if (!data.contact.name || !data.contact.email) {
    throw new Error('Name and email are required in contact information');
  }
  
  // Validate experience
  if (!Array.isArray(data.experience) || data.experience.length === 0) {
    throw new Error('At least one work experience entry is required');
  }
  
  console.log('   ✓ All required fields present');
  console.log('   ✓ Contact information valid');
  console.log(`   ✓ ${data.experience.length} work experience entries`);
  console.log(`   ✓ ${data.education.length} education entries`);
}

// Display resume statistics
function displayStatistics(data) {
  console.log('\n📊 Resume Statistics:');
  
  // Count skills
  let totalSkills = 0;
  if (data.technical_skills) {
    for (const category of Object.values(data.technical_skills)) {
      totalSkills += category.length;
    }
  }
  
  // Count achievements
  let totalHighlights = 0;
  for (const job of data.experience) {
    if (job.highlights) {
      totalHighlights += job.highlights.length;
    }
  }
  
  // Check for quantified achievements
  let quantifiedCount = 0;
  const quantifiers = /\d+[%$MKk]?|\b(increased|decreased|reduced|improved|saved)\b/i;
  
  for (const job of data.experience) {
    if (job.highlights) {
      for (const highlight of job.highlights) {
        if (quantifiers.test(highlight)) {
          quantifiedCount++;
        }
      }
    }
  }
  
  const quantificationRate = totalHighlights > 0 
    ? Math.round((quantifiedCount / totalHighlights) * 100) 
    : 0;
  
  console.log(`   • Total Skills: ${totalSkills}`);
  console.log(`   • Work Experience: ${data.experience.length} positions`);
  console.log(`   • Achievements: ${totalHighlights} bullet points`);
  console.log(`   • Quantification Rate: ${quantificationRate}% of achievements`);
  console.log(`   • Projects: ${data.projects ? data.projects.length : 0}`);
  console.log(`   • Certifications: ${data.certifications ? data.certifications.length : 0}`);
  
  // ATS score estimate
  const atsScore = calculateATSScore(data, quantificationRate);
  console.log(`\n🎯 Estimated ATS Compatibility Score: ${atsScore}%`);
  
  if (atsScore >= 80) {
    console.log('   ✅ Excellent ATS compatibility');
  } else if (atsScore >= 60) {
    console.log('   ⚠️ Good ATS compatibility, some improvements possible');
  } else {
    console.log('   ❌ Low ATS compatibility, consider improvements');
  }
}

// Calculate ATS compatibility score
function calculateATSScore(data, quantificationRate) {
  let score = 0;
  const weights = {
    contact: 15,
    summary: 15,
    skills: 20,
    experience: 20,
    education: 10,
    quantification: 10,
    keywords: 10
  };
  
  // Check each section
  if (data.contact && data.contact.email && data.contact.phone) score += weights.contact;
  if (data.professional_summary && data.professional_summary.length > 50) score += weights.summary;
  if (data.technical_skills && Object.keys(data.technical_skills).length > 0) score += weights.skills;
  if (data.experience && data.experience.length > 0) score += weights.experience;
  if (data.education && data.education.length > 0) score += weights.education;
  
  // Quantification bonus
  if (quantificationRate >= 50) {
    score += weights.quantification;
  } else {
    score += Math.round(weights.quantification * (quantificationRate / 50));
  }
  
  // Keyword check
  const commonKeywords = ['JavaScript', 'Python', 'AWS', 'Docker', 'React', 'Node.js', 
                         'Machine Learning', 'API', 'Database', 'Agile'];
  const resumeText = JSON.stringify(data).toLowerCase();
  let keywordMatches = 0;
  
  for (const keyword of commonKeywords) {
    if (resumeText.includes(keyword.toLowerCase())) {
      keywordMatches++;
    }
  }
  
  if (keywordMatches >= 5) {
    score += weights.keywords;
  } else {
    score += Math.round(weights.keywords * (keywordMatches / 5));
  }
  
  return score;
}

// Run the generator
if (require.main === module) {
  generateResume();
}

module.exports = { generateResume, validateResumeData, calculateATSScore };
# Complete Resume Generator Process Flow

**Application:** AI-Powered Dynamic Resume Generator with Multi-Agent Workflow
**Version:** 3.0 (Integrated Dynamic Workflow System)

---

## 🎯 Overview

This application generates highly-tailored resumes using a 6-agent AI pipeline with dynamic section configuration, workflow optimization, and visual layout customization.

---

## 📋 Complete Process Flow

### **PHASE 0: Application Launch**
1. Initialize GUI with 6 tabs (Job Description → Workflow Config → Run Pipeline → Customize Layout → Generate PDF → Console)
2. Attempt to load orchestrator modules (dynamic first, then standard)
3. Configure available AI models (Fast/Haiku, Balanced/Sonnet, Quality/Opus)
4. Load configuration registries (agents, sections, workflow templates)

---

### **PHASE 1: Job Description Input** (Tab 1)

#### Step 1.1: Input Method Selection
- **Option A:** Paste URL or full job description text (auto-detect)
- **Option B:** Upload job description text file
- **Option C:** Load existing job folder (resume from previous run)

#### Step 1.2: Company Information (Optional)
- **Manual Entry:** Enter company name, job title, company website
- **AI Extraction:** Use AI to automatically extract company info from job description
  - Parses job description text
  - Identifies company name, job title, and company URL
  - Pre-fills form fields for user review

#### Step 1.3: Input Validation
- Verify job description is provided (URL, text, or file)
- Validate file exists and is readable (if file method chosen)
- Ensure job folder contains required files (if folder method chosen)

#### Step 1.4: Proceed to Workflow Configuration
- User clicks "Next: Configure Workflow →"
- System moves to Workflow Config tab

---

### **PHASE 2: Workflow Configuration** (Tab 2 - NEW FEATURE)

#### Step 2.1: Job Analysis (Optional but Recommended)
**Agent 1 - Job Analyzer** performs initial analysis:
- **Input:** Job description text
- **Processing:**
  - Analyzes role type (technical, leadership, research, sales, etc.)
  - Identifies role focus (hands-on, strategic, hybrid)
  - Determines seniority level
  - Extracts key requirements and skills
  - Identifies industry and domain
- **Output:** `JobAnalysis` object with recommendations

#### Step 2.2: Workflow Recommendations
**Workflow Configurator** generates smart recommendations:
- **Section Recommendations:** Which resume sections to include
  - Core sections: contact, professional_summary, technical_expertise, experience, education
  - Optional sections: publications, certifications, leadership, achievements, work_samples
  - Priority scores for each section (1-10)
- **Agent Recommendations:** Which specialized agents to activate
  - Research content selector (for academic/research roles)
  - Portfolio curator (for creative/technical roles)
  - Leadership analyzer (for management roles)
- **Template Recommendation:** Best workflow template for the role
  - technical_role: Focus on skills and projects
  - research_role: Emphasize publications and education
  - leadership_role: Highlight management experience
  - standard: Balanced approach

#### Step 2.3: User Configuration
- **Auto-Accept Mode (default):** System automatically applies AI recommendations
- **Manual Mode:** User can review and customize recommendations
  - View recommended sections and priorities
  - Enable/disable specific sections
  - Adjust section order
  - Select alternative workflow template

#### Step 2.4: Workflow Finalization
- System creates `workflow_config` with:
  - Template name and description
  - List of enabled sections
  - Section priorities
  - Active agent list
  - Custom configuration parameters
- Configuration saved to job folder for reproducibility

---

### **PHASE 3: Multi-Agent Pipeline Execution** (Tab 3)

#### Step 3.1: Model Configuration
**User selects AI model strategy:**
- **Preset Selection:**
  - Fast: claude-3-5-haiku (quick, cost-effective)
  - Balanced: claude-sonnet-4-5 (optimal quality/speed)
  - Quality: claude-opus-4 (maximum quality)
- **Advanced Mode:** Per-agent model selection (6 individual selections)

#### Step 3.2: Pipeline Options Configuration
- **Phase Selection:**
  - Phase 1: Job Analysis + Content Selection
  - Phase 2: Resume Generation + Validation
  - Phase 3: Style Polish + Final QA
- **Additional Options:**
  - Skip style editing if draft is already good
  - Use parallel content selection (faster processing)

#### Step 3.3: Job Description Processing
- **URL Detection:** If input is URL, fetch content from web
- **Text Extraction:** Clean and normalize job description text
- **Company Info Extraction:** Use AI to extract missing company details
- **Folder Validation:** Verify existing folder structure (if resuming)

#### Step 3.4: Agent 1 - Job Analyzer (if not done in Phase 2)
- **Input:** Cleaned job description text
- **Processing:**
  - Extract technical requirements
  - Identify soft skill requirements
  - Determine years of experience needed
  - Identify must-have vs. nice-to-have qualifications
  - Analyze company culture indicators
- **Output:**
  - `JobAnalysis` object
  - Recommended sections and priorities
  - Key skills to emphasize
  - Workflow configuration (if dynamic orchestrator)

#### Step 3.5: Agent 2 - Content Selector
**Two modes available:**

**Standard Mode (Sequential):**
- Review candidate's master resume/experience database
- Match experiences to job requirements
- Score each experience item for relevance
- Select top experiences for inclusion

**Parallel Mode (Faster):**
- Splits content selection across multiple concurrent AI calls
- Technical skills analysis
- Experience matching
- Project selection
- Education/credentials review
- All processed simultaneously, then aggregated

**Output:**
- Selected experience entries
- Selected projects
- Relevant technical skills
- Education and certifications to highlight
- Publications/work samples (if applicable)

#### Step 3.6: Agent 3 - Resume Drafter
- **Input:**
  - Job analysis results
  - Selected content
  - Workflow configuration (enabled sections)
  - Dynamic schema (if using dynamic orchestrator)
- **Processing:**
  - Generate professional summary tailored to job
  - Organize technical skills by category
  - Write experience bullet points emphasizing relevant achievements
  - Format projects with quantifiable impact
  - Structure education section
  - Include optional sections based on workflow config
- **Output:**
  - Complete `ResumeDraft` object (JSON)
  - All sections populated with tailored content
  - Structured according to dynamic schema

#### Step 3.7: Agent 4 - Fabrication Validator
- **Input:** Draft resume JSON
- **Processing:**
  - **Accuracy Check:** Verify all claims are justified by source material
  - **Exaggeration Detection:** Flag overstated accomplishments
  - **Consistency Check:** Ensure timeline consistency, no contradictions
  - **Red Flag Detection:** Identify potential problematic claims
- **Validation Categories:**
  - ✅ Verified: Claim directly supported by source
  - ⚠️ Unverifiable: Cannot confirm from source material
  - ❌ Fabricated: Claim not supported or contradicted by source
- **Output:**
  - Validation report with flagged items
  - Corrected resume JSON
  - List of changes made

#### Step 3.8: Agent 5 - Voice & Style Editor
- **Input:** Validated resume JSON
- **Processing:**
  - **Tone Analysis:** Ensure professional, confident tone
  - **Consistency Check:** Maintain consistent voice across sections
  - **Clarity Enhancement:** Improve unclear or vague statements
  - **Impact Optimization:** Strengthen weak bullet points
  - **ATS Optimization:** Ensure keyword density without stuffing
  - **Grammar & Polish:** Final language refinement
- **Skip Condition:** Can be skipped if draft is already high quality
- **Output:**
  - Polished resume JSON
  - Style improvement notes

#### Step 3.9: Agent 6 - Final QA
- **Input:** Polished resume JSON
- **Final Checks:**
  - **Formatting:** Consistent punctuation, capitalization, spacing
  - **Completeness:** All required sections present
  - **Alignment:** Resume matches job requirements
  - **Length:** Appropriate length (typically 2 pages)
  - **Readability:** Clear, scannable structure
  - **ATS Compatibility:** Machine-readable format
- **Output:**
  - Final validated resume JSON
  - QA report with quality score
  - Recommended improvements (if any)

#### Step 3.10: Pipeline Completion
- Save all outputs to job folder:
  - `job_description.txt` - Original job description
  - `job_analysis.json` - Agent 1 analysis results
  - `content_selection.json` - Agent 2 selections
  - `resume_draft.json` - Agent 3 initial draft
  - `resume_validated.json` - Agent 4 validated version
  - `resume_polished.json` - Agent 5 polished version
  - `resume_final.json` - Agent 6 final version
  - `workflow_config.json` - Workflow configuration used
  - `pipeline_log.txt` - Detailed execution log
- Display completion status
- Ready for layout customization

---

### **PHASE 4: Layout Customization** (Tab 4)

#### Step 4.1: Load Resume JSON
- System loads `resume_final.json` from job folder
- Parses JSON structure to identify available sections
- Displays current layout configuration (or default)

#### Step 4.2: Visual Layout Editor
**User opens visual editor for drag-and-drop configuration:**

**Row-Based Layout System:**
- **Single Row:** One section at full width (100%)
- **Side-by-Side Row:** Two sections in columns (e.g., 50%/50% or 60%/40%)
- **Multi-Column Row:** 3+ sections in equal columns

**For Each Row, Configure:**
- **Sections:** Which resume sections to include
- **Widths:** Percentage width for each section
- **Column Gap:** Spacing between sections (default: 20px)
- **Page Break:** Allow/prevent page break after this row

#### Step 4.3: Quick Presets (Alternative to Manual)
**Pre-configured layout templates:**

**Standard Layout:**
- Professional Summary (full width)
- Technical Expertise (full width)
- Experience (full width)
- Projects (full width)
- Education + Publications (side-by-side, 50/50)

**Compact Layout (1-page optimized):**
- Professional Summary (full width)
- Technical Expertise + Education (side-by-side, 65/35)
- Experience (full width)
- Projects (full width)
- Compact spacing mode enabled

**Two-Column Layout:**
- Professional Summary (full width)
- Technical Expertise + Experience (side-by-side, 40/60)
- Projects + Education (side-by-side, 60/40)
- Skills displayed in single column

**Academic Layout:**
- Professional Summary (full width)
- Education + Publications (side-by-side, 50/50)
- Technical Expertise (full width)
- Experience (full width)
- Projects (full width)

#### Step 4.4: Section-Specific Options
- **Technical Expertise:**
  - Number of columns (1-4)
  - Center-align skills (yes/no)
- **Professional Summary:**
  - Style: paragraph or bullets
- **Spacing:**
  - Compact mode (reduced margins and spacing)

#### Step 4.5: Template Management
- **Save Template:** Export layout configuration as reusable JSON template
- **Load Template:** Import previously saved layout configuration
- Preview configuration in JSON format

#### Step 4.6: Layout Configuration Complete
- System saves `resume_layout_config.json` to job folder
- Configuration includes:
  - Row definitions (sections, widths, gaps, page breaks)
  - Section options (columns, styles, alignment)
  - Spacing preferences
  - Metadata (template name, created date)

---

### **PHASE 5: PDF Generation** (Tab 5)

#### Step 5.1: JSON Preview & Editing
- **Load Resume JSON:** Display `resume_final.json` in editable text area
- **Manual Editing:** User can modify JSON directly
  - Fix typos
  - Adjust wording
  - Reorder items
  - Add/remove content
- **Validation:** Check JSON syntax before proceeding
- **Save Option:** Save edited JSON as `resume_edited.json`

#### Step 5.2: Generation Options
- **Auto-open PDF:** Automatically open PDF after generation
- **Sync Edited JSON:** Save manual edits back to file
- **Output Location:** Display where PDF will be saved

#### Step 5.3: PDF Rendering Process
**Node.js-based PDF generator (`generate-pdf-enhanced.js`):**

**Load Data:**
- Read resume JSON (edited version if available, else final)
- Read layout configuration JSON
- Load any custom styling preferences

**Apply Layout:**
- Process row definitions
- Calculate column widths and positions
- Apply section-specific styling
- Handle page breaks

**Render Sections:**
1. **Header/Contact:**
   - Name (large, bold)
   - Contact information (email, phone, location, LinkedIn, GitHub)
   - Compact, ATS-friendly format

2. **Professional Summary:**
   - Paragraph or bullet format (based on config)
   - Tailored opening statement
   - Key qualifications highlighted

3. **Technical Expertise:**
   - Skills organized by category
   - Pill-style badges or clean list format
   - 1-4 columns (based on config)
   - Optional center alignment

4. **Experience:**
   - Company, title, dates
   - Location
   - Bullet points with quantifiable achievements
   - Keyword emphasis (bold)
   - Timeline visualization (optional)

5. **Projects:**
   - Project name and type
   - Technologies used
   - Key achievements
   - Links to demos/repos (if applicable)

6. **Education:**
   - Degree, institution, graduation date
   - GPA (if strong)
   - Honors, awards
   - Relevant coursework

7. **Publications** (if included):
   - Title, publication venue, date
   - Co-authors
   - Links or DOIs

8. **Work Samples/Portfolio** (if included):
   - Sample title and description
   - Technologies/tools used
   - Links to live demos or repositories

**Apply Styling:**
- Professional color scheme (blue accents, clean blacks/grays)
- ATS-friendly fonts (system fonts)
- Consistent spacing and margins
- Print-optimized CSS
- 2-page maximum (typically)

**Generate PDF:**
- Use Puppeteer to render HTML to PDF
- Apply proper PDF metadata
- Optimize file size
- Ensure text is selectable (not images)

#### Step 5.4: PDF Output
- **Save PDF:** `{Company_Name}_{Job_Title}_Resume.pdf`
- **Location:** Same folder as resume JSON files
- **Auto-open:** Launch PDF in default viewer (if enabled)
- **Confirmation:** Display success message with file path

#### Step 5.5: Console Logging
**Throughout all phases, Console tab shows:**
- Detailed progress messages
- Agent execution status
- Warnings and errors
- Timing information
- File paths for all saved outputs
- Success/failure notifications
- Color-coded messages (success=green, error=red, warning=yellow, info=blue)

---

## 🔄 Alternative Workflows

### **Quick Resume Update (Existing Folder)**
1. Select "Load Existing Folder" in Tab 1
2. Browse to previous job folder
3. Skip directly to Tab 3 to re-run specific phases
4. Modify layout in Tab 4 if needed
5. Regenerate PDF with new layout

### **Standard Workflow (No Dynamic Configuration)**
1. Input job description
2. Skip Tab 2 (Workflow Config)
3. Run full pipeline with default sections
4. Uses standard orchestrator (`orchestrator.py`)
5. All core sections included automatically

### **Dynamic Workflow (AI-Optimized)**
1. Input job description
2. Run job analysis in Tab 2
3. Review and accept AI recommendations
4. Run pipeline with optimized workflow
5. Uses dynamic orchestrator (`orchestrator_dynamic.py`)
6. Only relevant sections included

---

## 📊 Key Features & Capabilities

### **Multi-Agent AI System**
- 6 specialized AI agents working in sequence
- Each agent has specific expertise and validation role
- Agents can use different models (Haiku, Sonnet, Opus)
- Parallel processing option for faster execution

### **Dynamic Workflow Configuration**
- AI analyzes job to recommend optimal sections
- Supports 18+ different resume sections
- Template-based workflows for different role types
- Configurable agent activation based on role

### **Intelligent Content Selection**
- Matches candidate experience to job requirements
- Prioritizes most relevant skills and achievements
- Quantifies impact where possible
- Removes irrelevant information

### **Quality Assurance**
- Fabrication detection prevents false claims
- Style consistency across all sections
- Grammar and clarity optimization
- ATS compatibility verification

### **Flexible Layout System**
- Visual drag-and-drop editor
- Multiple preset templates
- Custom row/column configurations
- Section-specific styling options

### **Professional PDF Output**
- Clean, modern design
- ATS-friendly formatting
- Optimized for both human readers and parsing systems
- Consistent with industry standards

---

## 💾 File Structure (Job Folder)

After complete workflow, job folder contains:

```
{company_name}_{job_title}/
├── job_description.txt              # Original job posting
├── job_analysis.json                # Agent 1: Job analysis results
├── workflow_config.json             # Workflow configuration used
├── content_selection.json           # Agent 2: Selected content
├── resume_draft.json                # Agent 3: Initial draft
├── resume_validated.json            # Agent 4: Validated version
├── resume_polished.json             # Agent 5: Style-polished version
├── resume_final.json                # Agent 6: Final version
├── resume_edited.json               # (Optional) User-edited version
├── resume_layout_config.json        # Layout configuration
├── {Company}_{Title}_Resume.pdf     # Final PDF output
├── pipeline_log.txt                 # Detailed execution log
└── validation_report.json           # Quality assurance report
```

---

## ✅ Success Criteria

A successful resume generation includes:

1. **Relevance:** Resume directly addresses job requirements
2. **Accuracy:** All claims verified against source material
3. **Clarity:** Clear, concise, professional language
4. **Impact:** Quantifiable achievements highlighted
5. **ATS-Compatible:** Keyword-optimized, parseable format
6. **Professional Design:** Clean layout, proper spacing
7. **Appropriate Length:** Typically 2 pages, never more than 3
8. **Consistency:** Uniform style, tone, and formatting
9. **Completeness:** All relevant sections included
10. **Tailored:** Customized for specific role and company

---

## 🎯 End Result

**A production-ready, highly-tailored resume that:**
- Maximizes relevance to the specific job posting
- Passes ATS (Applicant Tracking System) filters
- Highlights candidate's most relevant qualifications
- Presents information clearly and professionally
- Maintains 100% accuracy and truthfulness
- Optimizes for both machine parsing and human review
- Can be regenerated with different layouts instantly
- Includes full audit trail of AI decision-making

---

**Total Process Time:**
- Quick workflow: 2-5 minutes (with AI analysis)
- Full workflow: 5-10 minutes (with review and customization)
- PDF regeneration: <30 seconds

**Human Involvement:**
- Minimal: Provide job description, review output
- Optional: Customize workflow, edit content, adjust layout
- Maximum Control: Full editing capability at every stage

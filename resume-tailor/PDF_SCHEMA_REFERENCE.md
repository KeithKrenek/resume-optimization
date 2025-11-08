# PDF-Compatible Resume JSON Schema - Quick Reference

## Purpose

This document provides a quick reference for the exact JSON structure required for successful PDF generation with `generate-pdf-enhanced.js`.

## Complete Valid Example

```json
{
  "contact": {
    "name": "Keith Thompson",
    "email": "keith@example.com",
    "phone": "617-555-0123",
    "location": "Boston, MA",
    "linkedin": "https://linkedin.com/in/keiththompson",
    "github": "https://github.com/keiththompson",
    "portfolio": "https://keiththompson.dev",
    "tagline": "AI/ML Engineer | Production Systems"
  },
  
  "professional_summary": "Engineering leader with 5+ years building mission-critical AI/ML systems achieving 100× efficiency gains and >90% prediction accuracy. Deep expertise in production LLM deployment and ML framework internals (custom PyTorch autograd functions, neuromorphic computing). Proven ability to coordinate across diverse stakeholder groups while maintaining rigorous safety standards.",
  
  "technical_expertise": {
    "Production ML & AI Systems": {
      "skills": ["Python", "PyTorch", "TensorFlow", "MLOps", "LLMs", "RAG"],
      "years": "6+",
      "proficiency": "expert",
      "context": "Built production systems achieving >90% accuracy, running 4+ years with automated retraining"
    },
    "Software Engineering": {
      "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL"],
      "years": "8+",
      "proficiency": "expert",
      "context": "Full-stack development with focus on scalable backend systems"
    },
    "Cloud & Infrastructure": {
      "skills": ["AWS", "Docker", "Kubernetes", "Terraform"],
      "years": "5+",
      "proficiency": "advanced",
      "context": "Deployed and maintained production ML systems serving millions of requests"
    }
  },
  
  "experience": [
    {
      "company": "Draper Laboratory",
      "title": "Senior Member of Technical Staff",
      "location": "Cambridge, MA",
      "dates": "Oct 2019 - Present",
      "achievements": [
        {
          "text": "Built ML pipeline processing 100+ manufacturing variables achieving >90% predictive accuracy. Prevented $10M+ delays through bi-weekly automated retraining over 4+ years.",
          "source_id": "exp_draper_2019",
          "metrics": [">90%", "$10M+", "4+ years", "100+"],
          "technologies": ["Python", "PyTorch", "XGBoost"]
        },
        {
          "text": "Led 4-engineer team delivering physics-based generative design tools for photonic ICs. Achieved 100× faster design cycles while maintaining optical performance requirements.",
          "source_id": "exp_draper_2019",
          "metrics": ["4-engineer", "100×"],
          "technologies": ["Python", "NumPy"]
        }
      ],
      "source_id": "exp_draper_2019"
    },
    {
      "company": "Previous Company",
      "title": "Software Engineer",
      "location": "Boston, MA",
      "dates": "Jan 2017 - Sep 2019",
      "achievements": [
        {
          "text": "Developed microservices architecture handling 1M+ daily requests with 99.9% uptime.",
          "source_id": "exp_previous_2017"
        }
      ],
      "source_id": "exp_previous_2017"
    }
  ],
  
  "bulleted_projects": [
    {
      "title": "AI Code Intelligence System",
      "org_context": "Personal Project / Open Source",
      "dates": "Jan 2024 - Mar 2024",
      "achievement1": "Challenge: Existing code review tools missed 40% of bugs in production systems.",
      "achievement2": "Approach: Built execution-grounded validation system using Python AST analysis, dynamic testing, and RAG-based code understanding.",
      "achievement3": "Impact: Reduced production bugs by 60% and improved code quality scores by 35% across team.",
      "technologies": ["Python", "PyTorch", "LangChain", "RAG", "AST"],
      "source_id": "proj_ai_code_2024"
    },
    {
      "title": "ML Model Deployment Platform",
      "org_context": "Draper Laboratory",
      "dates": "Jun 2023 - Dec 2023",
      "achievement1": "Challenge: Teams spending 2+ weeks per model deployment with frequent failures.",
      "achievement2": "Approach: Created automated deployment pipeline with built-in monitoring, versioning, and rollback capabilities.",
      "achievement3": "Impact: Reduced deployment time from weeks to hours. Enabled 50+ model deployments with zero downtime.",
      "technologies": ["Python", "Docker", "Kubernetes", "MLOps"],
      "source_id": "proj_deploy_2023"
    }
  ],
  
  "education": [
    {
      "degree": "M.S. in Computer Science",
      "institution": "Massachusetts Institute of Technology",
      "location": "Cambridge, MA",
      "graduation": "2017",
      "details": "Focus: Machine Learning and Artificial Intelligence. GPA: 3.9/4.0"
    },
    {
      "degree": "B.S. in Computer Engineering",
      "institution": "University of California, Berkeley",
      "location": "Berkeley, CA",
      "graduation": "2015"
    }
  ],
  
  "publications": [
    {
      "title": "Neuromorphic Computing for Edge AI: A Survey",
      "authors": "Thompson, K., Smith, J., Johnson, A.",
      "journal": "IEEE Transactions on Neural Networks",
      "year": "2024",
      "url": "https://doi.org/10.1109/TNNLS.2024.12345"
    },
    {
      "title": "Efficient Training of Large Language Models on Limited Hardware",
      "authors": "Thompson, K., Chen, L.",
      "journal": "NeurIPS 2023",
      "year": "2023",
      "url": "https://proceedings.neurips.cc/paper/2023/hash/abc123.html"
    }
  ],
  
  "work_samples": [
    {
      "title": "ML Framework Extension for PyTorch",
      "type": "Open Source Library",
      "description": "Custom autograd functions and optimizers for specialized neural architectures. Featured in PyTorch ecosystem showcase.",
      "url": "https://github.com/keiththompson/pytorch-extensions",
      "tech": ["Python", "PyTorch", "C++"],
      "impact": "5K+ GitHub stars, 50K+ downloads, used by Meta Research"
    },
    {
      "title": "Real-time Code Analysis Demo",
      "type": "Interactive Demo",
      "description": "Live demonstration of AST-based code analysis with execution grounding and bug detection.",
      "url": "https://code-analysis-demo.keiththompson.dev",
      "tech": ["Python", "React", "WebSockets"]
    }
  ],
  
  "citations": {
    "experience[0]": "exp_draper_2019",
    "experience[0].achievements[0]": "exp_draper_2019",
    "experience[0].achievements[1]": "exp_draper_2019",
    "experience[1]": "exp_previous_2017",
    "experience[1].achievements[0]": "exp_previous_2017",
    "projects[0]": "proj_ai_code_2024",
    "projects[1]": "proj_deploy_2023"
  }
}
```

## Field Requirements by Section

### Contact (All REQUIRED except portfolio)

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| name | string | YES | Full name | "Keith Thompson" |
| email | string | YES | Valid email | "keith@example.com" |
| phone | string | YES | Any format | "617-555-0123" |
| location | string | YES | City, State | "Boston, MA" |
| linkedin | string | NO | Full URL | "https://linkedin.com/in/..." |
| github | string | NO | Full URL | "https://github.com/..." |
| portfolio | string | NO | Full URL | "https://portfolio.com" |
| tagline | string | YES | 5-10 words | "AI/ML Engineer" |

### Professional Summary (REQUIRED)

- **Type**: string (NOT object/dict)
- **Length**: 2-4 sentences
- **Format**: Plain text, no special formatting

❌ WRONG:
```json
"professional_summary": {
  "text": "Summary here",
  "type": "technical"
}
```

✅ CORRECT:
```json
"professional_summary": "Engineering leader with 5+ years..."
```

### Technical Expertise (REQUIRED)

Each category must have ALL four fields:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| skills | array | YES | List of strings | ["Python", "PyTorch"] |
| years | string | YES | "X+" format | "6+" |
| proficiency | string | YES | expert\|advanced\|intermediate | "expert" |
| context | string | YES | Evidence statement | "Built production systems..." |

### Experience (REQUIRED)

Each experience entry:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| company | string | YES | Company name | "Draper Laboratory" |
| title | string | YES | Job title | "Senior Engineer" |
| location | string | YES | City, State | "Cambridge, MA" |
| dates | string | YES | MMM YYYY - MMM YYYY | "Oct 2019 - Present" |
| achievements | array | YES | See below | [...] |
| source_id | string | YES | Database ID | "exp_draper_2019" |

Achievement format (can be string OR object):

**String format** (simple):
```json
"achievements": [
  "Built ML pipeline achieving >90% accuracy",
  "Led 4-engineer team delivering design tools"
]
```

**Object format** (with metadata):
```json
"achievements": [
  {
    "text": "Built ML pipeline achieving >90% accuracy",
    "source_id": "exp_draper_2019",
    "metrics": [">90%", "4+ years"],
    "technologies": ["Python", "PyTorch"]
  }
]
```

### Projects (bulleted_projects) (OPTIONAL but recommended)

Each project:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| title | string | YES | Project name | "AI Code Intelligence" |
| org_context | string | YES | Organization/context | "Personal Project" |
| dates | string | YES | MMM YYYY - MMM YYYY | "Jan 2024 - Mar 2024" |
| achievement1 | string | YES | Challenge statement | "Challenge: ..." |
| achievement2 | string | YES | Approach | "Approach: ..." |
| achievement3 | string | NO | Impact | "Impact: ..." |
| achievement4 | string | NO | Additional impact | "..." |
| technologies | array | YES | Tech stack | ["Python", "React"] |
| source_id | string | YES | Database ID | "proj_ai_2024" |

### Education (REQUIRED)

Each education entry:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| degree | string | YES | Full degree name | "M.S. in Computer Science" |
| institution | string | YES | University name | "MIT" |
| location | string | NO | City, State | "Cambridge, MA" |
| graduation | string | YES | Year ONLY | "2017" |
| details | string | NO | GPA, honors, focus | "GPA: 3.9/4.0" |

⚠️ **IMPORTANT**: Use `graduation`, NOT `graduation_date`

### Publications (OPTIONAL)

Each publication:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| title | string | YES | Paper title | "Neuromorphic Computing..." |
| authors | string | YES | Author list | "Thompson, K., Smith, J." |
| journal | string | YES | Venue name | "IEEE Transactions..." |
| year | string | YES | Year | "2024" |
| url | string | YES | DOI or URL | "https://doi.org/..." |

All fields REQUIRED for hyperlinks to work.

### Work Samples (OPTIONAL)

Each work sample:

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| title | string | YES | Sample title | "ML Framework Extension" |
| type | string | YES | Type | "Open Source Library" |
| description | string | YES | Brief description | "Custom autograd functions..." |
| url | string | YES | Full URL | "https://github.com/..." |
| tech | array | NO | Tech stack | ["Python", "PyTorch"] |
| impact | string | NO | Impact metrics | "5K+ stars" |

## Date Format Rules

**CRITICAL**: All dates must follow these rules:

### Valid Formats:
- `"Oct 2019 - Jan 2025"` ✓
- `"Mar 2020 - Present"` ✓
- `"Jan 2023 - Dec 2023"` ✓
- `"2017"` ✓ (single year, for education only)

### Invalid Formats:
- `"October 2019 - January 2025"` ❌ (full month names)
- `"2019-2025"` ❌ (missing months)
- `"10/2019 - 01/2025"` ❌ (numeric format)
- `"2019 - Present"` ❌ (missing start month)

### Rules:
1. Always use 3-letter month abbreviation (Jan, Feb, Mar, etc.)
2. Use space-hyphen-space (" - ") as separator
3. "Present" is capitalized
4. Single years (like "2017") only for education graduation

## Common Mistakes

### 1. Professional Summary as Dict
❌ WRONG:
```json
"professional_summary": {
  "text": "Summary here",
  "tagline": "AI Engineer"
}
```

✅ CORRECT:
```json
"professional_summary": "Engineering leader with 5+ years..."
```

### 2. Missing Technical Expertise Fields
❌ WRONG:
```json
"technical_expertise": {
  "ML & AI": ["Python", "PyTorch"]
}
```

✅ CORRECT:
```json
"technical_expertise": {
  "ML & AI": {
    "skills": ["Python", "PyTorch"],
    "years": "6+",
    "proficiency": "expert",
    "context": "Built production systems..."
  }
}
```

### 3. Wrong Education Date Field
❌ WRONG:
```json
{
  "degree": "M.S. in CS",
  "graduation_date": "2017"
}
```

✅ CORRECT:
```json
{
  "degree": "M.S. in CS",
  "graduation": "2017"
}
```

### 4. Projects Without achievement1-4 Structure
❌ WRONG:
```json
{
  "title": "Project",
  "description": "Built a thing that does stuff"
}
```

✅ CORRECT:
```json
{
  "title": "Project",
  "achievement1": "Challenge: Problem statement",
  "achievement2": "Approach: How I solved it",
  "achievement3": "Impact: Quantified results"
}
```

### 5. Missing URLs in Publications
❌ WRONG:
```json
{
  "title": "Paper Title",
  "authors": "Smith, J.",
  "journal": "IEEE",
  "year": "2024"
  // Missing url field!
}
```

✅ CORRECT:
```json
{
  "title": "Paper Title",
  "authors": "Smith, J.",
  "journal": "IEEE",
  "year": "2024",
  "url": "https://doi.org/10.1109/..."
}
```

## Validation Checklist

Before generating PDF, verify:

- [ ] professional_summary is string (not dict)
- [ ] All dates in "MMM YYYY - MMM YYYY" format
- [ ] Contact has: name, email, phone, location, tagline
- [ ] Technical expertise categories have: skills, years, proficiency, context
- [ ] All experience entries have source_id
- [ ] All projects have achievement1 and achievement2 minimum
- [ ] Education uses "graduation" field
- [ ] Publications have all 5 required fields
- [ ] All URLs start with "https://"
- [ ] No missing required fields

## Testing

Test with this minimal valid example:

```json
{
  "contact": {
    "name": "Test User",
    "email": "test@test.com",
    "phone": "123-456-7890",
    "location": "City, State",
    "tagline": "Software Engineer"
  },
  "professional_summary": "Test summary sentence.",
  "technical_expertise": {
    "Software": {
      "skills": ["Python"],
      "years": "5+",
      "proficiency": "expert",
      "context": "Test context"
    }
  },
  "experience": [{
    "company": "Test Co",
    "title": "Engineer",
    "location": "City, State",
    "dates": "Jan 2020 - Present",
    "achievements": ["Built test system"],
    "source_id": "test_exp"
  }],
  "bulleted_projects": [],
  "education": [{
    "degree": "B.S. in CS",
    "institution": "University",
    "graduation": "2020"
  }],
  "citations": {}
}
```

Save as `test_resume.json` and run:
```bash
node generate-pdf-enhanced.js /path/to/folder/with/test_resume.json
```

Should generate PDF without errors.

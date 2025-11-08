"""
Pydantic Schemas for Multi-Agent Resume Generation (Enhanced for PDF Compatibility)
Provides type safety and validation for data passing between agents
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RoleType(str, Enum):
    """Type of role being applied for"""
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    TECHNICAL_LEAD = "technical_lead"
    ENGINEERING_MANAGER = "engineering_manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class RequirementType(str, Enum):
    """Classification of job requirements"""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    PREFERRED = "preferred"


# ============================================================================
# AGENT 1: JOB ANALYZER OUTPUT
# ============================================================================

class JobRequirement(BaseModel):
    """Single job requirement extracted from JD"""
    text: str = Field(description="Exact requirement text from JD")
    category: str = Field(description="Category (technical, leadership, domain, etc)")
    importance: RequirementType
    keywords: List[str] = Field(description="Key terms for matching")


class JobAnalysis(BaseModel):
    """Complete job analysis output from Agent 1"""
    job_title: str
    company: str
    role_type: RoleType

    # Core requirements
    must_have_requirements: List[JobRequirement]
    nice_to_have_requirements: List[JobRequirement]

    # Keywords for matching
    technical_keywords: List[str] = Field(description="Technical skills, tools, frameworks")
    domain_keywords: List[str] = Field(description="Industry, application domain")
    leadership_keywords: List[str] = Field(description="Leadership, management terms")

    # Company/role context
    company_values: List[str] = Field(default_factory=list, description="Company culture/values")
    role_focus: str = Field(description="Primary focus of role (e.g., 'production ML systems')")

    # Meta information
    years_experience_required: Optional[int] = None
    team_size_mentioned: Optional[int] = None
    success_metrics: List[str] = Field(default_factory=list, description="How success is measured")

    # Workflow recommendations (NEW - for dynamic configuration)
    recommended_sections: List[str] = Field(
        default_factory=list,
        description="Resume sections recommended based on job requirements (e.g., ['leadership', 'publications'])"
    )
    recommended_agents: List[str] = Field(
        default_factory=list,
        description="Optional agents recommended for this role (e.g., ['leadership_highlighter'])"
    )
    section_priorities: Dict[str, int] = Field(
        default_factory=dict,
        description="Priority ranking for each section (1-10, higher = more important)"
    )
    workflow_reasoning: str = Field(
        default="",
        description="Explanation of why specific sections/agents were recommended"
    )
    recommended_template: Optional[str] = Field(
        default=None,
        description="Suggested workflow template name (e.g., 'engineering_manager', 'senior_ic')"
    )

    # Raw for reference
    raw_jd_excerpt: str = Field(description="Key excerpt from JD for context")


# ============================================================================
# AGENT 2: CONTENT SELECTOR OUTPUT (Enhanced for PDF Compatibility)
# ============================================================================

class SelectedExperience(BaseModel):
    """Experience selected from database with provenance"""
    source_id: str = Field(description="Database ID (e.g., 'exp_draper_member_technical_staff_2019_2025')")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Match score to job requirements")
    match_reasons: List[str] = Field(description="Why this experience was selected")
    
    # Exact text from database
    company: str
    title: str
    dates: str  # Will be standardized to "MMM YYYY - MMM YYYY" format
    location: str
    core_description: str
    key_achievements: List[str]
    quantified_outcomes: Dict[str, Any]
    tech_stack: List[str]
    methods: List[str]
    domain_tags: List[str]
    
    # Variant selection
    persona_variant_selected: Optional[str] = Field(
        default=None,
        description="Which persona variant to use (e.g., 'leadership_focus')"
    )
    persona_achievements: Optional[List[str]] = Field(
        default=None,
        description="Achievements from selected persona variant"
    )


class SelectedProject(BaseModel):
    """Project selected from database with provenance"""
    source_id: str = Field(description="Database ID")
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reasons: List[str]
    
    # Exact text from database
    title: str
    org: str
    dates: str  # Will be standardized to "MMM YYYY - MMM YYYY" format
    core_description: str
    key_achievements: List[str]
    quantified_outcomes: Dict[str, Any]
    tech_stack: List[str]
    methods: List[str]
    domain_tags: List[str]
    
    # Structured response (optional - not all projects have this)
    structured_response: Optional[Dict[str, str]] = Field(
        default=None,
        description="Challenge, solution, impact structure"
    )
    
    # Variant selection
    persona_variant_selected: Optional[str] = None
    persona_achievements: Optional[List[str]] = None


class WorkSample(BaseModel):
    """Work sample/portfolio item"""
    title: str
    type: str  # "Demo", "App", "Tool", etc.
    description: str
    url: str
    tech: List[str] = Field(default_factory=list)
    impact: Optional[str] = None


class Publication(BaseModel):
    """Publication entry (PDF-compatible format)"""
    title: str
    authors: str  # Full author list as string
    journal: str  # Venue or journal name
    year: str  # Publication year
    url: str = ""  # DOI or direct URL


class ContentSelection(BaseModel):
    """Complete content selection output from Agent 2"""
    # Selected content
    selected_experiences: List[SelectedExperience] = Field(
        description="3-5 most relevant experiences"
    )
    selected_projects: List[SelectedProject] = Field(
        description="2-4 most relevant projects"
    )
    
    # Supporting content
    selected_skills: Dict[str, List[str]] = Field(
        description="Skills organized by category"
    )
    selected_education: List[Dict[str, Any]]
    selected_publications: List[Any] = Field(default_factory=list)  # Will be Publication objects after standardization
    selected_work_samples: List[Any] = Field(default_factory=list)  # Will be WorkSample objects
    
    # Contact info (flattened, PDF-compatible)
    contact_info: Dict[str, str]
    
    # Selection metadata
    selection_strategy: str = Field(
        description="Explanation of selection approach"
    )
    coverage_analysis: Dict[str, Any] = Field(
        description="How well selection covers requirements"
    )


# ============================================================================
# AGENT 3: RESUME DRAFTER OUTPUT (Enhanced for PDF Compatibility)
# ============================================================================

class TechnicalExpertiseCategory(BaseModel):
    """Single technical expertise category (PDF-compatible)"""
    skills: List[str] = Field(description="List of skills in this category")
    years: str = Field(description="Years of experience (e.g., '6+', '4+')")
    proficiency: str = Field(description="expert | advanced | intermediate")
    context: str = Field(description="Evidence-based capability statement")


class AchievementBullet(BaseModel):
    """Single achievement bullet with provenance"""
    text: str
    source_id: str
    metrics: List[str] = Field(default_factory=list, description="Extracted metrics")
    technologies: List[str] = Field(default_factory=list, description="Technologies mentioned")


class ExperienceEntry(BaseModel):
    """Experience entry (PDF-compatible)"""
    company: str
    title: str
    location: str
    dates: str  # MUST be "MMM YYYY - MMM YYYY" format
    achievements: List[Any]  # Can be strings or AchievementBullet objects
    source_id: str
    
    @field_validator('dates')
    @classmethod
    def validate_date_format(cls, v):
        """Ensure dates are in correct format"""
        import re
        # Allow formats: "MMM YYYY - MMM YYYY", "MMM YYYY - Present", or just "YYYY"
        if not re.match(r'^([A-Z][a-z]{2} \d{4} - ([A-Z][a-z]{2} \d{4}|Present)|\d{4})$', v):
            print(f"Warning: Date format may not be PDF-compatible: {v}")
        return v


class ProjectEntry(BaseModel):
    """Project entry (PDF-compatible with achievement1-4 structure)"""
    title: str
    org_context: str
    dates: str  # MUST be "MMM YYYY - MMM YYYY" format
    achievement1: str  # Challenge
    achievement2: Optional[str] = None  # Approach
    achievement3: Optional[str] = None  # Impact
    achievement4: Optional[str] = None  # Additional impact
    technologies: List[str] = Field(default_factory=list)
    source_id: str


class EducationEntry(BaseModel):
    """Education entry (PDF-compatible)"""
    degree: str
    institution: str
    location: Optional[str] = None
    graduation: str  # Year (NOT "graduation_date")
    details: Optional[str] = None  # GPA, honors, etc.


class ContactInfo(BaseModel):
    """Contact information (PDF-compatible with all expected fields)"""
    name: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    tagline: Optional[str] = None  # One-line professional identifier


class ResumeDraft(BaseModel):
    """Draft resume JSON (PDF-compatible structure)"""
    contact: Dict[str, str]  # Or ContactInfo
    professional_summary: str  # MUST be plain string (not dict)
    technical_expertise: Dict[str, Any]  # Dict[str, TechnicalExpertiseCategory]
    experience: List[Dict[str, Any]]  # List[ExperienceEntry]
    bulleted_projects: List[Dict[str, Any]]  # List[ProjectEntry]
    work_samples: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]]  # List[EducationEntry]
    publications: List[Dict[str, Any]] = Field(default_factory=list)  # List[Publication]
    awards_recognition: List[str] = Field(default_factory=list)
    
    # Metadata for validation
    citations: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of content to source_id"
    )
    
    @field_validator('professional_summary')
    @classmethod
    def validate_summary_is_string(cls, v):
        """Ensure professional_summary is a plain string"""
        if isinstance(v, dict):
            # Try to extract text field
            if 'text' in v:
                return v['text']
            raise ValueError("professional_summary must be a plain string, not a dict")
        return v


# ============================================================================
# AGENT 4: VALIDATION RESULTS
# ============================================================================

class ValidationIssue(BaseModel):
    """Single validation issue"""
    severity: str = Field(description="critical, warning, info")
    type: str = Field(description="Issue type")
    location: str = Field(description="Where in resume")
    message: str
    detail: Optional[str] = None


class ValidationResult(BaseModel):
    """Output from validation agent"""
    is_valid: bool
    issues: List[ValidationIssue]
    summary: str


# ============================================================================
# AGENT 6: FINAL QA RESULTS
# ============================================================================

class QAIssue(BaseModel):
    """Single QA issue"""
    severity: str = Field(description="critical, warning, info")
    category: str = Field(description="completeness, consistency, accuracy, professionalism, ats")
    location: str = Field(description="Where in resume")
    issue: str = Field(description="Clear description of the problem")
    recommendation: str = Field(description="How to fix it")
    example: Optional[str] = Field(default=None, description="Specific example if helpful")


class QAReport(BaseModel):
    """Comprehensive QA report from Agent 6"""
    overall_status: str = Field(description="pass, pass_with_warnings, fail")
    overall_score: int = Field(ge=0, le=100, description="Overall quality score")
    ready_to_submit: bool
    
    section_scores: Dict[str, int] = Field(description="Score for each section (0-100)")
    issues: List[QAIssue]
    strengths: List[str]
    areas_for_improvement: List[str]
    
    ats_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="ATS optimization analysis"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resume statistics (including page count)"
    )
    final_recommendation: str


# ============================================================================
# PIPELINE STATE
# ============================================================================

class PipelineState(BaseModel):
    """Tracks state across entire pipeline"""
    job_folder: str
    company_name: str
    job_title: str
    
    # Agent outputs (Phases 1-3)
    job_analysis: Optional[JobAnalysis] = None
    content_selection: Optional[ContentSelection] = None
    resume_draft: Optional[ResumeDraft] = None
    validation_result: Optional[ValidationResult] = None
    edited_resume: Optional[ResumeDraft] = None  # After Agent 5
    qa_report: Optional[QAReport] = None  # After Agent 6
    
    # Status tracking
    current_stage: str = "initialized"
    completed_stages: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Metadata
    pdf_generated: bool = False
    pdf_path: Optional[str] = None
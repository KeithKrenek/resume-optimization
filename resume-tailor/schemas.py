"""
Pydantic Schemas for Multi-Agent Resume Generation
Provides type safety and validation for data passing between agents
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
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
# AGENT 2: CONTENT SELECTOR OUTPUT
# ============================================================================

class SelectedExperience(BaseModel):
    """Experience selected from database with provenance"""
    source_id: str = Field(description="Database ID (e.g., 'exp_draper_member_technical_staff_2019_2025')")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Match score to job requirements")
    match_reasons: List[str] = Field(description="Why this experience was selected")
    
    # Exact text from database
    company: str
    title: str
    dates: str
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
    dates: str
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
    selected_publications: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Contact info (exact from database)
    contact_info: Dict[str, str]
    
    # Selection metadata
    selection_strategy: str = Field(
        description="Explanation of selection approach"
    )
    coverage_analysis: Dict[str, Any] = Field(
        description="How well selection covers requirements"
    )


# ============================================================================
# AGENT 3: RESUME DRAFTER OUTPUT
# ============================================================================

class ResumeDraft(BaseModel):
    """Draft resume JSON (structure matches target output)"""
    contact: Dict[str, str]
    professional_summary: str
    technical_expertise: Dict[str, Any]
    experience: List[Dict[str, Any]]
    bulleted_projects: List[Dict[str, Any]]
    work_samples: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]]
    publications: List[Dict[str, Any]] = Field(default_factory=list)
    awards_recognition: List[str] = Field(default_factory=list)
    
    # Metadata for validation
    citations: Dict[str, str] = Field(
        description="Map of content to source_id"
    )


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
        description="Resume statistics"
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

    # Workflow configuration (NEW for Phase 3 - dynamic workflows)
    workflow_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dynamic workflow configuration with enabled sections and agents"
    )

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

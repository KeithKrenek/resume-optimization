"""
Multi-Agent Resume Generation Orchestrator - Enhanced Implementation
Includes URL/text JD handling, company scraping, and automatic folder setup
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import anthropic
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import config, validate_config
from state_manager import StateManager
from job_analyzer import JobAnalyzerAgent
from content_selector import ContentSelectorAgent
from resume_drafter import ResumeDrafterAgent
from fabrication_validator import FabricationValidatorAgent
from voice_style_editor import VoiceStyleEditorAgent
from final_qa import FinalQAAgent
from schemas import PipelineState

console = Console()


class ResumeOrchestrator:
    """
    Orchestrates the complete multi-agent resume generation pipeline
    
    Phase 1 (Analysis & Selection):
    - Agent 1: Job Analyzer
    - Agent 2: Content Selector
    
    Phase 2 (Generation & Validation):
    - Agent 3: Resume Drafter
    - Agent 4: Fabrication Validator
    
    Phase 3 (Polish & Quality):
    - Agent 5: Voice & Style Editor
    - Agent 6: Final QA
    """
    
    def __init__(
        self,
        max_validation_retries: int = 2,
        max_qa_retries: int = 1
    ):
        """
        Initialize orchestrator and all agents
        
        Args:
            max_validation_retries: Maximum retries if validation fails
            max_qa_retries: Maximum retries if QA fails
        """
        validate_config()
        
        # Setup API client
        provider, api_key = config.get_primary_api_key()
        if provider != "anthropic":
            console.print("[yellow]Warning: Only Anthropic provider currently supported[/yellow]")
            api_key = config.anthropic_api_key
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.default_ai_model
        self.max_validation_retries = max_validation_retries
        self.max_qa_retries = max_qa_retries
        
        # Initialize all agents
        self.job_analyzer = JobAnalyzerAgent(self.client, self.model)
        self.content_selector = ContentSelectorAgent(self.client, self.model)
        self.resume_drafter = ResumeDrafterAgent(self.client, self.model)
        self.fabrication_validator = FabricationValidatorAgent(self.client, self.model)
        self.voice_style_editor = VoiceStyleEditorAgent(self.client, self.model)
        self.final_qa = FinalQAAgent(self.client, self.model)
        
        # State manager will be initialized per job
        self.state_manager: Optional[StateManager] = None
        
        console.print("[green]✓ Orchestrator initialized - All 6 agents ready[/green]")
        console.print(f"[dim]Model: {self.model}[/dim]")
        console.print(f"[dim]Validation retries: {self.max_validation_retries}, QA retries: {self.max_qa_retries}[/dim]")
    
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filenames"""
        # Remove or replace unsafe characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces and multiple underscores
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'_+', '_', text)
        # Limit length
        return text[:50].strip('_')
    
    def _scrape_url_content(self, url: str) -> Optional[str]:
        """
        Scrape content from a URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            console.print(f"[cyan]Fetching content from URL...[/cyan]")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
            
            console.print(f"[green]✓ Fetched {len(clean_text)} characters from URL[/green]")
            return clean_text
            
        except requests.RequestException as e:
            console.print(f"[red]Failed to fetch URL: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error scraping URL: {e}[/red]")
            return None
    
    def _scrape_company_info(self, url: str) -> Dict[str, str]:
        """
        Scrape basic company information from URL
        
        Args:
            url: Company website URL
            
        Returns:
            Dict with company info (name, description, etc.)
        """
        company_info = {
            "url": url,
            "name": "",
            "description": "",
            "scraped_at": datetime.now().isoformat()
        }
        
        try:
            console.print(f"[cyan]Fetching company info from {url}...[/cyan]")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract company name from title or og:site_name
            if soup.title:
                company_info["name"] = soup.title.string.strip()
            
            og_site_name = soup.find("meta", property="og:site_name")
            if og_site_name and og_site_name.get("content"):
                company_info["name"] = og_site_name["content"].strip()
            
            # Try to get description from meta tags
            description_meta = soup.find("meta", attrs={"name": "description"})
            if description_meta and description_meta.get("content"):
                company_info["description"] = description_meta["content"].strip()
            
            og_description = soup.find("meta", property="og:description")
            if og_description and og_description.get("content"):
                company_info["description"] = og_description["content"].strip()
            
            console.print(f"[green]✓ Company info retrieved[/green]")
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch company info: {e}[/yellow]")
        
        return company_info
    
    def _extract_company_and_title_from_jd(self, jd_text: str) -> Tuple[str, str]:
        """
        Try to extract company name and job title from job description text
        
        Args:
            jd_text: Job description text
            
        Returns:
            Tuple of (company_name, job_title)
        """
        company_name = "Company"
        job_title = "Position"
        
        lines = jd_text.split('\n')[:20]  # Check first 20 lines
        
        # Common patterns for job titles
        title_patterns = [
            r'(?:job title|position|role):\s*(.+)',
            r'^(.+?)\s+(?:position|role|opening)',
            r'hiring\s+(?:a|an)?\s*(.+)',
        ]
        
        # Common patterns for company names
        company_patterns = [
            r'(?:company|organization|employer):\s*(.+)',
            r'^(.+?)\s+is\s+(?:hiring|seeking|looking)',
            r'at\s+(.+?)\s+(?:we|our)',
        ]
        
        for line in lines:
            line = line.strip()
            
            # Try to extract job title
            if not job_title or job_title == "Position":
                for pattern in title_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        job_title = match.group(1).strip()
                        break
            
            # Try to extract company name
            if not company_name or company_name == "Company":
                for pattern in company_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        company_name = match.group(1).strip()
                        break
        
        return company_name, job_title
    
    def process_job_description_input(
        self,
        jd_input: str,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company_url: Optional[str] = None
    ) -> Tuple[str, str, str, Optional[Dict]]:
        """
        Process job description input (URL or text) and extract metadata
        
        Args:
            jd_input: URL or raw text of job description
            company_name: Optional company name override
            job_title: Optional job title override
            company_url: Optional company website URL
            
        Returns:
            Tuple of (jd_text, company_name, job_title, company_info)
        """
        console.print("\n[bold cyan]Processing Job Description Input[/bold cyan]")
        
        jd_text = ""
        company_info = None
        
        # Check if input is a URL
        jd_input = jd_input.strip()
        is_url = jd_input.startswith(('http://', 'https://'))
        
        if is_url:
            console.print(f"[cyan]Input detected as URL[/cyan]")
            jd_text = self._scrape_url_content(jd_input)
            if not jd_text:
                raise ValueError("Failed to fetch job description from URL")
        else:
            console.print(f"[cyan]Input detected as raw text ({len(jd_input)} chars)[/cyan]")
            jd_text = jd_input
        
        # Extract company/title from JD if not provided
        if not company_name or not job_title:
            extracted_company, extracted_title = self._extract_company_and_title_from_jd(jd_text)
            company_name = company_name or extracted_company
            job_title = job_title or extracted_title
            
            console.print(f"[yellow]Extracted from JD: {company_name} - {job_title}[/yellow]")
        
        # Fetch company info if URL provided
        if company_url:
            company_info = self._scrape_company_info(company_url)
        
        console.print(f"[green]✓ Job description processed:[/green]")
        console.print(f"  Company: {company_name}")
        console.print(f"  Title: {job_title}")
        console.print(f"  JD Length: {len(jd_text)} characters")
        
        return jd_text, company_name, job_title, company_info
    
    def create_job_folder(
        self,
        company_name: str,
        job_title: str,
        jd_text: str,
        company_info: Optional[Dict] = None
    ) -> str:
        """
        Create timestamped folder for job application with all necessary files
        
        Args:
            company_name: Company name
            job_title: Job title
            jd_text: Job description text
            company_info: Optional company information dict
            
        Returns:
            Path to created folder
        """
        console.print("\n[bold cyan]Creating Job Application Folder[/bold cyan]")
        
        # Create folder name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_company = self._sanitize_filename(company_name)
        safe_title = self._sanitize_filename(job_title)
        folder_name = f"{timestamp}_{safe_company}_{safe_title}"
        folder_path = os.path.join(config.applications_folder, folder_name)
        
        # Create directory structure
        os.makedirs(folder_path, exist_ok=True)
        os.makedirs(os.path.join(folder_path, "agent_outputs"), exist_ok=True)
        
        # Save job description
        jd_path = os.path.join(folder_path, "job_description.md")
        with open(jd_path, 'w', encoding='utf-8') as f:
            f.write(f"# Job Description: {job_title}\n")
            f.write(f"## Company: {company_name}\n")
            f.write(f"## Date: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("---\n\n")
            f.write(jd_text)
        
        console.print(f"[green]✓ Saved:[/green] job_description.md")
        
        # Save company info if available
        if company_info:
            company_info_path = os.path.join(folder_path, "company_info.json")
            with open(company_info_path, 'w', encoding='utf-8') as f:
                json.dump(company_info, f, indent=2)
            console.print(f"[green]✓ Saved:[/green] company_info.json")
        
        # Create empty placeholder files for user reference
        placeholders = {
            "cover_letter_draft.md": "# Cover Letter Draft\n\n[To be generated or written manually]\n",
            "notes.md": f"# Application Notes: {company_name} - {job_title}\n\n## Key Points\n\n## Follow-up\n\n## Timeline\n\n",
            "questions.md": "# Interview Questions\n\n## Technical Questions\n\n## Behavioral Questions\n\n## Questions for Them\n\n"
        }
        
        for filename, content in placeholders.items():
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        console.print(f"[green]✓ Created placeholder files[/green]")
        console.print(f"\n[bold green]✓ Job folder created:[/bold green] {folder_name}")
        console.print(f"[dim]Path: {folder_path}[/dim]")
        
        return folder_path
    
    def clean_unicode_escapes(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean Unicode escape sequences in JSON data
        Replaces common problematic characters with proper Unicode
        
        Args:
            json_data: Dictionary containing JSON data
            
        Returns:
            Cleaned dictionary
        """
        # Mapping of Unicode escapes to actual characters
        replacements = {
            r'\u2013': '–',  # en dash
            r'\u2014': '—',  # em dash
            r'\u2019': "'",  # right single quotation mark
            r'\u201c': '"',  # left double quotation mark
            r'\u201d': '"',  # right double quotation mark
            r'\u2022': '•',  # bullet
            r'\u00d7': '×',  # multiplication sign
            r'\u221d': '∝',  # proportional to
            r'\u2192': '→',  # rightwards arrow
            r'\u2190': '←',  # leftwards arrow
            r'\u2264': '≤',  # less than or equal to
            r'\u2265': '≥',  # greater than or equal to
            r'\u00b1': '±',  # plus-minus sign
            r'\u2248': '≈',  # almost equal to
        }
        
        # Convert to JSON string for replacement
        json_str = json.dumps(json_data, ensure_ascii=False)
        
        # Replace each Unicode escape
        for escape, char in replacements.items():
            json_str = json_str.replace(escape, char)
        
        # Convert back to dict
        return json.loads(json_str)
    
    def save_resume_json(
        self,
        resume_data: Dict[str, Any],
        output_path: str,
        clean_unicode: bool = True
    ) -> str:
        """
        Save resume JSON with optional Unicode cleaning
        
        Args:
            resume_data: Resume dictionary
            output_path: Path to save JSON file
            clean_unicode: Whether to clean Unicode escapes
            
        Returns:
            Path to saved file
        """
        if clean_unicode:
            resume_data = self.clean_unicode_escapes(resume_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓ Saved clean JSON:[/green] {os.path.basename(output_path)}")
        
        return output_path
    
    def load_database(self) -> Dict[str, Any]:
        """Load resume database"""
        console.print(f"[cyan]Loading database...[/cyan]")
        
        with open(config.database_path, 'r', encoding='utf-8') as f:
            database = json.load(f)
        
        exp_count = len(database.get('experiences', {}))
        proj_count = len(database.get('projects', {}))
        
        console.print(f"[green]✓ Database loaded:[/green] {exp_count} experiences, {proj_count} projects")
        
        return database
    
    def load_target_format_example(self) -> Optional[Dict[str, Any]]:
        """Load target format example if available"""
        example_path = Path(__file__).parent / "resume-target-output.json"
        
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def run_phase1(
        self,
        jd_text: str,
        company_name: str,
        job_title: str,
        job_folder: Optional[str] = None,
        company_info: Optional[Dict] = None
    ) -> PipelineState:
        """
        Run Phase 1: Job Analysis + Content Selection
        
        Args:
            jd_text: Job description text
            company_name: Company name
            job_title: Job title
            job_folder: Optional existing folder path
            company_info: Optional company information
            
        Returns:
            Pipeline state with results
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Multi-Agent Resume Generation Pipeline[/bold white]\n"
            "[dim]Phase 1: Job Analysis + Content Selection[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")
        
        # Create or use existing folder
        if job_folder is None:
            job_folder = self.create_job_folder(company_name, job_title, jd_text, company_info)
        
        # Initialize state manager
        self.state_manager = StateManager(job_folder)
        
        try:
            # Load database
            database = self.load_database()
            
            # AGENT 1: Analyze job description
            if self.state_manager.can_skip_stage("job_analysis_complete"):
                console.print("\n[yellow]⊳ Skipping Job Analysis (already complete)[/yellow]")
                job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
                from schemas import JobAnalysis
                job_analysis = JobAnalysis(**job_analysis_data)
            else:
                job_analysis = self.job_analyzer.analyze(jd_text)
                self.state_manager.set_job_analysis(job_analysis)
            
            # AGENT 2: Select content from database
            if self.state_manager.can_skip_stage("content_selection_complete"):
                console.print("\n[yellow]⊳ Skipping Content Selection (already complete)[/yellow]")
                content_data = self.state_manager.load_agent_output("content_selector")
                from schemas import ContentSelection
                content_selection = ContentSelection(**content_data)
            else:
                content_selection = self.content_selector.select(
                    job_analysis=job_analysis,
                    database=database
                )
                self.state_manager.set_content_selection(content_selection)
            
            # Save state
            self.state_manager.state.current_stage = "phase1_complete"
            self.state_manager.save_state()
            
            # Show summary
            self._show_phase1_summary(job_analysis, content_selection)
            
            return self.state_manager.state
            
        except Exception as e:
            self.state_manager.add_error(f"Phase 1 failed: {str(e)}")
            console.print(f"[bold red]✗ Phase 1 Failed:[/bold red] {e}")
            raise
    
    def run_phase2(
        self,
        job_folder: Optional[str] = None
    ) -> PipelineState:
        """
        Run Phase 2: Resume Generation + Validation
        
        Args:
            job_folder: Optional folder path (resume from existing)
            
        Returns:
            Pipeline state with results
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Phase 2: Resume Generation + Validation[/bold white]\n"
            "[dim]Agents 3 & 4 with automatic retry[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")
        
        # Initialize or restore state manager
        if job_folder:
            self.state_manager = StateManager(job_folder)
        
        if not self.state_manager:
            raise ValueError("No job folder - must run Phase 1 first or provide job_folder")
        
        try:
            # Load Phase 1 results
            if not self.state_manager.state.job_analysis:
                job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
                from schemas import JobAnalysis
                self.state_manager.state.job_analysis = JobAnalysis(**job_analysis_data)
            
            if not self.state_manager.state.content_selection:
                content_data = self.state_manager.load_agent_output("content_selector")
                from schemas import ContentSelection
                self.state_manager.state.content_selection = ContentSelection(**content_data)
            
            job_analysis = self.state_manager.state.job_analysis
            content_selection = self.state_manager.state.content_selection
            
            # Load target format example
            target_format = self.load_target_format_example()
            
            # AGENT 3 + 4: Generate and validate with retry
            validation_passed = False
            resume_draft = None
            validation_result = None
            
            for attempt in range(self.max_validation_retries + 1):
                if attempt > 0:
                    console.print(f"\n[yellow]Retry {attempt}/{self.max_validation_retries}: Regenerating resume...[/yellow]")
                
                # AGENT 3: Generate resume
                if attempt == 0 and self.state_manager.can_skip_stage("draft_complete"):
                    console.print("\n[yellow]⊳ Using existing draft[/yellow]")
                    draft_data = self.state_manager.load_agent_output("resume_drafter")
                    from schemas import ResumeDraft
                    resume_draft = ResumeDraft(**draft_data)
                else:
                    resume_draft = self.resume_drafter.draft(
                        job_analysis=job_analysis,
                        content_selection=content_selection,
                        target_format_example=target_format
                    )
                    self.state_manager.set_resume_draft(resume_draft)
                
                # AGENT 4: Validate
                validation_result = self.fabrication_validator.validate(
                    resume_draft=resume_draft,
                    content_selection=content_selection
                )
                self.state_manager.set_validation_result(validation_result)
                
                if validation_result.is_valid:
                    validation_passed = True
                    console.print("\n[bold green]✓ Validation Passed[/bold green]")
                    break
                else:
                    console.print(f"\n[bold red]✗ Validation Failed (Attempt {attempt + 1})[/bold red]")
                    
                    if attempt >= self.max_validation_retries:
                        console.print("[bold red]Maximum retries reached[/bold red]")
                        break
            
            if not validation_passed:
                raise ValueError("Resume validation failed after all retries")
            
            # Save validated resume with Unicode cleaning
            resume_path = os.path.join(self.state_manager.job_folder, "resume_validated.json")
            self.save_resume_json(resume_draft.model_dump(), resume_path, clean_unicode=True)
            
            # Save state
            self.state_manager.state.current_stage = "phase2_complete"
            self.state_manager.save_state()
            
            # Show summary
            self._show_phase2_summary(resume_draft, validation_result)
            
            return self.state_manager.state
            
        except Exception as e:
            self.state_manager.add_error(f"Phase 2 failed: {str(e)}")
            console.print(f"[bold red]✗ Phase 2 Failed:[/bold red] {e}")
            raise
    
    def run_phase3(
        self,
        job_folder: Optional[str] = None,
        skip_style_editing: bool = False
    ) -> PipelineState:
        """
        Run Phase 3: Style Polish + Final QA
        
        Args:
            job_folder: Optional folder path (resume from existing)
            skip_style_editing: Skip Agent 5 if already polished
            
        Returns:
            Pipeline state with results
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Phase 3: Style Polish + Final QA[/bold white]\n"
            "[dim]Agents 5 & 6 with automatic retry[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")
        
        # Initialize or restore state manager
        if job_folder:
            self.state_manager = StateManager(job_folder)
        
        if not self.state_manager:
            raise ValueError("No job folder - must run Phase 2 first or provide job_folder")
        
        try:
            # Load Phase 2 result
            if not self.state_manager.state.resume_draft:
                draft_data = self.state_manager.load_agent_output("resume_drafter")
                from schemas import ResumeDraft
                self.state_manager.state.resume_draft = ResumeDraft(**draft_data)
            
            resume_draft = self.state_manager.state.resume_draft
            
            # AGENT 5: Style editing (optional)
            if skip_style_editing:
                console.print("\n[yellow]⊳ Skipping style editing[/yellow]")
                edited_resume = resume_draft
            else:
                if self.state_manager.can_skip_stage("style_editing_complete"):
                    console.print("\n[yellow]⊳ Using existing edited version[/yellow]")
                    edited_data = self.state_manager.load_agent_output("voice_style_editor")
                    from schemas import ResumeDraft
                    edited_resume = ResumeDraft(**edited_data)
                else:
                    edited_resume = self.voice_style_editor.edit(
                        resume_draft=resume_draft,
                        verify_facts=True
                    )
                    self.state_manager.set_edited_resume(edited_resume)
            
            # AGENT 6: Final QA with retry
            qa_passed = False
            qa_report = None
            
            # Load job analysis for ATS check
            job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
            from schemas import JobAnalysis
            job_analysis = JobAnalysis(**job_analysis_data)
            
            for attempt in range(self.max_qa_retries + 1):
                if attempt > 0:
                    console.print(f"\n[yellow]QA Retry {attempt}/{self.max_qa_retries}[/yellow]")
                
                qa_report = self.final_qa.review(
                    resume_draft=edited_resume,
                    job_requirements=job_analysis.model_dump()
                )
                self.state_manager.set_qa_report(qa_report)
                
                # Check if passed or passed with warnings
                if qa_report.overall_status in ["pass", "pass_with_warnings"]:
                    qa_passed = True
                    break
                else:
                    if attempt >= self.max_qa_retries:
                        console.print("[bold yellow]QA warnings present but proceeding[/bold yellow]")
                        qa_passed = True  # Allow proceeding with warnings
                        break
            
            # Save final resume with Unicode cleaning
            final_resume_path = os.path.join(self.state_manager.job_folder, "resume_final.json")
            self.save_resume_json(edited_resume.model_dump(), final_resume_path, clean_unicode=True)
            
            # Save state
            self.state_manager.state.current_stage = "phase3_complete"
            self.state_manager.save_state()
            
            # Show summary
            self._show_phase3_summary(qa_report)
            
            return self.state_manager.state
            
        except Exception as e:
            self.state_manager.add_error(f"Phase 3 failed: {str(e)}")
            console.print(f"[bold red]✗ Phase 3 Failed:[/bold red] {e}")
            raise
    
    def generate_pdf(self) -> Optional[str]:
        """
        Generate PDF from final resume JSON using Node.js script
        
        Returns:
            Path to generated PDF or None if failed
        """
        if not self.state_manager:
            console.print("[red]No active job folder[/red]")
            return None
        
        console.print("\n[cyan]Generating PDF...[/cyan]")
        
        try:
            import subprocess
            
            # Find generate-pdf.js script
            script_path = Path(__file__).parent / "generate-pdf.js"
            
            if not script_path.exists():
                console.print(f"[red]PDF generator script not found: {script_path}[/red]")
                return None
            
            # Run Node.js script with job folder as argument
            result = subprocess.run(
                ["node", str(script_path), self.state_manager.job_folder],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                console.print("[green]✓ PDF generated successfully[/green]")
                console.print(result.stdout)
                
                # Find generated PDF
                pdf_files = list(Path(self.state_manager.job_folder).glob("*.pdf"))
                if pdf_files:
                    pdf_path = str(pdf_files[-1])  # Get most recent
                    self.state_manager.state.pdf_generated = True
                    self.state_manager.state.pdf_path = pdf_path
                    self.state_manager.save_state()
                    return pdf_path
            else:
                console.print(f"[red]PDF generation failed:[/red]")
                console.print(result.stderr)
                
        except FileNotFoundError:
            console.print("[red]Node.js not found - please install Node.js to generate PDFs[/red]")
        except subprocess.TimeoutExpired:
            console.print("[red]PDF generation timed out[/red]")
        except Exception as e:
            console.print(f"[red]Error generating PDF: {e}[/red]")
        
        return None
    
    def _show_phase1_summary(self, job_analysis, content_selection) -> None:
        """Display Phase 1 results summary"""
        console.print("\n[bold green]" + "="*70 + "[/bold green]")
        console.print("[bold green]Phase 1 Complete: Job Analyzed & Content Selected[/bold green]")
        console.print("[bold green]" + "="*70 + "[/bold green]\n")
        
        # Job Analysis Summary
        table = Table(title="Job Analysis", show_header=True, header_style="bold cyan")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Role Type", job_analysis.role_type)
        table.add_row("Must-Have Requirements", str(len(job_analysis.must_have_requirements)))
        table.add_row("Nice-to-Have Requirements", str(len(job_analysis.nice_to_have_requirements)))
        table.add_row("Technical Keywords", str(len(job_analysis.technical_keywords)))
        table.add_row("Domain Keywords", str(len(job_analysis.domain_keywords)))
        
        console.print(table)
        
        # Content Selection Summary
        coverage = content_selection.coverage_analysis
        coverage_pct = coverage.get('coverage_percentage', 0)
        
        table2 = Table(title="Content Selection", show_header=True, header_style="bold cyan")
        table2.add_column("Section", style="cyan")
        table2.add_column("Count/Score", style="white")
        
        table2.add_row("Selected Experiences", str(len(content_selection.selected_experiences)))
        table2.add_row("Selected Projects", str(len(content_selection.selected_projects)))
        table2.add_row("Requirement Coverage", f"{coverage_pct}%")
        table2.add_row("Skills Categories", str(len(content_selection.selected_skills)))
        
        console.print(table2)
    
    def _show_phase2_summary(self, resume_draft, validation_result) -> None:
        """Display Phase 2 results summary"""
        console.print("\n[bold green]" + "="*70 + "[/bold green]")
        console.print("[bold green]Phase 2 Complete: Resume Generated & Validated[/bold green]")
        console.print("[bold green]" + "="*70 + "[/bold green]\n")
        
        # Resume Statistics
        table = Table(title="Resume Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Section", style="cyan")
        table.add_column("Count", style="white")
        
        exp_count = len(resume_draft.experience)
        proj_count = len(resume_draft.bulleted_projects)
        total_achievements = sum(len(exp.get('achievements', [])) for exp in resume_draft.experience)
        
        table.add_row("Experiences", str(exp_count))
        table.add_row("Projects", str(proj_count))
        table.add_row("Achievement Bullets", str(total_achievements))
        table.add_row("Skills Categories", str(len(resume_draft.technical_expertise)))
        table.add_row("Summary Length", f"{len(resume_draft.professional_summary)} chars")
        
        console.print(table)
        
        # Validation Results
        table2 = Table(title="Validation Results", show_header=True, header_style="bold cyan")
        table2.add_column("Check", style="cyan")
        table2.add_column("Status", style="white")
        
        critical = sum(1 for i in validation_result.issues if i.severity == 'critical')
        warnings = sum(1 for i in validation_result.issues if i.severity == 'warning')
        
        status_color = "green" if validation_result.is_valid else "red"
        status_text = "✓ PASS" if validation_result.is_valid else "✗ FAIL"
        
        table2.add_row("Overall", f"[{status_color}]{status_text}[/{status_color}]")
        table2.add_row("Critical Issues", f"[red]{critical}[/red]" if critical > 0 else "[green]0[/green]")
        table2.add_row("Warnings", f"[yellow]{warnings}[/yellow]" if warnings > 0 else "[green]0[/green]")
        
        console.print(table2)
    
    def _show_phase3_summary(self, qa_report) -> None:
        """Display Phase 3 results summary"""
        console.print("\n[bold green]" + "="*70 + "[/bold green]")
        console.print("[bold green]Phase 3 Complete: Resume Polished & Quality Assured[/bold green]")
        console.print("[bold green]" + "="*70 + "[/bold green]\n")
        
        # QA Results
        table = Table(title="Final Quality Assessment", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Score/Status", style="white")
        
        status_color = "green" if qa_report.overall_status == "pass" else "yellow" if qa_report.overall_status == "pass_with_warnings" else "red"
        
        table.add_row("Overall Score", f"{qa_report.overall_score}/100")
        table.add_row("Status", f"[{status_color}]{qa_report.overall_status.upper().replace('_', ' ')}[/{status_color}]")
        table.add_row("Ready to Submit", "✓ Yes" if qa_report.ready_to_submit else "⚠ Review Needed")
        
        console.print(table)
        
        # Section Scores
        if qa_report.section_scores:
            table2 = Table(title="Section Quality Scores", show_header=True, header_style="bold cyan")
            table2.add_column("Section", style="cyan")
            table2.add_column("Score", style="white")
            
            for section, score in sorted(qa_report.section_scores.items(), key=lambda x: x[1], reverse=True):
                score_color = "green" if score >= 90 else "yellow" if score >= 75 else "red"
                table2.add_row(section.replace('_', ' ').title(), f"[{score_color}]{score}[/{score_color}]")
            
            console.print(table2)
        
        console.print(f"\n[bold]{qa_report.final_recommendation}[/bold]")
        console.print(f"\n[dim]Resume saved to: {self.state_manager.job_folder}/resume_final.json[/dim]")
    
    def generate_resume(
        self,
        jd_input: str,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company_url: Optional[str] = None,
        auto_generate_pdf: bool = False,
        skip_style_editing: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point for complete resume generation (all 3 phases)
        
        Args:
            jd_input: Job description URL or text
            company_name: Optional company name (will extract if not provided)
            job_title: Optional job title (will extract if not provided)
            company_url: Optional company website URL
            auto_generate_pdf: Automatically generate PDF at end
            skip_style_editing: Skip Agent 5 if not needed
            
        Returns:
            Results dictionary
        """
        # Process JD input
        jd_text, company_name, job_title, company_info = self.process_job_description_input(
            jd_input, company_name, job_title, company_url
        )
        
        # Run Phase 1
        state = self.run_phase1(jd_text, company_name, job_title, company_info=company_info)
        
        # Run Phase 2
        state = self.run_phase2()
        
        # Run Phase 3
        state = self.run_phase3(skip_style_editing=skip_style_editing)
        
        # Optionally generate PDF
        pdf_path = None
        if auto_generate_pdf:
            pdf_path = self.generate_pdf()
        
        # Mark as completed
        self.state_manager.mark_completed()
        
        return {
            "success": True,
            "folder_path": state.job_folder,
            "state": state,
            "phases_completed": ["phase1", "phase2", "phase3"],
            "pdf_generated": pdf_path is not None,
            "pdf_path": pdf_path
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Multi-Agent Resume Generator - Enhanced with URL/text input support"
    )
    parser.add_argument("--jd", help="Job description (URL or text file path or raw text)")
    parser.add_argument("--company", help="Company name (optional - will extract)")
    parser.add_argument("--title", help="Job title (optional - will extract)")
    parser.add_argument("--company-url", help="Company website URL")
    parser.add_argument("--pdf", action="store_true", help="Auto-generate PDF")
    parser.add_argument("--phase1-only", action="store_true", help="Run only Phase 1")
    parser.add_argument("--phase2-only", action="store_true", help="Run only Phase 2")
    parser.add_argument("--phase3-only", action="store_true", help="Run only Phase 3")
    parser.add_argument("--resume-folder", help="Resume from existing folder")
    parser.add_argument("--skip-style", action="store_true", help="Skip style editing (Agent 5)")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = ResumeOrchestrator()
    
    # Resume existing pipeline
    if args.resume_folder:
        console.print(f"[cyan]Resuming from folder: {args.resume_folder}[/cyan]")
        
        if args.phase2_only:
            state = orchestrator.run_phase2(job_folder=args.resume_folder)
        elif args.phase3_only:
            state = orchestrator.run_phase3(job_folder=args.resume_folder, skip_style_editing=args.skip_style)
        else:
            # Run remaining phases
            state = orchestrator.run_phase2(job_folder=args.resume_folder)
            state = orchestrator.run_phase3(skip_style_editing=args.skip_style)
        
        if args.pdf:
            orchestrator.generate_pdf()
        
        console.print("\n[bold green]✓ Pipeline Complete![/bold green]")
        return
    
    # Get JD input
    jd_input = None
    if args.jd:
        # Check if it's a file path
        if os.path.exists(args.jd):
            with open(args.jd, 'r', encoding='utf-8') as f:
                jd_input = f.read()
        else:
            # Assume it's either a URL or raw text
            jd_input = args.jd
    else:
        # For testing, use default
        console.print("[yellow]No JD provided - using test mode[/yellow]")
        test_jd_path = "test_job_description.md"
        if os.path.exists(test_jd_path):
            with open(test_jd_path, 'r', encoding='utf-8') as f:
                jd_input = f.read()
        else:
            console.print("[red]No job description available[/red]")
            return
    
    # Run pipeline
    if args.phase1_only:
        # Process JD first
        jd_text, company, title, company_info = orchestrator.process_job_description_input(
            jd_input, args.company, args.title, args.company_url
        )
        
        results = orchestrator.run_phase1(
            jd_text=jd_text,
            company_name=company,
            job_title=title,
            company_info=company_info
        )
        console.print("\n[bold green]✓ Phase 1 Complete![/bold green]")
    else:
        results = orchestrator.generate_resume(
            jd_input=jd_input,
            company_name=args.company,
            job_title=args.title,
            company_url=args.company_url,
            auto_generate_pdf=args.pdf,
            skip_style_editing=args.skip_style
        )
        
        if results["success"]:
            console.print("\n[bold green]✓ Complete Pipeline Finished![/bold green]")
            console.print(f"[green]Results saved to:[/green] {results['folder_path']}")
            
            if results['pdf_generated']:
                console.print(f"[green]PDF generated:[/green] {results['pdf_path']}")
        else:
            console.print("\n[bold red]✗ Pipeline failed[/bold red]")
            exit(1)


if __name__ == "__main__":
    main()

"""
Multi-Agent Resume Generation Orchestrator - Complete Implementation
Manages the pipeline of 6 specialized agents across 3 phases
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import anthropic
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
    
    def create_job_folder(
        self,
        company_name: str,
        job_title: str,
        jd_text: str
    ) -> str:
        """
        Create timestamped folder for job application
        
        Args:
            company_name: Company name
            job_title: Job title
            jd_text: Job description text
            
        Returns:
            Path to created folder
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        folder_name = f"{timestamp}_{company_name.replace(' ', '_')}_{job_title.replace(' ', '_')}"
        folder_path = os.path.join(config.applications_folder, folder_name)
        
        os.makedirs(folder_path, exist_ok=True)
        
        # Save job description
        jd_path = os.path.join(folder_path, "job_description.md")
        with open(jd_path, 'w', encoding='utf-8') as f:
            f.write(jd_text)
        
        console.print(f"[green]✓ Created folder:[/green] {folder_name}")
        
        return folder_path
    
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
        job_folder: Optional[str] = None
    ) -> PipelineState:
        """
        Run Phase 1: Job Analysis + Content Selection
        
        Args:
            jd_text: Job description text
            company_name: Company name
            job_title: Job title
            job_folder: Optional existing folder path
            
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
            job_folder = self.create_job_folder(company_name, job_title, jd_text)
        
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
            
            # Mark phase 1 complete
            self.state_manager.state.current_stage = "phase1_complete"
            self.state_manager.save_state()
            
            # Show summary
            self._show_phase1_summary(job_analysis, content_selection)
            
            return self.state_manager.state
            
        except Exception as e:
            console.print(f"\n[red]✗ Pipeline failed: {e}[/red]")
            if self.state_manager:
                self.state_manager.add_error(str(e))
            raise
    
    def run_phase2(
        self,
        job_folder: Optional[str] = None,
        force_redraft: bool = False
    ) -> PipelineState:
        """
        Run Phase 2: Resume Drafting + Validation
        
        Args:
            job_folder: Optional job folder path (uses current if None)
            force_redraft: Force re-generation even if draft exists
            
        Returns:
            Pipeline state with results
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Multi-Agent Resume Generation Pipeline[/bold white]\n"
            "[dim]Phase 2: Resume Drafting + Validation[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")
        
        # Initialize or use existing state manager
        if job_folder and not self.state_manager:
            self.state_manager = StateManager(job_folder)
        elif not self.state_manager:
            raise ValueError("No state manager initialized. Run phase1 first or provide job_folder.")
        
        state = self.state_manager.state
        
        # Verify Phase 1 is complete
        if "content_selection_complete" not in state.completed_stages:
            console.print("[red]✗ Phase 1 not complete. Run phase1 first.[/red]")
            raise ValueError("Phase 1 must be complete before Phase 2")
        
        try:
            # Load Phase 1 outputs
            from schemas import JobAnalysis, ContentSelection
            
            job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
            job_analysis = JobAnalysis(**job_analysis_data)
            
            content_data = self.state_manager.load_agent_output("content_selector")
            content_selection = ContentSelection(**content_data)
            
            # Load target format example
            target_format = self.load_target_format_example()
            
            # AGENT 3 & 4: Draft + Validate with retry loop
            validation_attempt = 0
            resume_draft = None
            validation_result = None
            
            while validation_attempt <= self.max_validation_retries:
                # Generate or load draft
                if force_redraft or validation_attempt > 0 or not self.state_manager.can_skip_stage("draft_complete"):
                    if validation_attempt > 0:
                        console.print(f"\n[yellow]Retry {validation_attempt}/{self.max_validation_retries}: Regenerating resume...[/yellow]")
                    
                    resume_draft = self.resume_drafter.draft(
                        job_analysis=job_analysis,
                        content_selection=content_selection,
                        target_format_example=target_format
                    )
                    
                    # Save draft
                    self.state_manager.set_resume_draft(resume_draft)
                else:
                    console.print("\n[yellow]⊳ Skipping Resume Drafting (already complete)[/yellow]")
                    from schemas import ResumeDraft
                    draft_data = self.state_manager.load_agent_output("resume_drafter")
                    resume_draft = ResumeDraft(**draft_data)
                
                # AGENT 4: Validate resume
                console.print("\n[cyan]Running validation...[/cyan]")
                
                # Quick structural validation first
                structural_issues = self.fabrication_validator.perform_structural_validation(
                    resume_draft=resume_draft,
                    content_selection=content_selection
                )
                
                if structural_issues:
                    console.print(f"\n[yellow]Found {len(structural_issues)} structural issues[/yellow]")
                    for issue in structural_issues[:5]:  # Show first 5
                        console.print(f"  • {issue.location}: {issue.message}")
                
                # Full validation
                validation_result = self.fabrication_validator.validate(
                    resume_draft=resume_draft,
                    content_selection=content_selection
                )
                
                # Save validation result
                self.state_manager.set_validation_result(validation_result)
                
                # Check if valid
                if validation_result.is_valid:
                    console.print("\n[bold green]✓ Validation passed![/bold green]")
                    break
                else:
                    critical_issues = [i for i in validation_result.issues if i.severity == 'critical']
                    
                    if validation_attempt < self.max_validation_retries:
                        console.print(f"\n[red]✗ Validation failed with {len(critical_issues)} critical issues[/red]")
                        console.print("[yellow]Will retry with corrections...[/yellow]")
                        validation_attempt += 1
                        force_redraft = True  # Force regeneration on retry
                    else:
                        console.print(f"\n[red]✗ Validation failed after {self.max_validation_retries} attempts[/red]")
                        console.print("[yellow]Proceeding with warnings. Manual review recommended.[/yellow]")
                        break
            
            # Mark phase 2 complete
            self.state_manager.state.current_stage = "phase2_complete"
            self.state_manager.save_state()
            
            # Show summary
            self._show_phase2_summary(resume_draft, validation_result)
            
            return self.state_manager.state
            
        except Exception as e:
            console.print(f"\n[red]✗ Phase 2 failed: {e}[/red]")
            if self.state_manager:
                self.state_manager.add_error(str(e))
            raise
    
    def run_phase3(
        self,
        job_folder: Optional[str] = None,
        skip_style_editing: bool = False
    ) -> PipelineState:
        """
        Run Phase 3: Voice & Style Editing + Final QA
        
        Args:
            job_folder: Optional job folder path (uses current if None)
            skip_style_editing: Skip Agent 5 if already perfect
            
        Returns:
            Pipeline state with results
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Multi-Agent Resume Generation Pipeline[/bold white]\n"
            "[dim]Phase 3: Voice & Style Editing + Final QA[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")
        
        # Initialize or use existing state manager
        if job_folder and not self.state_manager:
            self.state_manager = StateManager(job_folder)
        elif not self.state_manager:
            raise ValueError("No state manager initialized. Run previous phases first.")
        
        state = self.state_manager.state
        
        # Verify Phase 2 is complete
        if "validation_complete" not in state.completed_stages:
            console.print("[red]✗ Phase 2 not complete. Run phase2 first.[/red]")
            raise ValueError("Phase 2 must be complete before Phase 3")
        
        try:
            # Load Phase 2 output
            from schemas import ResumeDraft, JobAnalysis
            
            draft_data = self.state_manager.load_agent_output("resume_drafter")
            resume_draft = ResumeDraft(**draft_data)
            
            job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
            job_analysis = JobAnalysis(**job_analysis_data)
            
            # AGENT 5: Voice & Style Editing
            if skip_style_editing or self.state_manager.can_skip_stage("style_editing_complete"):
                if skip_style_editing:
                    console.print("\n[yellow]⊳ Skipping Style Editing (skip requested)[/yellow]")
                else:
                    console.print("\n[yellow]⊳ Skipping Style Editing (already complete)[/yellow]")
                    draft_data = self.state_manager.load_agent_output("voice_style_editor")
                    resume_draft = ResumeDraft(**draft_data)
                edited_resume = resume_draft
            else:
                edited_resume = self.voice_style_editor.edit(
                    resume_draft=resume_draft,
                    verify_facts=True  # Verify no facts changed
                )
                
                # Save edited version
                self.state_manager.set_edited_resume(edited_resume)
            
            # AGENT 6: Final QA with retry
            qa_attempt = 0
            qa_report = None
            
            while qa_attempt <= self.max_qa_retries:
                if qa_attempt > 0:
                    console.print(f"\n[yellow]QA Retry {qa_attempt}/{self.max_qa_retries}[/yellow]")
                
                # Prepare job requirements for ATS check
                job_requirements = {
                    "technical_keywords": job_analysis.technical_keywords,
                    "domain_keywords": job_analysis.domain_keywords,
                    "role_type": job_analysis.role_type
                }
                
                qa_report = self.final_qa.review(
                    resume_draft=edited_resume,
                    job_requirements=job_requirements
                )
                
                # Save QA report
                self.state_manager.set_qa_report(qa_report)
                
                # Check if passed
                if qa_report.overall_status == "pass" or qa_report.overall_status == "pass_with_warnings":
                    break
                else:
                    critical_issues = [i for i in qa_report.issues if i.severity == 'critical']
                    
                    if qa_attempt < self.max_qa_retries and len(critical_issues) > 0:
                        console.print(f"\n[red]✗ QA failed with {len(critical_issues)} critical issues[/red]")
                        console.print("[yellow]Retrying style editing...[/yellow]")
                        qa_attempt += 1
                        
                        # Re-run style editor with focus on issues
                        edited_resume = self.voice_style_editor.edit(
                            resume_draft=resume_draft,
                            verify_facts=True
                        )
                        self.state_manager.set_edited_resume(edited_resume)
                    else:
                        console.print(f"\n[yellow]⚠ QA complete with issues. Manual review recommended.[/yellow]")
                        break
            
            # Mark phase 3 complete
            self.state_manager.state.current_stage = "phase3_complete"
            self.state_manager.save_state()
            
            # Save final resume JSON
            final_path = self._save_final_resume(edited_resume)
            
            # Show summary
            self._show_phase3_summary(qa_report)
            
            return self.state_manager.state
            
        except Exception as e:
            console.print(f"\n[red]✗ Phase 3 failed: {e}[/red]")
            if self.state_manager:
                self.state_manager.add_error(str(e))
            raise
    
    def _save_final_resume(self, resume_draft) -> str:
        """Save final resume JSON to outputs"""
        output_path = os.path.join(
            self.state_manager.job_folder,
            "resume_final.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resume_draft.model_dump(), f, indent=2)
        
        console.print(f"\n[green]✓ Final resume saved:[/green] resume_final.json")
        
        return output_path
    
    def generate_pdf(self, resume_json_path: Optional[str] = None) -> Optional[str]:
        """
        Generate PDF from resume JSON using Node.js script
        
        Args:
            resume_json_path: Path to resume JSON (uses latest if None)
            
        Returns:
            Path to generated PDF or None if failed
        """
        try:
            import subprocess
            
            # Find Node.js script
            script_path = Path(__file__).parent / "generate-pdf.js"
            
            if not script_path.exists():
                console.print("[yellow]Warning: generate-pdf.js not found. Skipping PDF generation.[/yellow]")
                return None
            
            # Use provided path or default
            if not resume_json_path:
                resume_json_path = os.path.join(
                    self.state_manager.job_folder,
                    "resume_final.json"
                )
            
            if not os.path.exists(resume_json_path):
                console.print(f"[yellow]Warning: Resume JSON not found: {resume_json_path}[/yellow]")
                return None
            
            # Generate PDF
            pdf_path = resume_json_path.replace('.json', '.pdf')
            
            console.print("\n[cyan]Generating PDF...[/cyan]")
            result = subprocess.run(
                ['node', str(script_path), resume_json_path, pdf_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                console.print(f"[green]✓ PDF generated:[/green] {os.path.basename(pdf_path)}")
                
                # Update state
                self.state_manager.state.pdf_generated = True
                self.state_manager.state.pdf_path = pdf_path
                self.state_manager.save_state()
                
                return pdf_path
            else:
                console.print(f"[red]✗ PDF generation failed:[/red] {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            console.print("[red]✗ PDF generation timed out[/red]")
            return None
        except Exception as e:
            console.print(f"[yellow]Warning: Could not generate PDF: {e}[/yellow]")
            return None
    
    def _show_phase1_summary(self, job_analysis, content_selection) -> None:
        """Display Phase 1 results summary"""
        console.print("\n[bold green]" + "="*70 + "[/bold green]")
        console.print("[bold green]Phase 1 Complete: Ready for Resume Generation[/bold green]")
        console.print("[bold green]" + "="*70 + "[/bold green]\n")
        
        # Job Analysis Summary
        table = Table(title="Job Analysis", show_header=True, header_style="bold cyan")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Role Type", job_analysis.role_type)
        table.add_row("Must-Have Reqs", str(len(job_analysis.must_have_requirements)))
        table.add_row("Nice-to-Have Reqs", str(len(job_analysis.nice_to_have_requirements)))
        table.add_row("Technical Keywords", str(len(job_analysis.technical_keywords)))
        table.add_row("Role Focus", job_analysis.role_focus[:50] + "...")
        
        console.print(table)
        
        # Content Selection Summary
        table2 = Table(title="Content Selection", show_header=True, header_style="bold cyan")
        table2.add_column("Type", style="cyan")
        table2.add_column("Count", style="white")
        table2.add_column("Avg Relevance", style="green")
        
        avg_exp = sum(e.relevance_score for e in content_selection.selected_experiences) / len(content_selection.selected_experiences)
        avg_proj = sum(p.relevance_score for p in content_selection.selected_projects) / len(content_selection.selected_projects) if content_selection.selected_projects else 0
        
        table2.add_row("Experiences", str(len(content_selection.selected_experiences)), f"{avg_exp:.2f}")
        table2.add_row("Projects", str(len(content_selection.selected_projects)), f"{avg_proj:.2f}")
        table2.add_row("Skills Categories", str(len(content_selection.selected_skills)), "—")
        
        console.print(table2)
        
        # Coverage Analysis
        coverage = content_selection.coverage_analysis
        coverage_pct = coverage.get('coverage_percentage', 0)
        
        console.print(f"\n[cyan]Requirement Coverage:[/cyan] {coverage_pct}%")
        console.print(f"[green]✓ Covered:[/green] {coverage.get('must_have_requirements_covered', 0)}/{coverage.get('must_have_requirements_total', 0)} must-haves")
        
        if coverage.get('missing_requirements'):
            console.print(f"[yellow]⚠ Missing:[/yellow] {', '.join(coverage['missing_requirements'][:3])}")
        
        console.print(f"\n[dim]Outputs saved to: {self.state_manager.get_outputs_directory()}[/dim]")
    
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
        jd_text: str,
        company_name: str,
        job_title: str,
        company_url: Optional[str] = None,
        auto_generate_pdf: bool = False,
        skip_style_editing: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point for complete resume generation (all 3 phases)
        
        Args:
            jd_text: Job description text
            company_name: Company name
            job_title: Job title
            company_url: Optional company URL
            auto_generate_pdf: Automatically generate PDF at end
            skip_style_editing: Skip Agent 5 if not needed
            
        Returns:
            Results dictionary
        """
        # Run Phase 1
        state = self.run_phase1(jd_text, company_name, job_title)
        
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
        description="Multi-Agent Resume Generator - Complete Pipeline"
    )
    parser.add_argument("--jd-file", help="Path to job description file")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--title", help="Job title")
    parser.add_argument("--pdf", action="store_true", help="Auto-generate PDF")
    parser.add_argument("--phase1-only", action="store_true", help="Run only Phase 1")
    parser.add_argument("--phase2-only", action="store_true", help="Run only Phase 2")
    parser.add_argument("--phase3-only", action="store_true", help="Run only Phase 3")
    parser.add_argument("--resume-folder", help="Resume from existing folder")
    parser.add_argument("--skip-style", action="store_true", help="Skip style editing (Agent 5)")
    
    args = parser.parse_args()
    
    # For testing, use defaults
    if not args.resume_folder and not all([args.jd_file, args.company, args.title]):
        console.print("[yellow]Using test job description...[/yellow]")
        args.jd_file = "test_job_description.md"
        args.company = "Anthropic"
        args.title = "Engineering Manager Public Sector"
    
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
    
    # Load JD
    with open(args.jd_file, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Run pipeline
    if args.phase1_only:
        results = orchestrator.run_phase1(
            jd_text=jd_text,
            company_name=args.company,
            job_title=args.title
        )
        console.print("\n[bold green]✓ Phase 1 Complete![/bold green]")
    else:
        results = orchestrator.generate_resume(
            jd_text=jd_text,
            company_name=args.company,
            job_title=args.title,
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

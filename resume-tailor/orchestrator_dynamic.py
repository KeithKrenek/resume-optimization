"""
Dynamic Multi-Agent Resume Generation Orchestrator
Extends the base orchestrator with dynamic workflow configuration capabilities
Allows flexible section and agent selection based on job requirements
"""

import os
import json
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestrator import ResumeOrchestrator
from workflow_configurator import WorkflowConfigurator
from schema_builder import DynamicSchemaBuilder
from schemas import PipelineState, JobAnalysis

console = Console()


class DynamicResumeOrchestrator(ResumeOrchestrator):
    """
    Extended orchestrator with dynamic workflow configuration

    New Capabilities:
    - AI-recommended sections based on job description
    - Interactive or automatic workflow configuration
    - Dynamic resume schema generation
    - Flexible agent pipeline (future: optional agents)
    """

    def __init__(
        self,
        max_validation_retries: int = 2,
        max_qa_retries: int = 1,
        interactive_workflow: bool = False,
        auto_accept_recommendations: bool = True
    ):
        """
        Initialize dynamic orchestrator

        Args:
            max_validation_retries: Maximum retries if validation fails
            max_qa_retries: Maximum retries if QA fails
            interactive_workflow: Present workflow choices to user
            auto_accept_recommendations: Auto-accept AI recommendations (if not interactive)
        """
        # Initialize base orchestrator
        super().__init__(max_validation_retries, max_qa_retries)

        # Dynamic workflow configuration
        self.interactive_workflow = interactive_workflow
        self.auto_accept_recommendations = auto_accept_recommendations
        self.workflow_config: Optional[Dict[str, Any]] = None

        # Initialize builders
        self.schema_builder = DynamicSchemaBuilder()
        self.workflow_configurator: Optional[WorkflowConfigurator] = None

        console.print("[green]✓ Dynamic orchestrator initialized[/green]")
        console.print(f"[dim]Workflow mode: {'Interactive' if interactive_workflow else 'Automatic'}[/dim]")

    def configure_workflow(self, job_analysis: JobAnalysis) -> Dict[str, Any]:
        """
        Configure workflow based on job analysis

        Args:
            job_analysis: JobAnalysis from Agent 1

        Returns:
            Workflow configuration dictionary
        """
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Workflow Configuration[/bold white]\n"
            "[dim]Determining optimal sections and agents for this role[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")

        # Initialize configurator with job analysis
        self.workflow_configurator = WorkflowConfigurator(job_analysis=job_analysis)

        # Get configuration based on mode
        if self.interactive_workflow:
            # Interactive mode: present options to user
            config = self.workflow_configurator.present_recommendations_cli(
                auto_accept=False
            )
        else:
            # Automatic mode
            config = self.workflow_configurator.auto_configure()

            # Display recommendations
            console.print("[bold]AI Workflow Recommendations:[/bold]")
            console.print(f"  Template: {config['template_name']}")
            console.print(f"  Sections: {', '.join(config['enabled_sections'][:5])}" +
                         (f" (+{len(config['enabled_sections'])-5} more)" if len(config['enabled_sections']) > 5 else ""))
            console.print(f"\n  Reasoning: {config['reasoning'][:150]}...")

            if self.auto_accept_recommendations:
                console.print("\n[green]✓ Auto-accepting AI recommendations[/green]")
            else:
                # Prompt for confirmation
                response = input("\nAccept these recommendations? (Y/n): ").strip().lower()
                if response == 'n':
                    console.print("[yellow]Using standard workflow instead[/yellow]")
                    config = self._get_standard_workflow_config()

        # Store configuration
        self.workflow_config = config

        # Save config to job folder for reference
        if self.state_manager:
            config_path = os.path.join(self.state_manager.job_folder, "workflow_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            console.print(f"\n[green]✓ Workflow configuration saved[/green]")

        return config

    def _get_standard_workflow_config(self) -> Dict[str, Any]:
        """Get standard/default workflow configuration"""
        return {
            'template_name': 'standard',
            'enabled_sections': [
                'contact',
                'professional_summary',
                'technical_expertise',
                'experience',
                'bulleted_projects',
                'education'
            ],
            'enabled_agents': [
                'job_analyzer',
                'content_selector',
                'resume_drafter',
                'fabrication_validator',
                'voice_style_editor',
                'final_qa'
            ],
            'section_priorities': {},
            'reasoning': 'Using standard workflow with core sections',
            'role_type': 'individual_contributor'
        }

    def run_phase1_dynamic(
        self,
        jd_text: str,
        company_name: str,
        job_title: str,
        job_folder: Optional[str] = None,
        company_info: Optional[Dict] = None,
        existing_job_analysis: Optional[Any] = None
    ) -> PipelineState:
        """
        Run Phase 1 with dynamic workflow configuration

        This extends the base run_phase1 by adding workflow configuration
        after job analysis.

        Args:
            jd_text: Job description text
            company_name: Company name
            job_title: Job title
            job_folder: Optional existing folder path
            company_info: Optional company information
            existing_job_analysis: Optional pre-existing JobAnalysis (from GUI)

        Returns:
            Pipeline state with results and workflow config
        """
        # If we have existing job analysis from GUI, use it
        if existing_job_analysis:
            # Setup state manager
            if not job_folder:
                job_folder = self.setup_job_folder(company_name, job_title)
            self.state_manager.job_folder = job_folder

            # Create state with existing job analysis
            state = PipelineState(
                job_folder=job_folder,
                job_analysis=existing_job_analysis,
                current_stage="job_analyzed"
            )
            self.state_manager.state = state

            # Save job description
            jd_path = os.path.join(job_folder, "job_description.md")
            with open(jd_path, 'w', encoding='utf-8') as f:
                f.write(jd_text)

            # Still need to run content selection
            console.print("\n[bold cyan]=== Phase 1: Content Selection ===\n[/bold cyan]")
            console.print("[cyan]Skipping job analysis (using existing from workflow tab)[/cyan]")

            content_selection = self.content_selector.select(
                job_analysis=existing_job_analysis,
                experience_data=self.master_data.get('experience', []),
                projects_data=self.master_data.get('projects', []),
                skills_data=self.master_data.get('skills', {})
            )

            state.content_selection = content_selection
            state.current_stage = "phase1_complete"
            self.state_manager.save_state()

            job_analysis = existing_job_analysis
        else:
            # Run standard Phase 1
            state = super().run_phase1(jd_text, company_name, job_title, job_folder, company_info)
            job_analysis = state.job_analysis

        # Configure workflow based on job analysis
        if job_analysis:
            self.workflow_config = self.configure_workflow(job_analysis)

            # Store workflow config in state for later phases (NEW for Phase 3)
            if self.state_manager:
                self.state_manager.state.workflow_config = self.workflow_config
                self.state_manager.state.current_stage = "workflow_configured"
                self.state_manager.save_state()

        return state

    def build_dynamic_schema(self) -> type:
        """
        Build dynamic resume schema based on workflow configuration

        Returns:
            Dynamically generated Pydantic model
        """
        if not self.workflow_config:
            console.print("[yellow]No workflow config - using standard schema[/yellow]")
            enabled_sections = self._get_standard_workflow_config()['enabled_sections']
        else:
            enabled_sections = self.workflow_config['enabled_sections']

        console.print(f"\n[cyan]Building dynamic schema with {len(enabled_sections)} sections...[/cyan]")

        # Build the schema
        schema = self.schema_builder.build_resume_schema(
            enabled_sections=enabled_sections,
            schema_name="DynamicResumeDraft"
        )

        console.print("[green]✓ Dynamic schema created[/green]")
        console.print(f"[dim]Schema fields: {', '.join(list(schema.model_fields.keys())[:8])}...[/dim]")

        return schema

    def run_phase2_dynamic(
        self,
        job_folder: Optional[str] = None
    ) -> PipelineState:
        """
        Run Phase 2 with dynamic schema

        This now fully integrates dynamic schemas with the resume drafter.

        Args:
            job_folder: Optional folder path (resume from existing)

        Returns:
            Pipeline state with results
        """
        # Load workflow config if resuming
        if job_folder and not self.workflow_config:
            config_path = os.path.join(job_folder, "workflow_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.workflow_config = json.load(f)
                console.print("[green]✓ Loaded workflow configuration[/green]")

        # Build dynamic schema based on workflow configuration
        dynamic_schema = self.build_dynamic_schema()

        # Initialize or restore state manager
        if job_folder:
            self.state_manager = StateManager(job_folder)

        if not self.state_manager:
            raise ValueError("No job folder - must run Phase 1 first or provide job_folder")

        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Phase 2: Resume Generation + Validation (Dynamic)[/bold white]\n"
            "[dim]Using dynamic schema with configured sections[/dim]",
            border_style="cyan"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")

        try:
            # Load Phase 1 results
            from schemas import JobAnalysis, ContentSelection
            if not self.state_manager.state.job_analysis:
                job_analysis_data = self.state_manager.load_agent_output("job_analyzer")
                self.state_manager.state.job_analysis = JobAnalysis(**job_analysis_data)

            if not self.state_manager.state.content_selection:
                content_data = self.state_manager.load_agent_output("content_selector")
                self.state_manager.state.content_selection = ContentSelection(**content_data)

            job_analysis = self.state_manager.state.job_analysis
            content_selection = self.state_manager.state.content_selection

            # Load target format example
            target_format = self.load_target_format_example()

            # AGENT 3 + 4: Generate and validate with dynamic schema
            validation_passed = False
            resume_draft = None
            validation_result = None

            for attempt in range(self.max_validation_retries + 1):
                if attempt > 0:
                    console.print(f"\n[yellow]Retry {attempt}/{self.max_validation_retries}: Regenerating resume...[/yellow]")

                # AGENT 3: Generate resume with dynamic schema
                if attempt == 0 and self.state_manager.can_skip_stage("draft_complete"):
                    console.print("\n[yellow]⊳ Using existing draft[/yellow]")
                    draft_data = self.state_manager.load_agent_output("resume_drafter")
                    # Validate with dynamic schema
                    resume_draft = dynamic_schema(**draft_data)
                else:
                    # Generate with dynamic schema
                    resume_draft = self.resume_drafter.draft(
                        job_analysis=job_analysis,
                        content_selection=content_selection,
                        target_format_example=target_format,
                        dynamic_schema=dynamic_schema  # NEW: Pass dynamic schema!
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

    def generate_resume_dynamic(
        self,
        jd_input: str,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company_url: Optional[str] = None,
        auto_generate_pdf: bool = False,
        skip_style_editing: bool = False,
        job_analysis_result: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for dynamic resume generation (all 3 phases)

        This is the dynamic version that includes workflow configuration.

        Args:
            jd_input: Job description URL or text
            company_name: Optional company name (will extract if not provided)
            job_title: Optional job title (will extract if not provided)
            company_url: Optional company website URL
            auto_generate_pdf: Automatically generate PDF at end
            skip_style_editing: Skip Agent 5 if not needed
            job_analysis_result: Optional pre-existing JobAnalysis (from GUI workflow tab)

        Returns:
            Results dictionary including workflow configuration
        """
        # Process JD input
        jd_text, company_name, job_title, company_info = self.process_job_description_input(
            jd_input, company_name, job_title, company_url
        )

        # Run Phase 1 with dynamic workflow configuration
        # If job_analysis_result is provided from GUI, use it to configure workflow
        if job_analysis_result:
            console.print("[cyan]Using pre-existing job analysis from workflow configuration[/cyan]")
            # Still run Phase 1 to get content selection, but with existing job analysis
            state = self.run_phase1_dynamic(
                jd_text, company_name, job_title,
                company_info=company_info,
                existing_job_analysis=job_analysis_result
            )
        else:
            state = self.run_phase1_dynamic(jd_text, company_name, job_title, company_info=company_info)

        # Run Phase 2 with dynamic schema
        state = self.run_phase2_dynamic(self.state_manager.job_folder)

        # Run Phase 3 (standard)
        state = self.run_phase3(self.state_manager.job_folder, skip_style_editing)

        # Generate PDF if requested
        if auto_generate_pdf:
            pdf_path = self.generate_pdf()
            if pdf_path:
                state.pdf_generated = True
                state.pdf_path = pdf_path

        # Prepare results
        results = {
            "status": "success",
            "job_folder": self.state_manager.job_folder,
            "workflow_config": self.workflow_config,
            "job_analysis": state.job_analysis.model_dump() if state.job_analysis else None,
            "qa_report": state.qa_report.model_dump() if state.qa_report else None,
            "pdf_generated": state.pdf_generated,
            "pdf_path": state.pdf_path
        }

        self._show_final_summary(results)

        return results

    def _show_final_summary(self, results: Dict[str, Any]):
        """Show final summary with workflow information"""
        console.print("\n[bold cyan]" + "="*70 + "[/bold cyan]")
        console.print(Panel.fit(
            "[bold white]Resume Generation Complete[/bold white]",
            border_style="green"
        ))
        console.print("[bold cyan]" + "="*70 + "[/bold cyan]\n")

        # Workflow summary
        if results.get('workflow_config'):
            config = results['workflow_config']
            console.print("[bold]Workflow Used:[/bold]")
            console.print(f"  Template: {config.get('template_name', 'N/A')}")
            console.print(f"  Sections: {len(config.get('enabled_sections', []))} sections")
            console.print(f"  Role Type: {config.get('role_type', 'N/A')}")

        # Output files
        console.print("\n[bold]Generated Files:[/bold]")
        console.print(f"  Folder: {results['job_folder']}")
        console.print(f"  Resume: resume_final.json")
        if results.get('pdf_generated'):
            console.print(f"  PDF: {os.path.basename(results.get('pdf_path', 'resume_final.pdf'))}")

        # QA score
        if results.get('qa_report'):
            qa = results['qa_report']
            score = qa.get('overall_score', 0)
            status = qa.get('overall_status', 'unknown')

            score_color = 'green' if score >= 85 else 'yellow' if score >= 70 else 'red'
            console.print(f"\n[bold]Quality Score:[/bold] [{score_color}]{score}/100[/{score_color}] ({status})")

        console.print("\n[bold green]✓ All phases complete![/bold green]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Dynamic Multi-Agent Resume Generator with Workflow Configuration"
    )

    # Required arguments
    parser.add_argument(
        "--jd",
        required=True,
        help="Job description (URL or text file path)"
    )

    # Optional metadata
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--title", help="Job title")
    parser.add_argument("--company-url", help="Company website URL")

    # Workflow configuration options
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive workflow configuration mode"
    )
    parser.add_argument(
        "--no-auto-accept",
        action="store_true",
        help="Don't auto-accept AI recommendations (prompt for confirmation)"
    )

    # Output options
    parser.add_argument("--pdf", action="store_true", help="Generate PDF")
    parser.add_argument("--skip-style", action="store_true", help="Skip style editing")

    # Phase control
    parser.add_argument("--phase1-only", action="store_true", help="Run only Phase 1")
    parser.add_argument("--phase2-only", action="store_true", help="Run only Phase 2")
    parser.add_argument("--phase3-only", action="store_true", help="Run only Phase 3")
    parser.add_argument("--resume-folder", help="Resume from existing folder")

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = DynamicResumeOrchestrator(
        interactive_workflow=args.interactive,
        auto_accept_recommendations=not args.no_auto_accept
    )

    # Execute based on phase flags
    if args.phase1_only:
        # Phase 1 only
        jd_text, company, title, company_info = orchestrator.process_job_description_input(
            args.jd, args.company, args.title, args.company_url
        )
        orchestrator.run_phase1_dynamic(jd_text, company, title, company_info=company_info)

    elif args.phase2_only:
        # Phase 2 only
        if not args.resume_folder:
            console.print("[red]Error: --resume-folder required for --phase2-only[/red]")
            exit(1)
        orchestrator.run_phase2_dynamic(args.resume_folder)

    elif args.phase3_only:
        # Phase 3 only
        if not args.resume_folder:
            console.print("[red]Error: --resume-folder required for --phase3-only[/red]")
            exit(1)
        orchestrator.run_phase3(args.resume_folder, args.skip_style)

    else:
        # Full pipeline
        orchestrator.generate_resume_dynamic(
            jd_input=args.jd,
            company_name=args.company,
            job_title=args.title,
            company_url=args.company_url,
            auto_generate_pdf=args.pdf,
            skip_style_editing=args.skip_style
        )

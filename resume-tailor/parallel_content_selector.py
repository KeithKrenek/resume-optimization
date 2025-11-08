"""
Parallel Content Selector (REPLACES content_selector.py)
Orchestrates 5 specialized selector agents running in parallel
"""

import asyncio
import json
from typing import Dict, Any
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import all components
from base_agent import BaseAgent
from schemas import JobAnalysis, ContentSelection
from schema_transformer import SchemaTransformer
from content_aggregator import ContentAggregator
from deduplication_agent import DeduplicationAgent

from specialized_selectors.experience_selector import ExperienceSelectorAgent
from specialized_selectors.project_selector import ProjectSelectorAgent
from specialized_selectors.skills_selector import SkillsSelectorAgent
from specialized_selectors.publication_selector import PublicationSelectorAgent
from specialized_selectors.work_sample_selector import WorkSampleSelectorAgent


class ParallelContentSelector:
    """
    Main content selector using parallel specialized agents
    
    Architecture:
    1. Run 5 selector agents in parallel (async)
    2. Aggregate results (ContentAggregator)
    3. Deduplicate (DeduplicationAgent)
    4. Transform schema (SchemaTransformer)
    5. Return ContentSelection
    """
    
    def __init__(self, client, model: str):
        """
        Initialize parallel content selector
        
        Args:
            client: Anthropic API client
            model: Model name for all agents
        """
        self.client = client
        self.model = model
        self.console = Console()
        
        # Initialize all specialized agents
        self.exp_selector = ExperienceSelectorAgent(client, model)
        self.proj_selector = ProjectSelectorAgent(client, model)
        self.skills_selector = SkillsSelectorAgent(client, model)
        self.pub_selector = PublicationSelectorAgent(client, model)
        self.sample_selector = WorkSampleSelectorAgent(client, model)
        
        # Initialize aggregation and deduplication
        self.aggregator = ContentAggregator()
        self.deduplicator = DeduplicationAgent(similarity_threshold=0.80)
        
        self.console.print("[bold cyan]Parallel Content Selector initialized[/bold cyan]")
        self.console.print("  • 5 specialized selector agents")
        self.console.print("  • Parallel execution (async)")
        self.console.print("  • Automatic deduplication")
        self.console.print("  • Schema transformation")
    
    async def select_async(
        self,
        job_analysis: JobAnalysis,
        database: Dict[str, Any]
    ) -> ContentSelection:
        """
        Select content using parallel agent execution (async)
        
        Args:
            job_analysis: Structured job requirements
            database: Full resume database
            
        Returns:
            ContentSelection with all selected content
        """
        self.console.print("\n[bold cyan]" + "=" * 70 + "[/bold cyan]")
        self.console.print("[bold cyan]PARALLEL CONTENT SELECTION[/bold cyan]")
        self.console.print("[bold cyan]" + "=" * 70 + "[/bold cyan]")
        
        # Extract database sections
        experiences_db = database.get('experiences', {})
        projects_db = database.get('projects', {})
        skills_db = database.get('skills', {})
        publications_db = database.get('publications', {})
        work_samples_db = database.get('work_samples', [])
        contact_info = database.get('metadata', {}).get('contact', {})
        education = list(database.get('education', {}).values())
        
        # Phase 1: Parallel Selection
        self.console.print("\n[cyan]Phase 1: Running 5 selector agents in parallel...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Selecting content in parallel...", total=None)
            
            # Run all selectors in parallel
            results = await asyncio.gather(
                self._select_experiences_async(job_analysis, experiences_db),
                self._select_projects_async(job_analysis, projects_db, None),  # Will update after exp
                self._select_skills_async(job_analysis, skills_db),
                self._select_publications_async(job_analysis, publications_db),
                self._select_work_samples_async(job_analysis, work_samples_db),
                return_exceptions=True
            )
            
            progress.update(task, completed=True)
        
        # Unpack results
        exp_selection, proj_selection, skills_selection, pub_selection, sample_selection = results
        
        # Check for errors
        self._check_for_errors(results)
        
        # Phase 2: Aggregation
        self.console.print("\n[cyan]Phase 2: Aggregating all selections...[/cyan]")
        aggregated = self.aggregator.aggregate(
            experience_selection=exp_selection,
            project_selection=proj_selection,
            skills_selection=skills_selection,
            publication_selection=pub_selection,
            work_sample_selection=sample_selection,
            contact_info=contact_info,
            education=education
        )
        
        # Phase 3: Deduplication
        self.console.print("\n[cyan]Phase 3: Deduplicating content...[/cyan]")
        deduplicated = self.deduplicator.deduplicate(aggregated)
        
        # Phase 4: Schema Transformation
        self.console.print("\n[cyan]Phase 4: Applying schema transformations...[/cyan]")
        transformed = SchemaTransformer.transform_full_content_selection(deduplicated)
        
        # Validate with Pydantic
        self.console.print("\n[cyan]Phase 5: Validating schema...[/cyan]")
        try:
            content_selection = ContentSelection(**transformed)
            self.console.print("[green]✓ Schema validation passed[/green]")
        except Exception as e:
            self.console.print(f"[red]Schema validation error: {e}[/red]")
            self.console.print("[yellow]Returning raw transformed data[/yellow]")
            # Return as-is for debugging
            return transformed
        
        # Final summary
        self._show_final_summary(content_selection)
        
        return content_selection
    
    def select(
        self,
        job_analysis: JobAnalysis,
        database: Dict[str, Any]
    ) -> ContentSelection:
        """
        Synchronous wrapper for async select
        
        Args:
            job_analysis: Job requirements
            database: Resume database
            
        Returns:
            ContentSelection object
        """
        # Run async function in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.select_async(job_analysis, database)
        )
    
    async def _select_experiences_async(
        self,
        job_analysis: JobAnalysis,
        experiences_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run experience selector asynchronously"""
        try:
            return self.exp_selector.select(job_analysis, experiences_db)
        except Exception as e:
            self.console.print(f"[red]Experience selector error: {e}[/red]")
            return {'selected_experiences': [], 'selection_notes': f'Error: {e}'}
    
    async def _select_projects_async(
        self,
        job_analysis: JobAnalysis,
        projects_db: Dict[str, Any],
        selected_experiences: Any = None
    ) -> Dict[str, Any]:
        """Run project selector asynchronously"""
        try:
            return self.proj_selector.select(
                job_analysis,
                projects_db,
                selected_experiences
            )
        except Exception as e:
            self.console.print(f"[red]Project selector error: {e}[/red]")
            return {'selected_projects': [], 'selection_notes': f'Error: {e}'}
    
    async def _select_skills_async(
        self,
        job_analysis: JobAnalysis,
        skills_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run skills selector asynchronously"""
        try:
            return self.skills_selector.select(job_analysis, skills_db)
        except Exception as e:
            self.console.print(f"[red]Skills selector error: {e}[/red]")
            return {'selected_skills': {}, 'selection_notes': f'Error: {e}'}
    
    async def _select_publications_async(
        self,
        job_analysis: JobAnalysis,
        publications_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run publication selector asynchronously"""
        try:
            return self.pub_selector.select(job_analysis, publications_db)
        except Exception as e:
            self.console.print(f"[red]Publication selector error: {e}[/red]")
            return {'selected_publications': [], 'selection_notes': f'Error: {e}'}
    
    async def _select_work_samples_async(
        self,
        job_analysis: JobAnalysis,
        work_samples_db: list
    ) -> Dict[str, Any]:
        """Run work sample selector asynchronously"""
        try:
            return self.sample_selector.select(job_analysis, work_samples_db)
        except Exception as e:
            self.console.print(f"[red]Work sample selector error: {e}[/red]")
            return {'selected_work_samples': [], 'selection_notes': f'Error: {e}'}
    
    def _check_for_errors(self, results: tuple):
        """Check if any selector raised an exception"""
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_names = ['Experience', 'Project', 'Skills', 'Publication', 'Work Sample']
                self.console.print(f"[red]ERROR in {agent_names[i]} Selector: {result}[/red]")
                raise result
    
    def _show_final_summary(self, content_selection: ContentSelection):
        """Show final content selection summary"""
        self.console.print("\n[bold green]" + "=" * 70 + "[/bold green]")
        self.console.print("[bold green]PARALLEL SELECTION COMPLETE ✓[/bold green]")
        self.console.print("[bold green]" + "=" * 70 + "[/bold green]")
        
        summary = {
            "Experiences": len(content_selection.selected_experiences),
            "Projects": len(content_selection.selected_projects),
            "Skill Categories": len(content_selection.selected_skills),
            "Publications": len(content_selection.selected_publications),
            "Work Samples": len(getattr(content_selection, 'selected_work_samples', [])),
            "Education": len(content_selection.selected_education)
        }
        
        for key, value in summary.items():
            self.console.print(f"  {key}: [bold]{value}[/bold]")
        
        # Show avg relevance scores
        if content_selection.selected_experiences:
            avg_exp_score = sum(
                e.relevance_score for e in content_selection.selected_experiences
            ) / len(content_selection.selected_experiences)
            self.console.print(f"\n  Avg Experience Relevance: [bold]{avg_exp_score:.2f}[/bold]")
        
        if content_selection.selected_projects:
            avg_proj_score = sum(
                p.relevance_score for p in content_selection.selected_projects
            ) / len(content_selection.selected_projects)
            self.console.print(f"  Avg Project Relevance: [bold]{avg_proj_score:.2f}[/bold]")
        
        # Show coverage
        coverage = content_selection.coverage_analysis
        coverage_pct = coverage.get('coverage_percentage', 0)
        self.console.print(f"\n  Requirement Coverage: [bold]{coverage_pct}%[/bold]")
        
        self.console.print("\n[green]Ready for Resume Drafter (Agent 3)[/green]")


# Standalone test
if __name__ == "__main__":
    import anthropic
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Testing ParallelContentSelector...")
    print("=" * 70)
    
    # Mock job analysis
    class MockJobAnalysis:
        role_type = "engineering_manager"
        role_focus = "building production ML systems"
        must_have_requirements = []
        technical_keywords = ['Python', 'PyTorch', 'ML']
        leadership_keywords = ['team leadership']
        domain_keywords = ['production systems']
    
    # Mock minimal database
    mock_db = {
        'experiences': {
            'exp_1': {
                'id': 'exp_1',
                'company': 'Test Co',
                'title': 'Senior Engineer',
                'dates': '2020-2025',
                'location': 'Boston, MA',
                'core_description': 'ML work',
                'key_achievements': ['Built ML system'],
                'quantified_outcomes': {},
                'tech_stack': ['Python'],
                'methods': [],
                'domain_tags': [],
                'persona_variants': {}
            }
        },
        'projects': {},
        'skills': {
            'ai_ml': ['Python', 'PyTorch']
        },
        'publications': {},
        'work_samples': [],
        'education': {
            'edu_1': {
                'degree': 'M.S. CS',
                'institution': 'MIT',
                'graduation_date': '2019'
            }
        },
        'metadata': {
            'contact': {
                'name': 'Test User',
                'email': 'test@test.com',
                'phone': '123-456-7890',
                'location': 'Boston, MA'
            }
        }
    }
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    selector = ParallelContentSelector(client, "claude-sonnet-4-20250514")
    
    try:
        result = selector.select(MockJobAnalysis(), mock_db)
        print("\n✓ ParallelContentSelector test passed!")
        print(f"Selected {len(result.selected_experiences)} experiences")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

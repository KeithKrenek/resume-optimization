"""
Project Selector Agent
Selects 2-4 most relevant projects in parallel
"""

import json
import sys
from typing import Dict, Any, List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from schemas import JobAnalysis


class ProjectSelectorAgent(BaseAgent):
    """Selects relevant projects from database"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Project Selector Agent",
            agent_description="Selects 2-4 most relevant projects"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "project_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        projects_db: Dict[str, Any],
        selected_experiences: List[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Build prompt for project selection
        
        Args:
            job_analysis: Structured job requirements
            projects_db: Database of all projects
            selected_experiences: Already-selected experiences (to avoid duplication)
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB REQUIREMENTS\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include job analysis
        job_summary = {
            "role_type": job_analysis.role_type,
            "role_focus": job_analysis.role_focus,
            "technical_keywords": job_analysis.technical_keywords[:20],
            "domain_keywords": job_analysis.domain_keywords[:10]
        }
        prompt += json.dumps(job_summary, indent=2)
        
        # Include selected experiences for deduplication check
        if selected_experiences:
            prompt += "\n\n" + "═" * 70 + "\n"
            prompt += "ALREADY SELECTED EXPERIENCES (avoid duplication)\n"
            prompt += "═" * 70 + "\n\n"
            
            exp_summary = []
            for exp in selected_experiences:
                exp_summary.append({
                    "company": exp.get('company', ''),
                    "title": exp.get('title', ''),
                    "key_achievements": exp.get('key_achievements', [])[:3],  # First 3 bullets
                    "tech_stack": exp.get('tech_stack', [])
                })
            prompt += json.dumps(exp_summary, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "AVAILABLE PROJECTS (select from these ONLY)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include projects database
        prompt += json.dumps(projects_db, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "SELECTION TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += f"""
Now select 2-4 most relevant projects:

1. Score each project (0.0 to 1.0) based on job requirements
2. Check for duplication with selected experiences
3. Select top 2-4 that:
   - Match technical requirements
   - Add unique value (not in experience section)
   - Are recent (prefer last 3-5 years)
   - Have clear impact
4. Return EXACT database text with source_ids

Role type: {job_analysis.role_type}
- IC/Lead: Select 3-4 projects
- Manager: Select 2-3 projects
- Director+: Select 1-2 projects (optional)

Return ONLY the JSON in the format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse project selection response"""
        json_str = self.extract_json_from_response(response)
        
        if not json_str:
            json_str = response.strip()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]JSON parsing error: {e}[/red]")
            self.console.print(f"[dim]Response: {response[:500]}...[/dim]")
            raise
        
        if 'selected_projects' not in data:
            raise ValueError("Response missing 'selected_projects' field")
        
        selected = data['selected_projects']
        
        if selected:
            avg_score = sum(proj.get('relevance_score', 0) for proj in selected) / len(selected)
            
            self.show_summary({
                "Projects Selected": len(selected),
                "Average Relevance": f"{avg_score:.2f}",
                "Source IDs": ", ".join(proj.get('source_id', 'MISSING')[:20] for proj in selected)
            })
            
            self.console.print("\n[cyan]Selected Projects:[/cyan]")
            for proj in selected:
                score = proj.get('relevance_score', 0)
                source_id = proj.get('source_id', 'MISSING')
                title = proj.get('title', 'Unknown')
                self.console.print(f"  • [{score:.2f}] {title} ({source_id})")
        
        return data
    
    def select(
        self,
        job_analysis: JobAnalysis,
        projects_db: Dict[str, Any],
        selected_experiences: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method
        
        Args:
            job_analysis: Job requirements
            projects_db: Database of projects
            selected_experiences: Already selected experiences (for dedup)
            
        Returns:
            Selection dict with projects
        """
        return self.execute(
            job_analysis=job_analysis,
            projects_db=projects_db,
            selected_experiences=selected_experiences
        )

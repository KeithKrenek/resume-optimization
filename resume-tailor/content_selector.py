"""
Agent 2: Content Selector
Selects relevant database entries WITHOUT modification
"""

import json
from typing import Dict, Any
from pathlib import Path

from base_agent import BaseAgent
from schemas import JobAnalysis, ContentSelection


class ContentSelectorAgent(BaseAgent):
    """Selects relevant content from database without modification"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Content Selector Agent",
            agent_description="Selects relevant database entries verbatim - NO fabrication"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "content_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        database: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Build prompt for content selection
        
        Args:
            job_analysis: Output from Job Analyzer Agent
            database: Full resume database
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB ANALYSIS (from Agent 1)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include job analysis as JSON
        job_analysis_dict = job_analysis.model_dump()
        prompt += json.dumps(job_analysis_dict, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "RESUME DATABASE (select from these entries ONLY)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include full database
        prompt += "**EXPERIENCES:**\n\n"
        prompt += json.dumps(database.get('experiences', {}), indent=2)
        
        prompt += "\n\n**PROJECTS:**\n\n"
        prompt += json.dumps(database.get('projects', {}), indent=2)
        
        prompt += "\n\n**EDUCATION:**\n\n"
        prompt += json.dumps(database.get('education', {}), indent=2)
        
        prompt += "\n\n**SKILLS:**\n\n"
        prompt += json.dumps(database.get('skills', {}), indent=2)
        
        prompt += "\n\n**PUBLICATIONS:**\n\n"
        prompt += json.dumps(database.get('publications', {}), indent=2)
        
        prompt += "\n\n**CONTACT INFO:**\n\n"
        contact = database.get('metadata', {}).get('contact', {})
        prompt += json.dumps(contact, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "INSTRUCTIONS\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += f"""
Now select the most relevant content:

1. Match experiences/projects to job requirements
2. Score each selection (0.0 to 1.0 relevance)
3. Return EXACT text from database with source_ids
4. Select appropriate persona_variants when available
5. Explain match_reasons for each selection
6. Provide coverage analysis

Remember: COPY database text exactly. Do not modify or write new content.

Return your selection in the JSON format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> ContentSelection:
        """
        Parse JSON response into ContentSelection schema
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Validated ContentSelection object
        """
        # Extract JSON from response
        json_str = self.extract_json_from_response(response)
        
        if not json_str:
            raise ValueError("Could not extract JSON from response")
        
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]JSON parsing error: {e}[/red]")
            self.console.print(f"[dim]Response preview: {response[:500]}...[/dim]")
            raise
        
        # Validate with Pydantic
        try:
            selection = ContentSelection(**data)
        except Exception as e:
            self.console.print(f"[red]Validation error: {e}[/red]")
            self.console.print(f"[yellow]Raw data keys: {list(data.keys())}[/yellow]")
            raise
        
        # Show summary
        coverage = selection.coverage_analysis
        coverage_pct = coverage.get('coverage_percentage', 0)
        
        self.show_summary({
            "Selected Experiences": len(selection.selected_experiences),
            "Selected Projects": len(selection.selected_projects),
            "Average Exp Relevance": f"{sum(e.relevance_score for e in selection.selected_experiences) / len(selection.selected_experiences):.2f}",
            "Average Proj Relevance": f"{sum(p.relevance_score for p in selection.selected_projects) / len(selection.selected_projects):.2f}" if selection.selected_projects else "N/A",
            "Requirement Coverage": f"{coverage_pct}%",
            "Skills Categories": len(selection.selected_skills)
        })
        
        # Show experience IDs
        self.console.print("\n[cyan]Selected Experience IDs:[/cyan]")
        for exp in selection.selected_experiences:
            self.console.print(f"  • {exp.source_id} (score: {exp.relevance_score})")
        
        # Show project IDs
        if selection.selected_projects:
            self.console.print("\n[cyan]Selected Project IDs:[/cyan]")
            for proj in selection.selected_projects:
                self.console.print(f"  • {proj.source_id} (score: {proj.relevance_score})")
        
        return selection
    
    def select(
        self,
        job_analysis: JobAnalysis,
        database: Dict[str, Any]
    ) -> ContentSelection:
        """
        Convenience method for external callers
        
        Args:
            job_analysis: Structured job analysis
            database: Resume database
            
        Returns:
            ContentSelection object
        """
        return self.execute(
            job_analysis=job_analysis,
            database=database
        )

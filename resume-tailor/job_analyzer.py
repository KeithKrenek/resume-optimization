"""
Agent 1: Job Analyzer
Extracts structured requirements from job descriptions
"""

import json
from typing import Dict, Any
from pathlib import Path

from base_agent import BaseAgent
from schemas import JobAnalysis


class JobAnalyzerAgent(BaseAgent):
    """Analyzes job descriptions and extracts structured requirements"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Job Analyzer Agent",
            agent_description="Extracts structured requirements and keywords from job description"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "job_analyzer.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(self, job_description: str, **kwargs) -> str:
        """
        Build prompt for job analysis
        
        Args:
            job_description: Full job description text
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB DESCRIPTION TO ANALYZE\n"
        prompt += "═" * 70 + "\n\n"
        prompt += job_description
        prompt += "\n\n═" * 70 + "\n"
        prompt += "Now provide your analysis in JSON format only.\n"
        
        return prompt
    
    def parse_response(self, response: str) -> JobAnalysis:
        """
        Parse JSON response into JobAnalysis schema
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Validated JobAnalysis object
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
            analysis = JobAnalysis(**data)
        except Exception as e:
            self.console.print(f"[red]Validation error: {e}[/red]")
            self.console.print(f"[yellow]Raw data: {json.dumps(data, indent=2)[:500]}...[/yellow]")
            raise
        
        # Show summary
        self.show_summary({
            "Role Type": analysis.role_type,
            "Must-Have Requirements": len(analysis.must_have_requirements),
            "Nice-to-Have Requirements": len(analysis.nice_to_have_requirements),
            "Technical Keywords": len(analysis.technical_keywords),
            "Domain Keywords": len(analysis.domain_keywords),
            "Leadership Keywords": len(analysis.leadership_keywords),
            "Role Focus": analysis.role_focus[:60] + "..." if len(analysis.role_focus) > 60 else analysis.role_focus
        })
        
        return analysis
    
    def analyze(self, job_description: str) -> JobAnalysis:
        """
        Convenience method for external callers
        
        Args:
            job_description: Job description text
            
        Returns:
            JobAnalysis object
        """
        return self.execute(job_description=job_description)

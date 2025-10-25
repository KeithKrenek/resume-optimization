"""
Agent 3: Resume Drafter
Generates complete resume JSON using ONLY provided content with source citations
"""

import json
from typing import Dict, Any
from pathlib import Path

from base_agent import BaseAgent
from schemas import JobAnalysis, ContentSelection, ResumeDraft


class ResumeDrafterAgent(BaseAgent):
    """Generates resume JSON from selected content with strict source citation"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Resume Drafter Agent",
            agent_description="Generates complete resume JSON with source citations - NO fabrication"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "resume_drafter.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        content_selection: ContentSelection,
        target_format_example: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Build prompt for resume drafting
        
        Args:
            job_analysis: Output from Agent 1
            content_selection: Output from Agent 2
            target_format_example: Optional example of target format
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB ANALYSIS (from Agent 1)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include relevant parts of job analysis
        job_summary = {
            "role_type": job_analysis.role_type,
            "role_focus": job_analysis.role_focus,
            "must_have_requirements": [
                {"text": req.text, "keywords": req.keywords}
                for req in job_analysis.must_have_requirements[:10]  # Top 10
            ],
            "technical_keywords": job_analysis.technical_keywords,
            "leadership_keywords": job_analysis.leadership_keywords,
            "company_values": job_analysis.company_values
        }
        prompt += json.dumps(job_summary, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "SELECTED CONTENT (from Agent 2) - USE ONLY THIS CONTENT\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include selected content
        content_dict = content_selection.model_dump()
        prompt += json.dumps(content_dict, indent=2)
        
        if target_format_example:
            prompt += "\n\n" + "═" * 70 + "\n"
            prompt += "TARGET FORMAT EXAMPLE\n"
            prompt += "═" * 70 + "\n\n"
            prompt += json.dumps(target_format_example, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "INSTRUCTIONS\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += f"""
Now generate the complete resume JSON:

1. Use ONLY the content from Selected Content above
2. Structure according to the format specified in the instructions
3. Write in natural language (Keith's voice - no corporate speak)
4. CITE source_id for EVERY experience, project, and achievement
5. Adapt to role type: {job_analysis.role_type}
6. Focus on role: {job_analysis.role_focus}
7. Include keywords naturally: {', '.join(job_analysis.technical_keywords[:10])}

CRITICAL REMINDERS:
- Every achievement must have source_id
- No invention - use only provided content
- Natural voice - periods for separation, no em-dashes
- Specific metrics in context

Return ONLY the JSON, no additional text or markdown formatting.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> ResumeDraft:
        """
        Parse JSON response into ResumeDraft schema
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Validated ResumeDraft object
        """
        # Extract JSON from response
        json_str = self.extract_json_from_response(response)
        
        if not json_str:
            # Try the whole response as JSON
            json_str = response.strip()
        
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]JSON parsing error: {e}[/red]")
            self.console.print(f"[dim]Response preview: {response[:500]}...[/dim]")
            raise
        
        # Build citations map (for validation)
        citations = self._extract_citations(data)
        data['citations'] = citations
        
        # Validate with Pydantic
        try:
            draft = ResumeDraft(**data)
        except Exception as e:
            self.console.print(f"[red]Validation error: {e}[/red]")
            self.console.print(f"[yellow]Data keys: {list(data.keys())}[/yellow]")
            raise
        
        # Show summary
        exp_count = len(draft.experience)
        proj_count = len(draft.bulleted_projects)
        total_achievements = sum(len(exp.get('achievements', [])) for exp in draft.experience)
        
        self.show_summary({
            "Experiences": exp_count,
            "Projects": proj_count,
            "Total Achievement Bullets": total_achievements,
            "Citations": len(citations),
            "Summary Length": f"{len(draft.professional_summary)} chars",
            "Skill Categories": len(draft.technical_expertise)
        })
        
        # Show source citations
        self.console.print("\n[cyan]Source Citations:[/cyan]")
        source_ids = set()
        for exp in draft.experience:
            if 'source_id' in exp:
                source_ids.add(exp['source_id'])
        for proj in draft.bulleted_projects:
            if 'source_id' in proj:
                source_ids.add(proj['source_id'])
        
        for sid in sorted(source_ids):
            self.console.print(f"  • {sid}")
        
        return draft
    
    def _extract_citations(self, resume_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract all source_id citations from resume
        
        Args:
            resume_data: Resume JSON data
            
        Returns:
            Map of location to source_id
        """
        citations = {}
        
        # Extract from experiences
        for i, exp in enumerate(resume_data.get('experience', [])):
            exp_id = exp.get('source_id', 'MISSING')
            citations[f"experience[{i}]"] = exp_id
            
            # Extract from achievements
            for j, ach in enumerate(exp.get('achievements', [])):
                if isinstance(ach, dict):
                    ach_id = ach.get('source_id', exp_id)  # Default to parent if missing
                    citations[f"experience[{i}].achievements[{j}]"] = ach_id
        
        # Extract from projects
        for i, proj in enumerate(resume_data.get('bulleted_projects', [])):
            proj_id = proj.get('source_id', 'MISSING')
            citations[f"projects[{i}]"] = proj_id
        
        return citations
    
    def draft(
        self,
        job_analysis: JobAnalysis,
        content_selection: ContentSelection,
        target_format_example: Dict[str, Any] = None
    ) -> ResumeDraft:
        """
        Convenience method for external callers
        
        Args:
            job_analysis: Structured job analysis
            content_selection: Selected content
            target_format_example: Optional format example
            
        Returns:
            ResumeDraft object
        """
        return self.execute(
            job_analysis=job_analysis,
            content_selection=content_selection,
            target_format_example=target_format_example
        )

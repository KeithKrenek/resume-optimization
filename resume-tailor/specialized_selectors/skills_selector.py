"""
Skills Selector Agent
Organizes and selects relevant technical skills
"""

import json
import sys
from typing import Dict, Any
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from schemas import JobAnalysis


class SkillsSelectorAgent(BaseAgent):
    """Selects and organizes technical skills"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Skills Selector Agent",
            agent_description="Organizes technical skills into categories"
        )
        
        prompt_path = Path(__file__).parent / "skills_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        skills_db: Dict[str, Any],
        **kwargs
    ) -> str:
        """Build prompt for skills selection"""
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB REQUIREMENTS\n"
        prompt += "═" * 70 + "\n\n"
        
        job_summary = {
            "role_type": job_analysis.role_type,
            "technical_keywords": job_analysis.technical_keywords,
            "domain_keywords": job_analysis.domain_keywords,
            "leadership_keywords": job_analysis.leadership_keywords
        }
        prompt += json.dumps(job_summary, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "AVAILABLE SKILLS (select and organize from these)\n"
        prompt += "═" * 70 + "\n\n"
        prompt += json.dumps(skills_db, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "SELECTION TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += f"""
Organize skills into 3-6 logical categories:

1. Prioritize must-have technical skills from job requirements
2. Group related skills into clear categories
3. Ensure no duplicates across categories
4. Use professional category names
5. Include 3-8 skills per category

Role type: {job_analysis.role_type}

Return ONLY the JSON in the format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse skills selection response"""
        json_str = self.extract_json_from_response(response)
        
        if not json_str:
            json_str = response.strip()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]JSON parsing error: {e}[/red]")
            raise
        
        if 'selected_skills' not in data:
            raise ValueError("Response missing 'selected_skills' field")
        
        skills = data['selected_skills']
        total_skills = sum(len(v) for v in skills.values())
        
        self.show_summary({
            "Categories": len(skills),
            "Total Skills": total_skills,
            "Avg Skills/Category": f"{total_skills / len(skills):.1f}"
        })
        
        self.console.print("\n[cyan]Skill Categories:[/cyan]")
        for category, skill_list in skills.items():
            self.console.print(f"  • {category}: {len(skill_list)} skills")
        
        return data
    
    def select(
        self,
        job_analysis: JobAnalysis,
        skills_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convenience method"""
        return self.execute(
            job_analysis=job_analysis,
            skills_db=skills_db
        )

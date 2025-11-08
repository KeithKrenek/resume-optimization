"""
Publication Selector Agent
Selects 0-5 most relevant publications
"""

import json
import sys
from typing import Dict, Any
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from schemas import JobAnalysis


class PublicationSelectorAgent(BaseAgent):
    """Selects relevant publications"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Publication Selector Agent",
            agent_description="Selects relevant academic publications"
        )
        
        prompt_path = Path(__file__).parent / "publication_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        publications_db: Dict[str, Any],
        **kwargs
    ) -> str:
        """Build prompt"""
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"Job: {job_analysis.role_type}\n"
        prompt += f"Domain: {', '.join(job_analysis.domain_keywords[:5])}\n\n"
        prompt += "Publications:\n"
        prompt += json.dumps(publications_db, indent=2)
        prompt += "\n\nSelect 0-5 most relevant publications. Return JSON only."
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse response"""
        json_str = self.extract_json_from_response(response) or response.strip()
        data = json.loads(json_str)
        
        if 'selected_publications' not in data:
            data = {'selected_publications': [], 'selection_notes': 'No relevant publications'}
        
        selected = data['selected_publications']
        
        self.show_summary({
            "Publications Selected": len(selected)
        })
        
        return data
    
    def select(
        self,
        job_analysis: JobAnalysis,
        publications_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convenience method"""
        return self.execute(
            job_analysis=job_analysis,
            publications_db=publications_db
        )

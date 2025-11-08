"""
Work Sample Selector Agent
Selects 0-3 most impressive portfolio items
"""

import json
import sys
from typing import Dict, Any, List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from schemas import JobAnalysis


class WorkSampleSelectorAgent(BaseAgent):
    """Selects relevant work samples/portfolio items"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Work Sample Selector Agent",
            agent_description="Selects impressive portfolio items"
        )
        
        prompt_path = Path(__file__).parent / "work_sample_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        work_samples_db: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Build prompt"""
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"Job: {job_analysis.role_type}\n"
        prompt += f"Technical skills needed: {', '.join(job_analysis.technical_keywords[:10])}\n\n"
        prompt += "Work Samples:\n"
        prompt += json.dumps(work_samples_db, indent=2)
        prompt += "\n\nSelect 0-3 most impressive samples. Return JSON only."
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse response"""
        json_str = self.extract_json_from_response(response) or response.strip()
        data = json.loads(json_str)
        
        if 'selected_work_samples' not in data:
            data = {'selected_work_samples': [], 'selection_notes': 'No relevant work samples'}
        
        selected = data['selected_work_samples']
        
        self.show_summary({
            "Work Samples Selected": len(selected)
        })
        
        if selected:
            self.console.print("\n[cyan]Selected Work Samples:[/cyan]")
            for sample in selected:
                title = sample.get('title', 'Unknown')
                self.console.print(f"  • {title}")
        
        return data
    
    def select(
        self,
        job_analysis: JobAnalysis,
        work_samples_db: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convenience method"""
        return self.execute(
            job_analysis=job_analysis,
            work_samples_db=work_samples_db
        )

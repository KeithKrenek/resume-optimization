"""
Experience Selector Agent
Selects 3-5 most relevant work experiences in parallel
"""

import json
import sys
from typing import Dict, Any, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from schemas import JobAnalysis


class ExperienceSelectorAgent(BaseAgent):
    """Selects relevant work experiences from database"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Experience Selector Agent",
            agent_description="Selects 3-5 most relevant work experiences"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "experience_selector.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        job_analysis: JobAnalysis,
        experiences_db: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Build prompt for experience selection
        
        Args:
            job_analysis: Structured job requirements
            experiences_db: Database of all experiences
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "JOB REQUIREMENTS\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include relevant job analysis
        job_summary = {
            "role_type": job_analysis.role_type,
            "role_focus": job_analysis.role_focus,
            "must_have_requirements": [
                {
                    "text": req.text,
                    "category": req.category,
                    "keywords": req.keywords
                }
                for req in job_analysis.must_have_requirements[:15]
            ],
            "technical_keywords": job_analysis.technical_keywords[:20],
            "leadership_keywords": job_analysis.leadership_keywords[:10],
            "domain_keywords": job_analysis.domain_keywords[:10]
        }
        prompt += json.dumps(job_summary, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "AVAILABLE EXPERIENCES (select from these ONLY)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include experiences database
        prompt += json.dumps(experiences_db, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "SELECTION TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += f"""
Now select the 3-5 most relevant work experiences:

1. Score each experience (0.0 to 1.0) based on job requirements
2. Select top 3-5 based on:
   - Relevance score
   - Role type match (job is: {job_analysis.role_type})
   - Recency (prefer recent unless highly relevant)
   - Coverage of must-have requirements
3. Choose appropriate persona_variant for each
4. Return EXACT database text with source_ids

Return ONLY the JSON in the format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse experience selection response
        
        Args:
            response: Raw JSON response from Claude
            
        Returns:
            Dict with selected_experiences and metadata
        """
        # Extract JSON
        json_str = self.extract_json_from_response(response)
        
        if not json_str:
            json_str = response.strip()
        
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]JSON parsing error: {e}[/red]")
            self.console.print(f"[dim]Response preview: {response[:500]}...[/dim]")
            raise
        
        # Validate structure
        if 'selected_experiences' not in data:
            raise ValueError("Response missing 'selected_experiences' field")
        
        selected = data['selected_experiences']
        
        # Show summary
        if selected:
            avg_score = sum(exp.get('relevance_score', 0) for exp in selected) / len(selected)
            
            self.show_summary({
                "Experiences Selected": len(selected),
                "Average Relevance": f"{avg_score:.2f}",
                "Score Range": f"{min(exp.get('relevance_score', 0) for exp in selected):.2f} - {max(exp.get('relevance_score', 0) for exp in selected):.2f}",
                "Source IDs": ", ".join(exp.get('source_id', 'MISSING')[:20] for exp in selected)
            })
            
            # Show selections
            self.console.print("\n[cyan]Selected Experiences:[/cyan]")
            for exp in selected:
                score = exp.get('relevance_score', 0)
                source_id = exp.get('source_id', 'MISSING')
                company = exp.get('company', 'Unknown')
                title = exp.get('title', 'Unknown')
                self.console.print(f"  • [{score:.2f}] {company} - {title} ({source_id})")
        
        return data
    
    def select(
        self,
        job_analysis: JobAnalysis,
        experiences_db: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convenience method for external callers
        
        Args:
            job_analysis: Job requirements
            experiences_db: Database of experiences
            
        Returns:
            Selection dict with experiences
        """
        return self.execute(
            job_analysis=job_analysis,
            experiences_db=experiences_db
        )


# Standalone test
if __name__ == "__main__":
    import anthropic
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Testing ExperienceSelectorAgent...")
    
    # Mock job analysis
    class MockJobAnalysis:
        role_type = "engineering_manager"
        role_focus = "building production ML systems"
        must_have_requirements = [
            type('Req', (), {
                'text': 'Python and ML experience',
                'category': 'technical',
                'keywords': ['Python', 'ML']
            })
        ]
        technical_keywords = ['Python', 'PyTorch', 'ML']
        leadership_keywords = ['team leadership', 'mentoring']
        domain_keywords = ['production systems']
    
    # Mock database (minimal)
    mock_db = {
        "exp_test_2020": {
            "id": "exp_test_2020",
            "company": "Test Co",
            "title": "Senior Engineer",
            "dates": "2020-2025",
            "location": "Boston, MA",
            "core_description": "Built ML systems with Python and PyTorch",
            "key_achievements": ["Built production ML pipeline"],
            "quantified_outcomes": {"accuracy": ">90%"},
            "tech_stack": ["Python", "PyTorch"],
            "methods": ["ML", "MLOps"],
            "domain_tags": ["production systems"],
            "persona_variants": {
                "technical_depth": {
                    "achievements": ["Deep ML expertise demonstrated"]
                }
            }
        }
    }
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    agent = ExperienceSelectorAgent(client, "claude-sonnet-4-20250514")
    
    try:
        result = agent.select(MockJobAnalysis(), mock_db)
        print("\n✓ Test passed!")
        print(f"Selected {len(result['selected_experiences'])} experiences")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")

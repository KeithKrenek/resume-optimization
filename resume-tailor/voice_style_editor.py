"""
Agent 5: Voice & Style Editor
Refines language and style while preserving factual accuracy
"""

import json
from typing import Dict, Any
from pathlib import Path

from base_agent import BaseAgent
from schemas import ResumeDraft


class VoiceStyleEditorAgent(BaseAgent):
    """Refines resume language and style without changing facts"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Voice & Style Editor Agent",
            agent_description="Refines language and style - NO fact changes"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "voice_style_editor.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        resume_draft: ResumeDraft,
        **kwargs
    ) -> str:
        """
        Build prompt for style editing
        
        Args:
            resume_draft: Validated resume to edit
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "RESUME TO EDIT (already validated)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include resume draft
        draft_dict = resume_draft.model_dump()
        prompt += json.dumps(draft_dict, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "STYLE EDITING TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += """
Now refine the language and style:

1. Remove ALL corporate speak (spearhead, leverage, facilitate, etc.)
2. Convert passive voice to active voice
3. Add context to metrics (not just percentages)
4. Simplify punctuation (periods, not em-dashes)
5. Ensure natural, conversational tone
6. Maintain consistent style throughout

CRITICAL CONSTRAINTS:
- PRESERVE ALL source_ids (every single one)
- DO NOT change facts, metrics, or technologies
- DO NOT add new information
- ONLY improve language and clarity

Return the edited resume in the JSON format specified above, including:
- "original_text" field for each edited achievement
- "edits_made" list explaining changes
- "style_changes_summary" object with edit counts
"""
        
        return prompt
    
    def parse_response(self, response: str) -> ResumeDraft:
        """
        Parse edited resume response
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Edited ResumeDraft object
        """
        # Extract JSON from response
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
        
        # Extract style changes summary if present
        style_summary = data.pop('style_changes_summary', None)
        
        # Clean up data - extract text from dict fields if needed
        # Sometimes LLM returns professional_summary as a dict with 'text' field
        if isinstance(data.get('professional_summary'), dict):
            data['professional_summary'] = data['professional_summary'].get('text', '')
        
        # Clean up achievements - extract text if wrapped in dict
        for exp in data.get('experience', []):
            achievements = exp.get('achievements', [])
            cleaned_achievements = []
            for ach in achievements:
                if isinstance(ach, dict) and 'text' in ach:
                    # Keep the dict format for achievements (has source_id)
                    cleaned_achievements.append(ach)
                elif isinstance(ach, str):
                    cleaned_achievements.append(ach)
                else:
                    # Fallback
                    cleaned_achievements.append(ach)
            exp['achievements'] = cleaned_achievements
        
        # Validate with Pydantic (build citations if needed)
        if 'citations' not in data:
            citations = self._extract_citations(data)
            data['citations'] = citations
        
        try:
            edited_draft = ResumeDraft(**data)
        except Exception as e:
            self.console.print(f"[red]Validation error: {e}[/red]")
            self.console.print(f"[yellow]Data keys: {list(data.keys())}[/yellow]")
            # Show problematic field
            if 'professional_summary' in data:
                ps_type = type(data['professional_summary']).__name__
                self.console.print(f"[yellow]professional_summary type: {ps_type}[/yellow]")
                if isinstance(data['professional_summary'], dict):
                    self.console.print(f"[yellow]professional_summary keys: {list(data['professional_summary'].keys())}[/yellow]")
            raise
        
        # Show summary
        exp_count = len(edited_draft.experience)
        total_achievements = sum(len(exp.get('achievements', [])) for exp in edited_draft.experience)
        
        summary_data = {
            "Experiences Edited": exp_count,
            "Achievement Bullets": total_achievements,
            "Summary Length": f"{len(edited_draft.professional_summary)} chars"
        }
        
        if style_summary:
            summary_data.update({
                "Corporate Speak Removed": style_summary.get('corporate_speak_removed', 0),
                "Passive Voice Fixed": style_summary.get('passive_voice_fixed', 0),
                "Clarity Improved": style_summary.get('clarity_improved', 0),
                "Total Edits": style_summary.get('total_edits', 0)
            })
        
        self.show_summary(summary_data)
        
        # Show example edits
        if style_summary and style_summary.get('total_edits', 0) > 0:
            self.console.print("\n[cyan]Style Improvements:[/cyan]")
            self.console.print(f"  • Removed {style_summary.get('corporate_speak_removed', 0)} instances of corporate speak")
            self.console.print(f"  • Fixed {style_summary.get('passive_voice_fixed', 0)} passive voice constructions")
            self.console.print(f"  • Improved clarity in {style_summary.get('clarity_improved', 0)} bullets")
        
        return edited_draft
    
    def _extract_citations(self, resume_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract all source_id citations from resume"""
        citations = {}
        
        # Extract from experiences
        for i, exp in enumerate(resume_data.get('experience', [])):
            exp_id = exp.get('source_id', 'MISSING')
            citations[f"experience[{i}]"] = exp_id
            
            # Extract from achievements
            for j, ach in enumerate(exp.get('achievements', [])):
                if isinstance(ach, dict):
                    ach_id = ach.get('source_id', exp_id)
                    citations[f"experience[{i}].achievements[{j}]"] = ach_id
        
        # Extract from projects
        for i, proj in enumerate(resume_data.get('bulleted_projects', [])):
            proj_id = proj.get('source_id', 'MISSING')
            citations[f"projects[{i}]"] = proj_id
        
        return citations
    
    def verify_no_fact_changes(
        self,
        original: ResumeDraft,
        edited: ResumeDraft
    ) -> tuple[bool, list[str]]:
        """
        Verify that no facts were changed during editing
        
        Args:
            original: Original resume draft
            edited: Edited resume draft
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check contact info unchanged
        if original.contact != edited.contact:
            issues.append("Contact information was modified")
        
        # Check experience companies/titles/dates unchanged
        if len(original.experience) != len(edited.experience):
            issues.append(f"Experience count changed: {len(original.experience)} -> {len(edited.experience)}")
        
        for i, (orig_exp, edit_exp) in enumerate(zip(original.experience, edited.experience)):
            if orig_exp.get('company') != edit_exp.get('company'):
                issues.append(f"Experience {i}: Company changed")
            if orig_exp.get('title') != edit_exp.get('title'):
                issues.append(f"Experience {i}: Title changed")
            if orig_exp.get('dates') != edit_exp.get('dates'):
                issues.append(f"Experience {i}: Dates changed")
            if orig_exp.get('source_id') != edit_exp.get('source_id'):
                issues.append(f"Experience {i}: source_id changed!")
            
            # Check achievement source_ids preserved
            orig_achs = orig_exp.get('achievements', [])
            edit_achs = edit_exp.get('achievements', [])
            
            if len(orig_achs) != len(edit_achs):
                issues.append(f"Experience {i}: Achievement count changed")
            
            for j, (orig_ach, edit_ach) in enumerate(zip(orig_achs, edit_achs)):
                if isinstance(orig_ach, dict) and isinstance(edit_ach, dict):
                    if orig_ach.get('source_id') != edit_ach.get('source_id'):
                        issues.append(f"Experience {i}, Achievement {j}: source_id changed!")
        
        # Check project source_ids
        if len(original.bulleted_projects) != len(edited.bulleted_projects):
            issues.append(f"Project count changed: {len(original.bulleted_projects)} -> {len(edited.bulleted_projects)}")
        
        for i, (orig_proj, edit_proj) in enumerate(zip(original.bulleted_projects, edited.bulleted_projects)):
            if orig_proj.get('source_id') != edit_proj.get('source_id'):
                issues.append(f"Project {i}: source_id changed!")
        
        return len(issues) == 0, issues
    
    def edit(
        self,
        resume_draft: ResumeDraft,
        verify_facts: bool = True
    ) -> ResumeDraft:
        """
        Convenience method for external callers
        
        Args:
            resume_draft: Resume to edit
            verify_facts: Whether to verify no facts were changed
            
        Returns:
            Edited ResumeDraft object
        """
        edited = self.execute(resume_draft=resume_draft)
        
        # Verify no facts changed
        if verify_facts:
            is_valid, issues = self.verify_no_fact_changes(resume_draft, edited)
            
            if not is_valid:
                self.console.print("\n[red]⚠ WARNING: Fact verification failed![/red]")
                for issue in issues:
                    self.console.print(f"  • {issue}")
                
                # Ask whether to proceed
                self.console.print("\n[yellow]Using original version due to fact changes[/yellow]")
                return resume_draft
            else:
                self.console.print("\n[green]✓ Fact verification passed - no facts changed[/green]")
        
        return edited
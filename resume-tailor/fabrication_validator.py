"""
Agent 4: Fabrication Validator
Verifies that all resume claims are traceable to source content
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from base_agent import BaseAgent
from schemas import ResumeDraft, ContentSelection, ValidationResult, ValidationIssue


class FabricationValidatorAgent(BaseAgent):
    """Validates resume against source content to prevent fabrication"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Fabrication Validator Agent",
            agent_description="Verifies all claims are traceable to source content - NO fabrication"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "fabrication_validator.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        resume_draft: ResumeDraft,
        content_selection: ContentSelection,
        **kwargs
    ) -> str:
        """
        Build prompt for validation
        
        Args:
            resume_draft: Resume JSON to validate
            content_selection: Source content from Agent 2
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "RESUME DRAFT TO VALIDATE (from Agent 3)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include resume draft
        draft_dict = resume_draft.model_dump()
        prompt += json.dumps(draft_dict, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "SOURCE CONTENT (ONLY allowed sources from Agent 2)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include source content
        content_dict = content_selection.model_dump()
        prompt += json.dumps(content_dict, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "VALIDATION TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += """
Now validate the resume draft:

1. Verify ALL source_ids are present and valid
2. Check ALL claims are traceable to source content
3. Verify ALL metrics come from source quantified_outcomes or achievements
4. Confirm contact info matches exactly
5. Flag any fabricated or unverifiable content

CRITICAL CHECKS:
- Every experience must have source_id
- Every achievement must have source_id
- Every project must have source_id
- All source_ids must exist in provided sources
- All metrics must be traceable
- No invented companies, titles, or technologies

Return ONLY the validation JSON in the format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> ValidationResult:
        """
        Parse validation response
        
        Args:
            response: Raw response from Claude
            
        Returns:
            ValidationResult object
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
        
        # Convert issues to ValidationIssue objects
        issues = []
        for issue_data in data.get('issues', []):
            try:
                issue = ValidationIssue(**issue_data)
                issues.append(issue)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not parse issue: {e}[/yellow]")
                continue
        
        # Create ValidationResult
        result = ValidationResult(
            is_valid=data.get('is_valid', False),
            issues=issues,
            summary=data.get('validation_notes', '')
        )
        
        # Show summary
        critical_count = sum(1 for i in issues if i.severity == 'critical')
        warning_count = sum(1 for i in issues if i.severity == 'warning')
        info_count = sum(1 for i in issues if i.severity == 'info')
        
        self.show_summary({
            "Valid": "✓ Yes" if result.is_valid else "✗ No",
            "Critical Issues": critical_count,
            "Warnings": warning_count,
            "Info Items": info_count,
            "Total Issues": len(issues)
        })
        
        # Show issues by severity
        if critical_count > 0:
            self.console.print("\n[bold red]Critical Issues:[/bold red]")
            for issue in issues:
                if issue.severity == 'critical':
                    self.console.print(f"  • [{issue.type}] {issue.location}")
                    self.console.print(f"    {issue.message}")
        
        if warning_count > 0:
            self.console.print("\n[yellow]Warnings:[/yellow]")
            for issue in issues:
                if issue.severity == 'warning':
                    self.console.print(f"  • [{issue.type}] {issue.location}")
                    self.console.print(f"    {issue.message}")
        
        return result
    
    def validate(
        self,
        resume_draft: ResumeDraft,
        content_selection: ContentSelection
    ) -> ValidationResult:
        """
        Convenience method for external callers
        
        Args:
            resume_draft: Resume to validate
            content_selection: Source content
            
        Returns:
            ValidationResult object
        """
        return self.execute(
            resume_draft=resume_draft,
            content_selection=content_selection
        )
    
    def perform_structural_validation(
        self,
        resume_draft: ResumeDraft,
        content_selection: ContentSelection
    ) -> List[ValidationIssue]:
        """
        Perform basic structural validation before calling LLM
        Catches obvious issues quickly
        
        Args:
            resume_draft: Resume to validate
            content_selection: Source content
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Build set of valid source IDs
        valid_sources = set()
        for exp in content_selection.selected_experiences:
            valid_sources.add(exp.source_id)
        for proj in content_selection.selected_projects:
            valid_sources.add(proj.source_id)
        
        # Check experiences
        for i, exp in enumerate(resume_draft.experience):
            exp_source = exp.get('source_id')
            
            if not exp_source:
                issues.append(ValidationIssue(
                    severity='critical',
                    type='missing_source_id',
                    location=f'experience[{i}]',
                    message='Experience missing source_id field'
                ))
            elif exp_source not in valid_sources:
                issues.append(ValidationIssue(
                    severity='critical',
                    type='invalid_source_id',
                    location=f'experience[{i}]',
                    message=f'Invalid source_id: {exp_source}'
                ))
            
            # Check achievements
            for j, ach in enumerate(exp.get('achievements', [])):
                if isinstance(ach, dict):
                    ach_source = ach.get('source_id')
                    if not ach_source:
                        issues.append(ValidationIssue(
                            severity='critical',
                            type='missing_source_id',
                            location=f'experience[{i}].achievements[{j}]',
                            message='Achievement missing source_id field'
                        ))
                    elif ach_source not in valid_sources:
                        issues.append(ValidationIssue(
                            severity='critical',
                            type='invalid_source_id',
                            location=f'experience[{i}].achievements[{j}]',
                            message=f'Invalid source_id: {ach_source}'
                        ))
        
        # Check projects
        for i, proj in enumerate(resume_draft.bulleted_projects):
            proj_source = proj.get('source_id')
            
            if not proj_source:
                issues.append(ValidationIssue(
                    severity='critical',
                    type='missing_source_id',
                    location=f'bulleted_projects[{i}]',
                    message='Project missing source_id field'
                ))
            elif proj_source not in valid_sources:
                issues.append(ValidationIssue(
                    severity='critical',
                    type='invalid_source_id',
                    location=f'bulleted_projects[{i}]',
                    message=f'Invalid source_id: {proj_source}'
                ))
        
        return issues

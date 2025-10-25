"""
Agent 6: Final QA Agent
Comprehensive quality assurance before delivery
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from base_agent import BaseAgent
from schemas import ResumeDraft, QAReport, QAIssue


class FinalQAAgent(BaseAgent):
    """Performs comprehensive quality assurance on completed resume"""
    
    def __init__(self, client, model: str):
        super().__init__(
            client=client,
            model=model,
            agent_name="Final QA Agent",
            agent_description="Comprehensive quality assurance - Final check"
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "final_qa.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def build_prompt(
        self,
        resume_draft: ResumeDraft,
        job_requirements: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Build prompt for QA
        
        Args:
            resume_draft: Final resume to check
            job_requirements: Optional job requirements for ATS check
            
        Returns:
            Complete prompt
        """
        prompt = f"{self.prompt_template}\n\n"
        prompt += "═" * 70 + "\n"
        prompt += "RESUME TO REVIEW (final version)\n"
        prompt += "═" * 70 + "\n\n"
        
        # Include resume draft
        draft_dict = resume_draft.model_dump()
        prompt += json.dumps(draft_dict, indent=2)
        
        if job_requirements:
            prompt += "\n\n" + "═" * 70 + "\n"
            prompt += "JOB REQUIREMENTS (for ATS check)\n"
            prompt += "═" * 70 + "\n\n"
            prompt += json.dumps(job_requirements, indent=2)
        
        prompt += "\n\n" + "═" * 70 + "\n"
        prompt += "QUALITY ASSURANCE TASK\n"
        prompt += "═" * 70 + "\n\n"
        
        prompt += """
Now perform comprehensive quality assurance:

1. Check ALL sections for completeness
2. Verify contact information is valid
3. Review professional summary quality
4. Check ALL experience entries and bullets
5. Verify technical expertise section
6. Review projects (if present)
7. Check education section
8. Verify consistency throughout
9. Check ATS optimization
10. Assess professionalism and polish

For each issue found:
- Specify severity (critical/warning/info)
- Identify exact location
- Explain the problem clearly
- Provide specific recommendation

Return comprehensive QA report in the JSON format specified above.
"""
        
        return prompt
    
    def parse_response(self, response: str) -> QAReport:
        """
        Parse QA report response
        
        Args:
            response: Raw response from Claude
            
        Returns:
            QAReport object
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
        
        # Convert issues to QAIssue objects
        issues = []
        for issue_data in data.get('issues', []):
            try:
                issue = QAIssue(**issue_data)
                issues.append(issue)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not parse issue: {e}[/yellow]")
                continue
        
        # Create QAReport
        report = QAReport(
            overall_status=data.get('overall_status', 'unknown'),
            overall_score=data.get('overall_score', 0),
            ready_to_submit=data.get('ready_to_submit', False),
            section_scores=data.get('section_scores', {}),
            issues=issues,
            strengths=data.get('strengths', []),
            areas_for_improvement=data.get('areas_for_improvement', []),
            ats_analysis=data.get('ats_analysis', {}),
            statistics=data.get('statistics', {}),
            final_recommendation=data.get('final_recommendation', '')
        )
        
        # Show summary
        critical_count = sum(1 for i in issues if i.severity == 'critical')
        warning_count = sum(1 for i in issues if i.severity == 'warning')
        info_count = sum(1 for i in issues if i.severity == 'info')
        
        self.show_summary({
            "Overall Score": f"{report.overall_score}/100",
            "Status": report.overall_status.upper(),
            "Ready to Submit": "✓ Yes" if report.ready_to_submit else "✗ No",
            "Critical Issues": critical_count,
            "Warnings": warning_count,
            "Info Items": info_count,
            "Total Issues": len(issues)
        })
        
        # Show status with appropriate color
        if report.overall_status == "pass":
            self.console.print("\n[bold green]✓ Quality Check: PASSED[/bold green]")
        elif report.overall_status == "pass_with_warnings":
            self.console.print("\n[bold yellow]⚠ Quality Check: PASSED WITH WARNINGS[/bold yellow]")
        else:
            self.console.print("\n[bold red]✗ Quality Check: NEEDS REVISION[/bold red]")
        
        # Show issues by severity
        if critical_count > 0:
            self.console.print("\n[bold red]Critical Issues:[/bold red]")
            for issue in issues[:5]:  # Show first 5
                if issue.severity == 'critical':
                    self.console.print(f"  • [{issue.category}] {issue.location}")
                    self.console.print(f"    {issue.issue}")
                    if issue.recommendation:
                        self.console.print(f"    → {issue.recommendation}")
        
        if warning_count > 0:
            self.console.print("\n[yellow]Warnings:[/yellow]")
            for issue in issues[:5]:  # Show first 5
                if issue.severity == 'warning':
                    self.console.print(f"  • [{issue.category}] {issue.location}")
                    self.console.print(f"    {issue.issue}")
        
        # Show strengths
        if report.strengths:
            self.console.print("\n[green]Strengths:[/green]")
            for strength in report.strengths[:3]:
                self.console.print(f"  • {strength}")
        
        return report
    
    def review(
        self,
        resume_draft: ResumeDraft,
        job_requirements: Dict[str, Any] = None
    ) -> QAReport:
        """
        Convenience method for external callers
        
        Args:
            resume_draft: Resume to review
            job_requirements: Optional job requirements
            
        Returns:
            QAReport object
        """
        return self.execute(
            resume_draft=resume_draft,
            job_requirements=job_requirements
        )
    
    def perform_basic_checks(
        self,
        resume_draft: ResumeDraft
    ) -> List[QAIssue]:
        """
        Perform basic structural checks before calling LLM
        Quick validation of obvious issues
        
        Args:
            resume_draft: Resume to check
            
        Returns:
            List of QA issues found
        """
        issues = []
        
        # Check contact info
        if not resume_draft.contact.get('name'):
            issues.append(QAIssue(
                severity='critical',
                category='completeness',
                location='contact.name',
                issue='Name is missing',
                recommendation='Add full name to contact section'
            ))
        
        if not resume_draft.contact.get('email'):
            issues.append(QAIssue(
                severity='critical',
                category='completeness',
                location='contact.email',
                issue='Email is missing',
                recommendation='Add email address to contact section'
            ))
        
        # Check professional summary
        if not resume_draft.professional_summary or len(resume_draft.professional_summary) < 30:
            issues.append(QAIssue(
                severity='critical',
                category='completeness',
                location='professional_summary',
                issue='Professional summary is missing or too short',
                recommendation='Add 2-4 sentence professional summary'
            ))
        
        # Check experiences
        if not resume_draft.experience or len(resume_draft.experience) == 0:
            issues.append(QAIssue(
                severity='critical',
                category='completeness',
                location='experience',
                issue='No experience entries found',
                recommendation='Add at least 3 experience entries'
            ))
        
        # Check education
        if not resume_draft.education or len(resume_draft.education) == 0:
            issues.append(QAIssue(
                severity='warning',
                category='completeness',
                location='education',
                issue='No education entries found',
                recommendation='Add education information'
            ))
        
        # Check achievement counts
        total_achievements = sum(
            len(exp.get('achievements', [])) 
            for exp in resume_draft.experience
        )
        
        if total_achievements < 8:
            issues.append(QAIssue(
                severity='warning',
                category='completeness',
                location='experience',
                issue=f'Only {total_achievements} achievement bullets (recommended: 8-15)',
                recommendation='Add more specific achievements with metrics'
            ))
        elif total_achievements > 20:
            issues.append(QAIssue(
                severity='info',
                category='professionalism',
                location='experience',
                issue=f'{total_achievements} achievement bullets may be too many',
                recommendation='Consider condensing to 12-15 most impactful bullets'
            ))
        
        return issues

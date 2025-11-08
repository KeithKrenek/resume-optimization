"""
Agent 2: Content Selector (Enhanced with PDF Compatibility)
Selects relevant database entries WITHOUT modification
PLUS post-processing for PDF schema compatibility
"""

import json
from typing import Dict, Any
from pathlib import Path

from base_agent import BaseAgent
from schemas import JobAnalysis, ContentSelection
from date_formatter import standardize_date, extract_year_from_date


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
        
        prompt += "\n\n**WORK SAMPLES:**\n\n"
        prompt += json.dumps(database.get('work_samples', []), indent=2)
        
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
5. Include work_samples if relevant (2-3 max)
6. Explain match_reasons for each selection
7. Provide coverage analysis

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
            "Selected Work Samples": len(selection.get('selected_work_samples', [])),
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
    
    def _standardize_for_pdf(self, selection: ContentSelection) -> ContentSelection:
        """
        Post-process selection to ensure PDF schema compatibility
        
        This method:
        1. Standardizes all dates to "MMM YYYY - MMM YYYY" format
        2. Flattens contact info (links → top-level)
        3. Transforms publications schema (venue→journal, doi→url)
        4. Ensures all required fields are present
        
        Args:
            selection: Raw selection from agent
            
        Returns:
            Standardized selection ready for PDF generation
        """
        self.console.print("\n[cyan]Post-processing for PDF compatibility...[/cyan]")
        
        # 1. Standardize dates in experiences
        for exp in selection.selected_experiences:
            original_date = exp.dates
            exp.dates = standardize_date(exp.dates)
            if original_date != exp.dates:
                self.console.print(f"[dim]  Date standardized: '{original_date}' → '{exp.dates}'[/dim]")
        
        # 2. Standardize dates in projects
        for proj in selection.selected_projects:
            original_date = proj.dates
            proj.dates = standardize_date(proj.dates)
            if original_date != proj.dates:
                self.console.print(f"[dim]  Date standardized: '{original_date}' → '{proj.dates}'[/dim]")
        
        # 3. Flatten and enhance contact info
        contact = selection.contact_info.copy()
        
        # Flatten nested 'links' if present
        if 'links' in contact:
            links = contact.pop('links')
            if isinstance(links, dict):
                contact.update(links)
        
        # Ensure URLs have https:// prefix
        for field in ['linkedin', 'github', 'portfolio']:
            if field in contact and contact[field]:
                url = contact[field]
                if not url.startswith('http'):
                    contact[field] = f"https://{url}"
        
        selection.contact_info = contact
        
        # 4. Transform publications for PDF compatibility
        if selection.selected_publications:
            transformed_pubs = []
            
            for pub in selection.selected_publications:
                # Handle both dict and object formats
                pub_dict = pub if isinstance(pub, dict) else (
                    pub.__dict__ if hasattr(pub, '__dict__') else pub
                )
                
                # Map database fields to PDF expectations
                transformed = {
                    'title': pub_dict.get('title', ''),
                    'authors': pub_dict.get('authors', ''),
                    # venue → journal
                    'journal': pub_dict.get('venue') or pub_dict.get('journal', ''),
                    # Extract year from date field
                    'year': extract_year_from_date(pub_dict.get('date', '')) or pub_dict.get('year', ''),
                    # doi → url (construct if needed)
                    'url': self._construct_publication_url(pub_dict)
                }
                
                transformed_pubs.append(transformed)
            
            selection.selected_publications = transformed_pubs
            self.console.print(f"[dim]  Transformed {len(transformed_pubs)} publications for PDF[/dim]")
        
        # 5. Ensure work samples have required fields
        if hasattr(selection, 'selected_work_samples') and selection.selected_work_samples:
            for sample in selection.selected_work_samples:
                # Ensure URL is present and formatted
                if isinstance(sample, dict) and 'url' in sample and sample['url']:
                    if not sample['url'].startswith('http'):
                        sample['url'] = f"https://{sample['url']}"
        
        self.console.print("[green]✓ PDF compatibility post-processing complete[/green]")
        
        return selection
    
    def _construct_publication_url(self, pub_dict: Dict[str, Any]) -> str:
        """
        Construct publication URL from available fields
        
        Priority:
        1. Use 'url' field if present
        2. Construct from 'doi' if present
        3. Return empty string
        """
        # Direct URL
        if pub_dict.get('url'):
            url = pub_dict['url']
            return url if url.startswith('http') else f"https://{url}"
        
        # Construct from DOI
        if pub_dict.get('doi'):
            doi = pub_dict['doi']
            # Remove https://doi.org/ prefix if present
            doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
            return f"https://doi.org/{doi}"
        
        return ''
    
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
            ContentSelection object (standardized for PDF)
        """
        # Get raw selection from agent
        raw_selection = self.execute(
            job_analysis=job_analysis,
            database=database
        )
        
        # Post-process for PDF compatibility
        standardized_selection = self._standardize_for_pdf(raw_selection)
        
        return standardized_selection
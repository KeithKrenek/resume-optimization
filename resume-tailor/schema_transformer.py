"""
Schema Transformer
Handles all deterministic schema transformations between database and PDF formats
"""

from typing import Dict, Any, List, Optional
import re
from date_formatter import standardize_date, extract_year_from_date


class SchemaTransformer:
    """
    Centralized schema transformation layer
    Handles ALL database → PDF field mappings
    """
    
    @staticmethod
    def transform_education_entry(db_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform database education entry to PDF-compatible format
        
        Key transformations:
        - graduation_date → graduation (year only)
        - Ensure all required fields present
        
        Args:
            db_entry: Education entry from database
            
        Returns:
            PDF-compatible education entry
        """
        # Extract year from graduation_date
        graduation_date = db_entry.get('graduation_date', '')
        graduation_year = extract_year_from_date(graduation_date)
        
        return {
            'degree': db_entry.get('degree', ''),
            'institution': db_entry.get('institution', ''),
            'location': db_entry.get('location', ''),
            'graduation': graduation_year or '',  # KEY: graduation_date → graduation
            'details': db_entry.get('details', '') or db_entry.get('gpa', '')
        }
    
    @staticmethod
    def transform_publication_entry(db_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform database publication entry to PDF-compatible format
        
        Key transformations:
        - venue → journal
        - doi → url (construct full URL)
        - date → year (extract year only)
        
        Args:
            db_entry: Publication entry from database
            
        Returns:
            PDF-compatible publication entry
        """
        # Extract year from date field
        pub_date = db_entry.get('date', '')
        year = extract_year_from_date(pub_date)
        
        return {
            'title': db_entry.get('title', ''),
            'authors': db_entry.get('authors', ''),
            'journal': db_entry.get('venue', ''),  # KEY: venue → journal
            'year': year or '',
            'url': SchemaTransformer._construct_publication_url(db_entry)  # KEY: doi → url
        }
    
    @staticmethod
    def _construct_publication_url(db_entry: Dict[str, Any]) -> str:
        """
        Construct publication URL from available fields
        
        Priority:
        1. Use 'url' field if present
        2. Construct from 'doi' field if present
        3. Return empty string
        
        Args:
            db_entry: Publication entry from database
            
        Returns:
            Full URL or empty string
        """
        # Check for direct URL
        if db_entry.get('url'):
            url = db_entry['url']
            # Ensure https:// prefix
            return url if url.startswith('http') else f"https://{url}"
        
        # Construct from DOI
        if db_entry.get('doi'):
            doi = db_entry['doi']
            # Remove any existing doi.org prefix
            doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
            return f"https://doi.org/{doi}"
        
        return ''
    
    @staticmethod
    def transform_contact_info(db_contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform and flatten contact information
        
        Key transformations:
        - Flatten nested 'links' dict to top-level
        - Ensure all URLs have https:// prefix
        - Handle both flat and nested structures
        
        Args:
            db_contact: Contact info from database metadata
            
        Returns:
            Flattened, PDF-compatible contact info
        """
        contact = db_contact.copy()
        
        # Flatten nested 'links' if present
        if 'links' in contact and isinstance(contact['links'], dict):
            links = contact.pop('links')
            contact.update(links)
        
        # Ensure URLs have https:// prefix
        url_fields = ['linkedin', 'github', 'portfolio', 'website']
        for field in url_fields:
            if field in contact and contact[field]:
                url = str(contact[field])
                if url and not url.startswith('http'):
                    contact[field] = f"https://{url}"
        
        return contact
    
    @staticmethod
    def transform_work_sample(db_sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform work sample to PDF-compatible format
        
        Key transformations:
        - Ensure URL has https:// prefix
        - Standardize tech field (ensure list)
        
        Args:
            db_sample: Work sample from database
            
        Returns:
            PDF-compatible work sample
        """
        sample = db_sample.copy()
        
        # Ensure URL has prefix
        if 'url' in sample and sample['url']:
            url = str(sample['url'])
            if not url.startswith('http'):
                sample['url'] = f"https://{url}"
        
        # Ensure tech is list
        if 'tech' in sample and not isinstance(sample['tech'], list):
            sample['tech'] = [sample['tech']] if sample['tech'] else []
        
        return sample
    
    @staticmethod
    def standardize_dates_in_selection(selection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize all dates in a content selection to PDF-compatible format
        
        Applies standardize_date() to all date fields in:
        - experiences
        - projects
        
        Args:
            selection: Content selection dict with experiences and projects
            
        Returns:
            Selection with standardized dates
        """
        # Standardize experience dates
        if 'selected_experiences' in selection:
            for exp in selection['selected_experiences']:
                if 'dates' in exp:
                    exp['dates'] = standardize_date(exp['dates'])
        
        # Standardize project dates
        if 'selected_projects' in selection:
            for proj in selection['selected_projects']:
                if 'dates' in proj:
                    proj['dates'] = standardize_date(proj['dates'])
        
        return selection
    
    @staticmethod
    def transform_full_content_selection(
        selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply all necessary transformations to a complete content selection
        
        This is the main entry point for transforming Agent 2 output
        to PDF-compatible format.
        
        Args:
            selection: Raw content selection from selector agents
            
        Returns:
            Fully transformed, PDF-compatible selection
        """
        transformed = selection.copy()
        
        # 1. Standardize dates
        transformed = SchemaTransformer.standardize_dates_in_selection(transformed)
        
        # 2. Transform education entries
        if 'selected_education' in transformed:
            transformed['selected_education'] = [
                SchemaTransformer.transform_education_entry(edu)
                for edu in transformed['selected_education']
            ]
        
        # 3. Transform publications
        if 'selected_publications' in transformed:
            transformed['selected_publications'] = [
                SchemaTransformer.transform_publication_entry(pub)
                for pub in transformed['selected_publications']
            ]
        
        # 4. Transform contact info
        if 'contact_info' in transformed:
            transformed['contact_info'] = SchemaTransformer.transform_contact_info(
                transformed['contact_info']
            )
        
        # 5. Transform work samples
        if 'selected_work_samples' in transformed:
            transformed['selected_work_samples'] = [
                SchemaTransformer.transform_work_sample(sample)
                for sample in transformed['selected_work_samples']
            ]
        
        return transformed


# Unit tests
if __name__ == "__main__":
    print("Testing SchemaTransformer...")
    print("=" * 70)
    
    # Test education transformation
    print("\n1. Education transformation:")
    db_edu = {
        'degree': 'M.S. in Computer Science',
        'institution': 'MIT',
        'location': 'Cambridge, MA',
        'graduation_date': '2019',
        'gpa': '3.9/4.0'
    }
    pdf_edu = SchemaTransformer.transform_education_entry(db_edu)
    print(f"   graduation_date: {db_edu['graduation_date']} → graduation: {pdf_edu['graduation']}")
    assert pdf_edu['graduation'] == '2019', "Year extraction failed"
    assert 'graduation_date' not in pdf_edu, "Old field still present"
    print("   ✓ Education transformation passed")
    
    # Test publication transformation
    print("\n2. Publication transformation:")
    db_pub = {
        'title': 'Test Paper',
        'authors': 'Smith, J., Doe, A.',
        'venue': 'IEEE Conference',
        'date': '2024',
        'doi': '10.1109/TEST.2024.12345'
    }
    pdf_pub = SchemaTransformer.transform_publication_entry(db_pub)
    print(f"   venue: {db_pub['venue']} → journal: {pdf_pub['journal']}")
    print(f"   doi: {db_pub['doi']} → url: {pdf_pub['url']}")
    assert pdf_pub['journal'] == 'IEEE Conference', "Venue→journal failed"
    assert pdf_pub['url'].startswith('https://doi.org/'), "DOI→URL failed"
    assert pdf_pub['year'] == '2024', "Year extraction failed"
    print("   ✓ Publication transformation passed")
    
    # Test contact info transformation
    print("\n3. Contact info transformation:")
    db_contact = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'links': {
            'linkedin': 'linkedin.com/in/johndoe',
            'github': 'github.com/johndoe'
        }
    }
    pdf_contact = SchemaTransformer.transform_contact_info(db_contact)
    print(f"   Flattened links: {list(pdf_contact.keys())}")
    assert 'links' not in pdf_contact, "Links not flattened"
    assert pdf_contact['linkedin'].startswith('https://'), "URL prefix missing"
    print("   ✓ Contact info transformation passed")
    
    # Test date standardization
    print("\n4. Date standardization:")
    selection = {
        'selected_experiences': [
            {'dates': '2019-2025', 'company': 'Test Co'}
        ],
        'selected_projects': [
            {'dates': 'October 2020 - Present', 'title': 'Test Project'}
        ]
    }
    standardized = SchemaTransformer.standardize_dates_in_selection(selection)
    exp_date = standardized['selected_experiences'][0]['dates']
    proj_date = standardized['selected_projects'][0]['dates']
    print(f"   Experience: '2019-2025' → '{exp_date}'")
    print(f"   Project: 'October 2020 - Present' → '{proj_date}'")
    assert 'Jan' in exp_date and 'Dec' in exp_date, "Date standardization failed"
    assert 'Oct' in proj_date and 'Present' in proj_date, "Date standardization failed"
    print("   ✓ Date standardization passed")
    
    print("\n" + "=" * 70)
    print("All SchemaTransformer tests passed! ✓")

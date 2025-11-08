"""
Deduplication Agent
Identifies and removes duplicate content across resume sections using fuzzy matching
"""

from typing import Dict, Any, List, Tuple
from difflib import SequenceMatcher
from rich.console import Console


class DeduplicationAgent:
    """
    Identifies and removes duplicate achievement text across sections
    Uses fuzzy string matching (Option A) - no LLM calls needed
    """
    
    def __init__(self, similarity_threshold: float = 0.80):
        """
        Initialize deduplication agent
        
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider duplicate
                                0.80 = 80% similar
        """
        self.console = Console()
        self.similarity_threshold = similarity_threshold
    
    def deduplicate(
        self,
        content_selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Remove duplicate content from selection
        
        Priority order (keep in higher priority, remove from lower):
        1. Experience achievements (highest priority)
        2. Project achievements
        3. Work samples (lowest priority)
        
        Args:
            content_selection: Aggregated content from ContentAggregator
            
        Returns:
            Deduplicated content selection with metadata about removals
        """
        self.console.print("\n[cyan]Running deduplication analysis...[/cyan]")
        
        # Extract all text content with source tracking
        all_texts = self._extract_all_texts(content_selection)
        
        # Find duplicates
        duplicates = self._find_duplicates(all_texts)
        
        if not duplicates:
            self.console.print("[green]✓ No duplicates found[/green]")
            return content_selection
        
        # Remove duplicates (keep higher priority version)
        deduplicated = self._remove_duplicates(content_selection, duplicates)
        
        # Add deduplication metadata
        deduplicated['deduplication_summary'] = {
            'duplicates_found': len(duplicates),
            'duplicates_removed': self._count_removals(duplicates),
            'duplicate_details': [
                {
                    'kept': dup['kept']['location'],
                    'removed': [r['location'] for r in dup['removed']],
                    'similarity': f"{dup['similarity']:.0%}"
                }
                for dup in duplicates
            ]
        }
        
        # Show summary
        self._show_summary(duplicates)
        
        return deduplicated
    
    def _extract_all_texts(
        self,
        selection: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract all achievement/description texts with source tracking
        
        Returns:
            List of dicts with 'text', 'location', 'section', 'priority'
        """
        texts = []
        
        # 1. Experience achievements (Priority 1 - highest)
        for i, exp in enumerate(selection.get('selected_experiences', [])):
            exp_id = exp.get('source_id', f'exp_{i}')
            
            # Key achievements
            for j, ach in enumerate(exp.get('key_achievements', [])):
                texts.append({
                    'text': ach if isinstance(ach, str) else ach.get('text', ''),
                    'location': f'experience[{i}].key_achievements[{j}]',
                    'section': 'experience',
                    'priority': 1,
                    'source_id': exp_id,
                    'index': (i, j)
                })
            
            # Persona achievements (if selected)
            for j, ach in enumerate(exp.get('persona_achievements', [])):
                texts.append({
                    'text': ach if isinstance(ach, str) else ach.get('text', ''),
                    'location': f'experience[{i}].persona_achievements[{j}]',
                    'section': 'experience',
                    'priority': 1,
                    'source_id': exp_id,
                    'index': (i, j, 'persona')
                })
        
        # 2. Project achievements (Priority 2)
        for i, proj in enumerate(selection.get('selected_projects', [])):
            proj_id = proj.get('source_id', f'proj_{i}')
            
            # Key achievements
            for j, ach in enumerate(proj.get('key_achievements', [])):
                texts.append({
                    'text': ach if isinstance(ach, str) else ach.get('text', ''),
                    'location': f'project[{i}].key_achievements[{j}]',
                    'section': 'project',
                    'priority': 2,
                    'source_id': proj_id,
                    'index': (i, j)
                })
            
            # Structured response (challenge, solution, impact)
            # FIX: Handle None value for structured_response
            structured = proj.get('structured_response') or {}
            for key in ['challenge', 'solution', 'impact']:
                if key in structured and structured[key]:  # Also check if value is not None/empty
                    texts.append({
                        'text': structured[key],
                        'location': f'project[{i}].structured_response.{key}',
                        'section': 'project',
                        'priority': 2,
                        'source_id': proj_id,
                        'index': (i, key)
                    })
        
        # 3. Work samples (Priority 3 - lowest)
        for i, sample in enumerate(selection.get('selected_work_samples', [])):
            texts.append({
                'text': sample.get('description', ''),
                'location': f'work_sample[{i}].description',
                'section': 'work_sample',
                'priority': 3,
                'source_id': sample.get('source_id', f'sample_{i}'),
                'index': (i,)
            })
        
        # Filter out empty texts
        texts = [t for t in texts if t['text'] and len(t['text']) > 20]
        
        return texts
    
    def _find_duplicates(
        self,
        texts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find duplicate texts using fuzzy matching
        
        Returns:
            List of duplicate groups with kept/removed items
        """
        duplicates = []
        processed = set()
        
        # Compare all pairs
        for i, text1 in enumerate(texts):
            if i in processed:
                continue
            
            matches = []
            
            for j, text2 in enumerate(texts):
                if i == j or j in processed:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(text1['text'], text2['text'])
                
                if similarity >= self.similarity_threshold:
                    matches.append({
                        'text': text2,
                        'similarity': similarity
                    })
                    processed.add(j)
            
            # If matches found, create duplicate group
            if matches:
                # Sort matches by priority (keep highest priority)
                all_items = [text1] + [m['text'] for m in matches]
                all_items.sort(key=lambda x: (x['priority'], -len(x['text'])))
                
                kept = all_items[0]  # Highest priority
                removed = all_items[1:]  # Lower priority items
                
                duplicates.append({
                    'kept': kept,
                    'removed': removed,
                    'similarity': max(m['similarity'] for m in matches)
                })
                
                processed.add(i)
        
        return duplicates
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        # Normalize text for comparison
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, t1, t2).ratio()
    
    def _remove_duplicates(
        self,
        selection: Dict[str, Any],
        duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Remove duplicate items from selection
        
        Args:
            selection: Content selection
            duplicates: List of duplicate groups
            
        Returns:
            Selection with duplicates removed
        """
        deduplicated = selection.copy()
        
        # Track items to remove
        to_remove = []
        for dup_group in duplicates:
            for item in dup_group['removed']:
                to_remove.append({
                    'section': item['section'],
                    'location': item['location'],
                    'index': item['index']
                })
        
        # Remove from experiences
        exp_removals = [r for r in to_remove if r['section'] == 'experience']
        if exp_removals:
            deduplicated['selected_experiences'] = self._remove_from_experiences(
                deduplicated['selected_experiences'],
                exp_removals
            )
        
        # Remove from projects
        proj_removals = [r for r in to_remove if r['section'] == 'project']
        if proj_removals:
            deduplicated['selected_projects'] = self._remove_from_projects(
                deduplicated['selected_projects'],
                proj_removals
            )
        
        # Remove from work samples
        sample_removals = [r for r in to_remove if r['section'] == 'work_sample']
        if sample_removals:
            deduplicated['selected_work_samples'] = self._remove_from_work_samples(
                deduplicated['selected_work_samples'],
                sample_removals
            )
        
        return deduplicated
    
    def _remove_from_experiences(
        self,
        experiences: List[Dict[str, Any]],
        removals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove specific achievements from experiences"""
        cleaned = []
        
        for i, exp in enumerate(experiences):
            exp_copy = exp.copy()
            
            # Check for removals in this experience
            exp_removals = [r for r in removals if r['index'][0] == i]
            
            if exp_removals:
                # Remove specific achievements
                if 'key_achievements' in exp_copy:
                    ach_indices = [r['index'][1] for r in exp_removals if len(r['index']) == 2]
                    exp_copy['key_achievements'] = [
                        ach for j, ach in enumerate(exp_copy['key_achievements'])
                        if j not in ach_indices
                    ]
                
                # Remove persona achievements if needed
                if 'persona_achievements' in exp_copy:
                    persona_indices = [r['index'][1] for r in exp_removals if len(r['index']) == 3]
                    exp_copy['persona_achievements'] = [
                        ach for j, ach in enumerate(exp_copy['persona_achievements'])
                        if j not in persona_indices
                    ]
            
            # Only keep experience if it still has achievements
            if exp_copy.get('key_achievements') or exp_copy.get('persona_achievements'):
                cleaned.append(exp_copy)
        
        return cleaned
    
    def _remove_from_projects(
        self,
        projects: List[Dict[str, Any]],
        removals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove specific achievements from projects"""
        cleaned = []
        
        for i, proj in enumerate(projects):
            proj_copy = proj.copy()
            
            # Check for removals in this project
            proj_removals = [r for r in removals if r['index'][0] == i]
            
            if proj_removals:
                # Remove key achievements
                if 'key_achievements' in proj_copy:
                    ach_indices = [r['index'][1] for r in proj_removals if isinstance(r['index'][1], int)]
                    proj_copy['key_achievements'] = [
                        ach for j, ach in enumerate(proj_copy['key_achievements'])
                        if j not in ach_indices
                    ]
                
                # Remove structured response fields if needed
                # (Typically we don't remove these, but flag for review)
            
            # Keep project if it still has content
            if proj_copy.get('key_achievements') or proj_copy.get('structured_response'):
                cleaned.append(proj_copy)
        
        return cleaned
    
    def _remove_from_work_samples(
        self,
        samples: List[Dict[str, Any]],
        removals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove entire work samples if flagged as duplicate"""
        indices_to_remove = [r['index'][0] for r in removals]
        cleaned = [s for i, s in enumerate(samples) if i not in indices_to_remove]
        return cleaned
    
    def _count_removals(self, duplicates: List[Dict[str, Any]]) -> int:
        """Count total items removed"""
        return sum(len(dup['removed']) for dup in duplicates)
    
    def _show_summary(self, duplicates: List[Dict[str, Any]]):
        """Display deduplication summary"""
        if not duplicates:
            return
        
        total_removed = self._count_removals(duplicates)
        
        self.console.print(f"\n[yellow]⚠ Found {len(duplicates)} duplicate groups[/yellow]")
        self.console.print(f"[yellow]  Removed {total_removed} duplicate items[/yellow]")
        
        # Show first few duplicates
        for i, dup in enumerate(duplicates[:3]):
            kept = dup['kept']
            similarity = dup['similarity']
            
            self.console.print(f"\n  Duplicate Group {i+1} ({similarity:.0%} similar):")
            self.console.print(f"    [green]Kept:[/green] {kept['location']}")
            for removed in dup['removed']:
                self.console.print(f"    [red]Removed:[/red] {removed['location']}")
        
        if len(duplicates) > 3:
            self.console.print(f"\n  ... and {len(duplicates) - 3} more duplicate groups")
        
        self.console.print("\n[green]✓ Deduplication complete[/green]")


# Unit tests
if __name__ == "__main__":
    print("Testing DeduplicationAgent...")
    print("=" * 70)
    
    # Test similarity calculation
    agent = DeduplicationAgent(similarity_threshold=0.80)
    
    text1 = "Built ML pipeline processing 100+ variables achieving >90% accuracy"
    text2 = "Built machine learning pipeline processing 100+ variables with >90% accuracy"
    text3 = "Completely different content about frontend development"
    
    sim_12 = agent._calculate_similarity(text1, text2)
    sim_13 = agent._calculate_similarity(text1, text3)
    
    print(f"\n1. Similarity calculation:")
    print(f"   Text1 vs Text2 (should be high): {sim_12:.2%}")
    print(f"   Text1 vs Text3 (should be low): {sim_13:.2%}")
    
    assert sim_12 > 0.80, "Similar texts not detected"
    assert sim_13 < 0.40, "Dissimilar texts incorrectly matched"
    print("   ✓ Similarity calculation passed")
    
    # Test deduplication
    print("\n2. Deduplication test:")
    
    mock_selection = {
        'selected_experiences': [{
            'source_id': 'exp_1',
            'key_achievements': [
                "Built ML pipeline with 90% accuracy",
                "Led team of 4 engineers"
            ]
        }],
        'selected_projects': [{
            'source_id': 'proj_1',
            'key_achievements': [
                "Built machine learning pipeline achieving 90% accuracy",  # Duplicate!
                "Created React dashboard"
            ]
        }],
        'selected_work_samples': []
    }
    
    deduplicated = agent.deduplicate(mock_selection)
    
    # Check that duplicate was removed from projects
    proj_achs = deduplicated['selected_projects'][0]['key_achievements']
    assert len(proj_achs) == 1, "Duplicate not removed from projects"
    assert "React" in proj_achs[0], "Wrong achievement removed"
    
    # Check that original was kept in experiences
    exp_achs = deduplicated['selected_experiences'][0]['key_achievements']
    assert len(exp_achs) == 2, "Experience achievement incorrectly removed"
    
    print("   ✓ Deduplication logic passed")
    
    print("\n" + "=" * 70)
    print("All DeduplicationAgent tests passed! ✓")
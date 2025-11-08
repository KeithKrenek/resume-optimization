"""
Workflow Configurator
Interactive configuration system for resume generation workflow
Allows users to customize sections and agents based on AI recommendations
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from schemas import JobAnalysis
from schema_builder import DynamicSchemaBuilder


class WorkflowConfigurator:
    """Handles workflow configuration based on job analysis and user preferences"""

    def __init__(
        self,
        job_analysis: Optional[JobAnalysis] = None,
        section_registry_path: Optional[str] = None,
        agent_registry_path: Optional[str] = None,
        template_registry_path: Optional[str] = None
    ):
        """Initialize configurator with registries and job analysis"""
        self.job_analysis = job_analysis

        # Load registries
        base_dir = Path(__file__).parent / "config"

        if section_registry_path is None:
            section_registry_path = base_dir / "section_registry.json"
        if agent_registry_path is None:
            agent_registry_path = base_dir / "agent_registry.json"
        if template_registry_path is None:
            template_registry_path = base_dir / "workflow_templates.json"

        with open(section_registry_path, 'r') as f:
            self.section_registry = json.load(f)
        with open(agent_registry_path, 'r') as f:
            self.agent_registry = json.load(f)
        with open(template_registry_path, 'r') as f:
            self.template_registry = json.load(f)

        self.schema_builder = DynamicSchemaBuilder(section_registry_path)

    def get_ai_recommendations(self) -> Dict[str, Any]:
        """
        Get AI-generated recommendations from job analysis

        Returns:
            Dictionary with recommended sections, agents, and reasoning
        """
        if not self.job_analysis:
            return self._get_default_recommendations()

        # Get recommendations from job analysis
        recommendations = {
            'template': self.job_analysis.recommended_template,
            'sections': self.job_analysis.recommended_sections,
            'agents': self.job_analysis.recommended_agents,
            'section_priorities': self.job_analysis.section_priorities,
            'reasoning': self.job_analysis.workflow_reasoning,
            'role_type': self.job_analysis.role_type
        }

        # If no template recommended, try to auto-select one
        if not recommendations['template']:
            recommendations['template'] = self._select_template_by_role_type(
                self.job_analysis.role_type
            )

        # Merge recommended sections with template sections
        if recommendations['template']:
            template = self.template_registry['templates'].get(recommendations['template'])
            if template:
                template_sections = template['sections']

                # If sections were recommended, merge them with template sections
                if recommendations['sections']:
                    # Merge: start with template sections, add recommended ones
                    all_sections = self.schema_builder.merge_section_lists(
                        template_sections,
                        recommendations['sections']
                    )
                    recommendations['sections'] = all_sections
                else:
                    # No recommendations, use template as-is
                    recommendations['sections'] = template_sections

                # Merge section priorities
                if not recommendations['section_priorities']:
                    recommendations['section_priorities'] = template.get('section_priorities', {})

        # If agents not recommended, use template defaults
        if not recommendations['agents'] and recommendations['template']:
            template = self.template_registry['templates'].get(recommendations['template'])
            if template:
                recommendations['agents'] = template['agents']

        return recommendations

    def _get_default_recommendations(self) -> Dict[str, Any]:
        """Get default recommendations when no job analysis available"""
        return {
            'template': 'individual_contributor',
            'sections': [
                'contact',
                'professional_summary',
                'technical_expertise',
                'experience',
                'bulleted_projects',
                'education'
            ],
            'agents': [
                'job_analyzer',
                'content_selector',
                'resume_drafter',
                'fabrication_validator',
                'voice_style_editor',
                'final_qa'
            ],
            'section_priorities': {},
            'reasoning': 'Using default configuration for individual contributor role',
            'role_type': 'individual_contributor'
        }

    def _select_template_by_role_type(self, role_type: str) -> str:
        """Select appropriate template based on role type"""
        role_to_template = {
            'individual_contributor': 'individual_contributor',
            'technical_lead': 'technical_lead',
            'engineering_manager': 'engineering_manager',
            'senior_manager': 'senior_manager',
            'director': 'director',
            'executive': 'executive'
        }
        return role_to_template.get(role_type, 'individual_contributor')

    def present_recommendations_cli(self, auto_accept: bool = False) -> Dict[str, Any]:
        """
        Present recommendations to user via CLI and get their choices

        Args:
            auto_accept: If True, automatically accept all recommendations

        Returns:
            Final workflow configuration
        """
        recommendations = self.get_ai_recommendations()

        print("\n" + "=" * 70)
        print("WORKFLOW CONFIGURATION")
        print("=" * 70)

        if self.job_analysis:
            print(f"\nJob Title: {self.job_analysis.job_title}")
            print(f"Company: {self.job_analysis.company}")
            print(f"Role Type: {self.job_analysis.role_type}")
        print(f"\nRecommended Template: {recommendations['template']}")

        print("\n--- AI REASONING ---")
        print(recommendations['reasoning'])

        print("\n--- RECOMMENDED SECTIONS ---")
        for i, section in enumerate(recommendations['sections'], 1):
            section_info = self.section_registry['sections'].get(section, {})
            priority = recommendations['section_priorities'].get(section, 5)
            required = "✓ required" if section_info.get('required', False) else f"  priority: {priority}/10"
            print(f"  {i:2}. {section:25} {required}")
            print(f"      {section_info.get('description', '')}")

        print("\n--- RECOMMENDED AGENTS ---")
        for i, agent_name in enumerate(recommendations['agents'], 1):
            agent_info = self._get_agent_info(agent_name)
            if agent_info:
                print(f"  {i}. {agent_info.get('name', agent_name)}")
                print(f"     {agent_info.get('description', '')}")

        if auto_accept:
            print("\n✓ Auto-accepting recommendations")
            return self._build_workflow_config(recommendations)

        # Interactive customization
        print("\n" + "-" * 70)
        print("OPTIONS:")
        print("  1. Accept all recommendations")
        print("  2. Customize sections")
        print("  3. Use a different template")
        print("  4. View all available sections")
        print("  5. View all available agents")

        choice = input("\nYour choice (1-5): ").strip()

        if choice == '1':
            return self._build_workflow_config(recommendations)
        elif choice == '2':
            return self._customize_sections_interactive(recommendations)
        elif choice == '3':
            return self._select_template_interactive()
        elif choice == '4':
            self._show_all_sections()
            return self.present_recommendations_cli(auto_accept=False)
        elif choice == '5':
            self._show_all_agents()
            return self.present_recommendations_cli(auto_accept=False)
        else:
            print("Invalid choice. Using recommendations.")
            return self._build_workflow_config(recommendations)

    def _customize_sections_interactive(self, recommendations: Dict) -> Dict[str, Any]:
        """Allow user to customize section selection"""
        print("\n--- CUSTOMIZE SECTIONS ---")
        current_sections = recommendations['sections'].copy()

        # Show available sections
        all_sections = self.schema_builder.get_all_available_sections()
        section_groups = self.schema_builder.get_section_groups()

        print("\nCurrent sections:", ", ".join(current_sections))
        print("\nAvailable section groups:")
        for group_name, group_sections in section_groups.items():
            print(f"  {group_name}: {', '.join(group_sections)}")

        print("\nEnter sections to ADD (comma-separated) or press Enter to skip:")
        add_input = input("> ").strip()
        if add_input:
            to_add = [s.strip() for s in add_input.split(',')]
            current_sections.extend(to_add)

        print("\nEnter sections to REMOVE (comma-separated) or press Enter to skip:")
        remove_input = input("> ").strip()
        if remove_input:
            to_remove = [s.strip() for s in remove_input.split(',')]
            current_sections = [s for s in current_sections if s not in to_remove]

        # Remove duplicates and sort
        current_sections = self.schema_builder.merge_section_lists(current_sections, [])

        # Validate
        valid, invalid = self.schema_builder.validate_sections(current_sections)
        if invalid:
            print(f"\nWarning: Invalid sections removed: {invalid}")
            current_sections = valid

        print(f"\nFinal sections: {', '.join(current_sections)}")

        # Update recommendations
        recommendations['sections'] = current_sections
        return self._build_workflow_config(recommendations)

    def _select_template_interactive(self) -> Dict[str, Any]:
        """Allow user to select a different template"""
        print("\n--- AVAILABLE TEMPLATES ---")
        templates = self.template_registry['templates']

        template_list = list(templates.keys())
        for i, template_name in enumerate(template_list, 1):
            template = templates[template_name]
            print(f"\n{i}. {template['name']}")
            print(f"   {template['description']}")
            print(f"   Sections: {', '.join(template['sections'][:4])}...")

        choice = input("\nSelect template number: ").strip()
        try:
            template_idx = int(choice) - 1
            if 0 <= template_idx < len(template_list):
                template_name = template_list[template_idx]
                template = templates[template_name]
                recommendations = {
                    'template': template_name,
                    'sections': template['sections'],
                    'agents': template['agents'],
                    'section_priorities': template.get('section_priorities', {}),
                    'reasoning': template['description'],
                    'role_type': template.get('role_types', ['individual_contributor'])[0]
                }
                return self._build_workflow_config(recommendations)
        except (ValueError, IndexError):
            pass

        print("Invalid selection. Using original recommendations.")
        return self._build_workflow_config(self.get_ai_recommendations())

    def _show_all_sections(self):
        """Display all available sections"""
        print("\n--- ALL AVAILABLE SECTIONS ---")
        sections = self.section_registry['sections']

        for section_name, section_info in sections.items():
            print(f"\n{section_name}")
            print(f"  Description: {section_info['description']}")
            print(f"  Type: {section_info['schema_type']}")
            print(f"  Required: {section_info['required']}")
            if section_info.get('triggers'):
                print(f"  Triggers: {', '.join(section_info['triggers'][:5])}")

    def _show_all_agents(self):
        """Display all available agents"""
        print("\n--- CORE AGENTS ---")
        for agent_name, agent_info in self.agent_registry['core_agents'].items():
            print(f"\n{agent_info['name']}")
            print(f"  {agent_info['description']}")
            print(f"  Phase: {agent_info['phase']}, Required: {agent_info['required']}")

        print("\n--- OPTIONAL AGENTS ---")
        for agent_name, agent_info in self.agent_registry['optional_agents'].items():
            print(f"\n{agent_info['name']} ({agent_info.get('status', 'available')})")
            print(f"  {agent_info['description']}")
            if agent_info.get('triggers'):
                print(f"  Triggered by: {', '.join(agent_info['triggers'][:5])}")

    def _get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Get agent information from registry"""
        if agent_name in self.agent_registry['core_agents']:
            return self.agent_registry['core_agents'][agent_name]
        elif agent_name in self.agent_registry['optional_agents']:
            return self.agent_registry['optional_agents'][agent_name]
        return None

    def _build_workflow_config(self, recommendations: Dict) -> Dict[str, Any]:
        """Build final workflow configuration from recommendations"""
        config = {
            'template_name': recommendations['template'],
            'enabled_sections': recommendations['sections'],
            'enabled_agents': recommendations['agents'],
            'section_priorities': recommendations['section_priorities'],
            'reasoning': recommendations['reasoning'],
            'role_type': recommendations['role_type'],
        }

        # Validate sections
        valid_sections, invalid_sections = self.schema_builder.validate_sections(
            config['enabled_sections']
        )
        if invalid_sections:
            print(f"\nWarning: Removed invalid sections: {invalid_sections}")
            config['enabled_sections'] = valid_sections

        return config

    def auto_configure(self) -> Dict[str, Any]:
        """
        Automatic configuration using AI recommendations without user interaction

        Returns:
            Final workflow configuration
        """
        recommendations = self.get_ai_recommendations()
        return self._build_workflow_config(recommendations)

    def save_user_preferences(self, config: Dict[str, Any], output_path: Optional[str] = None):
        """Save user's workflow configuration as preferences"""
        if output_path is None:
            output_path = Path(__file__).parent / "config" / "user_preferences.json"

        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✓ Configuration saved to {output_path}")

    def load_user_preferences(self, preferences_path: Optional[str] = None) -> Optional[Dict]:
        """Load previously saved user preferences"""
        if preferences_path is None:
            preferences_path = Path(__file__).parent / "config" / "user_preferences.json"

        try:
            with open(preferences_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None


if __name__ == "__main__":
    # Test the configurator
    print("Testing Workflow Configurator\n")

    # Test without job analysis (default config)
    print("=== Test 1: Default Configuration ===")
    configurator = WorkflowConfigurator()
    default_config = configurator.auto_configure()
    print(f"Template: {default_config['template_name']}")
    print(f"Sections: {default_config['enabled_sections']}")
    print(f"Agents: {len(default_config['enabled_agents'])} agents")

    # Test with mock job analysis
    print("\n=== Test 2: With Job Analysis ===")
    from schemas import JobAnalysis, RoleType

    mock_job_analysis = JobAnalysis(
        job_title="Senior Engineering Manager",
        company="TechCorp",
        role_type=RoleType.ENGINEERING_MANAGER,
        must_have_requirements=[],
        nice_to_have_requirements=[],
        technical_keywords=["python", "aws", "microservices"],
        domain_keywords=["fintech"],
        leadership_keywords=["team building", "mentorship"],
        role_focus="Build and lead engineering teams",
        raw_jd_excerpt="Lead a team of 10 engineers...",
        recommended_template="engineering_manager",
        recommended_sections=["leadership", "strategic_initiatives"],
        recommended_agents=["leadership_highlighter"],
        section_priorities={"leadership": 10, "technical_expertise": 8},
        workflow_reasoning="This role emphasizes people management and team leadership"
    )

    configurator_with_analysis = WorkflowConfigurator(job_analysis=mock_job_analysis)
    config_with_analysis = configurator_with_analysis.auto_configure()
    print(f"Template: {config_with_analysis['template_name']}")
    print(f"Sections: {config_with_analysis['enabled_sections']}")
    print(f"Reasoning: {config_with_analysis['reasoning']}")

    print("\n✓ Configurator tests complete")

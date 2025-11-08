"""
Dynamic Schema Builder
Generates Pydantic models at runtime based on enabled sections from section registry
"""

import json
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo


class DynamicSchemaBuilder:
    """Builds dynamic Pydantic schemas based on section configuration"""

    def __init__(self, section_registry_path: Optional[str] = None):
        """Initialize with section registry"""
        if section_registry_path is None:
            # Default to config/section_registry.json relative to this file
            base_dir = Path(__file__).parent
            section_registry_path = base_dir / "config" / "section_registry.json"

        with open(section_registry_path, 'r') as f:
            self.registry = json.load(f)

        self.sections = self.registry['sections']

    def build_resume_schema(
        self,
        enabled_sections: List[str],
        schema_name: str = "DynamicResumeDraft"
    ) -> Type[BaseModel]:
        """
        Dynamically create ResumeDraft Pydantic schema based on enabled sections

        Args:
            enabled_sections: List of section names to include
            schema_name: Name for the generated schema class

        Returns:
            Dynamically created Pydantic BaseModel class
        """
        field_definitions = {}

        # Build field definitions for each enabled section
        for section_name in enabled_sections:
            if section_name not in self.sections:
                print(f"Warning: Section '{section_name}' not found in registry, skipping")
                continue

            section_config = self.sections[section_name]
            field_type, field_info = self._get_field_definition(section_config)
            field_definitions[section_name] = (field_type, field_info)

        # Always include citations for validation
        field_definitions['citations'] = (
            Dict[str, str],
            Field(
                default_factory=dict,
                description="Map of content to source_id for validation"
            )
        )

        # Create dynamic Pydantic model
        dynamic_model = create_model(schema_name, **field_definitions)
        return dynamic_model

    def _get_field_definition(self, section_config: Dict) -> tuple:
        """
        Convert section config to Pydantic field definition (type, Field)

        Args:
            section_config: Section configuration from registry

        Returns:
            Tuple of (field_type, Field) for Pydantic model
        """
        schema_type = section_config['schema_type']
        required = section_config['required']
        description = section_config['description']

        # Determine field type
        if schema_type == 'string':
            field_type = str
            default = ... if required else ""

        elif schema_type == 'dict':
            field_type = Dict[str, Any]
            default = ... if required else Field(default_factory=dict)

        elif schema_type == 'list':
            field_type = List[Dict[str, Any]]
            default = ... if required else Field(default_factory=list)

        else:
            # Fallback to Any
            field_type = Any
            default = ... if required else None

        # Create Field with description
        if default is ...:
            field_info = Field(description=description)
        elif isinstance(default, FieldInfo):
            field_info = default
            # Note: FieldInfo is immutable in Pydantic v2, so we can't modify it
            # Just use it as-is
        else:
            field_info = Field(default=default, description=description)

        return field_type, field_info

    def get_section_schema(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Get the item schema for a specific section"""
        if section_name not in self.sections:
            return None

        section_config = self.sections[section_name]
        return section_config.get('item_schema', None)

    def get_enabled_sections_for_role(self, role_type: str) -> List[str]:
        """Get default enabled sections for a role type"""
        role_defaults = self.registry.get('role_type_defaults', {})
        return role_defaults.get(role_type, self._get_core_sections())

    def _get_core_sections(self) -> List[str]:
        """Get core sections that are always enabled"""
        section_groups = self.registry.get('section_groups', {})
        return section_groups.get('core', [
            'contact',
            'professional_summary',
            'experience',
            'education'
        ])

    def get_sections_by_triggers(self, keywords: List[str]) -> List[str]:
        """
        Find sections that should be enabled based on keyword triggers

        Args:
            keywords: List of keywords from job description

        Returns:
            List of section names that match triggers
        """
        matched_sections = []
        keywords_lower = [k.lower() for k in keywords]

        for section_name, section_config in self.sections.items():
            triggers = section_config.get('triggers', [])
            if not triggers:
                continue

            # Check if any trigger matches any keyword
            for trigger in triggers:
                trigger_lower = trigger.lower()
                for keyword in keywords_lower:
                    if trigger_lower in keyword or keyword in trigger_lower:
                        matched_sections.append(section_name)
                        break  # Move to next section once matched

                if section_name in matched_sections:
                    break

        return list(set(matched_sections))  # Remove duplicates

    def merge_section_lists(
        self,
        base_sections: List[str],
        additional_sections: List[str],
        exclude_sections: Optional[List[str]] = None
    ) -> List[str]:
        """
        Merge and deduplicate section lists, maintaining order

        Args:
            base_sections: Base list of sections
            additional_sections: Sections to add
            exclude_sections: Sections to exclude

        Returns:
            Merged, deduplicated, and sorted section list
        """
        # Combine and deduplicate
        combined = list(dict.fromkeys(base_sections + additional_sections))

        # Exclude unwanted sections
        if exclude_sections:
            combined = [s for s in combined if s not in exclude_sections]

        # Sort by order defined in registry
        def get_order(section_name: str) -> int:
            if section_name not in self.sections:
                return 999
            return self.sections[section_name].get('order', 999)

        combined.sort(key=get_order)
        return combined

    def validate_sections(self, section_names: List[str]) -> tuple:
        """
        Validate that all sections exist in registry

        Returns:
            Tuple of (valid_sections, invalid_sections)
        """
        valid = []
        invalid = []

        for section_name in section_names:
            if section_name in self.sections:
                valid.append(section_name)
            else:
                invalid.append(section_name)

        return valid, invalid

    def get_section_info(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Get full configuration info for a section"""
        return self.sections.get(section_name)

    def get_all_available_sections(self) -> List[str]:
        """Get list of all available section names"""
        return list(self.sections.keys())

    def get_section_groups(self) -> Dict[str, List[str]]:
        """Get predefined section groups (core, technical, leadership, etc.)"""
        return self.registry.get('section_groups', {})


# Convenience function for backward compatibility
def create_standard_resume_schema() -> Type[BaseModel]:
    """Create the standard resume schema with all core sections"""
    builder = DynamicSchemaBuilder()
    core_sections = builder._get_core_sections()

    # Add standard optional sections
    standard_sections = core_sections + [
        'technical_expertise',
        'bulleted_projects',
        'publications',
        'awards_recognition',
        'work_samples'
    ]

    return builder.build_resume_schema(standard_sections, "StandardResumeDraft")


if __name__ == "__main__":
    # Test the schema builder
    print("Testing Dynamic Schema Builder\n")

    builder = DynamicSchemaBuilder()

    # Test 1: Build schema for engineering manager
    print("=== Test 1: Engineering Manager Schema ===")
    em_sections = [
        'contact',
        'professional_summary',
        'leadership',
        'technical_expertise',
        'experience',
        'bulleted_projects',
        'education'
    ]
    em_schema = builder.build_resume_schema(em_sections, "EngineeringManagerResume")
    print(f"Created schema with fields: {list(em_schema.model_fields.keys())}")

    # Test 2: Get sections by role type
    print("\n=== Test 2: Default Sections by Role ===")
    for role_type in ['individual_contributor', 'engineering_manager', 'director']:
        sections = builder.get_enabled_sections_for_role(role_type)
        print(f"{role_type}: {sections}")

    # Test 3: Match sections by triggers
    print("\n=== Test 3: Sections Matched by Keywords ===")
    test_keywords = ['management', 'leadership', 'research', 'publications', 'certified']
    matched = builder.get_sections_by_triggers(test_keywords)
    print(f"Keywords: {test_keywords}")
    print(f"Matched sections: {matched}")

    # Test 4: Validate sections
    print("\n=== Test 4: Section Validation ===")
    test_sections = ['contact', 'experience', 'invalid_section', 'leadership']
    valid, invalid = builder.validate_sections(test_sections)
    print(f"Valid: {valid}")
    print(f"Invalid: {invalid}")

    print("\n✓ Schema builder tests complete")

"""
Test Dynamic Orchestrator Integration
Tests workflow configuration and dynamic schema building
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from schemas import JobAnalysis, RoleType
from workflow_configurator import WorkflowConfigurator
from schema_builder import DynamicSchemaBuilder


def test_workflow_configuration():
    """Test workflow configuration with mock job analysis"""
    print("\n" + "="*70)
    print("TEST 1: Workflow Configuration")
    print("="*70)

    # Create mock job analysis for engineering manager role
    mock_job_analysis = JobAnalysis(
        job_title="Senior Engineering Manager",
        company="TechCorp",
        role_type=RoleType.ENGINEERING_MANAGER,
        must_have_requirements=[],
        nice_to_have_requirements=[],
        technical_keywords=["Python", "AWS", "microservices", "Kubernetes"],
        domain_keywords=["fintech", "payments"],
        leadership_keywords=["team building", "mentorship", "hiring"],
        role_focus="Build and lead engineering teams to deliver financial services platform",
        raw_jd_excerpt="Lead a team of 10 engineers...",
        recommended_template="engineering_manager",
        recommended_sections=["leadership", "strategic_initiatives", "technical_expertise"],
        recommended_agents=["leadership_highlighter"],
        section_priorities={
            "leadership": 10,
            "strategic_initiatives": 9,
            "technical_expertise": 8,
            "experience": 10,
            "professional_summary": 9
        },
        workflow_reasoning="This role emphasizes people management and strategic technical leadership. The leadership section is essential to showcase team management experience."
    )

    # Test auto-configuration
    configurator = WorkflowConfigurator(job_analysis=mock_job_analysis)
    config = configurator.auto_configure()

    print("\n✓ Workflow configuration generated:")
    print(f"  Template: {config['template_name']}")
    print(f"  Enabled sections: {len(config['enabled_sections'])}")
    print(f"  Sections: {', '.join(config['enabled_sections'][:5])}...")
    print(f"  Reasoning: {config['reasoning'][:100]}...")

    assert config['template_name'] == 'engineering_manager'
    assert 'leadership' in config['enabled_sections']
    assert len(config['enabled_sections']) > 0

    print("\n[PASS] Workflow configuration test")
    return config


def test_dynamic_schema_building(workflow_config):
    """Test dynamic schema building from workflow config"""
    print("\n" + "="*70)
    print("TEST 2: Dynamic Schema Building")
    print("="*70)

    builder = DynamicSchemaBuilder()

    # Build schema from workflow config
    enabled_sections = workflow_config['enabled_sections']
    schema = builder.build_resume_schema(enabled_sections, "TestResumeDraft")

    print(f"\n✓ Dynamic schema created:")
    print(f"  Schema name: {schema.__name__}")
    print(f"  Fields: {len(schema.model_fields)}")
    print(f"  Field names: {', '.join(list(schema.model_fields.keys())[:8])}...")

    # Verify expected sections are in schema
    assert 'contact' in schema.model_fields
    assert 'professional_summary' in schema.model_fields
    assert 'leadership' in schema.model_fields
    assert 'experience' in schema.model_fields
    assert 'citations' in schema.model_fields  # Always included

    # Test schema instantiation
    try:
        instance = schema(
            contact={"name": "Test User", "email": "test@example.com"},
            professional_summary="Test summary",
            leadership=[],
            technical_expertise={},
            experience=[],
            education=[],
            citations={}
        )
        print(f"\n✓ Schema instantiation successful")
        print(f"  Instance type: {type(instance).__name__}")
    except Exception as e:
        print(f"\n✗ Schema instantiation failed: {e}")
        raise

    print("\n[PASS] Dynamic schema building test")
    return schema


def test_section_triggers():
    """Test section matching by keywords"""
    print("\n" + "="*70)
    print("TEST 3: Section Trigger Matching")
    print("="*70)

    builder = DynamicSchemaBuilder()

    # Test different keyword sets
    test_cases = [
        {
            'keywords': ['management', 'leadership', 'team lead'],
            'expected_sections': ['leadership']
        },
        {
            'keywords': ['research', 'publications', 'phd'],
            'expected_sections': ['publications']
        },
        {
            'keywords': ['certified', 'aws certification'],
            'expected_sections': ['certifications']
        },
        {
            'keywords': ['portfolio', 'design samples'],
            'expected_sections': ['work_samples']
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        keywords = test_case['keywords']
        matched = builder.get_sections_by_triggers(keywords)

        print(f"\nTest case {i}:")
        print(f"  Keywords: {keywords}")
        print(f"  Matched sections: {matched}")

        # Check if expected sections are matched
        for expected in test_case['expected_sections']:
            assert expected in matched, f"Expected '{expected}' to be matched for keywords {keywords}"

    print("\n[PASS] Section trigger matching test")


def test_role_type_defaults():
    """Test default sections for different role types"""
    print("\n" + "="*70)
    print("TEST 4: Role Type Default Sections")
    print("="*70)

    builder = DynamicSchemaBuilder()

    role_types = [
        'individual_contributor',
        'engineering_manager',
        'director',
        'executive'
    ]

    for role_type in role_types:
        sections = builder.get_enabled_sections_for_role(role_type)
        print(f"\n{role_type}:")
        print(f"  Default sections ({len(sections)}): {', '.join(sections)}")

        # All roles should have core sections
        assert 'contact' in sections
        assert 'professional_summary' in sections
        assert 'experience' in sections
        assert 'education' in sections

    # Engineering manager should have leadership
    em_sections = builder.get_enabled_sections_for_role('engineering_manager')
    assert 'leadership' in em_sections

    # Director should have strategic initiatives
    director_sections = builder.get_enabled_sections_for_role('director')
    assert 'strategic_initiatives' in director_sections

    print("\n[PASS] Role type defaults test")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("DYNAMIC ORCHESTRATOR INTEGRATION TESTS")
    print("="*70)

    try:
        # Test 1: Workflow configuration
        config = test_workflow_configuration()

        # Test 2: Dynamic schema building
        schema = test_dynamic_schema_building(config)

        # Test 3: Section trigger matching
        test_section_triggers()

        # Test 4: Role type defaults
        test_role_type_defaults()

        # All tests passed
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nThe dynamic orchestrator is ready for integration!")
        print("\nNext steps:")
        print("  1. Test with real AI by running orchestrator_dynamic.py")
        print("  2. Verify workflow recommendations from job analyzer")
        print("  3. Test interactive mode")
        print("  4. Integrate dynamic schema into resume drafter (future)")

        return True

    except AssertionError as e:
        print(f"\n\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

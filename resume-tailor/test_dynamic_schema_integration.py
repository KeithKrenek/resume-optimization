"""
Test Dynamic Schema Integration with Resume Drafter
Tests that resume drafter properly uses dynamic schemas
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from schemas import JobAnalysis, ContentSelection, RoleType
from schema_builder import DynamicSchemaBuilder
from typing import Type
from pydantic import BaseModel


def test_schema_builder_with_custom_sections():
    """Test building a dynamic schema with custom sections"""
    print("\n" + "="*70)
    print("TEST 1: Dynamic Schema Building with Custom Sections")
    print("="*70)

    builder = DynamicSchemaBuilder()

    # Test with engineering manager sections
    sections = [
        'contact',
        'professional_summary',
        'leadership',
        'technical_expertise',
        'experience',
        'bulleted_projects',
        'education'
    ]

    schema = builder.build_resume_schema(sections, "EngineeringManagerResume")

    print(f"\n✓ Schema created: {schema.__name__}")
    print(f"  Fields: {list(schema.model_fields.keys())}")

    # Verify all expected fields are present
    assert 'contact' in schema.model_fields
    assert 'professional_summary' in schema.model_fields
    assert 'leadership' in schema.model_fields
    assert 'technical_expertise' in schema.model_fields
    assert 'experience' in schema.model_fields
    assert 'citations' in schema.model_fields

    print("\n[PASS] Dynamic schema building test")
    return schema


def test_schema_instantiation():
    """Test that dynamic schema can be instantiated"""
    print("\n" + "="*70)
    print("TEST 2: Dynamic Schema Instantiation")
    print("="*70)

    builder = DynamicSchemaBuilder()

    sections = [
        'contact',
        'professional_summary',
        'technical_expertise',
        'experience',
        'education'
    ]

    schema = builder.build_resume_schema(sections, "TestResume")

    # Create instance with minimal data
    try:
        instance = schema(
            contact={"name": "Test User", "email": "test@example.com"},
            professional_summary="Software engineer with 10 years experience",
            technical_expertise={"Languages": ["Python", "JavaScript"]},
            experience=[{
                "company": "Test Corp",
                "title": "Engineer",
                "dates": "2020-Present",
                "location": "Remote",
                "source_id": "exp_test_01",
                "achievements": ["Built systems"]
            }],
            education=[{
                "degree": "BS Computer Science",
                "institution": "University",
                "year": "2015"
            }],
            citations={"experience[0]": "exp_test_01"}
        )

        print(f"\n✓ Instance created successfully")
        print(f"  Type: {type(instance).__name__}")
        print(f"  Fields populated: {len([k for k, v in instance.model_dump().items() if v])}")

        # Verify model_dump works
        data = instance.model_dump()
        assert 'contact' in data
        assert data['contact']['name'] == "Test User"
        assert data['professional_summary'] == "Software engineer with 10 years experience"

        print("\n[PASS] Schema instantiation test")
        return instance

    except Exception as e:
        print(f"\n[FAIL] Schema instantiation failed: {e}")
        raise


def test_different_section_combinations():
    """Test various section combinations"""
    print("\n" + "="*70)
    print("TEST 3: Different Section Combinations")
    print("="*70)

    builder = DynamicSchemaBuilder()

    test_cases = [
        {
            'name': 'IC Role',
            'sections': ['contact', 'professional_summary', 'technical_expertise', 'experience', 'bulleted_projects', 'education']
        },
        {
            'name': 'Director Role',
            'sections': ['contact', 'professional_summary', 'leadership', 'strategic_initiatives', 'experience', 'education']
        },
        {
            'name': 'Research Role',
            'sections': ['contact', 'professional_summary', 'publications', 'experience', 'technical_expertise', 'education']
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test case {i}: {test_case['name']}")
        schema = builder.build_resume_schema(test_case['sections'], f"{test_case['name'].replace(' ', '')}Resume")
        print(f"    Sections: {len(schema.model_fields)} fields")
        print(f"    Fields: {', '.join(list(schema.model_fields.keys())[:5])}...")

        # Verify each section is in the schema
        for section in test_case['sections']:
            assert section in schema.model_fields, f"Missing section: {section}"

    print("\n[PASS] Different section combinations test")


def test_resume_drafter_compatibility():
    """Test that dynamic schemas are compatible with resume drafter expectations"""
    print("\n" + "="*70)
    print("TEST 4: Resume Drafter Compatibility")
    print("="*70)

    builder = DynamicSchemaBuilder()

    # Build schema similar to what orchestrator would create
    sections = [
        'contact',
        'professional_summary',
        'technical_expertise',
        'experience',
        'bulleted_projects',
        'education'
    ]

    schema = builder.build_resume_schema(sections, "DrafterCompatibleResume")

    # Simulate what resume drafter would do
    resume_data = {
        'contact': {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            'location': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/johndoe',
            'github': 'github.com/johndoe'
        },
        'professional_summary': 'Senior software engineer with expertise in distributed systems.',
        'technical_expertise': {
            'Languages': ['Python', 'Go', 'JavaScript'],
            'Frameworks': ['Django', 'React'],
            'Cloud': ['AWS', 'GCP']
        },
        'experience': [{
            'company': 'Tech Corp',
            'title': 'Senior Engineer',
            'dates': '2020-Present',
            'location': 'SF, CA',
            'source_id': 'exp_techcorp_2020',
            'achievements': [
                'Built microservices architecture',
                'Improved system performance by 50%'
            ]
        }],
        'bulleted_projects': [{
            'title': 'Distributed Cache System',
            'org': 'Tech Corp',
            'dates': '2021',
            'source_id': 'proj_cache_2021',
            'description': 'High-performance caching layer',
            'achievements': [
                'Reduced latency by 70%',
                'Handles 1M requests/sec'
            ],
            'tech_stack': ['Redis', 'Go', 'Kubernetes']
        }],
        'education': [{
            'degree': 'BS Computer Science',
            'field': 'Computer Science',
            'institution': 'Stanford University',
            'year': '2015'
        }],
        'citations': {
            'experience[0]': 'exp_techcorp_2020',
            'projects[0]': 'proj_cache_2021'
        }
    }

    try:
        instance = schema(**resume_data)
        print(f"\n✓ Resume drafter compatible schema works")
        print(f"  Created instance with realistic resume data")
        print(f"  Experiences: {len(instance.experience)}")
        print(f"  Projects: {len(instance.bulleted_projects)}")
        print(f"  Citations: {len(instance.citations)}")

        # Verify model_dump for saving
        dumped = instance.model_dump()
        assert 'contact' in dumped
        assert 'experience' in dumped
        assert 'citations' in dumped

        print("\n[PASS] Resume drafter compatibility test")

    except Exception as e:
        print(f"\n[FAIL] Compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """Run all dynamic schema integration tests"""
    print("\n" + "="*70)
    print("DYNAMIC SCHEMA INTEGRATION TESTS")
    print("="*70)

    try:
        # Test 1: Schema building
        schema = test_schema_builder_with_custom_sections()

        # Test 2: Schema instantiation
        instance = test_schema_instantiation()

        # Test 3: Different combinations
        test_different_section_combinations()

        # Test 4: Resume drafter compatibility
        test_resume_drafter_compatibility()

        # All tests passed
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nDynamic schema integration is working correctly!")
        print("\nKey capabilities verified:")
        print("  ✓ Dynamic schema building from section lists")
        print("  ✓ Schema instantiation with resume data")
        print("  ✓ Multiple section combinations")
        print("  ✓ Compatibility with resume drafter expectations")
        print("  ✓ model_dump() for serialization")

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

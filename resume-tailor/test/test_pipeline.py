"""
Test script for Phase 1 Multi-Agent Pipeline
Verifies that Agents 1-2 work correctly
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '/home/claude')

from rich.console import Console
from rich.panel import Panel

console = Console()


def test_schemas():
    """Test that schemas import correctly"""
    console.print("\n[cyan]Testing schemas...[/cyan]")
    
    try:
        from schemas import (
            JobAnalysis, ContentSelection, 
            JobRequirement, SelectedExperience,
            RoleType, RequirementType
        )
        console.print("[green]✓ Schemas imported successfully[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Schema import failed: {e}[/red]")
        return False


def test_state_manager():
    """Test state manager"""
    console.print("\n[cyan]Testing state manager...[/cyan]")
    
    try:
        from state_manager import StateManager
        
        # Create test folder
        test_folder = "/tmp/test_job_folder"
        os.makedirs(test_folder, exist_ok=True)
        
        # Initialize state manager
        sm = StateManager(test_folder)
        
        # Test save/load
        sm.save_state()
        assert os.path.exists(sm.state_file), "State file not saved after save_state()"
        
        console.print("[green]✓ State manager working[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ State manager test failed: {e}[/red]")
        return False


def test_base_agent():
    """Test base agent class"""
    console.print("\n[cyan]Testing base agent...[/cyan]")
    
    try:
        from base_agent import BaseAgent
        console.print("[green]✓ Base agent imported[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Base agent import failed: {e}[/red]")
        return False


def test_agents():
    """Test agent imports"""
    console.print("\n[cyan]Testing agents...[/cyan]")
    
    try:
        from job_analyzer import JobAnalyzerAgent
        from content_selector import ContentSelectorAgent
        console.print("[green]✓ Agents imported successfully[/green]")
        
        # Check prompts exist
        from pathlib import Path
        
        job_analyzer_prompt = Path("job_analyzer.md")
        content_selector_prompt = Path("content_selector.md")
        
        assert job_analyzer_prompt.exists(), "Job analyzer prompt not found"
        assert content_selector_prompt.exists(), "Content selector prompt not found"
        
        console.print("[green]✓ Agent prompts found[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Agent test failed: {e}[/red]")
        return False


def test_config():
    """Test configuration"""
    console.print("\n[cyan]Testing configuration...[/cyan]")
    
    try:
        from config import config
        
        # Check critical settings
        console.print(f"  API Key present: {'✓' if config.anthropic_api_key else '✗'}")
        console.print(f"  Model: {config.default_ai_model}")
        console.print(f"  Database path: {config.database_path}")
        
        # Note: We won't fail if paths don't exist in test environment
        console.print("[green]✓ Configuration loaded[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Config test failed: {e}[/red]")
        return False


def test_orchestrator():
    """Test orchestrator import"""
    console.print("\n[cyan]Testing orchestrator...[/cyan]")
    
    try:
        from orchestrator import ResumeOrchestrator
        console.print("[green]✓ Orchestrator imported[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Orchestrator import failed: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def run_all_tests():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold cyan]Phase 1 Pipeline Tests[/bold cyan]\n"
        "[dim]Verifying all components are working[/dim]",
        border_style="cyan"
    ))
    
    tests = [
        ("Schemas", test_schemas),
        ("State Manager", test_state_manager),
        ("Base Agent", test_base_agent),
        ("Agents", test_agents),
        ("Configuration", test_config),
        ("Orchestrator", test_orchestrator),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            console.print(f"[red]✗ Test '{name}' crashed: {e}[/red]")
            results.append((name, False))
    
    # Summary
    console.print("\n" + "="*70)
    console.print("[bold cyan]Test Summary[/bold cyan]")
    console.print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[green]✓ PASS[/green]" if result else "[red]✗ FAIL[/red]"
        console.print(f"{status} - {name}")
    
    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("\n[bold green]✓ All tests passed! System is ready.[/bold green]")
        return 0
    else:
        console.print("\n[bold yellow]⚠ Some tests failed. Review output above.[/bold yellow]")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

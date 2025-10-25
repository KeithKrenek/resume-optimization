#!/usr/bin/env python3
"""
Quick Setup Script for Resume Generation Pipeline
Helps configure the system interactively
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required = {
        'anthropic': 'Anthropic API client',
        'pydantic': 'Data validation',
        'rich': 'Terminal formatting',
        'dotenv': 'Environment variables'
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package if package != 'dotenv' else 'python_dotenv')
            print(f"✓ {package:20s} - {description}")
        except ImportError:
            print(f"❌ {package:20s} - {description} [MISSING]")
            missing.append(package)
    
    if missing:
        print("\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing)} --break-system-packages")
        return False
    
    return True

def check_node():
    """Check if Node.js is available for PDF generation"""
    print_header("Checking Node.js (for PDF generation)")
    
    try:
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js installed: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  Node.js not found - PDF generation will not work")
            return False
    except FileNotFoundError:
        print("⚠️  Node.js not found - PDF generation will not work")
        return False

def create_env_file():
    """Create .env file interactively"""
    print_header("Configuration Setup")
    
    env_path = Path('.env')
    
    if env_path.exists():
        response = input("📝 .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return
    
    print("\nPlease provide the following configuration:\n")
    
    # API Key
    api_key = input("Anthropic API Key: ").strip()
    if not api_key:
        print("❌ API key is required")
        return
    
    # Database path
    print("\nDatabase file location:")
    database_path = input("Path to keith_resume_database.json: ").strip()
    if not database_path:
        database_path = "./keith_resume_database.json"
    
    # Applications folder
    print("\nOutput folder:")
    applications_folder = input("Folder for resume applications [./applications]: ").strip()
    if not applications_folder:
        applications_folder = "./applications"
    
    # Create applications folder if it doesn't exist
    os.makedirs(applications_folder, exist_ok=True)
    
    # Write .env file
    env_content = f"""# Anthropic API Configuration
ANTHROPIC_API_KEY={api_key}

# File Paths
DATABASE_PATH={database_path}
APPLICATIONS_FOLDER={applications_folder}
INSTRUCTIONS_FOLDER=./assistant-instructions

# Model Settings
DEFAULT_AI_MODEL=claude-sonnet-4-5-20250929
TEMPERATURE=0.2
MAX_TOKENS=16000

# Validation Settings
STRICT_VALIDATION=true
FLAG_UNKNOWN_SOURCES=true
ALLOW_MINOR_PARAPHRASING=true

# Retrieval Settings
TOP_K_EXPERIENCES=8
TOP_K_PROJECTS=6
MIN_RELEVANCE_SCORE=0.3
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✓ Created {env_path}")
    print(f"✓ Applications will be saved to: {applications_folder}")

def check_required_files():
    """Check if required files exist"""
    print_header("Checking Required Files")
    
    required_files = {
        'schemas.py': 'Data schemas',
        'config.py': 'Configuration',
        'state_manager.py': 'State management',
        'orchestrator.py': 'Main orchestrator',
        'job_analyzer.py': 'Agent 1',
        'content_selector.py': 'Agent 2',
        'resume_drafter.py': 'Agent 3',
        'fabrication_validator.py': 'Agent 4'
    }
    
    missing = []
    
    for filename, description in required_files.items():
        if Path(filename).exists():
            print(f"✓ {filename:30s} - {description}")
        else:
            print(f"❌ {filename:30s} - {description} [MISSING]")
            missing.append(filename)
    
    if missing:
        print("\n⚠️  Some files are missing. Ensure all files are in place.")
        return False
    
    return True

def check_prompts():
    """Check if prompt files exist"""
    print_header("Checking Prompt Files")
    
    # Create prompts directory if it doesn't exist
    prompts_dir = Path('prompts')
    if not prompts_dir.exists():
        prompts_dir.mkdir()
        print(f"✓ Created {prompts_dir} directory")
    
    prompts = {
        'job_analyzer.md': 'Job Analyzer prompt',
        'content_selector.md': 'Content Selector prompt',
        'resume_drafter.md': 'Resume Drafter prompt',
        'fabrication_validator.md': 'Fabrication Validator prompt'
    }
    
    missing = []
    
    for filename, description in prompts.items():
        prompt_path = prompts_dir / filename
        
        # Check both in prompts/ and root
        if prompt_path.exists() or Path(filename).exists():
            print(f"✓ {filename:30s} - {description}")
        else:
            print(f"⚠️  {filename:30s} - {description} [NOT IN prompts/]")
            
            # Check if it's in root and offer to move
            if Path(filename).exists():
                response = input(f"   Move {filename} to prompts/? (Y/n): ")
                if response.lower() != 'n':
                    Path(filename).rename(prompt_path)
                    print(f"   ✓ Moved to prompts/")
            else:
                missing.append(filename)
    
    if missing:
        print(f"\n⚠️  Some prompts missing from prompts/: {', '.join(missing)}")
    
    return len(missing) == 0

def verify_database():
    """Verify database file exists and is valid JSON"""
    print_header("Verifying Database")
    
    from config import config
    
    db_path = Path(config.database_path)
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("\nPlease ensure keith_resume_database.json exists at the configured path")
        return False
    
    try:
        import json
        with open(db_path, 'r') as f:
            db = json.load(f)
        
        exp_count = len(db.get('experiences', {}))
        proj_count = len(db.get('projects', {}))
        
        print(f"✓ Database loaded successfully")
        print(f"  - {exp_count} experiences")
        print(f"  - {proj_count} projects")
        
        return True
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return False

def run_test():
    """Offer to run test suite"""
    print_header("Testing")
    
    response = input("Run test suite? (Y/n): ")
    if response.lower() == 'n':
        return
    
    print("\nRunning tests...\n")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'test_complete_pipeline.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
    except Exception as e:
        print(f"❌ Could not run tests: {e}")

def show_next_steps():
    """Show next steps"""
    print_header("Setup Complete!")
    
    print("""
✓ All checks passed! You're ready to generate resumes.

📚 Next Steps:

1. Test the pipeline:
   python orchestrator.py
   (This will use the test job description)

2. Generate a real resume:
   python orchestrator.py \\
     --jd-file path/to/job_description.md \\
     --company "Company Name" \\
     --title "Job Title"

3. Generate with PDF:
   python orchestrator.py --jd-file job.md --company X --title Y --pdf

4. Resume a failed pipeline:
   python orchestrator.py --resume-folder /path/to/job/folder

📖 Documentation:
   - README.md: Complete usage guide
   - IMPROVEMENTS.md: What was built and improved
   - test_complete_pipeline.py: Run all tests

💡 Tips:
   - Review generated resumes before sending
   - Edit resume_final.json if needed, then regenerate PDF
   - Check validation warnings for potential issues
   - Keep your database up to date

Questions? Check README.md for troubleshooting guide.
""")

def main():
    """Main setup flow"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     Multi-Agent Resume Generation Pipeline - Quick Setup        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Node.js", check_node),
        ("Required Files", check_required_files),
        ("Prompt Files", check_prompts),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error during {name}: {e}")
            results.append((name, False))
    
    # Configuration
    try:
        create_env_file()
    except Exception as e:
        print(f"❌ Error creating .env: {e}")
        results.append(("Configuration", False))
    else:
        results.append(("Configuration", True))
    
    # Verify database
    try:
        db_ok = verify_database()
        results.append(("Database", db_ok))
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        results.append(("Database", False))
    
    # Summary
    print_header("Setup Summary")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✓" if ok else "❌"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        # Offer to run tests
        run_test()
        
        # Show next steps
        show_next_steps()
        return 0
    else:
        print("\n⚠️  Some checks failed. Please resolve the issues above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)

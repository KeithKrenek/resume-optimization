"""
Quick Test Script for Batch 1 Updates
Verifies all fixes are working correctly
Run this after updating your GUI to ensure everything works.

Usage:
    python test_batch_1.py
"""

import sys
import os

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    
    print(f"{color}{status}{reset} {name}")
    if message:
        print(f"     {message}")

def test_imports():
    """Test if all required modules can be imported"""
    print_header("TEST 1: Import Verification")
    
    tests = []
    
    # Test basic imports
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
        tests.append(("tkinter modules", True, ""))
    except ImportError as e:
        tests.append(("tkinter modules", False, str(e)))
    
    try:
        import threading
        tests.append(("threading", True, ""))
    except ImportError as e:
        tests.append(("threading", False, str(e)))
    
    try:
        from io import StringIO
        tests.append(("StringIO", True, ""))
    except ImportError as e:
        tests.append(("StringIO", False, str(e)))
    
    # Try importing orchestrator (optional)
    try:
        from orchestrator import ResumeOrchestrator
        tests.append(("orchestrator_enhanced", True, ""))
    except ImportError:
        tests.append(("orchestrator_enhanced", False, "Optional - OK if missing"))
    
    for name, passed, msg in tests:
        print_test(name, passed, msg)
    
    return all(t[1] or "Optional" in t[2] for t in tests)

def test_gui_file_syntax():
    """Test if updated GUI file has valid Python syntax"""
    print_header("TEST 2: GUI File Syntax Check")
    
    if not os.path.exists("resume_generator_gui.py"):
        print_test("GUI file exists", False, "resume_generator_gui.py not found")
        return False
    
    try:
        with open("resume_generator_gui.py", 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, "resume_generator_gui.py", "exec")
        print_test("GUI syntax valid", True, "No syntax errors")
        return True
    except SyntaxError as e:
        print_test("GUI syntax valid", False, f"Line {e.lineno}: {e.msg}")
        return False

def test_gui_features():
    """Test if GUI has required Batch 1 features"""
    print_header("TEST 3: Batch 1 Feature Verification")
    
    if not os.path.exists("resume_generator_gui.py"):
        print("Skipping - GUI file not found")
        return False
    
    with open("resume_generator_gui.py", 'r', encoding='utf-8') as f:
        code = f.read()
    
    features = [
        ("Console tab created", "self.tab_console" in code),
        ("_create_console_tab method", "def _create_console_tab" in code),
        ("_log_console method", "def _log_console" in code),
        ("Console text widget", "self.console_text" in code),
        ("Button style mapping", "style.map(" in code),
        ("Input visibility method", "def _update_input_visibility" in code),
        ("Frame show/hide logic", "pack_forget()" in code),
        ("TeeOutput class", "class TeeOutput" in code),
        ("Stdout redirection", "sys.stdout = " in code),
    ]
    
    for name, passed in features:
        print_test(name, passed, "" if passed else "Not found in code")
    
    return all(f[1] for f in features)

def test_orchestrator_import():
    """Test orchestrator import statement"""
    print_header("TEST 4: Orchestrator Import Check")
    
    if not os.path.exists("resume_generator_gui.py"):
        print("Skipping - GUI file not found")
        return False
    
    with open("resume_generator_gui.py", 'r', encoding='utf-8') as f:
        code = f.read()
    
    tests = [
        ("Uses orchestrator_enhanced", "from orchestrator_enhanced import" in code),
        ("Not using orchestrator_complete", "from orchestrator_complete import" not in code),
    ]
    
    for name, passed in tests:
        print_test(name, passed)
    
    return all(t[1] for t in tests)

def test_pdf_fix():
    """Verify PDF double-open fix is present"""
    print_header("TEST 5: PDF Double-Open Fix")
    
    if not os.path.exists("resume_generator_gui.py"):
        print("Skipping - GUI file not found")
        return False
    
    with open("resume_generator_gui.py", 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Check that messagebox comes before os.startfile in _generate_pdf
    generate_pdf_start = code.find("def _generate_pdf")
    if generate_pdf_start == -1:
        print_test("_generate_pdf method exists", False)
        return False
    
    # Get the _generate_pdf method
    method_end = code.find("\n    def ", generate_pdf_start + 1)
    if method_end == -1:
        method_end = len(code)
    
    method_code = code[generate_pdf_start:method_end]
    
    # Find positions
    messagebox_pos = method_code.find("messagebox.showinfo")
    startfile_pos = method_code.find("os.startfile")
    
    if messagebox_pos == -1:
        print_test("messagebox.showinfo present", False)
        return False
    
    if startfile_pos == -1:
        print_test("PDF opening code present", True, "Note: os.startfile not found (may use subprocess)")
    else:
        fixed = messagebox_pos < startfile_pos
        print_test("messagebox before PDF open", fixed, 
                  "PDF should open AFTER messagebox" if not fixed else "")
        return fixed
    
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  BATCH 1 VERIFICATION TEST SUITE".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Syntax", test_gui_file_syntax()))
    results.append(("Features", test_gui_features()))
    results.append(("Orchestrator", test_orchestrator_import()))
    results.append(("PDF Fix", test_pdf_fix()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%\n")
    
    if passed == total:
        print("\033[92m✓ ALL TESTS PASSED!\033[0m")
        print("\nYour Batch 1 updates are correctly installed.")
        print("You can now proceed to test the GUI manually.")
    else:
        print("\033[91m✗ SOME TESTS FAILED\033[0m")
        print("\nPlease review the failed tests above.")
        print("See MIGRATION_GUIDE.md for help.")
    
    print("\n" + "="*70)
    
    # Manual testing reminder
    print("\nNext Steps:")
    print("1. Run the GUI: python resume_generator_gui.py")
    print("2. Check the Console tab")
    print("3. Test input field visibility")
    print("4. Test button visibility")
    print("5. If possible, run a full pipeline test")
    print("\nSee BATCH_1_CHANGES.md for detailed testing instructions.")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

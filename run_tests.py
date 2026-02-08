#!/usr/bin/env python3
"""
Test runner for BC Hydro Electricity Utilization Analyzer
Runs all tests in the tests/ directory or a specific test if specified.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def run_test_file(test_file):
    """
    Run a single test file.
    
    Args:
        test_file: Path to the test file
        
    Returns:
        tuple: (test_name, passed, message)
    """
    test_name = test_file.stem
    
    try:
        # Load the test module
        spec = importlib.util.spec_from_file_location(test_name, test_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the test
        if hasattr(module, 'run_test'):
            passed, message = module.run_test()
            return (test_name, passed, message)
        else:
            return (test_name, False, "Test file missing run_test() function")
    except Exception as e:
        return (test_name, False, f"Error running test: {str(e)}")

def main():
    """Main test runner."""
    tests_dir = Path('tests')
    
    if not tests_dir.exists():
        print("Error: tests/ directory not found")
        sys.exit(1)
    
    # Determine which tests to run
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        if not test_name.endswith('.py'):
            test_name += '.py'
        test_file = tests_dir / test_name
        
        if not test_file.exists():
            print(f"Error: Test file '{test_file}' not found")
            sys.exit(1)
        
        test_files = [test_file]
    else:
        # Run all tests
        test_files = sorted(tests_dir.glob('test_*.py'))
    
    if not test_files:
        print("No test files found in tests/ directory")
        sys.exit(1)
    
    # Run tests
    print("=" * 70)
    print("BC Hydro Electricity Utilization Analyzer - Test Suite")
    print("=" * 70)
    print()
    
    results = []
    for test_file in test_files:
        test_name, passed, message = run_test_file(test_file)
        results.append((test_name, passed, message))
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")
        print()
    
    # Summary
    print("=" * 70)
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()

# Made with Bob

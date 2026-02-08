#!/usr/bin/env python3
"""
Test: Help option displays help and exits without processing
"""

import subprocess
import sys

def run_test():
    """
    Test that -? displays help and exits without processing.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        # Run the script with -? option
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py', '-?'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check that it exited successfully
        if result.returncode != 0:
            return (False, f"Expected exit code 0, got {result.returncode}")
        
        # Check that help text is displayed
        output = result.stdout
        expected_strings = [
            "BC Hydro Electricity Consumption Analyzer",
            "USAGE:",
            "OPTIONS:",
            "-help, --help, -?",
            "EXAMPLES:"
        ]
        
        missing = []
        for expected in expected_strings:
            if expected not in output:
                missing.append(expected)
        
        if missing:
            return (False, f"Help output missing expected strings: {', '.join(missing)}")
        
        # Check that no processing occurred (no "Processing file" message)
        if "Processing file:" in output or "Processing file:" in result.stderr:
            return (False, "Script should not process files when displaying help")
        
        return (True, "Help displayed correctly without processing")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 10 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

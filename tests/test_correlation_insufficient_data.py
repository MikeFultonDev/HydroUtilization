#!/usr/bin/env python3
"""Test correlation analysis with insufficient data."""

import subprocess
import os
from pathlib import Path

def run_test():
    """
    Test that correlation analysis rejects insufficient data (hourly file with <90 days).
    
    Returns:
        tuple: (passed, message)
    """
    try:
        result = subprocess.run(
            ['python3', 'analyze_temp_correlation.py', 
             'input/bchydro.com-hourly-for-weeks-consumption.csv'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should fail with exit code 1
        if result.returncode != 1:
            return (False, f"Expected exit code 1, got {result.returncode}")
        
        # Check for error message
        output = result.stdout + result.stderr
        if 'Insufficient data' not in output:
            return (False, "Missing 'Insufficient data' error message")
        
        if 'need at least 90' not in output:
            return (False, "Missing minimum data requirement message")
        
        # Verify no output file was created
        output_file = Path('output/bchydro.com-hourly-for-weeks-consumption_correlation.png')
        if output_file.exists():
            # Clean up if it exists from previous run
            output_file.unlink()
        
        return (True, "Correctly rejected insufficient data (<90 days)")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

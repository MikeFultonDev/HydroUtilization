#!/usr/bin/env python3
"""Test correlation analysis with sufficient data."""

import subprocess
import os
from pathlib import Path

def run_test():
    """
    Test that correlation analysis works with sufficient data (daily consumption file).
    
    Returns:
        tuple: (passed, message)
    """
    try:
        result = subprocess.run(
            ['python3', 'analyze_temp_correlation.py', 
             'input/bchydro.com-daily-consumption.csv'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check exit code
        if result.returncode != 0:
            return (False, f"Command failed with exit code {result.returncode}\nStderr: {result.stderr}")
        
        # Check output file exists
        output_file = Path('output/bchydro.com-daily-consumption_correlation.png')
        if not output_file.exists():
            return (False, f"Output file {output_file} not created")
        
        # Check for expected output messages
        output = result.stdout + result.stderr
        if 'Analyzing' not in output:
            return (False, "Missing 'Analyzing' message in output")
        
        if 'Analysis graph saved as:' not in output:
            return (False, "Missing 'Analysis graph saved' message")
        
        if 'Pearson Correlation Coefficient:' not in output:
            return (False, "Missing correlation coefficient in output")
        
        return (True, "Correlation analysis with sufficient data successful")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

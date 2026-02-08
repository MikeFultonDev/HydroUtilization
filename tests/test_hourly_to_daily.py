#!/usr/bin/env python3
"""Test hourly data aggregation to daily."""

import subprocess
import os
from pathlib import Path

def run_test():
    """
    Test aggregating hourly data to daily with --nodisplay.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py',
             'input/bchydro.com-hourly-consumption.csv', '--daily', '--nodisplay'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check exit code
        if result.returncode != 0:
            return (False, f"Command failed with exit code {result.returncode}\nStderr: {result.stderr}")
        
        # Check output file exists
        output_file = Path('output/bchydro.com-hourly-consumption.png')
        if not output_file.exists():
            return (False, f"Output file {output_file} not created")
        
        # Check for expected output messages
        output = result.stdout + result.stderr
        if 'Detected interval type: hourly' not in output:
            return (False, "Did not detect hourly interval type")
        
        if 'Aggregating hourly data to daily' not in output:
            return (False, "Did not aggregate to daily")
        
        return (True, "Hourly to daily aggregation successful")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

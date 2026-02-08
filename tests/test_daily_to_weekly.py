#!/usr/bin/env python3
"""Test daily data aggregation to weekly."""

import subprocess
import os
from pathlib import Path

def run_test():
    """
    Test aggregating daily data to weekly with --nodisplay.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py',
             'input/bchydro.com-daily-consumption.csv', '--weekly', '--nodisplay'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check exit code
        if result.returncode != 0:
            return (False, f"Command failed with exit code {result.returncode}\nStderr: {result.stderr}")
        
        # Check output file exists
        output_file = Path('output/bchydro.com-daily-consumption.png')
        if not output_file.exists():
            return (False, f"Output file {output_file} not created")
        
        # Check for expected output messages
        output = result.stdout + result.stderr
        if 'Detected interval type: daily' not in output:
            return (False, "Did not detect daily interval type")
        
        if 'Aggregating daily data to weekly' not in output:
            return (False, "Did not aggregate to weekly")
        
        return (True, "Daily to weekly aggregation successful")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

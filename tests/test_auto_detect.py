#!/usr/bin/env python3
"""
Test: Auto-detect CSV file in input directory
"""

import subprocess
import os
from pathlib import Path

def run_test():
    """
    Test that the script auto-detects and processes the CSV file in input/ directory.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        # Check that input directory exists and has a CSV file
        input_dir = Path('input')
        if not input_dir.exists():
            return (False, "input/ directory does not exist")
        
        csv_files = list(input_dir.glob('bchydro.com-consumption-*.csv'))
        if len(csv_files) == 0:
            return (False, "No CSV files found in input/ directory")
        if len(csv_files) > 1:
            return (False, f"Multiple CSV files found in input/ directory: {len(csv_files)}")
        
        csv_file = csv_files[0]
        
        # Run the script with --nodisplay option
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py', '--nodisplay'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that it exited successfully
        if result.returncode != 0:
            return (False, f"Script failed with exit code {result.returncode}\nStderr: {result.stderr}")
        
        # Check that it processed the correct file
        output = result.stdout + result.stderr
        if f"Processing file: {csv_file}" not in output:
            return (False, f"Expected to process {csv_file}, but output was:\n{output}")
        
        # Check that output file was created
        expected_output = Path('output') / (csv_file.stem + '.png')
        if not expected_output.exists():
            return (False, f"Expected output file {expected_output} was not created")
        
        # Check that "Graph saved" message appears
        if "Graph saved as:" not in output:
            return (False, "Missing 'Graph saved as:' message in output")
        
        # Check that graph was not displayed (no "Opening graph" message)
        if "Opening graph for display" in output:
            return (False, "Graph should not be displayed with --nodisplay option")
        
        return (True, f"Successfully auto-detected and processed {csv_file.name}")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

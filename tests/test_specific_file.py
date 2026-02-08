#!/usr/bin/env python3
"""
Test: Process a specific CSV file from /tmp directory
"""

import subprocess
import shutil
import os
from pathlib import Path

def run_test():
    """
    Test that the script can process a specific CSV file from /tmp directory.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        # Find the CSV file in input directory
        input_dir = Path('input')
        csv_files = list(input_dir.glob('bchydro.com-consumption-*.csv'))
        
        if len(csv_files) == 0:
            return (False, "No CSV files found in input/ directory to copy")
        
        source_file = csv_files[0]
        
        # Copy to /tmp with name hourly.csv
        tmp_file = Path('/tmp/hourly.csv')
        shutil.copy2(source_file, tmp_file)
        
        if not tmp_file.exists():
            return (False, f"Failed to copy file to {tmp_file}")
        
        # Run the script with the specific file and --nodisplay
        result = subprocess.run(
            ['python3', 'generate_hourly_graph.py', str(tmp_file), '--nodisplay'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that it exited successfully
        if result.returncode != 0:
            # Clean up
            tmp_file.unlink(missing_ok=True)
            return (False, f"Script failed with exit code {result.returncode}\nStderr: {result.stderr}")
        
        # Check that it processed the correct file
        output = result.stdout + result.stderr
        if f"Processing file: {tmp_file}" not in output:
            tmp_file.unlink(missing_ok=True)
            return (False, f"Expected to process {tmp_file}, but output was:\n{output}")
        
        # Check that output file was created with correct name
        expected_output = Path('output/hourly.png')
        if not expected_output.exists():
            tmp_file.unlink(missing_ok=True)
            return (False, f"Expected output file {expected_output} was not created")
        
        # Check that "Graph saved" message appears
        if "Graph saved as:" not in output:
            tmp_file.unlink(missing_ok=True)
            expected_output.unlink(missing_ok=True)
            return (False, "Missing 'Graph saved as:' message in output")
        
        # Check that graph was not displayed
        if "Opening graph for display" in output:
            tmp_file.unlink(missing_ok=True)
            expected_output.unlink(missing_ok=True)
            return (False, "Graph should not be displayed with --nodisplay option")
        
        # Clean up
        tmp_file.unlink(missing_ok=True)
        expected_output.unlink(missing_ok=True)
        
        return (True, f"Successfully processed {tmp_file} and created output/hourly.png")
        
    except subprocess.TimeoutExpired:
        tmp_file.unlink(missing_ok=True)
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        tmp_file.unlink(missing_ok=True)
        return (False, f"Test error: {str(e)}")

# Made with Bob

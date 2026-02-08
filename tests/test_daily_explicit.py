#!/usr/bin/env python3
"""
Test: Process daily CSV file with explicit path
"""

import subprocess
from pathlib import Path

def run_test():
    """
    Test that the script processes daily CSV file when explicitly specified.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        # Check that the daily CSV file exists
        csv_file = Path('input/bchydro.com-daily-consumption.csv')
        if not csv_file.exists():
            return (False, "Daily CSV file not found in input/ directory")
        
        # Run the script with explicit file path and --nodisplay
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py', str(csv_file), '--nodisplay'],
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
        
        # Check that it detected daily interval type
        if "Detected interval type: daily" not in output:
            return (False, "Expected to detect 'daily' interval type")
        
        # Check that output file was created
        expected_output = Path('output/bchydro.com-daily-consumption.png')
        if not expected_output.exists():
            return (False, f"Expected output file {expected_output} was not created")
        
        # Check that "Graph saved" message appears
        if "Graph saved as:" not in output:
            return (False, "Missing 'Graph saved as:' message in output")
        
        # Check that graph was not displayed
        if "Opening graph for display" in output:
            return (False, "Graph should not be displayed with --nodisplay option")
        
        # Verify the graph is wide (daily graphs should be wider than 14 inches)
        # We can't directly check the image dimensions, but we can verify it was created
        file_size = expected_output.stat().st_size
        if file_size < 10000:  # Should be at least 10KB for a proper graph
            return (False, f"Output file seems too small ({file_size} bytes)")
        
        return (True, f"Successfully processed daily data from {csv_file.name}")
        
    except subprocess.TimeoutExpired:
        return (False, "Test timed out after 30 seconds")
    except Exception as e:
        return (False, f"Test error: {str(e)}")

# Made with Bob

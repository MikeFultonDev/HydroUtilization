# Test Suite for BC Hydro Electricity Consumption Analyzer

This directory contains automated tests to ensure the application functions correctly for both hourly and daily consumption data.

## Running Tests

### Run All Tests

From the project root directory:

```bash
python3 run_tests.py
```

Or make it executable and run directly:

```bash
chmod +x run_tests.py
./run_tests.py
```

### Run a Specific Test

To run a single test file:

```bash
python3 run_tests.py test_help
```

Or with the .py extension:

```bash
python3 run_tests.py test_help.py
```

## Available Tests

### Hourly Data Tests

#### test_help.py
Tests that the help option (`-?`, `--help`, `-help`) displays help information and exits without processing any files.

**Validates:**
- Help text is displayed
- Expected sections are present (USAGE, OPTIONS, EXAMPLES)
- No file processing occurs
- Exit code is 0

#### test_auto_detect.py
Tests that the script automatically detects and processes hourly CSV file in the `input/` directory when no file is specified.

**Validates:**
- CSV file is found in `input/` directory
- File is processed successfully (hourly data)
- Hourly interval type detected
- Output PNG is created in `output/` directory
- `--nodisplay` option prevents graph display
- Exit code is 0

#### test_specific_file.py
Tests that the script can process a specific hourly CSV file from an arbitrary location (uses `/tmp/hourly.csv`).

**Validates:**
- File is copied to `/tmp/hourly.csv`
- Script processes the specified file (hourly data)
- Hourly interval type detected
- Output PNG is created with correct name (`output/hourly.png`)
- `--nodisplay` option prevents graph display
- Cleanup occurs after test
- Exit code is 0

### Daily Data Tests

#### test_daily_auto_detect.py
Tests that the script processes daily CSV file with explicit file specification.

**Validates:**
- Daily CSV file exists in `input/` directory
- File is processed successfully (daily data)
- Daily interval type detected
- Output PNG is created in `output/` directory
- `--nodisplay` option prevents graph display
- Exit code is 0

#### test_daily_explicit.py
Tests that the script processes daily CSV file when explicitly specified by path.

**Validates:**
- Daily CSV file is processed with explicit path
- Daily interval type detected
- Output PNG is created with correct name
- Output file size is reasonable (>10KB)
- `--nodisplay` option prevents graph display
- Exit code is 0

#### test_daily_specific_file.py
Tests that the script can process a specific daily CSV file from an arbitrary location (uses `/tmp/daily.csv`).

**Validates:**
- File is copied to `/tmp/daily.csv`
- Script processes the specified file (daily data)
- Daily interval type detected
- Output PNG is created with correct name (`output/daily.png`)
- `--nodisplay` option prevents graph display
- Cleanup occurs after test
- Exit code is 0

## Test Output

Tests provide clear pass/fail status:

```
======================================================================
BC Hydro Electricity Consumption Analyzer - Test Suite
======================================================================

✓ PASS: test_auto_detect
  Successfully auto-detected and processed bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.csv

✓ PASS: test_daily_auto_detect
  Successfully processed daily data from bchydro.com-daily-consumption.csv

✓ PASS: test_daily_explicit
  Successfully processed daily data from bchydro.com-daily-consumption.csv

✓ PASS: test_daily_specific_file
  Successfully processed /tmp/daily.csv and created output/daily.png

✓ PASS: test_help
  Help displayed correctly without processing

✓ PASS: test_specific_file
  Successfully processed /tmp/hourly.csv and created output/hourly.png

======================================================================
Tests run: 6
Passed: 6
Failed: 0
======================================================================
```

## Writing New Tests

To add a new test:

1. Create a new file in the `tests/` directory with the naming pattern `test_*.py`
2. Implement a `run_test()` function that returns a tuple: `(passed: bool, message: str)`
3. The test will be automatically discovered and run by `run_tests.py`

Example test structure:

```python
#!/usr/bin/env python3
"""
Test: Description of what this test validates
"""

import subprocess
from pathlib import Path

def run_test():
    """
    Test description.
    
    Returns:
        tuple: (passed, message)
    """
    try:
        # Test implementation
        result = subprocess.run(
            ['python3', 'generate_consumption_graph.py', '--some-option'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Validate results
        if result.returncode != 0:
            return (False, f"Failed with exit code {result.returncode}")
        
        # More validation...
        
        return (True, "Test passed successfully")
        
    except Exception as e:
        return (False, f"Test error: {str(e)}")
```

## Test Requirements

- Tests should be self-contained and not depend on each other
- Tests should clean up any temporary files they create
- Tests should use `--nodisplay` to prevent opening windows
- Tests should have reasonable timeouts (typically 30 seconds)
- Tests should provide clear, descriptive messages

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```bash
# In your CI script
python3 run_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed!"
    exit 1
fi
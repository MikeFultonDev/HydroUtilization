# BC Hydro Electricity Consumption Analyzer

A Python application that generates visual analysis of electricity consumption data (hourly or daily) from BC Hydro, overlaying temperature data to show correlations between weather and energy usage.

## Features

- **Flexible Analysis**: Automatically detects and processes both hourly and daily consumption data
- **Hourly Analysis**: Visualizes electricity usage by hour of the day
- **Daily Analysis**: Visualizes electricity usage by day of the month
- **Temperature Overlay**: Displays outdoor temperature data alongside consumption (hourly or daily average)
- **Automatic File Detection**: Intelligently finds BC Hydro CSV files in the `input/` directory
- **Organized Output**: Saves graphs to the `output/` directory with matching filenames
- **Automatic Display**: Opens the generated graph automatically (optional)
- **High-Quality Output**: Generates publication-ready PNG graphs at 300 DPI

## Requirements

- Python 3.7 or higher
- Virtual environment (recommended)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install required packages**:
   ```bash
   pip install pandas matplotlib requests
   ```

## Project Structure

```
HydroUtilization/
├── input/                          # Place your BC Hydro CSV files here
│   └── bchydro.com-consumption-*.csv
├── output/                         # Generated graphs are saved here
│   └── bchydro.com-consumption-*.png
├── generate_hourly_graph.py        # Main script
├── README.md                       # This file
└── venv/                          # Virtual environment (created during setup)
```

## Usage

### Basic Usage (Auto-detect CSV file)

Place your BC Hydro CSV file (hourly or daily) in the `input/` directory, then run:

```bash
python3 generate_consumption_graph.py
```

The script will automatically:
- Find any file matching the pattern `bchydro.com-consumption-*.csv` in the `input/` directory
- Detect whether it's hourly or daily data
- Generate the appropriate graph and display it

### Specify a Specific File

To process a specific CSV file:

```bash
python3 generate_consumption_graph.py input/your-file.csv
```

Examples:
```bash
# Process hourly data
python3 generate_consumption_graph.py input/bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.csv

# Process daily data
python3 generate_consumption_graph.py input/bchydro.com-daily-consumption.csv
```

### Display Options

By default, the graph is automatically opened after creation. You can control this behavior:

```bash
# Generate and display the graph (default)
python3 generate_consumption_graph.py

# Generate without displaying
python3 generate_consumption_graph.py --nodisplay

# Explicitly request display
python3 generate_consumption_graph.py --display
```

### Get Help

Display usage information:

```bash
python3 generate_consumption_graph.py --help
```

### Multiple Files Handling

If multiple BC Hydro CSV files exist in the `input/` directory, the script will display an error and list all matching files. You must then specify which file to process:

```bash
Error: Multiple files found matching pattern 'input/bchydro.com-consumption-*.csv':
  - input/bchydro.com-consumption-file1.csv
  - input/bchydro.com-consumption-file2.csv

Please specify which file to process as a command-line argument:
  python3 generate_consumption_graph.py <filename>
```

## Output

The script generates PNG files in the `output/` directory with the same base name as the input file:

- **Input**: `input/bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.csv`
- **Output**: `output/bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.png`

Each graph shows:
- Blue bars: Net electricity consumption (kWh) per period (hour or day)
- Red line: Outdoor temperature (°C) - hourly or daily average
- Location and date/date range information in the title
- Title indicates whether data is "Hourly" or "Daily"

## CSV File Format

The script expects BC Hydro consumption CSV files with the following columns:
- `Interval Start Date/Time`: Timestamp for each reading
  - Hourly format: `YYYY-MM-DD HH:MM` (e.g., "2026-02-06 14:00")
  - Daily format: `YYYY-MM-DD` (e.g., "2025-08-01")
- `Net Consumption (kWh)`: Electricity consumption in kilowatt-hours
- `Service Address`: Property address
- `City`: City name

The script automatically detects the format based on the timestamp.

## Weather Data

Temperature data is automatically fetched from the Open-Meteo API (free, no API key required) based on:
- Location extracted from the CSV file
- Date or date range of the consumption data
- Coordinates for Brackendale, BC (can be modified in the script for other locations)
- For hourly data: Fetches hourly temperatures
- For daily data: Fetches daily average temperatures

## Troubleshooting

### No CSV files found
```
Error: No files found matching pattern 'input/bchydro.com-consumption-*.csv'
```
**Solution**: Ensure your BC Hydro CSV file is in the `input/` directory, or specify the full path to the file.

### File not found
```
Error: Specified file 'filename.csv' does not exist.
```
**Solution**: Check the file path and ensure the file exists.

### Missing dependencies
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution**: Install required packages:
```bash
pip install pandas matplotlib requests
```

### Weather data unavailable
If weather data cannot be fetched, the script will continue and generate the graph with only consumption data.

## Customization

### Modify Location Coordinates

To change the location for weather data (around line 240 in `generate_consumption_graph.py`):

```python
latitude = 49.7833   # Your latitude
longitude = -123.1333  # Your longitude
```

### Change Graph Appearance

Modify the matplotlib styling in the script:
- Colors: `color_consumption` and `color_temp` variables
- Figure size: `figsize=(14, 6)` parameter
- DPI: `dpi=300` in the `savefig()` call

## Example Workflow

```bash
# 1. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install pandas matplotlib requests

# 2. Place your CSV file in the input directory
cp ~/Downloads/bchydro.com-consumption-*.csv input/

# 3. Run the script (graph will open automatically)
python3 generate_consumption_graph.py

# 4. Find your output in the output directory
ls output/
```

## Command-Line Options Summary

| Option | Description |
|--------|-------------|
| `--help`, `-help`, `-?` | Display help message |
| `--display` | Display graph after creation (default) |
| `--nodisplay` | Don't display graph after creation |
| `<filename>` | Specify a specific CSV file to process |

## Testing

The project includes a comprehensive test suite to ensure functionality.

### Run All Tests

```bash
python3 run_tests.py
```

### Run a Specific Test

```bash
python3 run_tests.py test_help
```

### Available Tests

**Hourly Data Tests:**
- **test_help.py**: Validates help display functionality
- **test_auto_detect.py**: Tests automatic CSV file detection
- **test_specific_file.py**: Tests processing files from arbitrary locations

**Daily Data Tests:**
- **test_daily_auto_detect.py**: Tests explicit daily file processing
- **test_daily_explicit.py**: Tests daily file with explicit path
- **test_daily_specific_file.py**: Tests daily files from arbitrary locations

All 6 tests pass successfully, validating both hourly and daily data processing.

For more information about testing, see [tests/README.md](tests/README.md).

## License

This tool is provided as-is for analyzing BC Hydro consumption data.

## Support

For issues or questions, please refer to the script's inline documentation or modify the code to suit your specific needs.
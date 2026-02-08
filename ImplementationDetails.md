# BC Hydro Electricity Consumption Analyzer - Implementation Details

## Overview
A Python application that generates bar graphs showing electricity consumption data from BC Hydro CSV files, with temperature overlays from Open-Meteo weather API. Supports hourly, daily, and weekly data with automatic detection and aggregation capabilities.

## Core Features

### 1. Data Format Detection
- **Automatic interval detection** based on timestamp format in CSV
- Hourly data: Contains time component (space or 'T' separator)
- Daily data: Date only, no time component
- Weekly data: Generated through aggregation

### 2. Data Processing Pipeline

#### Hourly Data (`process_hourly_data`)
- Groups by hour (0-23) and sums consumption
- Adds `IsOvernight` flag for hours 0-6 (midnight to 6am inclusive)
- Returns consumption data with Period (hour), consumption values, and date range

#### Daily Data (`process_daily_data`)
- Creates sequential day indices starting from 0
- Adds `DayOfWeek` (0=Monday, 6=Sunday) and `IsWeekend` flag (Saturday/Sunday)
- Preserves `IsComplete` column if present (from aggregation)
- Returns consumption data with Period (day index), consumption values, dates, and date range

#### Aggregation Functions

**Daily Aggregation (`aggregate_to_daily`)**
- Converts hourly data to daily totals
- Groups by date and sums consumption
- Counts hours per day to detect partial days
- Marks days as complete only if they have 24 hours
- Preserves metadata (City, Service Address)

**Weekly Aggregation (`aggregate_to_weekly`)**
- Converts hourly or daily data to weekly totals
- Calculates week start date (Monday) using `dayofweek` offset
- For hourly: Counts unique dates per week
- For daily: Counts days per week
- Marks weeks as complete only if they have 7 days
- Preserves metadata

### 3. Weather Data Integration

#### Hourly Temperature (`fetch_hourly_temperature`)
- Uses Open-Meteo Archive API
- Fetches hourly temperature for specific date
- Returns DataFrame with Period (hour) and Temperature

#### Daily Temperature (`fetch_daily_temperature`)
- Fetches daily mean temperature for date range
- Returns DataFrame with Period (day index) and Temperature

#### Weekly Temperature
- Aggregates daily temperature data by week
- Calculates mean temperature per week
- Aligns with consumption week boundaries

### 4. Visualization

#### Graph Configuration
- **Hourly**: 14x8 inches
- **Daily/Weekly**: Dynamic width (0.3 inches per period, minimum 14 inches) x 8 inches height
- Dual y-axes: Consumption (left, steelblue) and Temperature (right, orangered)

#### Color Scheme
- **Regular bars**: Steelblue (#4682B4), alpha=0.7
- **Weekend/Overnight bars**: Dark blue (#2F4F7F), alpha=0.85
  - Daily: Saturday and Sunday darker
  - Hourly: Hours 0-6 (midnight-6am) darker
- **Partial period bars**: Steelblue with grey edges, diagonal hatching (//)
- **Temperature line**: Orangered, linewidth=2.5

#### Y-Axis Padding
- Consumption: 15% padding above maximum
- Temperature: 15% padding above max, 5% below min
- Prevents legend overlap with data

#### Legend
- Font size: 9pt
- Location: Upper left
- Combined consumption and temperature entries
- No separate entries for weekend/overnight shading

#### X-Axis Labels
- **Hourly**: 0-23 hour labels
- **Daily**: Date labels (YYYY-MM-DD format)
  - ≤31 days: Every day
  - 32-90 days: Every 7 days
  - >90 days: Every 14 days
- **Weekly**: Week start dates (YYYY-MM-DD format)
  - ≤12 weeks: Every week
  - >12 weeks: Every other week

#### Value Labels
- Consumption values displayed on top of each bar
- Temperature values displayed above each point
- Font sizes: 8pt (consumption), 7pt (temperature)

### 5. Command-Line Interface

#### Arguments
- `[filename]`: Optional CSV file path (relative or absolute)
- `--help`, `-help`, `-?`: Display help message
- `--nodisplay`: Save graph without displaying
- `--display`: Display graph (default)
- `--daily`: Aggregate to daily (hourly→daily)
- `--weekly`: Aggregate to weekly (hourly/daily→weekly)

#### File Discovery
1. If filename provided: Use that file
2. If no filename: Search `input/` directory for `bchydro.com-consumption-*.csv`
3. Error if file not found or multiple matches

### 6. Output
- Saves PNG to `output/` directory
- Filename matches input CSV name
- DPI: 150
- Bbox: tight (no extra whitespace)
- Auto-creates output directory if needed

## Data Structures

### Consumption DataFrame Columns
- `Period`: Sequential index (hour/day/week number)
- `Net Consumption (kWh)`: Consumption value
- `Date`: Date object for labeling (daily/weekly only)
- `IsComplete`: Boolean indicating full period (24 hours or 7 days)
- `IsWeekend`: Boolean for Saturday/Sunday (daily only)
- `IsOvernight`: Boolean for hours 0-6 (hourly only)
- `DayOfWeek`: Integer 0-6 (daily only)

### Temperature DataFrame Columns
- `Period`: Matches consumption Period for alignment
- `Temperature`: Temperature in Celsius

## Key Implementation Details

### Partial Period Detection
- **Daily from hourly**: Count hours per day, complete if 24
- **Weekly from daily**: Count days per week, complete if 7
- **Weekly from hourly**: Count unique dates per week, complete if 7

### Metadata Preservation
- Extract City and Service Address before groupby operations
- Re-add to aggregated DataFrames
- Ensures location info available for graph title

### Date Handling
- Use pandas `to_datetime` for parsing
- Calculate week starts: `date - timedelta(dayofweek)`
- Week starts on Monday (dayofweek=0)

### Error Handling
- Graceful weather API failures (proceed without temperature)
- File validation before processing
- Clear error messages for missing files

## Dependencies
- **pandas**: Data manipulation and aggregation
- **matplotlib**: Graph generation
- **requests**: Weather API calls
- **pathlib**: File path handling
- **subprocess**: Test execution

## Testing Strategy

### Test Coverage
1. Auto-detection of CSV files
2. Explicit file path handling
3. Daily data processing
4. Hourly data processing
5. Hourly→daily aggregation
6. Hourly→weekly aggregation
7. Daily→weekly aggregation
8. Help display
9. File copying to /tmp

### Test Framework
- Custom test runner (`run_tests.py`)
- Each test returns `(passed, message)` tuple
- Tests use `--nodisplay` to avoid GUI interaction
- 30-second timeout per test

## Configuration Constants
- **Location**: Brackendale, BC (49.7833°N, 123.1333°W)
- **Weather API**: https://archive-api.open-meteo.com/v1/archive
- **Input directory**: `input/`
- **Output directory**: `output/`
- **Graph DPI**: 150
- **Figure height**: 8 inches
- **Minimum figure width**: 14 inches

## Future Enhancement Considerations
- Configurable location coordinates
- Multiple location support
- Custom color schemes
- Export to other formats (SVG, PDF)
- Interactive graphs (plotly)
- Cost analysis (rate calculations)
- Comparison between periods
- Peak/off-peak hour highlighting
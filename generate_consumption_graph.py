#!/usr/bin/env python3
"""
Generate a bar graph showing electricity consumption (hourly or daily) with temperature overlay.
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests
import sys
import glob
import os

def print_help():
    """Print usage information and exit."""
    print("""
BC Hydro Electricity Consumption Analyzer
==========================================

USAGE:
    python3 generate_consumption_graph.py [OPTIONS] [CSV_FILE]

OPTIONS:
    -help, --help, -?    Display this help message and exit
    --display            Display the graph after creation (default)
    --nodisplay          Do not display the graph after creation
    --daily              Aggregate data to daily averages (for hourly data)
    --weekly             Aggregate data to weekly averages (for hourly or daily data)
    --text               Generate text output file with consumption and temperature data
                        (excludes partial periods)

ARGUMENTS:
    CSV_FILE             Path to a specific BC Hydro consumption CSV file
                        (optional if only one matching file exists in input/)

DESCRIPTION:
    Generates a bar graph showing electricity consumption with temperature overlay.
    The script automatically detects whether the data is hourly or daily based on
    the timestamp format. You can aggregate data to coarser granularities:
    
    - Use --daily to convert hourly data to daily averages
    - Use --weekly to convert hourly or daily data to weekly averages
    - Use --text to generate a tab-separated text file with the data
    
    If no CSV file is specified, the script will automatically search for files
    matching 'bchydro.com-consumption-*.csv' in the input/ directory.
    Output is saved to the output/ directory.

EXAMPLES:
    # Auto-detect CSV file (if only one exists in input/)
    python3 generate_consumption_graph.py

    # Process a specific file
    python3 generate_consumption_graph.py input/bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.csv

    # Process without displaying the graph
    python3 generate_consumption_graph.py --nodisplay
    
    # Aggregate hourly data to daily averages
    python3 generate_consumption_graph.py --daily input/hourly-file.csv
    
    # Aggregate daily data to weekly averages
    python3 generate_consumption_graph.py --weekly input/daily-file.csv
    
    # Aggregate hourly data to weekly averages
    python3 generate_consumption_graph.py --weekly input/hourly-file.csv

    # Display help
    python3 generate_consumption_graph.py --help

OUTPUT:
    output/<input_filename>.png - Graph showing consumption and temperature

REQUIREMENTS:
    - pandas
    - matplotlib
    - requests

For more information, see README.md
""")
    sys.exit(0)

def find_csv_file(specified_file=None):
    """
    Find the CSV file to process.
    
    Args:
        specified_file: Optional path to a specific CSV file
        
    Returns:
        Path to the CSV file to process
        
    Raises:
        SystemExit: If no file found or multiple files found without specification
    """
    if specified_file:
        if not os.path.exists(specified_file):
            print(f"Error: Specified file '{specified_file}' does not exist.")
            sys.exit(1)
        return specified_file
    
    # Look for files matching the pattern in the input directory
    input_dir = 'input'
    pattern = os.path.join(input_dir, 'bchydro.com-consumption-*.csv')
    matching_files = glob.glob(pattern)
    
    if len(matching_files) == 0:
        print(f"Error: No files found matching pattern '{pattern}'")
        print(f"Please place your BC Hydro CSV file in the '{input_dir}/' directory,")
        print("or specify a CSV file as a command-line argument.")
        sys.exit(1)
    elif len(matching_files) > 1:
        print(f"Error: Multiple files found matching pattern '{pattern}':")
        for f in matching_files:
            print(f"  - {f}")
        print("\nPlease specify which file to process as a command-line argument:")
        print(f"  python3 {sys.argv[0]} <filename>")
        sys.exit(1)
    
    return matching_files[0]

def detect_interval_type(df):
    """
    Detect if the data is hourly or daily based on timestamp format.
    
    Args:
        df: DataFrame with 'Interval Start Date/Time' column
        
    Returns:
        str: 'hourly' or 'daily'
    """
    sample_timestamp = str(df['Interval Start Date/Time'].iloc[0])
    
    # Check if timestamp contains time component (has space or 'T' separator)
    if ' ' in sample_timestamp or 'T' in sample_timestamp:
        return 'hourly'
    else:
        return 'daily'

def process_hourly_data(df):
    """Process hourly consumption data."""
    df['DateTime'] = pd.to_datetime(df['Interval Start Date/Time'])
    df['Hour'] = df['DateTime'].dt.hour
    df['Date'] = df['DateTime'].dt.date
    
    # Group by hour and sum consumption
    consumption_data = df.groupby('Hour')['Net Consumption (kWh)'].sum().reset_index()
    consumption_data.columns = ['Period', 'Net Consumption (kWh)']
    
    # Mark as complete (all 24 hours present)
    consumption_data['IsComplete'] = True
    
    # Add flag for overnight hours (midnight to 6am inclusive)
    consumption_data['IsOvernight'] = consumption_data['Period'] <= 6
    
    return consumption_data, df['Date'].iloc[0], df['Date'].iloc[-1]

def process_daily_data(df):
    """Process daily consumption data."""
    df['Date'] = pd.to_datetime(df['Interval Start Date/Time'])
    
    # Create sequential day numbers starting from 0
    df = df.sort_values('Date')
    df['DayIndex'] = range(len(df))
    
    # Add day of week (0=Monday, 6=Sunday)
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    
    # Keep the date for labeling and preserve IsComplete if it exists
    if 'IsComplete' in df.columns:
        consumption_data = df[['DayIndex', 'Net Consumption (kWh)', 'Date', 'IsComplete', 'DayOfWeek']].copy()
        consumption_data.columns = ['Period', 'Net Consumption (kWh)', 'Date', 'IsComplete', 'DayOfWeek']
    else:
        consumption_data = df[['DayIndex', 'Net Consumption (kWh)', 'Date', 'DayOfWeek']].copy()
        consumption_data.columns = ['Period', 'Net Consumption (kWh)', 'Date', 'DayOfWeek']
        # Mark as complete (full days) only if not already set
        consumption_data['IsComplete'] = True
    
    # Add flag for weekend days (Saturday=5, Sunday=6)
    consumption_data['IsWeekend'] = consumption_data['DayOfWeek'] >= 5
    
    return consumption_data, df['Date'].iloc[0].date(), df['Date'].iloc[-1].date()

def fetch_hourly_temperature(latitude, longitude, date):
    """Fetch hourly temperature data for a specific date."""
    try:
        weather_url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': str(date),
            'end_date': str(date),
            'hourly': 'temperature_2m',
            'timezone': 'America/Vancouver'
        }
        
        response = requests.get(weather_url, params=params)
        weather_data = response.json()
        
        if 'hourly' in weather_data:
            temperatures = weather_data['hourly']['temperature_2m']
            hours = list(range(24))
            return pd.DataFrame({'Period': hours, 'Temperature': temperatures})
        return None
    except Exception as e:
        print(f"Warning: Error fetching weather data: {e}")
        return None

def fetch_daily_temperature(latitude, longitude, start_date, end_date):
    """Fetch daily average temperature data for a date range."""
    try:
        weather_url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'daily': 'temperature_2m_mean',
            'timezone': 'America/Vancouver'
        }
        
        response = requests.get(weather_url, params=params)
        weather_data = response.json()
        
        if 'daily' in weather_data:
            dates = pd.to_datetime(weather_data['daily']['time'])
            temperatures = weather_data['daily']['temperature_2m_mean']
            # Create sequential day indices
            day_indices = list(range(len(dates)))
            return pd.DataFrame({'Period': day_indices, 'Temperature': temperatures, 'Date': dates})
        return None
    except Exception as e:
        print(f"Warning: Error fetching weather data: {e}")
        return None

def aggregate_to_daily(df, interval_type):
    """Aggregate hourly data to daily totals."""
    if interval_type != 'hourly':
        # Already daily or will be handled elsewhere
        return df, 'daily'
    
    # Preserve metadata from first row
    metadata = {
        'City': df['City'].iloc[0],
        'Service Address': df['Service Address'].iloc[0]
    }
    
    df['DateTime'] = pd.to_datetime(df['Interval Start Date/Time'])
    df['Date'] = df['DateTime'].dt.date
    
    # Count hours per day to detect partial days
    hours_per_day = df.groupby('Date').size().reset_index(name='HourCount')
    
    # Group by date and calculate daily totals (sum for consumption)
    daily_data = df.groupby('Date').agg({
        'Net Consumption (kWh)': 'sum'
    }).reset_index()
    
    # Merge hour counts
    daily_data = daily_data.merge(hours_per_day, on='Date')
    
    # Mark days as complete if they have 24 hours
    daily_data['IsComplete'] = daily_data['HourCount'] == 24
    
    # Add back metadata
    daily_data['City'] = metadata['City']
    daily_data['Service Address'] = metadata['Service Address']
    daily_data['Interval Start Date/Time'] = daily_data['Date'].astype(str)
    
    return daily_data, 'daily'

def aggregate_to_weekly(df, interval_type):
    """Aggregate hourly or daily data to weekly totals."""
    # Preserve metadata from first row
    metadata = {
        'City': df['City'].iloc[0],
        'Service Address': df['Service Address'].iloc[0]
    }
    
    df['DateTime'] = pd.to_datetime(df['Interval Start Date/Time'])
    
    # Get the week start date (Monday)
    df['WeekStart'] = df['DateTime'] - pd.to_timedelta(df['DateTime'].dt.dayofweek, unit='D')
    df['WeekStart'] = df['WeekStart'].dt.date
    
    # Count days per week to detect partial weeks
    if interval_type == 'hourly':
        # For hourly data, count unique dates per week
        days_per_week = df.groupby('WeekStart')['DateTime'].apply(lambda x: x.dt.date.nunique()).reset_index(name='DayCount')
    else:
        # For daily data, count days per week
        days_per_week = df.groupby('WeekStart').size().reset_index(name='DayCount')
    
    # Group by week and calculate weekly totals
    weekly_data = df.groupby('WeekStart').agg({
        'Net Consumption (kWh)': 'sum'
    }).reset_index()
    
    # Merge day counts
    weekly_data = weekly_data.merge(days_per_week, on='WeekStart')
    
    # Mark weeks as complete if they have 7 days
    weekly_data['IsComplete'] = weekly_data['DayCount'] == 7
    
    # Add back metadata
    weekly_data['City'] = metadata['City']
    weekly_data['Service Address'] = metadata['Service Address']
    weekly_data['Interval Start Date/Time'] = weekly_data['WeekStart'].astype(str)
    
    return weekly_data, 'weekly'

# Parse command-line arguments
csv_file = None
display_graph = True  # Default is to display
aggregation = None  # None, 'daily', or 'weekly'
text_output = False  # Generate text output

for arg in sys.argv[1:]:
    # Check for help flags
    if arg in ['-help', '--help', '-?']:
        print_help()
    elif arg == '--nodisplay':
        display_graph = False
    elif arg == '--display':
        display_graph = True
    elif arg == '--daily':
        aggregation = 'daily'
    elif arg == '--weekly':
        aggregation = 'weekly'
    elif arg == '--text':
        text_output = True
    elif not arg.startswith('--') and not arg.startswith('-'):
        csv_file = arg

# Find and validate the CSV file
csv_file = find_csv_file(csv_file)
print(f"Processing file: {csv_file}")

# Read the CSV file
df = pd.read_csv(csv_file)

# Convert 'Net Consumption (kWh)' to numeric
df['Net Consumption (kWh)'] = pd.to_numeric(df['Net Consumption (kWh)'])

# Detect interval type
interval_type = detect_interval_type(df)
print(f"Detected interval type: {interval_type}")

# Apply aggregation if requested
if aggregation == 'daily' and interval_type == 'hourly':
    print(f"Aggregating hourly data to daily averages")
    df, interval_type = aggregate_to_daily(df, interval_type)
elif aggregation == 'weekly':
    print(f"Aggregating {interval_type} data to weekly averages")
    df, interval_type = aggregate_to_weekly(df, interval_type)
elif aggregation == 'daily' and interval_type == 'daily':
    print("Data is already daily, no aggregation needed")
elif aggregation == 'daily' and interval_type == 'weekly':
    print("Warning: Cannot aggregate weekly data to daily (coarser to finer)")

# Process data based on interval type (after any aggregation)
if interval_type == 'hourly':
    consumption_data, start_date, end_date = process_hourly_data(df)
    x_label = 'Hour of Day'
    title_period = 'Hourly'
    date_range = str(start_date)
elif interval_type == 'weekly':
    consumption_data, start_date, end_date = process_daily_data(df)  # Reuse daily processing
    x_label = 'Week Starting'
    title_period = 'Weekly'
    date_range = f"{start_date} to {end_date}"
else:  # daily
    consumption_data, start_date, end_date = process_daily_data(df)
    x_label = 'Day'
    title_period = 'Daily'
    date_range = f"{start_date} to {end_date}"

# Get location information
city = df['City'].iloc[0]
address = df['Service Address'].iloc[0]

# Fetch weather data
latitude = 49.7833  # Brackendale, BC
longitude = -123.1333

if interval_type == 'hourly':
    temp_df = fetch_hourly_temperature(latitude, longitude, start_date)
elif interval_type == 'weekly':
    # For weekly data, fetch daily temps and aggregate to weekly
    temp_df = fetch_daily_temperature(latitude, longitude, start_date, end_date)
    if temp_df is not None:
        # Aggregate temperature to weekly averages
        temp_df['Date'] = pd.to_datetime(temp_df['Date'])
        temp_df['WeekStart'] = temp_df['Date'] - pd.to_timedelta(temp_df['Date'].dt.dayofweek, unit='D')
        weekly_temp = temp_df.groupby('WeekStart').agg({'Temperature': 'mean'}).reset_index()
        weekly_temp['Period'] = range(len(weekly_temp))
        temp_df = weekly_temp[['Period', 'Temperature']]
else:  # daily
    temp_df = fetch_daily_temperature(latitude, longitude, start_date, end_date)

if temp_df is None:
    print("Warning: Could not fetch weather data, proceeding without temperature overlay")

# Create figure with dual y-axes - make it wider for daily/weekly data
if interval_type in ['daily', 'weekly']:
    num_periods = len(consumption_data)
    # Use wider figure for daily/weekly data (at least 0.3 inches per period, minimum 14 inches)
    fig_width = max(14, num_periods * 0.3)
    fig, ax1 = plt.subplots(figsize=(fig_width, 8))
else:
    fig, ax1 = plt.subplots(figsize=(14, 8))

# Plot consumption bars on primary y-axis with different styles for complete/incomplete periods
color_consumption = 'steelblue'
color_consumption_dark = '#2F4F7F'  # Much darker blue for weekends/overnight

# Determine if we need special shading for weekends or overnight hours
has_weekend = 'IsWeekend' in consumption_data.columns
has_overnight = 'IsOvernight' in consumption_data.columns

# Check if we have IsComplete column
if 'IsComplete' in consumption_data.columns:
    # Plot complete periods with solid bars
    complete_mask = consumption_data['IsComplete']
    if complete_mask.any():
        # For daily data, separate weekdays and weekends
        if has_weekend:
            # Weekday complete periods
            weekday_complete = complete_mask & ~consumption_data['IsWeekend']
            if weekday_complete.any():
                ax1.bar(consumption_data.loc[weekday_complete, 'Period'],
                        consumption_data.loc[weekday_complete, 'Net Consumption (kWh)'],
                        color=color_consumption, edgecolor='black', linewidth=0.5, alpha=0.7,
                        label='Net Consumption (Complete)')
            
            # Weekend complete periods (darker)
            weekend_complete = complete_mask & consumption_data['IsWeekend']
            if weekend_complete.any():
                ax1.bar(consumption_data.loc[weekend_complete, 'Period'],
                        consumption_data.loc[weekend_complete, 'Net Consumption (kWh)'],
                        color=color_consumption_dark, edgecolor='black', linewidth=0.5, alpha=0.85)
        # For hourly data, separate daytime and overnight
        elif has_overnight:
            # Daytime complete periods
            daytime_complete = complete_mask & ~consumption_data['IsOvernight']
            if daytime_complete.any():
                ax1.bar(consumption_data.loc[daytime_complete, 'Period'],
                        consumption_data.loc[daytime_complete, 'Net Consumption (kWh)'],
                        color=color_consumption, edgecolor='black', linewidth=0.5, alpha=0.7,
                        label='Net Consumption (Complete)')
            
            # Overnight complete periods (darker)
            overnight_complete = complete_mask & consumption_data['IsOvernight']
            if overnight_complete.any():
                ax1.bar(consumption_data.loc[overnight_complete, 'Period'],
                        consumption_data.loc[overnight_complete, 'Net Consumption (kWh)'],
                        color=color_consumption_dark, edgecolor='black', linewidth=0.5, alpha=0.85)
        else:
            # No special shading needed
            ax1.bar(consumption_data.loc[complete_mask, 'Period'],
                    consumption_data.loc[complete_mask, 'Net Consumption (kWh)'],
                    color=color_consumption, edgecolor='black', linewidth=0.5, alpha=0.7,
                    label='Net Consumption (Complete)')
    
    # Plot incomplete periods with hatched bars to indicate partial data
    incomplete_mask = ~consumption_data['IsComplete']
    if incomplete_mask.any():
        ax1.bar(consumption_data.loc[incomplete_mask, 'Period'],
                consumption_data.loc[incomplete_mask, 'Net Consumption (kWh)'],
                color=color_consumption, edgecolor='grey', linewidth=2, alpha=0.7,
                hatch='//', label='Net Consumption (Partial)')
else:
    # No completeness info, plot all as solid
    ax1.bar(consumption_data['Period'], consumption_data['Net Consumption (kWh)'],
            color=color_consumption, edgecolor='black', linewidth=0.5, alpha=0.7,
            label='Net Consumption')
ax1.set_xlabel(x_label, fontsize=12, fontweight='bold')
ax1.set_ylabel('Net Consumption (kWh)', fontsize=12, fontweight='bold', color=color_consumption)
ax1.tick_params(axis='y', labelcolor=color_consumption)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Set y-axis limits to add padding at top for legend
max_consumption = consumption_data['Net Consumption (kWh)'].max()
ax1.set_ylim(0, max_consumption * 1.15)  # Add 15% padding at top

# Set x-axis ticks based on interval type
if interval_type == 'hourly':
    ax1.set_xticks(range(0, 24))
elif interval_type == 'weekly':
    # For weekly data, show week start dates
    num_weeks = len(consumption_data)
    tick_interval = 1 if num_weeks <= 12 else 2  # Show every week or every other week
    
    tick_positions = consumption_data['Period'][::tick_interval]
    tick_labels = [d.strftime('%Y-%m-%d') for d in consumption_data['Date'][::tick_interval]]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
else:  # daily
    # For daily data, show date labels
    # Show every Nth day to avoid overcrowding
    num_days = len(consumption_data)
    if num_days <= 31:
        tick_interval = 1
    elif num_days <= 90:
        tick_interval = 7  # Weekly
    else:
        tick_interval = 14  # Bi-weekly
    
    tick_positions = consumption_data['Period'][::tick_interval]
    tick_labels = [d.strftime('%Y-%m-%d') for d in consumption_data['Date'][::tick_interval]]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha='right')

# Add value labels on top of each bar
for i, row in consumption_data.iterrows():
    ax1.text(row['Period'], row['Net Consumption (kWh)'],
             f"{row['Net Consumption (kWh)']:.1f}",
             ha='center', va='bottom', fontsize=8)

# Plot temperature line on secondary y-axis if available
if temp_df is not None:
    ax2 = ax1.twinx()
    color_temp = 'orangered'
    ax2.plot(temp_df['Period'], temp_df['Temperature'],
             color=color_temp, linewidth=2.5, marker='o', markersize=5,
             label='Temperature (°C)', zorder=5)
    ax2.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold', color=color_temp)
    ax2.tick_params(axis='y', labelcolor=color_temp)
    
    # Set y-axis limits for temperature to add padding at top
    min_temp = temp_df['Temperature'].min()
    max_temp = temp_df['Temperature'].max()
    temp_range = max_temp - min_temp
    ax2.set_ylim(min_temp - temp_range * 0.05, max_temp + temp_range * 0.15)  # Add 15% padding at top
    
    # Add temperature value labels
    for i, row in temp_df.iterrows():
        ax2.text(row['Period'], row['Temperature'],
                 f"{row['Temperature']:.1f}°C",
                 ha='center', va='bottom', fontsize=7, color=color_temp)
    
    # Combine legends with smaller font
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)

plt.title(f'{title_period} Electricity Consumption and Temperature\n{address}, {city} - {date_range}',
          fontsize=14, fontweight='bold')

plt.tight_layout()

# Create output directory if it doesn't exist
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# Generate output filename based on input filename
input_basename = os.path.basename(csv_file)
output_basename = os.path.splitext(input_basename)[0] + '.png'
output_file = os.path.join(output_dir, output_basename)

# Save the graph
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nGraph saved as: {output_file}")
print("Graph generation complete!")

# Generate text output if requested
if text_output:
    text_output_file = os.path.join(output_dir, os.path.splitext(input_basename)[0] + '.txt')
    with open(text_output_file, 'w') as f:
        # Write header
        f.write("Date/Time\tNet Consumption (kWh)\tTemperature (°C)\n")
        
        # Iterate through consumption data
        for idx, row in consumption_data.iterrows():
            # Skip partial periods
            if 'IsComplete' in consumption_data.columns and not row['IsComplete']:
                continue
            
            # Format date/time based on interval type
            if interval_type == 'hourly':
                # For hourly, show hour (0-23)
                date_time = f"{int(row['Period']):02d}:00"
            elif 'Date' in consumption_data.columns:
                # For daily/weekly, show date
                date_time = row['Date'].strftime('%Y-%m-%d')
            else:
                date_time = str(row['Period'])
            
            # Get consumption value
            consumption = row['Net Consumption (kWh)']
            
            # Get temperature value if available
            if temp_df is not None:
                temp_row = temp_df[temp_df['Period'] == row['Period']]
                if not temp_row.empty:
                    temperature = f"{temp_row['Temperature'].iloc[0]:.1f}"
                else:
                    temperature = 'N/A'
            else:
                temperature = 'N/A'
            
            # Write line
            f.write(f"{date_time}\t{consumption:.2f}\t{temperature}\n")
    
    print(f"Text output saved as: {text_output_file}")

# Display the graph if requested
if display_graph:
    print(f"Opening graph for display...")
    import subprocess
    import platform
    
    system = platform.system()
    try:
        if system == 'Darwin':  # macOS
            subprocess.run(['open', output_file], check=True)
        elif system == 'Windows':
            os.startfile(output_file)
        elif system == 'Linux':
            subprocess.run(['xdg-open', output_file], check=True)
        else:
            print(f"Automatic display not supported on {system}. Please open {output_file} manually.")
    except Exception as e:
        print(f"Could not automatically open the graph: {e}")
        print(f"Please open {output_file} manually.")

# Made with Bob

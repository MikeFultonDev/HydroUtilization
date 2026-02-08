#!/usr/bin/env python3
"""
Generate a bar graph showing electricity utilization by hour of the day with temperature overlay.
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
BC Hydro Electricity Utilization Analyzer
==========================================

USAGE:
    python3 generate_hourly_graph.py [OPTIONS] [CSV_FILE]

OPTIONS:
    -help, --help, -?    Display this help message and exit
    --display            Display the graph after creation (default)
    --nodisplay          Do not display the graph after creation

ARGUMENTS:
    CSV_FILE             Path to a specific BC Hydro consumption CSV file
                        (optional if only one matching file exists in input/)

DESCRIPTION:
    Generates a bar graph showing hourly electricity consumption with
    temperature overlay. If no CSV file is specified, the script will
    automatically search for files matching 'bchydro.com-consumption-*.csv'
    in the input/ directory. Output is saved to the output/ directory.

EXAMPLES:
    # Auto-detect CSV file (if only one exists in input/)
    python3 generate_hourly_graph.py

    # Process a specific file
    python3 generate_hourly_graph.py input/bchydro.com-consumption-XXXXXXXX0385-2026-02-07-154641.csv

    # Process without displaying the graph
    python3 generate_hourly_graph.py --nodisplay

    # Display help
    python3 generate_hourly_graph.py --help

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

# Parse command-line arguments
csv_file = None
display_graph = True  # Default is to display

for arg in sys.argv[1:]:
    # Check for help flags
    if arg in ['-help', '--help', '-?']:
        print_help()
    elif arg == '--nodisplay':
        display_graph = False
    elif arg == '--display':
        display_graph = True
    elif not arg.startswith('--') and not arg.startswith('-'):
        csv_file = arg

# Find and validate the CSV file
csv_file = find_csv_file(csv_file)
print(f"Processing file: {csv_file}")

# Read the CSV file
df = pd.read_csv(csv_file)

# Extract hour from the 'Interval Start Date/Time' column
df['Hour'] = pd.to_datetime(df['Interval Start Date/Time']).dt.hour

# Convert 'Net Consumption (kWh)' to numeric
df['Net Consumption (kWh)'] = pd.to_numeric(df['Net Consumption (kWh)'])

# Group by hour and sum the net consumption
hourly_consumption = df.groupby('Hour')['Net Consumption (kWh)'].sum().reset_index()

# Get location and date information
city = df['City'].iloc[0]
address = df['Service Address'].iloc[0]
date = pd.to_datetime(df['Interval Start Date/Time'].iloc[0]).date()

# Fetch weather data from Open-Meteo API (free, no API key required)
# Coordinates for Brackendale, BC (approximate)
latitude = 49.7833
longitude = -123.1333

try:
    weather_url = f"https://archive-api.open-meteo.com/v1/archive"
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
        temp_df = pd.DataFrame({'Hour': hours, 'Temperature': temperatures})
    else:
        print("Warning: Could not fetch weather data, proceeding without temperature overlay")
        temp_df = None
except Exception as e:
    print(f"Warning: Error fetching weather data: {e}")
    temp_df = None

# Create figure with dual y-axes
fig, ax1 = plt.subplots(figsize=(14, 6))

# Plot consumption bars on primary y-axis
color_consumption = 'steelblue'
ax1.bar(hourly_consumption['Hour'], hourly_consumption['Net Consumption (kWh)'],
        color=color_consumption, edgecolor='black', linewidth=0.5, alpha=0.7, label='Net Consumption')
ax1.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
ax1.set_ylabel('Net Consumption (kWh)', fontsize=12, fontweight='bold', color=color_consumption)
ax1.tick_params(axis='y', labelcolor=color_consumption)
ax1.set_xticks(range(0, 24))
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels on top of each bar
for i, row in hourly_consumption.iterrows():
    ax1.text(row['Hour'], row['Net Consumption (kWh)'],
             f"{row['Net Consumption (kWh)']:.2f}",
             ha='center', va='bottom', fontsize=8)

# Plot temperature line on secondary y-axis if available
if temp_df is not None:
    ax2 = ax1.twinx()
    color_temp = 'orangered'
    ax2.plot(temp_df['Hour'], temp_df['Temperature'],
             color=color_temp, linewidth=2.5, marker='o', markersize=5,
             label='Temperature (°C)', zorder=5)
    ax2.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold', color=color_temp)
    ax2.tick_params(axis='y', labelcolor=color_temp)
    
    # Add temperature value labels
    for i, row in temp_df.iterrows():
        ax2.text(row['Hour'], row['Temperature'],
                 f"{row['Temperature']:.1f}°C",
                 ha='center', va='bottom', fontsize=7, color=color_temp)
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title(f'Electricity Utilization and Temperature by Hour\n{address}, {city} - {date}',
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

#!/usr/bin/env python3
"""
Analyze the correlation between temperature and electricity consumption.
Usage: python3 analyze_temp_correlation.py <csv_file>
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import sys
import os
import subprocess
import tempfile

# Check command line arguments
if len(sys.argv) < 2:
    print("Usage: python3 analyze_temp_correlation.py <csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

# Verify input file exists
if not os.path.exists(csv_file):
    print(f"Error: File '{csv_file}' not found")
    sys.exit(1)

# Generate text file using generate_consumption_graph.py
print(f"Generating text data from {csv_file}...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
    temp_txt_file = temp_file.name

# Run generate_consumption_graph.py with --text option
# Add --daily flag to ensure hourly data is aggregated to daily
result = subprocess.run(
    ['python3', 'generate_consumption_graph.py', csv_file, '--daily', '--text', '--nodisplay'],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Error generating text file: {result.stderr}")
    sys.exit(1)

# Find the generated text file
input_basename = os.path.basename(csv_file)
text_basename = os.path.splitext(input_basename)[0] + '.txt'
text_file = os.path.join('output', text_basename)

if not os.path.exists(text_file):
    print(f"Error: Expected text file '{text_file}' not found")
    sys.exit(1)

print(f"Reading data from {text_file}...")

# Read the text data
df = pd.read_csv(text_file, sep='\t')

# Clean column names
df.columns = df.columns.str.strip()

# Convert to numeric and drop any NaN values
df['Net Consumption (kWh)'] = pd.to_numeric(df['Net Consumption (kWh)'])
df['Temperature (°C)'] = pd.to_numeric(df['Temperature (°C)'])
df = df.dropna()

# Check if we have enough data (at least 90 days / 3 months)
min_data_points = 90
if len(df) < min_data_points:
    print(f"Error: Insufficient data for correlation analysis")
    print(f"Found {len(df)} data points, but need at least {min_data_points} (approximately 3 months)")
    print(f"Please provide a dataset covering at least 3 months of daily consumption data")
    sys.exit(1)

print(f"Analyzing {len(df)} data points\n")

# Calculate correlation
correlation = df[['Temperature (°C)', 'Net Consumption (kWh)']].corr().iloc[0, 1]
print(f"Pearson Correlation Coefficient: {correlation:.4f}")

# Perform linear regression
temp_values = df['Temperature (°C)'].values
consumption_values = df['Net Consumption (kWh)'].values
slope, intercept, r_value, p_value, std_err = stats.linregress(temp_values, consumption_values)
print(f"R-squared: {r_value**2:.4f}")
print(f"P-value: {p_value:.6f}")
print(f"Linear equation: Consumption = {slope:.2f} * Temperature + {intercept:.2f}")

# Find optimal temperature (minimum consumption point)
# Fit a quadratic curve to find the U-shape
z = np.polyfit(df['Temperature (°C)'], df['Net Consumption (kWh)'], 2)
p = np.poly1d(z)

# Find the vertex (minimum point) of the parabola
optimal_temp = -z[1] / (2 * z[0])
min_consumption = p(optimal_temp)

print(f"\nQuadratic fit: Consumption = {z[0]:.4f}*T² + {z[1]:.4f}*T + {z[2]:.2f}")
print(f"Optimal temperature (minimum consumption): {optimal_temp:.1f}°C")
print(f"Minimum consumption at optimal temp: {min_consumption:.1f} kWh")

# Create visualization - single plot with quadratic fit
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Scatter plot
ax.scatter(df['Temperature (°C)'], df['Net Consumption (kWh)'],
           alpha=0.6, s=50, color='steelblue', edgecolors='black', linewidth=0.5,
           label='Daily consumption data')

# Plot quadratic curve
temp_range = np.linspace(df['Temperature (°C)'].min(), df['Temperature (°C)'].max(), 100)
ax.plot(temp_range, p(temp_range), 'r-', linewidth=2, label='Quadratic fit')

ax.set_xlabel('Temperature (°C)', fontsize=12, fontweight='bold')
ax.set_ylabel('Net Consumption (kWh) per day', fontsize=12, fontweight='bold')
ax.set_title('Temperature vs Daily Electricity Consumption\n(Quadratic Relationship)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10)

# Add text box with statistics
textstr = f'Quadratic fit: y = {z[0]:.4f}x² + {z[1]:.4f}x + {z[2]:.1f}\n'
textstr += f'Correlation: {correlation:.4f}\n'
textstr += f'R²: {r_value**2:.4f}\n'
textstr += f'Data range: {df["Temperature (°C)"].min():.1f}°C to {df["Temperature (°C)"].max():.1f}°C'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props)

# Generate output filename
output_basename = os.path.splitext(input_basename)[0] + '_correlation.png'
output_file = os.path.join('output', output_basename)

plt.tight_layout()
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\nAnalysis graph saved as: {output_file}")

# Display the graph
print("Opening graph for display...")
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
except Exception as e:
    print(f"Could not automatically open the graph: {e}")

# Clean up the temporary text file
try:
    os.remove(text_file)
    print(f"Cleaned up temporary file: {text_file}")
except Exception as e:
    print(f"Warning: Could not remove temporary file {text_file}: {e}")

# Additional analysis: categorize by temperature ranges
print("\n" + "="*60)
print("CONSUMPTION BY TEMPERATURE RANGE")
print("="*60)

bins = [-10, 5, 10, 15, 20, 25, 30]
labels = ['<5°C', '5-10°C', '10-15°C', '15-20°C', '20-25°C', '>25°C']
df['Temp Range'] = pd.cut(df['Temperature (°C)'], bins=bins, labels=labels)

temp_analysis = df.groupby('Temp Range', observed=True).agg({
    'Net Consumption (kWh)': ['mean', 'std', 'count']
}).round(2)

print(temp_analysis)

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print(f"The correlation coefficient of {correlation:.4f} indicates a {'strong negative' if correlation < -0.7 else 'moderate negative' if correlation < -0.3 else 'weak negative' if correlation < 0 else 'weak positive' if correlation < 0.3 else 'moderate positive' if correlation < 0.7 else 'strong positive'} linear relationship.")
print(f"\nThe quadratic fit reveals a U-shaped relationship:")
print(f"- Optimal (comfortable) temperature: {optimal_temp:.1f}°C")
print(f"- Below {optimal_temp:.1f}°C: Heating increases consumption")
print(f"- Above {optimal_temp:.1f}°C: Cooling increases consumption")
print(f"- Minimum consumption occurs at the optimal temperature")

# Made with Bob

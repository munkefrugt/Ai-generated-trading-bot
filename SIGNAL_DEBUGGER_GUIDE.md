# Signal Debugger Grid - Usage Guide

## Overview

The **signal debugger grid** is a visual panel below your main Ichimoku chart that shows which boolean signal conditions are active at each candle.

- **Y-axis**: Condition names
- **X-axis**: Candle/date/time (shares same index with main chart)
- **Visual**: Green blocks = True (condition active), Light gray = False (condition inactive)
- **Grid lines**: Horizontal separators between condition rows for clarity

## Key Features

✓ Reusable and modular  
✓ Works with any list of boolean condition columns  
✓ Easy to add more conditions later  
✓ Does not depend on a final buy signal  
✓ Shares x-axis with main chart for synchronized zooming  

## How It Works

### 1. Add Boolean Condition Columns to Your DataFrame

Each condition should be a column with values 0 (False) or 1 (True).

```python
# Example: price_above_cloud condition
df["price_above_cloud"] = (df["Close"] > max(df["senkou_span_a"], df["senkou_span_b"])).astype(int)

# Example: any other boolean condition
df["my_condition"] = (df["Close"] > df["SMA_20"]).astype(int)
```

### 2. Call plot_results() with Signal Columns

```python
from plotting.chart import plot_results

# Show the chart with signal debugger grid
plot_results(
    df,
    trades,
    show_signal_grid=True,
    signal_columns=['price_above_cloud', 'my_condition']  # List your conditions here
)
```

### 3. Parameters

**`plot_results(df, trades, show_signal_grid=True, signal_columns=None)`**

- **df**: DataFrame with datetime index and condition columns
- **trades**: List of trade dicts (from backtest)
- **show_signal_grid**: Boolean, show/hide the debugger grid (default: True)
- **signal_columns**: List of column names to display. If None, defaults to `['price_above_cloud']`

## Example: Adding Multiple Conditions

```python
import pandas as pd
import numpy as np

# Load your data and calculate indicators
df = get_btc_data()
df = add_ichimoku(df)
df = generate_cloud_signals(df)  # Creates price_above_cloud
df, trades, stats = run_backtest(df)

# Create additional test conditions
df["price_above_sma_20"] = (df["Close"] > df["Close"].rolling(20).mean()).astype(int)
df["tenkan_above_kijun"] = (df["tenkan_sen"] > df["kijun_sen"]).astype(int)
df["price_above_sma_50"] = (df["Close"] > df["Close"].rolling(50).mean()).astype(int)

# Plot with all conditions in the debugger grid
plot_results(
    df,
    trades,
    show_signal_grid=True,
    signal_columns=[
        'price_above_cloud',
        'price_above_sma_20',
        'tenkan_above_kijun',
        'price_above_sma_50'
    ]
)
```

## The plot_signal_debug_grid() Function

If you need to use the function directly:

```python
from plotting.chart import plot_signal_debug_grid

# Add debugger to an existing Plotly figure
plot_signal_debug_grid(
    fig,                                           # Plotly figure object
    df,                                            # DataFrame with conditions
    ['price_above_cloud', 'my_condition'],         # List of condition columns
    row_offset=2,                                  # Which subplot row (2 = second row)
    colors_map=None                                # Optional: custom colors
)
```

## Current Implementation

The following columns are now available in your data after `generate_cloud_signals()`:

- **`buy_signal`**: 1 when price crosses above cloud, 0 otherwise
- **`sell_signal`**: 1 when price dips into cloud, 0 otherwise
- **`price_above_cloud`**: 1 when price is above cloud (continuous), 0 otherwise

## Testing

A test script is included: `test_signal_grid.py`

```bash
source venv/bin/activate
python test_signal_grid.py
```

This demonstrates the grid with 3 conditions:
1. `price_above_cloud` (real)
2. `test_condition_1` (random)
3. `test_condition_2` (SMA-based)

## Tips

- Start with 1-3 conditions for clarity
- Add more conditions as your strategy evolves
- Conditions are displayed in the order you provide them
- True values (1) are always shown as green blocks
- The hovertext shows condition name, time, and True/False value
- Zoom in the main chart and the grid zooms with it (shared x-axis)

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import pandas as pd
import numpy as np


def plot_signal_debug_grid(fig, df, condition_columns, row_offset=2, colors_map=None):
    """
    Add a signal debugger grid as a heatmap-style visualization to a Plotly figure.

    Each row represents a boolean condition. True values appear as colored blocks,
    False values are light/empty. Grid shares x-axis with main chart.

    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        Figure object with subplots (from make_subplots)
    df : pandas.DataFrame
        DataFrame with datetime index and boolean condition columns
    condition_columns : list of str
        List of column names to display as conditions (should be boolean: 0/1)
    row_offset : int
        Which subplot row to start plotting (default 2, assuming main chart is row 1)
    colors_map : dict, optional
        Dict mapping condition names to colors. If None, uses default colors.

    Returns:
    --------
    None (modifies fig in place)
    """

    if not condition_columns:
        print("No condition columns provided to plot_signal_debug_grid()")
        return

    # Default color mapping
    if colors_map is None:
        colors_map = {
            "price_above_cloud": "rgba(0, 200, 0, 0.8)",  # green
            "default": "rgba(100, 150, 255, 0.8)",  # blue
        }

    # Get only valid columns that exist in dataframe
    valid_columns = [col for col in condition_columns if col in df.columns]

    if not valid_columns:
        print(
            f"Warning: None of the condition columns {condition_columns} found in dataframe"
        )
        return

    print(f"Plotting signal debug grid with conditions: {valid_columns}")

    # Prepare data for heatmap
    # Rows are conditions, columns are time points
    heatmap_data = []
    heatmap_labels = []

    for col in valid_columns:
        # Convert column values (0/1) to list
        values = df[col].fillna(0).astype(int).tolist()
        heatmap_data.append(values)
        heatmap_labels.append(col)

    # Add heatmap trace to the subplot
    heatmap = go.Heatmap(
        z=heatmap_data,
        x=df.index,
        y=heatmap_labels,
        colorscale=[
            [0, "rgba(240, 240, 240, 1)"],  # False = light gray
            [1, "rgba(0, 200, 0, 0.9)"],  # True = green
        ],
        showscale=False,
        hovertemplate="<b>%{y}</b><br>Time: %{x}<br>Active: %{z}<extra></extra>",
        colorbar=dict(thickness=0, len=0),
    )

    fig.add_trace(heatmap, row=row_offset, col=1)

    # Add horizontal grid lines between conditions
    for i in range(len(valid_columns) + 1):
        fig.add_hline(
            y=i - 0.5,
            line_dash="solid",
            line_color="rgba(150, 150, 150, 0.3)",
            line_width=1,
            row=row_offset,
            col=1,
        )

    # Format the debug grid y-axis
    fig.update_yaxes(
        title_text="Conditions",
        row=row_offset,
        col=1,
        tickmode="linear",
        tick0=0,
        dtick=1,
    )

    print(f"Signal debug grid ready with {len(valid_columns)} conditions")


def plot_results(df, trades, show_signal_grid=True, signal_columns=None):
    """
    Plot backtest results with price, trendline, cloud, trades, and signal debugger.
    Uses Plotly for interactive plotting with subplots.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC, trendline, and Ichimoku columns
    trades : list
        List of trade dicts with entry_time, entry_price, exit_time, exit_price
    show_signal_grid : bool
        Whether to show the signal debugger grid (default True)
    signal_columns : list of str, optional
        Which boolean columns to display in debugger. If None, uses ['price_above_cloud']
    """

    # Default signal columns to display
    if signal_columns is None:
        signal_columns = ["price_above_cloud"]

    # Create figure with 2 rows if showing signal grid, else 1 row
    if show_signal_grid:
        # Row 1: main chart (height ratio 3)
        # Row 2: debugger grid (height ratio 1)
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.75, 0.25],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        )
    else:
        fig = make_subplots(specs=[[{"secondary_y": False}]])

    # Use datetime index for x-axis
    x = df.index

    # Determine which row to plot main chart on
    main_row = 1

    # Plot close price
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["Close"],
            name="Close",
            line=dict(color="black", width=1.5),
            mode="lines",
        ),
        row=main_row,
        col=1,
    )

    # Apply Gaussian smoothing to the close price
    df["Smoothed_Close"] = gaussian_filter1d(df["Close"], sigma=2)

    # Plot Gaussian smoothed line
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["Smoothed_Close"],
            name="Smoothed Close",
            line=dict(color="blue", width=2, dash="dot"),
            mode="lines",
        ),
        row=main_row,
        col=1,
    )

    # Apply coarse Gaussian smoothing to the close price
    df["Coarse_Smoothed_Close"] = gaussian_filter1d(df["Close"], sigma=10)

    # Plot coarse Gaussian smoothed line
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["Coarse_Smoothed_Close"],
            name="Coarse Smoothed Close",
            line=dict(color="orange", width=2, dash="dash"),
            mode="lines",
        ),
        row=main_row,
        col=1,
    )

    # Find local extrema for the fine smoothed line
    smoothed = df["Smoothed_Close"].values
    peaks_smoothed, _ = find_peaks(smoothed)
    troughs_smoothed, _ = find_peaks(-smoothed)

    # Plot local extrema for fine smoothed line
    fig.add_trace(
        go.Scatter(
            x=x[peaks_smoothed],
            y=df["Smoothed_Close"].iloc[peaks_smoothed],
            name="Smoothed Peaks",
            mode="markers",
            marker=dict(
                symbol="circle",
                size=8,
                color="blue",
                line=dict(width=1, color="darkblue"),
            ),
        ),
        row=main_row,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x[troughs_smoothed],
            y=df["Smoothed_Close"].iloc[troughs_smoothed],
            name="Smoothed Troughs",
            mode="markers",
            marker=dict(
                symbol="circle",
                size=8,
                color="lightblue",
                line=dict(width=1, color="darkblue"),
            ),
        ),
        row=main_row,
        col=1,
    )

    # Find local extrema for the coarse smoothed line
    coarse_smoothed = df["Coarse_Smoothed_Close"].values
    peaks_coarse, _ = find_peaks(coarse_smoothed)
    troughs_coarse, _ = find_peaks(-coarse_smoothed)

    # Plot local extrema for coarse smoothed line
    fig.add_trace(
        go.Scatter(
            x=x[peaks_coarse],
            y=df["Coarse_Smoothed_Close"].iloc[peaks_coarse],
            name="Coarse Peaks",
            mode="markers",
            marker=dict(
                symbol="diamond",
                size=10,
                color="orange",
                line=dict(width=1, color="darkorange"),
            ),
        ),
        row=main_row,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x[troughs_coarse],
            y=df["Coarse_Smoothed_Close"].iloc[troughs_coarse],
            name="Coarse Troughs",
            mode="markers",
            marker=dict(
                symbol="diamond",
                size=10,
                color="gold",
                line=dict(width=1, color="darkorange"),
            ),
        ),
        row=main_row,
        col=1,
    )

    # Plot trendline
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["trendline_value"],
            name="Trendline",
            line=dict(color="red", width=2, dash="dash"),
            mode="lines",
        ),
        row=main_row,
        col=1,
    )

    # Plot Ichimoku clouds
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["senkou_span_a"],
            name="Senkou Span A",
            line=dict(color="green", width=1),
            mode="lines",
            opacity=0.7,
        ),
        row=main_row,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["senkou_span_b"],
            name="Senkou Span B",
            line=dict(color="red", width=1),
            mode="lines",
            opacity=0.7,
        ),
        row=main_row,
        col=1,
    )

    # Fill between senkou spans for cloud
    cloud_x = list(x) + list(x)[::-1]
    fig.add_trace(
        go.Scatter(
            x=cloud_x,
            y=df["senkou_span_a"].tolist() + df["senkou_span_b"].tolist()[::-1],
            fill="toself",
            fillcolor="rgba(0, 0, 255, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Cloud",
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        ),
        row=main_row,
        col=1,
    )

    # Plot Chikou Span (lagging span)
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["chikou_span"],
            name="Chikou Span",
            line=dict(color="purple", width=2, dash="dot"),
            mode="lines",
            opacity=0.7,
        ),
        row=main_row,
        col=1,
    )

    # Mark buy and sell signals from dataframe
    buy_signals = df[df["buy_signal"] == 1]
    sell_signals = df[df["sell_signal"] == 1]

    # Plot buy signals
    if len(buy_signals) > 0:
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals["Close"].values,
                name="Buy",
                mode="markers",
                marker=dict(symbol="triangle-up", size=10, color="green"),
            ),
            row=main_row,
            col=1,
        )

    # Plot sell signals
    if len(sell_signals) > 0:
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=sell_signals["Close"].values,
                name="Sell",
                mode="markers",
                marker=dict(symbol="triangle-down", size=10, color="red"),
            ),
            row=main_row,
            col=1,
        )

    # Add signal debugger grid if requested
    if show_signal_grid:
        plot_signal_debug_grid(fig, df, signal_columns, row_offset=2)

    # Update layout for interactivity
    fig.update_layout(
        title="BTC-USD 15m Backtest: Price, Trendline, Ichimoku Cloud, and Signal Debugger",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        autosize=True,
        height=900 if show_signal_grid else 600,
    )

    # Configure main chart x-axis
    fig.update_xaxes(rangeslider=dict(visible=False), type="date", row=main_row, col=1)

    # Configure main chart y-axis
    fig.update_yaxes(fixedrange=False, row=main_row, col=1)

    # Configure debug grid x-axis (if present)
    if show_signal_grid:
        fig.update_xaxes(type="date", row=2, col=1)

    # Show the interactive plot
    fig.show()

    # Save as interactive HTML with responsive sizing
    output_file = "backtest_chart.html"
    config = {
        "responsive": True,
        "scrollZoom": True,
        "displayModeBar": True,
    }
    fig.write_html(output_file, config=config)
    print(f"\nInteractive chart saved to {output_file}")

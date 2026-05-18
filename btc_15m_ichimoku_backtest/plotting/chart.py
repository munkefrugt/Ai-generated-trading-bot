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
    Plot backtest results with price, cloud, trades, equity curve, and cash.
    Uses Plotly for interactive plotting with subplots.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC, indicator, and equity/cash columns
    trades : list
        List of Trade objects with entry/exit times and prices
    show_signal_grid : bool
        Whether to show the signal debugger grid (default True)
    signal_columns : list of str, optional
        Which boolean columns to display in debugger. If None, uses ['price_above_cloud']
    """

    # Default signal columns to display
    if signal_columns is None:
        signal_columns = ["price_above_cloud"]

    # Create figure with appropriate number of rows
    # Row 1: main chart (height ratio 2.5)
    # Row 2: debugger grid (height ratio 0.8) - optional
    # Row 3: equity (height ratio 1)
    # Row 4: cash (height ratio 1)
    num_rows = 4 if show_signal_grid else 3

    if show_signal_grid:
        fig = make_subplots(
            rows=num_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.50, 0.20, 0.15, 0.15],
            specs=[
                [{"secondary_y": False}],
                [{"secondary_y": False}],
                [{"secondary_y": False}],
                [{"secondary_y": False}],
            ],
        )
    else:
        fig = make_subplots(
            rows=num_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.60, 0.20, 0.20],
            specs=[
                [{"secondary_y": False}],
                [{"secondary_y": False}],
                [{"secondary_y": False}],
            ],
        )

    # Use datetime index for x-axis
    x = df.index
    main_row = 1
    grid_row = 2 if show_signal_grid else None
    equity_row = 3 if show_signal_grid else 2
    cash_row = 4 if show_signal_grid else 3

    # Plot close price
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["Close"],
            name="Close",
            line=dict(color="black", width=2.5),
            mode="lines",
        ),
        row=main_row,
        col=1,
    )

    # Plot EMAs
    ema_colors = {
        9: "rgba(255, 0, 255, 0.7)",  # Magenta
        20: "rgba(0, 255, 255, 0.7)",  # Cyan
        50: "rgba(255, 165, 0, 0.7)",  # Orange
        200: "rgba(0, 0, 255, 0.7)",  # Blue
        500: "rgba(128, 0, 128, 0.7)",  # Purple
        1000: "rgba(128, 0, 0, 0.7)",  # Red
        1500: "rgba(0, 128, 0, 0.7)",  # Dark green
        2000: "rgba(128, 128, 0, 0.7)",  # Olive
    }

    for period in [9, 20, 50, 200, 500, 1000, 1500, 2000]:
        if f"ema_{period}" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=df[f"ema_{period}"],
                    name=f"EMA {period}",
                    line=dict(color=ema_colors[period], width=1.5),
                    mode="lines",
                    opacity=0.8,
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
            line=dict(color="green", width=1.5),
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
            line=dict(color="red", width=1.5),
            mode="lines",
            opacity=0.7,
        ),
        row=main_row,
        col=1,
    )

    if "tenkan_sen" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df["tenkan_sen"],
                name="Tenkan Sen",
                line=dict(color="orange", width=1.5, dash="dash"),
                mode="lines",
                opacity=0.8,
            ),
            row=main_row,
            col=1,
        )

    if "kijun_sen" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df["kijun_sen"],
                name="Kijun Sen",
                line=dict(color="blue", width=1.5, dash="dash"),
                mode="lines",
                opacity=0.8,
            ),
            row=main_row,
            col=1,
        )

    # Plot SuperTrend if available
    if "supertrend" in df.columns:
        bullish_supertrend = df["supertrend"].where(df["supertrend_dir"] == 1)
        bearish_supertrend = df["supertrend"].where(df["supertrend_dir"] == -1)

        fig.add_trace(
            go.Scatter(
                x=x,
                y=bullish_supertrend,
                name="SuperTrend Bullish",
                line=dict(color="green", width=2),
                mode="lines",
                opacity=0.85,
            ),
            row=main_row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=bearish_supertrend,
                name="SuperTrend Bearish",
                line=dict(color="red", width=2),
                mode="lines",
                opacity=0.85,
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
            line=dict(color="purple", width=3, dash="dot"),
            mode="lines",
            opacity=0.7,
        ),
        row=main_row,
        col=1,
    )

    # Mark trades from trades list
    # Plot buy markers at entry points
    if trades:
        buy_times = [trade.entry_time for trade in trades]
        buy_prices = [trade.entry_price for trade in trades]

        if buy_times:
            fig.add_trace(
                go.Scatter(
                    x=buy_times,
                    y=buy_prices,
                    name="Buy",
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=10, color="green"),
                ),
                row=main_row,
                col=1,
            )

    # Plot sell markers at exit points
    if trades:
        sell_times = [trade.exit_time for trade in trades]
        sell_prices = [trade.exit_price for trade in trades]

        if sell_times:
            fig.add_trace(
                go.Scatter(
                    x=sell_times,
                    y=sell_prices,
                    name="Sell",
                    mode="markers",
                    marker=dict(symbol="triangle-down", size=10, color="red"),
                ),
                row=main_row,
                col=1,
            )

    # Add signal debugger grid if requested
    if show_signal_grid:
        plot_signal_debug_grid(fig, df, signal_columns, row_offset=grid_row)

    # Plot Equity
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["equity"],
            name="Equity",
            line=dict(color="blue", width=2),
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(0, 0, 255, 0.1)",
        ),
        row=equity_row,
        col=1,
    )

    # Plot Cash
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["cash"],
            name="Cash",
            line=dict(color="green", width=2),
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(0, 255, 0, 0.1)",
        ),
        row=cash_row,
        col=1,
    )

    # Update layout for interactivity
    fig.update_layout(
        title="BTC-USD 15m Backtest: Price, Ichimoku, Equity & Cash",
        xaxis_title="Time",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            bgcolor="rgba(255,255,255,0.9)",
        ),
        autosize=True,
        height=1100 if show_signal_grid else 900,
        margin=dict(r=200 if show_signal_grid else 160),
    )

    # Configure y-axes titles
    fig.update_yaxes(title_text="Price (USD)", row=main_row, col=1)
    fig.update_yaxes(title_text="Equity ($)", row=equity_row, col=1)
    fig.update_yaxes(title_text="Cash ($)", row=cash_row, col=1)

    # Configure main chart x-axis
    fig.update_xaxes(rangeslider=dict(visible=False), type="date", row=main_row, col=1)

    # Configure other x-axes
    fig.update_xaxes(type="date", row=equity_row, col=1)
    fig.update_xaxes(type="date", row=cash_row, col=1)

    if show_signal_grid:
        fig.update_xaxes(type="date", row=grid_row, col=1)

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

"""
Signal debugger grid with real Ichimoku buy-condition layers.
This demonstrates the classic Ichimoku buy logic with visual debugging.
"""

import sys

sys.path.insert(0, "btc_15m_ichimoku_backtest")

from data.fetch import get_btc_data
from indicators.ichimoku import add_ichimoku
from structure.swings import find_swing_highs, find_swing_lows
from structure.trendline import build_descending_trendline
from structure.channel_finder import find_channels
from strategy.signals import generate_signals, generate_cloud_signals
from backtest.engine import run_backtest
from plotting.chart import plot_results
import numpy as np

if __name__ == "__main__":
    print("Loading data and calculating indicators...")
    df = get_btc_data()
    df = add_ichimoku(df)
    df = find_swing_highs(df)
    df = find_swing_lows(df)

    print("Building trendline...")
    df, trendline_info = build_descending_trendline(df)

    print("Generating cloud signals...")
    df = generate_cloud_signals(df)

    print("Running backtest...")
    df, trades, stats = run_backtest(df)

    # Create real Ichimoku buy-condition layers
    print("Creating real Ichimoku buy-condition layers...")

    # Layer 1: Price position
    print("  Layer 1: Price position")
    df["close_above_cloud"] = (
        df["Close"] > df[["senkou_span_a", "senkou_span_b"]].max(axis=1)
    ).astype(int)
    df["close_above_tenkan"] = (df["Close"] > df["tenkan_sen"]).astype(int)
    df["close_above_kijun"] = (df["Close"] > df["kijun_sen"]).astype(int)
    df["close_above_tenkan_and_kijun"] = (
        (df["Close"] > df["tenkan_sen"]) & (df["Close"] > df["kijun_sen"])
    ).astype(int)

    # Layer 2: Tenkan/Kijun relationships
    print("  Layer 2: Tenkan/Kijun relationships")
    df["tenkan_above_kijun"] = (df["tenkan_sen"] > df["kijun_sen"]).astype(int)

    # Bullish TK cross now: tenkan crosses above kijun
    df["tk_cross_now"] = (
        (df["tenkan_sen"] > df["kijun_sen"])
        & (df["tenkan_sen"].shift(1) <= df["kijun_sen"].shift(1))
    ).astype(int)

    # Bullish TK cross recent: within last 5 bars
    df["tk_cross_recent"] = (
        df["tk_cross_now"].rolling(window=5).max().fillna(0).astype(int)
    )

    # Bullish TK cross near: within last 10 bars
    df["tk_cross_near"] = (
        df["tk_cross_now"].rolling(window=10).max().fillna(0).astype(int)
    )

    # Layer 3: Chikou line of sight
    print("  Layer 3: Chikou line of sight")
    df["chikou_above_price_26"] = (df["Close"] > df["Close"].shift(26)).astype(int)
    df["chikou_above_cloud_26"] = (
        df["Close"] > df[["senkou_span_a", "senkou_span_b"]].shift(26).max(axis=1)
    ).astype(int)
    df["chikou_above_tenkan_26"] = (df["Close"] > df["tenkan_sen"].shift(26)).astype(
        int
    )
    df["chikou_above_kijun_26"] = (df["Close"] > df["kijun_sen"].shift(26)).astype(int)
    df["chikou_line_clear"] = (
        (df["chikou_above_price_26"] == 1)
        & (df["chikou_above_cloud_26"] == 1)
        & (df["chikou_above_tenkan_26"] == 1)
        & (df["chikou_above_kijun_26"] == 1)
    ).astype(int)

    # Layer 4: Future cloud (using current cloud as proxy for future cloud)
    print("  Layer 4: Future cloud")
    df["current_cloud_bullish"] = (df["senkou_span_a"] > df["senkou_span_b"]).astype(
        int
    )
    df["senkou_a_rising"] = (df["senkou_span_a"] > df["senkou_span_a"].shift(1)).astype(
        int
    )
    df["senkou_b_rising"] = (df["senkou_span_b"] > df["senkou_span_b"].shift(1)).astype(
        int
    )

    # Layer 5: Entry quality filter
    print("  Layer 5: Entry quality filter")
    # Price not too far above Kijun (within 2% of Kijun)
    df["price_not_overextended"] = (
        (df["Close"] - df["kijun_sen"]) / df["kijun_sen"] < 0.02
    ).astype(int)

    # Layer 6: Scoring (removed from grid display)
    print("  Layer 6: Scoring")
    # Count how many bullish conditions are true
    bullish_columns = [
        "close_above_cloud",
        "close_above_tenkan",
        "close_above_kijun",
        "close_above_tenkan_and_kijun",
        "tenkan_above_kijun",
        "tk_cross_recent",
        "chikou_line_clear",
        "current_cloud_bullish",
        "price_not_overextended",
    ]
    df["ichimoku_bullish_score"] = df[bullish_columns].sum(axis=1)

    # Layer 7: Final buy signal
    print("  Layer 7: Final buy signal")
    # Simple threshold: at least 5 out of 8 conditions true
    df["classic_ichimoku_buy_signal"] = (df["ichimoku_bullish_score"] >= 5).astype(int)

    print(f"\nDataFrame shape: {df.shape}")
    print(
        f"Columns added: {[col for col in df.columns if 'ichimoku' in col.lower() or col in bullish_columns]}"
    )

    # Check condition counts
    print(f"\nCondition counts:")
    for col in bullish_columns + ["classic_ichimoku_buy_signal"]:
        if col in df.columns:
            count = df[col].sum()
            print(f"  {col}: {count} True values")

    # Plot with signal debugger grid showing all conditions
    print("\nPlotting chart with signal debugger grid...")
    condition_list = [
        # Layer 1: Price position
        "close_above_cloud",
        "close_above_tenkan",
        "close_above_kijun",
        "close_above_tenkan_and_kijun",
        # Layer 2: Tenkan/Kijun relationships
        "tenkan_above_kijun",
        "tk_cross_recent",
        # Layer 3: Chikou line of sight
        "chikou_line_clear",
        # Layer 4: Current cloud (proxy for future cloud)
        "current_cloud_bullish",
        # Layer 5: Entry quality filter
        "price_not_overextended",
        # Layer 7: Final buy signal
        "classic_ichimoku_buy_signal",
    ]

    plot_results(df, trades, show_signal_grid=True, signal_columns=condition_list)

    print("\n✓ Real Ichimoku buy-condition debugger complete!")
    print("  Chart saved to backtest_chart.html")

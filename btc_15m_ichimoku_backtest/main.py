from data.fetch import get_btc_data
from indicators.ichimoku import add_ichimoku
from structure.swings import find_swing_highs, find_swing_lows
from structure.trendline import build_descending_trendline
from structure.channel_finder import find_channels
from strategy.signals import generate_signals, generate_cloud_signals
from backtest.engine import run_backtest
from plotting.chart import plot_results

if __name__ == "__main__":
    df = get_btc_data()
    df = add_ichimoku(df)
    df = find_swing_highs(df)
    df = find_swing_lows(df)

    # Find hierarchical channels
    print("\n=== Channel Analysis ===")
    channel_analysis = find_channels(df)

    if channel_analysis["macro_channel"]:
        macro = channel_analysis["macro_channel"]
        print(f"\nMacro Channel:")
        print(f"  Type: {macro['type']}")
        print(f"  Score: {macro['score']:.2f}")
        print(f"  Coverage: {macro['coverage']:.2%}")
        print(f"  Upper touches: {macro['upper_touches']}")
        print(f"  Lower touches: {macro['lower_touches']}")
    else:
        print("\nNo valid macro channel found")

    if channel_analysis["inner_channels"]:
        print(f"\nInner Channels: {len(channel_analysis['inner_channels'])}")
        for i, inner in enumerate(channel_analysis["inner_channels"]):
            print(
                f"  {i+1}. {inner['type']} - touches: {inner['touches']}, score: {inner['score']:.2f}"
            )

    if channel_analysis["local_channels"]:
        print(f"\nLocal Channels: {len(channel_analysis['local_channels'])}")
        for i, local in enumerate(channel_analysis["local_channels"]):
            print(
                f"  {i+1}. {local['type']} - coverage: {local['coverage']:.2%}, score: {local['score']:.2f}"
            )

    if channel_analysis["touch_zones"]:
        print(f"\nTouch Zones: {len(channel_analysis['touch_zones'])}")
        for i, zone in enumerate(channel_analysis["touch_zones"][:5]):
            print(
                f"  {i+1}. {zone['type']} @ ${zone['avg_price']:.2f} - touches: {zone['touch_count']}"
            )

    breakout = channel_analysis["breakout_context"]
    print(f"\nBreakout Context:")
    print(f"  Bullish: {breakout.get('potential_bullish_breakout_context', False)}")
    print(f"  Bearish: {breakout.get('potential_bearish_breakout_context', False)}")
    print(f"  Position in macro: {breakout.get('current_position_in_macro', 0):.2%}")

    df, trendline_info = build_descending_trendline(df)
    df = generate_cloud_signals(df)
    df, trades, stats = run_backtest(df)

    print("\nTrendline Info:")
    print(f"Valid: {trendline_info['valid']}")
    print(f"Slope: {trendline_info['slope']}")
    print(f"Intercept: {trendline_info['intercept']}")
    print(f"Touch Count: {trendline_info['touch_count']}")
    print(f"Anchor Points: {len(trendline_info['anchor_points'])}")

    print("\nBacktest Stats:")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Total Return: {stats['total_return_pct']:.2f}%")
    print(f"Max Drawdown: {stats['max_drawdown_pct']:.2f}%")

    print("\nTrades:")
    for i, trade in enumerate(trades, 1):
        print(
            f"  Trade {i}: Entry {trade['entry_time']} @ {trade['entry_price']:.2f} -> "
            f"Exit {trade['exit_time']} @ {trade['exit_price']:.2f} "
            f"({trade['return_pct']:+.2f}%)"
        )

    plot_results(df, trades)

from data.fetch import get_btc_data
from indicators.ichimoku import add_ichimoku
from indicators.ema import add_ema
from strategy.signals import (
    generate_signals,
    generate_cloud_signals,
    add_ema_conditions,
)
from backtest.engine import run_backtest
from plotting.chart import plot_results

if __name__ == "__main__":
    df = get_btc_data()
    df = add_ichimoku(df)
    df = add_ema(df, periods=[9, 20, 50, 200, 500])
    df = add_ema_conditions(df, periods=[9, 20, 50, 200, 500])

    df = generate_cloud_signals(df)
    df, trades, stats = run_backtest(df)

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

    plot_results(df, trades, signal_columns=["price_above_cloud", "all_emas_bullish"])

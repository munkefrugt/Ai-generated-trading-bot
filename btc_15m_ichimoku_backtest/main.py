from data.fetch import get_btc_data
from indicators.ichimoku import add_ichimoku
from indicators.ema import add_ema
from indicators.supertrend import add_supertrend
from strategy.signals import add_ema_conditions
from backtest.engine import run_backtest
from plotting.chart import plot_results

if __name__ == "__main__":
    df = get_btc_data()
    # df.to_csv("btc_15m_data_60_days_down_and_up_marts_17_may_17-.csv")
    df = add_ichimoku(df)
    df = add_ema(df, periods=[9, 20, 50, 200, 500, 1000, 1500, 2000])
    df = add_supertrend(df, period=10, multiplier=3.0)
    df = add_ema_conditions(df, periods=[9, 20, 50, 200, 500, 1000, 1500, 2000])

    df, trades, stats = run_backtest(df)
    # print(df[["Close", "senkou_span_a", "senkou_span_b"]].tail(30))
    print("\nBacktest Stats:")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Total Return: {stats['total_return_pct']:.2f}%")
    print(f"Max Drawdown: {stats['max_drawdown_pct']:.2f}%")
    print(
        f"Total time in market: {stats['total_time_in_market_days']} days ({stats['time_in_market_pct']:.1f}%)"
    )
    print(f"Average percent gain per trade-day: {stats['avg_pct_per_trade_day']:.2f}%")
    print(f"Average winning trade: {stats['avg_winning_trade_pct']:.2f}%")
    print(f"Average losing trade: {stats['avg_losing_trade_pct']:.2f}%")
    print(f"Median trade return: {stats['median_trade_pct']:.2f}%")
    print(f"Largest winner: {stats['largest_winner_pct']:.2f}%")
    print(f"Largest loser: {stats['largest_loser_pct']:.2f}%")
    print(f"Profit factor: {stats['profit_factor']:.2f}")

    print("\nTrade return distribution:")
    for bucket, count in stats["trade_return_buckets"].items():
        print(f"{bucket}: {count}")

    plot_results(df, trades, signal_columns=["price_above_cloud", "all_emas_bullish"])

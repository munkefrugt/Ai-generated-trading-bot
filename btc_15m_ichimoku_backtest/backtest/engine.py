import pandas as pd
from strategy.trade import Trade
from strategy.buy import should_buy
from strategy.sell import should_sell

TRADE_RETURN_BUCKET_EDGES = [
    -float("inf"),
    -5,
    -2,
    -1,
    -0.5,
    0,
    0.5,
    1,
    2,
    5,
    float("inf"),
]
TRADE_RETURN_BUCKET_LABELS = [
    "<-5%",
    "-5% to -2%",
    "-2% to -1%",
    "-1% to -0.5%",
    "-0.5% to 0%",
    "0% to 0.5%",
    "0.5% to 1%",
    "1% to 2%",
    "2% to 5%",
    ">5%",
]


def run_backtest(df, initial_cash=10000.0):
    """
    Run a long-only backtest by evaluating buy/sell conditions at each bar.

    Entry: when buy condition becomes true
    Exit: when sell condition becomes true

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC and indicator columns
    initial_cash : float
        Starting capital (default 10000)

    Returns:
    --------
    tuple (df, trades, stats)
        df: DataFrame with equity, cash, and position_value columns added
        trades: list of completed Trade objects
        stats: dict with performance metrics
    """
    df = df.copy()
    df["cash"] = initial_cash
    df["position_value"] = 0.0
    df["equity"] = initial_cash

    cash = initial_cash
    position = False  # Whether we're in a trade
    position_size = 0  # Number of shares/coins held
    entry_price = None  # Price we entered at
    entry_time = None  # Time we entered

    trades = []
    equity_values = [initial_cash]

    # Loop through bars to evaluate buy/sell conditions
    for i in range(len(df)):
        # Check for entry condition (act on this bar)
        if not position and should_buy(df, i):
            row = df.iloc[i]
            # Enter at this bar's close
            entry_price = row["Close"]
            entry_time = df.index[i]
            position_size = cash / entry_price
            cash = 0
            position = True
            # print(
            #     "DEBUG TRADE ENTRY:",
            #     entry_time,
            #     f"O={row['Open']}",
            #     f"H={row['High']}",
            #     f"L={row['Low']}",
            #     f"C={row['Close']}",
            #     f"entry_price={entry_price:.8f}",
            # )

        # Check for exit condition (act on this bar)
        if position and should_sell(df, i):
            row = df.iloc[i]
            # Exit at this bar's close
            exit_price = row["Close"]
            exit_time = df.index[i]

            # Create trade object
            trade = Trade(
                entry_time=entry_time,
                entry_price=entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
            )
            trades.append(trade)
            # print(
            #     "DEBUG TRADE EXIT:",
            #     exit_time,
            #     f"O={row['Open']}",
            #     f"H={row['High']}",
            #     f"L={row['Low']}",
            #     f"C={row['Close']}",
            #     f"exit_price={exit_price:.8f}",
            #     f"return_pct={trade.return_pct:.2f}%",
            # )

            cash = position_size * exit_price
            position = False
            position_size = 0
            entry_price = None
            entry_time = None

        # Update equity, cash, and position_value for this bar
        if position:
            # Position value = current position mark-to-market
            position_value = position_size * df["Close"].iloc[i]
            total_equity = cash + position_value
            df.loc[df.index[i], "position_value"] = position_value
            df.loc[df.index[i], "cash"] = cash
            df.loc[df.index[i], "equity"] = total_equity
            equity_values.append(total_equity)
        else:
            # No position: equity = cash
            df.loc[df.index[i], "position_value"] = 0.0
            df.loc[df.index[i], "cash"] = cash
            df.loc[df.index[i], "equity"] = cash
            equity_values.append(cash)

    # If still in position at end, close it at last valid close
    if position:
        # Find last non-NaN close price
        exit_price = None
        exit_idx = None
        for idx in range(len(df) - 1, -1, -1):
            if not pd.isna(df["Close"].iloc[idx]):
                exit_price = df["Close"].iloc[idx]
                exit_idx = idx
                break

        if exit_price is not None and exit_idx is not None:
            row = df.iloc[exit_idx]
            exit_time = df.index[exit_idx]

            trade = Trade(
                entry_time=entry_time,
                entry_price=entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
            )
            trades.append(trade)
            # print(
            #     "DEBUG TRADE EXIT (forced close):",
            #     exit_time,
            #     f"O={row['Open']}",
            #     f"H={row['High']}",
            #     f"L={row['Low']}",
            #     f"C={row['Close']}",
            #     f"exit_price={exit_price:.8f}",
            #     f"return_pct={trade.return_pct:.2f}%",
            # )

            cash = position_size * exit_price

    # Calculate total days in dataset
    last_real_idx = df["Close"].last_valid_index()
    total_dataset_duration_days = (last_real_idx - df.index[0]).total_seconds() / (
        24 * 3600
    )

    # Calculate stats
    final_equity = cash
    total_return_pct = ((final_equity - initial_cash) / initial_cash) * 100

    num_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.return_pct > 0)
    win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0

    # Calculate average percent gain per trade-day
    sum_return_pct = sum(t.return_pct for t in trades)
    sum_duration_days = sum(t.duration_days for t in trades)
    avg_pct_per_trade_day = (
        sum_return_pct / sum_duration_days if sum_duration_days > 0 else 0
    )

    # Calculate time in market
    time_in_market_pct = (
        (sum_duration_days / total_dataset_duration_days) * 100
        if total_dataset_duration_days > 0
        else 0
    )

    # Calculate max drawdown
    peak_equity = initial_cash
    max_drawdown = 0
    for eq in equity_values:
        if eq > peak_equity:
            peak_equity = eq
        drawdown = ((peak_equity - eq) / peak_equity) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Build trade return summary
    returns = pd.Series([t.return_pct for t in trades], dtype="float64")
    avg_winning_trade_pct = (
        returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0.0
    )
    avg_losing_trade_pct = (
        returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0.0
    )
    median_trade_pct = returns.median() if len(returns) > 0 else 0.0
    largest_winner_pct = returns.max() if len(returns) > 0 else 0.0
    largest_loser_pct = returns.min() if len(returns) > 0 else 0.0
    gross_profit = returns[returns > 0].sum()
    gross_loss = -returns[returns < 0].sum()
    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf") if gross_profit > 0 else 0.0
    )

    bucket_bins = pd.cut(
        returns,
        bins=TRADE_RETURN_BUCKET_EDGES,
        labels=TRADE_RETURN_BUCKET_LABELS,
        right=False,
    )
    bucket_counts = bucket_bins.value_counts().reindex(
        TRADE_RETURN_BUCKET_LABELS, fill_value=0
    )

    stats = {
        "total_trades": num_trades,
        "win_rate": win_rate,
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown,
        "total_time_in_market_days": sum_duration_days,
        "time_in_market_pct": time_in_market_pct,
        "avg_pct_per_trade_day": avg_pct_per_trade_day,
        "avg_winning_trade_pct": avg_winning_trade_pct,
        "avg_losing_trade_pct": avg_losing_trade_pct,
        "median_trade_pct": median_trade_pct,
        "largest_winner_pct": largest_winner_pct,
        "largest_loser_pct": largest_loser_pct,
        "profit_factor": profit_factor,
        "trade_return_buckets": bucket_counts.to_dict(),
    }

    return df, trades, stats

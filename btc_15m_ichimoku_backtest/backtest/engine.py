import pandas as pd


def run_backtest(df, initial_cash=10000.0):
    """
    Run a simple long-only backtest based on buy and sell signals.

    Entry: on next bar open after buy_signal == 1
    Exit: on next bar open after sell_signal == 1

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with buy_signal and sell_signal columns
    initial_cash : float
        Starting capital (default 10000)

    Returns:
    --------
    tuple (df, trades, stats)
        df: DataFrame with equity column added
        trades: list of completed trades
        stats: dict with performance metrics
    """
    df = df.copy()
    df["equity"] = initial_cash

    cash = initial_cash
    position = False  # Whether we're in a trade
    position_size = 0  # Number of shares/coins held
    entry_idx = None  # Index of entry signal
    entry_price = None  # Price we entered at
    entry_time = None  # Time we entered

    trades = []
    equity_values = [initial_cash]

    # Loop through bars to process signals
    for i in range(len(df)):
        # Check for entry signal (act on next bar open)
        if i > 0 and df["buy_signal"].iloc[i - 1] == 1 and not position:
            # Enter on this bar's open
            entry_price = df["Open"].iloc[i]
            entry_time = df.index[i]
            position_size = cash / entry_price
            cash = 0
            position = True
            entry_idx = i

        # Check for exit signal (act on next bar open)
        if i > 0 and df["sell_signal"].iloc[i - 1] == 1 and position:
            # Exit on this bar's open
            exit_price = df["Open"].iloc[i]
            exit_time = df.index[i]

            # Calculate trade
            exit_value = position_size * exit_price
            trade_return_pct = ((exit_price - entry_price) / entry_price) * 100

            trades.append(
                {
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "return_pct": trade_return_pct,
                }
            )

            cash = exit_value
            position = False
            position_size = 0
            entry_price = None
            entry_time = None

        # Update equity
        if position:
            # Equity = current position value
            current_value = position_size * df["Close"].iloc[i]
            df.loc[df.index[i], "equity"] = current_value
            equity_values.append(current_value)
        else:
            # Equity = cash
            df.loc[df.index[i], "equity"] = cash
            equity_values.append(cash)

    # If still in position at end, close it at last close
    if position:
        exit_price = df["Close"].iloc[-1]
        exit_time = df.index[-1]
        exit_value = position_size * exit_price
        trade_return_pct = ((exit_price - entry_price) / entry_price) * 100

        trades.append(
            {
                "entry_time": entry_time,
                "entry_price": entry_price,
                "exit_time": exit_time,
                "exit_price": exit_price,
                "return_pct": trade_return_pct,
            }
        )

        cash = exit_value

    # Calculate stats
    final_equity = cash
    total_return_pct = ((final_equity - initial_cash) / initial_cash) * 100

    num_trades = len(trades)
    winning_trades = sum(1 for t in trades if t["return_pct"] > 0)
    win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0

    # Calculate max drawdown
    peak_equity = initial_cash
    max_drawdown = 0
    for eq in equity_values:
        if eq > peak_equity:
            peak_equity = eq
        drawdown = ((peak_equity - eq) / peak_equity) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    stats = {
        "total_trades": num_trades,
        "win_rate": win_rate,
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown,
    }

    return df, trades, stats

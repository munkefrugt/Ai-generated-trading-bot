import pandas as pd


def all_emas_bullish(df, i, periods=[9, 20, 50, 200, 500]):
    """
    Check if all EMAs have a positive slope (current > previous) at bar i.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with EMA columns
    i : int
        Positional index
    periods : list
        List of EMA periods to check

    Returns:
    --------
    bool
        True if all EMAs have positive slope, False otherwise
    """
    if i < 1:  # Need previous bar
        return False

    for period in periods:
        col_name = f"ema_{period}"
        if col_name not in df.columns:
            return False

        curr_val = df[col_name].iloc[i]
        prev_val = df[col_name].iloc[i - 1]

        if pd.isna(curr_val) or pd.isna(prev_val):
            return False

        # If any EMA doesn't have positive slope, return False
        if curr_val <= prev_val:
            return False

    return True


def is_ichimoku_bullish(df, i):
    """
    Check if Ichimoku conditions are bullish at bar i.

    Returns True only if:
    - Close is above both senkou_span_a and senkou_span_b
    - tenkan_sen > kijun_sen

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Ichimoku columns
    i : int
        Positional index

    Returns:
    --------
    bool
        True if bullish, False otherwise
    """
    close = df["Close"].iloc[i]
    span_a = df["senkou_span_a"].iloc[i]
    span_b = df["senkou_span_b"].iloc[i]
    tenkan = df["tenkan_sen"].iloc[i]
    kijun = df["kijun_sen"].iloc[i]

    # Check if any required value is NaN
    if (
        pd.isna(close)
        or pd.isna(span_a)
        or pd.isna(span_b)
        or pd.isna(tenkan)
        or pd.isna(kijun)
    ):
        return False

    # Close above both clouds AND tenkan > kijun
    return close > span_a and close > span_b and tenkan > kijun


def generate_signals(df):
    """
    Generate trading signals based on Ichimoku.

    Adds columns:
    - breakout_signal: 1 on entry (Ichimoku bullish)
    - exit_signal: 1 on exit (close below kijun)
    - position_signal: 1 on entry, 0 on exit

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Ichimoku columns

    Returns:
    --------
    pandas.DataFrame
        Updated DataFrame with signal columns
    """
    df = df.copy()

    # Initialize signal columns
    df["breakout_signal"] = 0
    df["exit_signal"] = 0
    df["position_signal"] = 0

    # Iterate through bars starting from bar 1 (need previous bar)
    for i in range(1, len(df)):
        curr_close = df["Close"].iloc[i]
        curr_kijun = df["kijun_sen"].iloc[i]

        # Entry signal: Ichimoku bullish condition
        if is_ichimoku_bullish(df, i):
            df.loc[df.index[i], "breakout_signal"] = 1
            df.loc[df.index[i], "position_signal"] = 1

        # Exit signal: close below kijun
        if not pd.isna(curr_kijun) and curr_close < curr_kijun:
            df.loc[df.index[i], "exit_signal"] = 1
            df.loc[df.index[i], "position_signal"] = 0

    return df


def generate_cloud_signals(df):
    """
    Generate simple buy/sell signals based on price and Ichimoku cloud.

    Buy signal: Price crosses above cloud (above both senkou_span_a and senkou_span_b)
    Sell signal: Price dips into cloud (below the cloud)

    Adds columns:
    - buy_signal: 1 on buy, 0 otherwise
    - sell_signal: 1 on sell, 0 otherwise
    - price_above_cloud: 1 when price is above cloud, 0 otherwise

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Close, senkou_span_a, and senkou_span_b columns

    Returns:
    --------
    pandas.DataFrame
        Updated DataFrame with signal columns
    """
    df = df.copy()

    # Initialize signal columns
    df["buy_signal"] = 0
    df["sell_signal"] = 0
    df["price_above_cloud"] = 0

    # Iterate through bars starting from bar 1 (need previous bar)
    for i in range(1, len(df)):
        curr_close = df["Close"].iloc[i]
        prev_close = df["Close"].iloc[i - 1]
        curr_span_a = df["senkou_span_a"].iloc[i]
        curr_span_b = df["senkou_span_b"].iloc[i]
        prev_span_a = df["senkou_span_a"].iloc[i - 1]
        prev_span_b = df["senkou_span_b"].iloc[i - 1]

        # Skip if any value is NaN
        if (
            pd.isna(curr_close)
            or pd.isna(curr_span_a)
            or pd.isna(curr_span_b)
            or pd.isna(prev_close)
            or pd.isna(prev_span_a)
            or pd.isna(prev_span_b)
        ):
            continue

        # Cloud boundaries
        cloud_top_prev = max(prev_span_a, prev_span_b)
        cloud_bottom_prev = min(prev_span_a, prev_span_b)
        cloud_top_curr = max(curr_span_a, curr_span_b)
        cloud_bottom_curr = min(curr_span_a, curr_span_b)

        # Continuous condition: price above cloud
        if curr_close > cloud_top_curr:
            df.loc[df.index[i], "price_above_cloud"] = 1

        # Buy signal: price crosses above cloud (was at or below, now above)
        if prev_close <= cloud_top_prev and curr_close > cloud_top_curr:
            df.loc[df.index[i], "buy_signal"] = 1

        # Sell signal: price dips into cloud (was above, now in or below)
        if prev_close > cloud_top_prev and curr_close <= cloud_bottom_curr:
            df.loc[df.index[i], "sell_signal"] = 1

    return df


def add_ema_conditions(df, periods=[9, 20, 50, 200, 500]):
    """
    Add EMA slope condition columns to DataFrame.

    Adds columns:
    - all_emas_bullish: 1 when all EMAs have positive slope, 0 otherwise

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with EMA columns

    Returns:
    --------
    pandas.DataFrame
        Updated DataFrame with EMA condition columns
    """
    df = df.copy()

    # Initialize condition column
    df["all_emas_bullish"] = 0

    # Iterate through bars starting from bar 1
    for i in range(1, len(df)):
        if all_emas_bullish(df, i, periods=periods):
            df.loc[df.index[i], "all_emas_bullish"] = 1

    return df

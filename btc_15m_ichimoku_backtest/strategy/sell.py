import pandas as pd


def should_sell(df, i):
    """
    Determine if we should sell at bar i.

    Sell signal: Price dips into cloud (was above, now in or below)

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Close and cloud columns
    i : int
        Current bar index

    Returns:
    --------
    bool
        True if sell conditions are met
    """
    if i < 1:  # Need previous bar
        return False

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
        return False

    # Cloud boundaries
    cloud_top_prev = max(prev_span_a, prev_span_b)
    cloud_top_curr = max(curr_span_a, curr_span_b)

    # Sell signal: crossed from above cloud into/below cloud
    sell_by_cloud = prev_close > cloud_top_prev and curr_close <= cloud_top_curr

    # Sell signal: EMA 9 crosses down under EMA 20
    curr_ema_9 = df["ema_9"].iloc[i]
    curr_ema_20 = df["ema_20"].iloc[i]
    prev_ema_9 = df["ema_9"].iloc[i - 1]
    prev_ema_20 = df["ema_20"].iloc[i - 1]

    if (
        pd.isna(curr_ema_9)
        or pd.isna(curr_ema_20)
        or pd.isna(prev_ema_9)
        or pd.isna(prev_ema_20)
    ):
        return sell_by_cloud

    ema_cross_down = prev_ema_9 > prev_ema_20 and curr_ema_9 <= curr_ema_20

    return sell_by_cloud or ema_cross_down

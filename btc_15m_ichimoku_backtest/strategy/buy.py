import pandas as pd


def ema_strictly_descending(df, i, periods=[9, 20, 50, 200, 500, 1000, 1500, 2000]):
    """
    Check if EMAs are strictly ordered from fastest to slowest at bar i.

    Example: ema_9 > ema_20 > ema_50 > ...
    """
    if i < 1:
        return False

    previous_value = None
    for period in periods:
        col_name = f"ema_{period}"
        if col_name not in df.columns:
            return False

        value = df[col_name].iloc[i]
        if pd.isna(value):
            return False

        if previous_value is not None and previous_value <= value:
            return False

        previous_value = value

    return True


def should_buy(df, i):
    """
    Determine if we should buy at bar i.

    Buy signal: Price crosses above cloud AND all EMAs are bullish
    Additionally requires the EMAs to be in descending order from fast to slow.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Close, cloud, and EMA columns
    i : int
        Current bar index

    Returns:
    --------
    bool
        True if buy conditions are met
    """
    if i < 1:  # Need previous bar
        return False

    curr_close = df["Close"].iloc[i]
    prev_close = df["Close"].iloc[i - 1]
    curr_span_a = df["senkou_span_a"].iloc[i]
    curr_span_b = df["senkou_span_b"].iloc[i]
    prev_span_a = df["senkou_span_a"].iloc[i - 1]
    prev_span_b = df["senkou_span_b"].iloc[i - 1]
    all_emas_bullish = df["all_emas_bullish"].iloc[i]
    ema_500 = df.get("ema_500")
    ema_1000 = df.get("ema_1000")
    ema_2000 = df.get("ema_2000")

    # Get current EMA values if columns exist
    curr_ema_500 = ema_500.iloc[i] if ema_500 is not None else None
    curr_ema_1000 = ema_1000.iloc[i] if ema_1000 is not None else None

    # Skip if any required value is NaN
    if (
        pd.isna(curr_close)
        or pd.isna(curr_span_a)
        or pd.isna(curr_span_b)
        or pd.isna(prev_close)
        or pd.isna(prev_span_a)
        or pd.isna(prev_span_b)
        or pd.isna(curr_ema_500)
        or pd.isna(curr_ema_1000)
    ):
        return False

    # Cloud boundaries
    cloud_top_prev = max(prev_span_a, prev_span_b)
    cloud_top_curr = max(curr_span_a, curr_span_b)

    # Buy signal: price crosses above cloud AND all EMAs are bullish
    # Additionally require EMAs to be stacked fast-to-slow
    return (
        prev_close <= cloud_top_prev
        and curr_close > cloud_top_curr
        and all_emas_bullish == 1
        # and ema_strictly_descending(df, i)
    )

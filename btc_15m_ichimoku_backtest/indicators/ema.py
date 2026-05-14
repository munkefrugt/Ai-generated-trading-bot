def add_ema(df, periods=[9, 20, 50, 200, 500]):
    """
    Add Exponential Moving Average (EMA) columns to DataFrame.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data (requires 'Close' column)
    periods : list
        List of EMA periods to calculate (default: [9, 20, 50, 200, 500])

    Returns:
    --------
    pandas.DataFrame
        DataFrame with new EMA columns added
    """
    df = df.copy()

    for period in periods:
        df[f"ema_{period}"] = df["Close"].ewm(span=period, adjust=False).mean()

    return df

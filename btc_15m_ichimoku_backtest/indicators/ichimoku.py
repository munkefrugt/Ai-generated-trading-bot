def add_ichimoku(df):
    """
    Add Ichimoku cloud columns to DataFrame.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data (requires 'High' and 'Low' columns)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with new Ichimoku columns added
    """
    df = df.copy()

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    df["tenkan_sen"] = (
        df["High"].rolling(window=9).max() + df["Low"].rolling(window=9).min()
    ) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    df["kijun_sen"] = (
        df["High"].rolling(window=26).max() + df["Low"].rolling(window=26).min()
    ) / 2

    # Senkou Span A (Leading Span A): ((Tenkan-sen + Kijun-sen) / 2).shift(26)
    df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(26)

    # Senkou Span B (Leading Span B): ((52-period high + 52-period low) / 2).shift(26)
    df["senkou_span_b"] = (
        (df["High"].rolling(window=52).max() + df["Low"].rolling(window=52).min()) / 2
    ).shift(26)

    # Chikou Span (Lagging Span): close.shift(-26)
    df["chikou_span"] = df["Close"].shift(-26)

    return df

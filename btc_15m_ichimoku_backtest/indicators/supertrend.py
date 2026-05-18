import numpy as np
import pandas as pd


def add_supertrend(df, period=10, multiplier=3.0):
    """
    Add SuperTrend indicator columns to the DataFrame.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data (requires 'High', 'Low', 'Close')
    period : int
        ATR lookback window length (default 10)
    multiplier : float
        ATR multiplier used to set the SuperTrend band distance (default 3.0)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with 'supertrend' and 'supertrend_dir' columns.
    """
    df = df.copy()

    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.rolling(window=period, min_periods=period).mean()
    hl2 = (high + low) / 2.0

    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    final_upper = upper_band.copy()
    final_lower = lower_band.copy()
    supertrend = pd.Series(index=df.index, dtype="float64")
    supertrend_dir = pd.Series(index=df.index, dtype="Int8")

    for i in range(len(df)):
        if i == 0:
            final_upper.iloc[i] = upper_band.iloc[i]
            final_lower.iloc[i] = lower_band.iloc[i]
            supertrend.iloc[i] = np.nan
            supertrend_dir.iloc[i] = 1
            continue

        if (
            upper_band.iloc[i] < final_upper.iloc[i - 1]
            or close.iloc[i - 1] > final_upper.iloc[i - 1]
        ):
            final_upper.iloc[i] = upper_band.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        if (
            lower_band.iloc[i] > final_lower.iloc[i - 1]
            or close.iloc[i - 1] < final_lower.iloc[i - 1]
        ):
            final_lower.iloc[i] = lower_band.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        if close.iloc[i] <= final_upper.iloc[i]:
            supertrend.iloc[i] = final_upper.iloc[i]
            supertrend_dir.iloc[i] = -1
        else:
            supertrend.iloc[i] = final_lower.iloc[i]
            supertrend_dir.iloc[i] = 1

    df["supertrend"] = supertrend
    df["supertrend_dir"] = supertrend_dir
    df["supertrend_period"] = period
    df["supertrend_multiplier"] = multiplier

    return df

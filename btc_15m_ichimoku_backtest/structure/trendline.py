import pandas as pd


def get_recent_swing_high_points(df, max_points=3):
    """
    Extract the most recent confirmed swing high points.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with 'swing_high' column
    max_points : int
        Maximum number of recent swing highs to return (default 3)

    Returns:
    --------
    list of dict
        Each dict contains:
        - index_pos: positional index in the DataFrame
        - datetime: the datetime index value
        - price: the swing high price
    """
    swing_highs = df[df["swing_high"].notna()].copy()

    if len(swing_highs) == 0:
        return []

    # Get the most recent swing highs
    recent = swing_highs.tail(max_points)

    points = []
    for idx, (datetime_idx, row) in enumerate(recent.iterrows()):
        # Find the positional index in the original df
        pos = df.index.get_loc(datetime_idx)
        points.append(
            {"index_pos": pos, "datetime": datetime_idx, "price": row["swing_high"]}
        )

    return points


def build_descending_trendline(df, max_points=3, min_touches=2, tolerance_pct=0.003):
    """
    Build a descending trendline from recent swing highs.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with 'swing_high' column and OHLC data
    max_points : int
        Maximum swing highs to use (default 3)
    min_touches : int
        Minimum touches required for valid trendline (default 2)
    tolerance_pct : float
        Tolerance percentage for counting touches (default 0.003 = 0.3%)

    Returns:
    --------
    tuple (updated_df, trendline_info)
        updated_df: DataFrame with 'trendline_value' column
        trendline_info: dict with keys:
            - valid: bool
            - slope: float
            - intercept: float
            - touch_count: int
            - anchor_points: list of dicts
    """
    df = df.copy()
    df["trendline_value"] = float("nan")

    # Get recent swing high points
    anchor_points = get_recent_swing_high_points(df, max_points)

    trendline_info = {
        "valid": False,
        "slope": None,
        "intercept": None,
        "touch_count": 0,
        "anchor_points": anchor_points,
    }

    # Check if we have enough anchor points
    if len(anchor_points) < 2:
        return df, trendline_info

    # Check if swing highs are descending
    for i in range(1, len(anchor_points)):
        if anchor_points[i]["price"] >= anchor_points[i - 1]["price"]:
            # Not descending
            return df, trendline_info

    # Calculate slope and intercept from first and last anchor point
    first_point = anchor_points[0]
    last_point = anchor_points[-1]

    x1 = first_point["index_pos"]
    y1 = first_point["price"]
    x2 = last_point["index_pos"]
    y2 = last_point["price"]

    # Calculate slope
    if x2 == x1:
        # Vertical line, invalid
        return df, trendline_info

    slope = (y2 - y1) / (x2 - x1)

    # Check if slope is negative (descending)
    if slope >= 0:
        return df, trendline_info

    # Calculate intercept: y = mx + b => b = y - mx
    intercept = y1 - slope * x1

    # Calculate trendline values for all bars
    for i in range(len(df)):
        trendline_value = slope * i + intercept
        df.loc[df.index[i], "trendline_value"] = trendline_value

    # Count touches: high within tolerance_pct of trendline
    touch_count = 0
    high_values = df["High"].values
    trendline_values = df["trendline_value"].values

    for i in range(len(df)):
        trendline_val = trendline_values[i]
        high = high_values[i]

        # Check if high is close to trendline within tolerance
        if not (pd.isna(trendline_val) or pd.isna(high)):
            tolerance = trendline_val * tolerance_pct
            if abs(high - trendline_val) <= tolerance:
                touch_count += 1

    # Update trendline_info
    trendline_info["slope"] = slope
    trendline_info["intercept"] = intercept
    trendline_info["touch_count"] = touch_count

    # Mark as valid if touch_count meets minimum
    if touch_count >= min_touches:
        trendline_info["valid"] = True

    return df, trendline_info

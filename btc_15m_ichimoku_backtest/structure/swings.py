def find_swing_highs(df, lookback=3, lookforward=3):
    """
    Identify confirmed swing highs in the DataFrame.
    
    A swing high is a high that is higher than the highs in the lookback bars 
    before it and the lookforward bars after it.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data (requires 'High' column)
    lookback : int
        Number of bars to look back (default 3)
    lookforward : int
        Number of bars to look forward (default 3)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with 'swing_high' column added (NaN for non-swings)
    """
    df = df.copy()
    df['swing_high'] = float('nan')
    
    high_values = df['High'].values
    
    # Only check bars with enough lookback and lookforward data
    for i in range(lookback, len(df) - lookforward):
        current_high = high_values[i]
        
        # Check if current high is higher than all lookback bars before it
        past_max = high_values[i - lookback:i].max()
        if current_high <= past_max:
            continue
        
        # Check if current high is higher than all lookforward bars after it
        future_max = high_values[i + 1:i + lookforward + 1].max()
        if current_high <= future_max:
            continue
        
        # It's a swing high
        df.loc[df.index[i], 'swing_high'] = current_high
    
    return df


def find_swing_lows(df, lookback=3, lookforward=3):
    """
    Identify confirmed swing lows in the DataFrame.
    
    A swing low is a low that is lower than the lows in the lookback bars 
    before it and the lookforward bars after it.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data (requires 'Low' column)
    lookback : int
        Number of bars to look back (default 3)
    lookforward : int
        Number of bars to look forward (default 3)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with 'swing_low' column added (NaN for non-swings)
    """
    df = df.copy()
    df['swing_low'] = float('nan')
    
    low_values = df['Low'].values
    
    # Only check bars with enough lookback and lookforward data
    for i in range(lookback, len(df) - lookforward):
        current_low = low_values[i]
        
        # Check if current low is lower than all lookback bars before it
        past_min = low_values[i - lookback:i].min()
        if current_low >= past_min:
            continue
        
        # Check if current low is lower than all lookforward bars after it
        future_min = low_values[i + 1:i + lookforward + 1].min()
        if current_low >= future_min:
            continue
        
        # It's a swing low
        df.loc[df.index[i], 'swing_low'] = current_low
    
    return df
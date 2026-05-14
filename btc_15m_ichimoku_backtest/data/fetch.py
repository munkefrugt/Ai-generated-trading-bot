import yfinance as yf
import pandas as pd


def get_btc_data():
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(period="60d", interval="15m")

    # Extend dataframe with 26 empty periods (15m intervals) for future cloud projection
    last_time = df.index[-1]
    future_dates = pd.date_range(
        start=last_time + pd.Timedelta(minutes=15), periods=26, freq="15min"
    )
    future_df = pd.DataFrame(index=future_dates)
    df = pd.concat([df, future_df])

    return df

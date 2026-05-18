import yfinance as yf
import pandas as pd
import os

# test noise: ADA-USD
# "BTC-USD"


def get_btc_data():
    ticker = yf.Ticker("ETH-USD")
    df = ticker.history(period="60d", interval="15m")
    # df.to_csv("data/btc_15m_data_60_days_down_and_up_marts_17_may_17-.csv")

    # Extend dataframe with 26 empty periods (15m intervals) for future cloud projection
    last_time = df.index[-1]
    future_dates = pd.date_range(
        start=last_time + pd.Timedelta(minutes=15), periods=26, freq="15min"
    )
    future_df = pd.DataFrame(index=future_dates)
    df = pd.concat([df, future_df])

    return df

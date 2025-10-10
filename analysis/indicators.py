import pandas as pd

def moving_average(df, column="Close", window=7):
    df[f"MA_{window}"] = df[column].rolling(window=window).mean()
    return df

def volatility(df, column="Close", window=7):
    df[f"Vol_{window}"] = df[column].rolling(window=window).std()
    return df

if __name__ == "__main__":
    import data.fetch_data as fetch
    df = fetch.fetch_crypto("BTC-USD")
    df = moving_average(df)
    df = volatility(df)
    print(df.tail())

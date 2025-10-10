import plotly.graph_objects as go

def plot_candlestick(df, title="Candlestick Chart"):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Price")
    return fig

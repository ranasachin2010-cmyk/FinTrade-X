# pip install streamlit yfinance plotly pandas numpy
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="AI Stock Analyzer", layout="wide")
st.title("📈 AI Market Analysis")

symbol = st.text_input("Stock Symbol (NSE)", "RELIANCE").upper().strip()
period = st.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y"], index=1)

def detect_patterns(df):
    patterns = []
    o, h, l, c = df['Open'].iloc[-1], df['High'].iloc[-1], df['Low'].iloc[-1], df['Close'].iloc[-1]
    body = abs(c - o)
    candle_range = h - l
    if candle_range == 0: return patterns
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    if body <= candle_range * 0.1:
        patterns.append(("Doji", "Indecision / Reversal possible", "🟡"))
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        patterns.append(("Hammer", "Bullish Reversal", "🟢"))
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        patterns.append(("Shooting Star", "Bearish Reversal", "🔴"))
    if len(df) > 1:
        o1, c1 = df['Open'].iloc[-2], df['Close'].iloc[-2]
        if c1 < o1 and c > o and c > o1 and o < c1:
            patterns.append(("Bullish Engulfing", "Strong Bullish", "🟢"))
        if c1 > o1 and c < o and c < o1 and o > c1:
            patterns.append(("Bearish Engulfing", "Strong Bearish", "🔴"))
    return patterns

if st.button("Analyze"):
    with st.spinner("Analyzing..."):
        ticker_sym = symbol + ".NS" if ".NS" not in symbol else symbol
        df = yf.Ticker(ticker_sym).history(period=period, interval="1d").dropna()

        if df.empty:
            st.error("Data nahi mila. Symbol check karo.")
        else:
            current = float(df['Close'].iloc[-1])
            support = float(df['Low'].tail(20).min())
            resistance = float(df['High'].tail(20).max())

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"₹{current:.2f}")
            col2.metric("Support", f"₹{support:.2f}")
            col3.metric("Resistance", f"₹{resistance:.2f}")

            # Candlestick Chart
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Candles"
            )])
            # EMA 20
            df['EMA20'] = df['Close'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='orange', width=1), name='EMA 20'))
            
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            # AI

# pip install streamlit yfinance plotly pandas numpy
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(page_title="AI Stock Analyzer Pro", layout="wide")
st.title("📈 AI Market Analysis Pro")

# --- Sidebar for multi-stock ---
st.sidebar.header("Settings")
symbols_input = st.sidebar.text_input("Stocks (comma se alag karo)", "RELIANCE, HUDCO, TCS")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
period = st.sidebar.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y"], index=1)
main_symbol = st.selectbox("Analysis ke liye stock chuno", symbols)

# --- Helper Functions ---
def calc_rsi(close, n=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(n).mean()
    loss = -delta.where(delta < 0, 0).rolling(n).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def calc_macd(close):
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

def detect_patterns(df):
    patterns = []
    o, h, l, c = df['Open'].iloc[-1], df['High'].iloc[-1], df['Low'].iloc[-1], df['Close'].iloc[-1]
    body = abs(c - o)
    rng = h - l
    if rng == 0: return patterns
    uw = h - max(c,o)
    lw = min(c,o) - l
    if body <= rng * 0.1: patterns.append("Doji")
    if lw > body*2 and uw < body*0.5: patterns.append("Hammer 🟢")
    if uw > body*2 and lw < body*0.5: patterns.append("Shooting Star 🔴")
    return patterns

def ai_signal(df):
    # Score based system
    score = 0
    reasons = []
    rsi = df['RSI'].iloc[-1]
    macd, sig = df['MACD'].iloc[-1], df['Signal'].iloc[-1]
    price = df['Close'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]

    if rsi < 30:
        score += 2; reasons.append("RSI Oversold (<30) - Buy chance")
    elif rsi > 70:
        score -= 2; reasons.append("RSI Overbought (>70) - Sell pressure")
    else:
        reasons.append(f"RSI Neutral ({rsi:.1f})")

    if macd > sig:
        score += 1; reasons.append("MACD Bullish crossover")
    else:
        score -= 1; reasons.append("MACD Bearish")

    if price > ema20:
        score += 1; reasons.append("Price EMA20 ke upar")
    else:
        score -= 1; reasons.append("Price EMA20 ke neeche")

    if score >= 2: return "STRONG BUY 🟢", reasons
    elif score == 1: return "BUY 🟢", reasons
    elif score == -1: return "SELL 🔴", reasons
    elif score <= -2: return "STRONG SELL 🔴", reasons
    else: return "HOLD 🟡", reasons

@st.cache_data(ttl=600)
def get_data(sym, period):
    t = sym + ".NS" if ".NS" not in sym else sym
    df = yf.Ticker(t).history(period=period, interval="1d").dropna()
    return df

# --- 3. Multiple Stocks Compare ---
st.subheader("📊 3. Multiple Stocks Compare")
comp_data = []
for sym in symbols:
    try:
        df_c = get_data(sym, period)
        if not df_c.empty:
            chg = (df_c['Close'].iloc[-1] - df_c['Close'].iloc[0]) / df_c['Close'].iloc[0] * 100
            comp_data.append({"Symbol": sym, "Price": round(float(df_c['Close'].iloc[-1]),2), f"{period} Return %": round(float(chg),2)})
    except: pass

if comp_data:
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

# --- Main Analysis ---
if st.button("Analyze", type="primary"):
    df = get_data(main_symbol, period)
    if df.empty:
        st.error("Data nahi mila")
    else:
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['RSI'] = calc_rsi(df['Close'])
        df['MACD'], df['Signal'] = calc_macd(df['Close'])

        curr = float(df['Close'].iloc[-1])
        sup = float(df['Low'].tail(20).min())
        res = float(df['High'].tail(20).max())

        c1,c2,c3 = st.columns(3)
        c1.metric("Price", f"₹{curr:.2f}")
        c2.metric("Support", f"₹{sup:.2f}")
        c3.metric("Resistance", f"₹{res:.2f}")

        # --- 2. AI Buy/Sell ---
        st.subheader("🤖 2. AI Buy/Sell Signal")
        signal, reasons = ai_signal(df)
        if "BUY" in signal: st.success(f"## {signal}")
        elif "SELL" in signal: st.error(f"## {signal}")
        else: st.warning(f"## {signal}")
        for r in reasons: st.write("- " + r)

        pats = detect_patterns(df)
        if pats: st.info("Patterns: " + ", ".join(pats))

        # --- 1. Chart with RSI + MACD ---
        st.subheader("📉 1. RSI & MACD Chart")
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            vertical_spacing=0.05, row_heights=[0.6,0.2,0.2],
                            subplot_titles=('Price + EMA20', 'RSI', 'MACD'))

        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='orange',width=1), name='EMA20'), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue'), name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='red'), name='Signal'), row=3, col=1)

        fig.update_layout(height=700, xaxis_rangeslider_visible=False, template="plotly_dark",
                          margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

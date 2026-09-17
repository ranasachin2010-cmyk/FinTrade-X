import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from textblob import TextBlob
import requests

# --- Page Config ---
st.set_page_config(page_title="AI Stock Analyzer Pro", layout="wide")
st.title("🤖 AI Stock Analyzer Pro - Indian Market")

# --- Sidebar ---
st.sidebar.header("Settings")
symbols_input = st.sidebar.text_input("NSE Symbols (comma separated)", "RELIANCE,TCS,ATGL,PCJEWELLER")
timeframe = st.sidebar.selectbox("Timeframe", ["1mo","3mo","6mo","1y"], index=1)
st.sidebar.subheader("🔔 Price Alert")
alert_high = st.sidebar.number_input("Alert above", value=650.0)
alert_low = st.sidebar.number_input("Alert below", value=550.0)

# --- Functions ---
def get_fundamentals(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        info = t.info
        return {
            "pe": info.get("trailingPE", "N/A"),
            "mcap": info.get("marketCap", "N/A"),
            "high52": info.get("fiftyTwoWeekHigh", "N/A"),
            "low52": info.get("fiftyTwoWeekLow", "N/A"),
            "div": info.get("dividendYield", "N/A")
        }
    except:
        return {}

def analyze_stock(symbol, tf):
    df = yf.download(symbol + ".NS", period=tf, interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACDs'] = macd['MACDs_12_26_9']
    df['EMA20'] = ta.ema(df['Close'], length=20)
    df['EMA50'] = ta.ema(df['Close'], length=50)

    last = df.iloc[-1]
    rsi = float(last['RSI'])
    macd_bull = float(last['MACD']) > float(last['MACDs'])
    price_above_ema20 = float(last['Close']) > float(last['EMA20'])

    score = 0
    if rsi < 30: score += 2
    elif rsi < 50: score += 1
    elif rsi > 70: score -= 2
    if macd_bull: score += 2
    else: score -= 1
    if price_above_ema20: score += 1
    else: score -= 1

    if score >= 3: signal = "STRONG BUY 🟢"
    elif score >= 1: signal = "BUY 🟢"
    elif score <= -2: signal = "STRONG SELL 🔴"
    elif score < 0: signal = "SELL 🔴"
    else: signal = "HOLD 🟡"

    # Target / Stoploss
    recent_high = float(df['High'].tail(20).max())
    recent_low = float(df['Low'].tail(20).min())
    target = round(recent_high, 2)
    stoploss = round(recent_low, 2)

    # Backtest simple
    df['Signal'] = 0
    df.loc[(df['RSI']<35) & (df['MACD']>df['MACDs']), 'Signal'] = 1
    df.loc[(df['RSI']>70) | (df['MACD']<df['MACDs']), 'Signal'] = -1
    df['Returns'] = df['Close'].pct_change()
    df['Strat'] = df['Signal'].shift(1) * df['Returns']
    ai_ret = (1+df['Strat'].fillna(0)).prod()-1
    bh_ret = (1+df['Returns'].fillna(0)).prod()-1

    return df, rsi, macd_bull, price_above_ema20, signal, target, stoploss, ai_ret*100, bh_ret*100

# --- Screener ---
st.sidebar.subheader("🔍 Screener")
if st.sidebar.button("Scan Top BUY Signals"):
    screen_list = ["RELIANCE","TCS","HDFCBANK","INFY","ITC","SBIN","TATAMOTORS","ATGL","PCJEWELLER","ONGC"]
    results = []
    for s in screen_list:
        try:
            out = analyze_stock(s, timeframe)
            if out:
                _,_,_,_,sig,_,_,_,_ = out
                if "BUY" in sig:
                    results.append((s,sig))
        except: pass
    if results:
        st.sidebar.success("BUY Signals:")
        for s,sig in results:
            st.sidebar.write(f"{s}: {sig}")
    else:
        st.sidebar.info("No STRONG BUY right now")

# --- Main ---
symbols = [x.strip().upper() for x in symbols_input.split(",") if x.strip()]

for sym in symbols:
    st.header(f"📊 {sym}")
    out = analyze_stock(sym, timeframe)
    if not out:
        st.error(f"{sym} ka data nahi mila. Symbol check karo (jaise PCJEWELLER)")
        continue
    df, rsi, macd_bull, above_ema20, signal, target, stoploss, ai_ret, bh_ret = out
    price = float(df['Close'].iloc[-1])

    # Price Alert
    if price >= alert_high:
        st.warning(f"🔔 {sym} {alert_high} ke upar hai! Price: {price:.2f}")
    if price <= alert_low:
        st.warning(f"🔔 {sym} {alert_low} ke neeche hai! Price: {price:.2f}")

    col1,col2,col3 = st.columns(3)
    col1.metric("Price", f"₹{price:.2f}")
    col2.metric("RSI", f"{rsi:.1f}")
    col3.metric("AI Signal", signal)

    if "BUY" in signal:
        st.success(f"🎯 Target: ₹{target} | 🛑 Stop-Loss: ₹{stoploss}")

    # Fundamentals
    fund = get_fundamentals(sym)
    st.subheader("💰 Fundamentals")
    c1,c2,c3,c4 = st.columns(4)
    c1.write(f"P/E: {fund.get('pe')}")
    c2.write(f"52W High: {fund.get('high52')}")
    c3.write(f"52W Low: {fund.get('low52')}")
    c4.write(f"Div Yield: {fund.get('div')}")

    # Backtest
    st.subheader("🧪 Backtesting")
    b1,b2 = st.columns(2)
    b1.metric("AI Strategy Return", f"{ai_ret:.2f}%")
    b2.metric("Buy & Hold Return", f"{bh_ret:.2f}%")
    winner = "AI 🤖" if ai_ret > bh_ret else "Buy&Hold"
    st.write(f"Winner: **{winner}** - " + ("AI ne market ko beat kiya!" if ai_ret>bh_ret else "Market hold karna better raha."))

    # Chart
    st.subheader("RSI & MACD Chart + Support/Resistance")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='orange'), name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='blue'), name="EMA50"))
    # Support Resistance
    res = df['High'].tail(30).max()
    sup = df['Low'].tail(30).min()
    fig.add_hline(y=res, line_dash="dot", line_color="red", annotation_text="Resistance")
    fig.add_hline(y=sup, line_dash="dot", line_color="green", annotation_text="Support")
    st.plotly_chart(fig, use_container_width=True)

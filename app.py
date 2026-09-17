import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="AI Stock Analyzer Pro", layout="wide")
st.title("🤖 AI Stock Analyzer Pro - Indian Market")

st.sidebar.header("Settings")
symbols_input = st.sidebar.text_input("NSE Symbols (comma separated)", "RELIANCE,TCS,ATGL,PCJEWELLER")
timeframe = st.sidebar.selectbox("Timeframe", ["1mo","3mo","6mo","1y"], index=1)

def rsi_calc(series, length=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=length-1, min_periods=length).mean()
    avg_loss = loss.ewm(com=length-1, min_periods=length).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd_calc(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def get_fundamentals(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        info = t.info
        return {
            "pe": info.get("trailingPE", "N/A"),
            "high52": info.get("fiftyTwoWeekHigh", "N/A"),
            "low52": info.get("fiftyTwoWeekLow", "N/A"),
            "div": info.get("dividendYield", "N/A")
        }
    except:
        return {"pe":"N/A","high52":"N/A","low52":"N/A","div":"N/A"}

def get_news(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        raw = t.news[:5]
        out = []
        for n in raw:
            c = n.get('content', {})
            title = c.get('title') or n.get('title') or "No title"
            click = c.get('clickThroughUrl') or {}
            link = click.get('url') if isinstance(click, dict) else None
            link = link or n.get('link') or "#"
            # provider name
            provider = c.get('provider', {}).get('displayName', '') if isinstance(c.get('provider'), dict) else ''
            out.append({"title": title, "link": link, "provider": provider})
        return out
    except:
        return []

def analyze_stock(symbol, tf):
    df = yf.download(symbol + ".NS", period=tf, interval="1d", progress=False)
    if df.empty or len(df) < 30:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['RSI'] = rsi_calc(df['Close'])
    df['MACD'], df['MACDs'] = macd_calc(df['Close'])
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
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
    target = round(float(df['High'].tail(20).max()), 2)
    stoploss = round(float(df['Low'].tail(20).min()), 2)
    df['Signal'] = 0
    df.loc[(df['RSI']<35) & (df['MACD']>df['MACDs']), 'Signal'] = 1
    df.loc[(df['RSI']>70) | (df['MACD']<df['MACDs']), 'Signal'] = -1
    df['Returns'] = df['Close'].pct_change()
    df['Strat'] = df['Signal'].shift(1) * df['Returns']
    ai_ret = (1+df['Strat'].fillna(0)).prod()-1
    bh_ret = (1+df['Returns'].fillna(0)).prod()-1
    return df, rsi, signal, target, stoploss, ai_ret*100, bh_ret*100

st.sidebar.subheader("🔍 Screener")
if st.sidebar.button("Scan Top BUY Signals"):
    screen_list = ["RELIANCE","TCS","HDFCBANK","INFY","ITC","SBIN","TATAMOTORS","ATGL","PCJEWELLER","ONGC"]
    results = []
    for s in screen_list:
        try:
            out = analyze_stock(s, timeframe)
            if out and "BUY" in out[2]:
                results.append((s, out[2]))
        except: pass
    if results:
        st.sidebar.success("BUY Signals:")
        for s,sig in results:
            st.sidebar.write(f"{s}: {sig}")
    else:
        st.sidebar.info("No STRONG BUY right now")

symbols = [x.strip().upper() for x in symbols_input.split(",") if x.strip()]

for sym in symbols:
    st.header(f"📊 {sym}")
    out = analyze_stock(sym, timeframe)
    if not out:
        st.error(f"{sym} ka data nahi mila")
        continue
    df, rsi, signal, target, stoploss, ai_ret, bh_ret = out
    price = float(df['Close'].iloc[-1])
    c1,c2,c3 = st.columns(3)
    c1.metric("Price", f"₹{price:.2f}")
    c2.metric("RSI", f"{rsi:.1f}")
    c3.metric("AI Signal", signal)
    st.success(f"🎯 Target: ₹{target} | 🛑 Stop-Loss: ₹{stoploss}")
    fund = get_fundamentals(sym)
    st.subheader("💰 Fundamentals")
    f1,f2,f3,f4 = st.columns(4)
    f1.write(f"P/E: {fund.get('pe')}")
    f2.write(f"52W High: {fund.get('high52')}")
    f3.write(f"52W Low: {fund.get('low52')}")
    f4.write(f"Div Yield: {fund.get('div')}")
    st.subheader("🧪 Backtesting")
    b1,b2 = st.columns(2)
    b1.metric("AI Strategy Return", f"{ai_ret:.2f}%")
    b2.metric("Buy & Hold Return", f"{bh_ret:.2f}%")
    st.subheader("📰 Latest News")
    news_list = get_news(sym)
    if news_list:
        for n in news_list:
            st.write(f"- [{n['title']}]({n['link']}) {f\"({n['provider']})\" if n['provider'] else ''}")
    else:
        st.write("News nahi mili")
    st.subheader("📈 Candlestick Chart + Support/Resistance")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='orange'), name="EMA20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='blue'), name="EMA50"))
    res = float(df['High'].tail(30).max())
    sup = float(df['Low'].tail(30).min())
    fig.add_hline(y=res, line_dash="dot", line_color="red", annotation_text="Resistance")
    fig.add_hline(y=sup, line_dash="dot", line_color="green", annotation_text="Support")
    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

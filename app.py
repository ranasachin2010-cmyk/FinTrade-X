# requirements.txt
# streamlit
# yfinance
# plotly
# pandas
# numpy
# requests

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
import urllib.parse

st.set_page_config(page_title="AI Stock Analyzer Pro", layout="wide")
st.title("📈 AI Market Analysis Pro")

st.sidebar.header("Settings")
symbols_input = st.sidebar.text_input("Stocks (comma se alag karo)", "RELIANCE, ATGL, TCS, INFY, HDFCBANK")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
period = st.sidebar.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y"], index=1)
main_symbol = st.selectbox("Analysis ke liye stock chuno", symbols)

# --- Price Alert Settings ---
st.sidebar.subheader("🔔 Price Alert")
alert_high = st.sidebar.number_input("Alert jab price iske UPAR jaye", value=0.0)
alert_low = st.sidebar.number_input("Alert jab price iske NEECHE jaye", value=0.0)

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

def ai_signal_row(rsi_v, macd_v, sig_v, price_v, ema20_v):
    score = 0
    if rsi_v < 30: score+=2
    elif rsi_v > 70: score-=2
    if macd_v > sig_v: score+=1
    else: score-=1
    if price_v > ema20_v: score+=1
    else: score-=1
    return score

def get_news_sentiment(sym):
    try:
        clean_sym = sym.replace(".NS","")
        query = urllib.parse.quote(f"{clean_sym} stock NSE India")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=10)
        root = ET.fromstring(r.content)
        titles = []
        for item in root.findall('.//item')[:10]:
            t = item.find('title')
            if t is not None and t.text:
                titles.append(t.text.rsplit(' - ',1)[0])
        pos_words = ['gain','rise','up','bull','profit','growth','surge','upgrade','positive','high','record','buy','strong','jump','rally']
        neg_words = ['fall','down','bear','loss','drop','decline','downgrade','negative','low','sell','weak','fraud','case','crash','plunge']
        pos, neg = 0,0
        for title in titles:
            tl=title.lower()
            if any(w in tl for w in pos_words): pos+=1
            elif any(w in tl for w in neg_words): neg+=1
        return pos, neg, titles
    except:
        return 0,0,[]

@st.cache_data(ttl=600)
def get_data(sym, period):
    t = sym + ".NS" if ".NS" not in sym else sym
    return yf.Ticker(t).history(period=period, interval="1d").dropna()

# --- 5. Top Gainers / Losers Scanner ---
st.subheader("🚀 5. Top Gainers / Losers Scanner")
if st.button("Scan Market"):
    scan_results = []
    with st.spinner("Scanning..."):
        for sym in symbols:
            try:
                df_s = get_data(sym, "5d")
                if len(df_s)>=2:
                    chg = (df_s['Close'].iloc[-1]-df_s['Close'].iloc[-2])/df_s['Close'].iloc[-2]*100
                    scan_results.append({"Symbol":sym, "Price":round(float(df_s['Close'].iloc[-1]),2), "Day Change %":round(float(chg),2)})
            except: pass
    if scan_results:
        sdf = pd.DataFrame(scan_results).sort_values("Day Change %", ascending=False)
        c1,c2 = st.columns(2)
        c1.success("Top Gainers")
        c1.dataframe(sdf.head(3), use_container_width=True)
        c2.error("Top Losers")
        c2.dataframe(sdf.tail(3).sort_values("Day Change %"), use_container_width=True)

st.subheader("📊 3. Multiple Stocks Compare")
comp_data=[]
for sym in symbols:
    try:
        df_c=get_data(sym, period)
        if not df_c.empty:
            chg=(df_c['Close'].iloc[-1]-df_c['Close'].iloc[0])/df_c['Close'].iloc[0]*100
            comp_data.append({"Symbol":sym,"Price":round(float(df_c['Close'].iloc[-1]),2),f"{period} Return %":round(float(chg),2)})
    except: pass
if comp_data: st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

if st.button("Analyze", type="primary"):
    df=get_data(main_symbol, period)
    if df.empty:
        st.error("Data nahi mila")
    else:
        df['EMA20']=df['Close'].ewm(span=20).mean()
        df['RSI']=calc_rsi(df['Close'])
        df['MACD'],df['Signal']=calc_macd(df['Close'])
        curr=float(df['Close'].iloc[-1])
        sup=float(df['Low'].tail(20).min()); res=float(df['High'].tail(20).max())

        # --- Price Alert Check ---
        if alert_high>0 and curr>alert_high:
            st.success(f"🔔 ALERT: {main_symbol} ₹{curr:.2f} tumhare target ₹{alert_high} ke UPAR hai! Profit book karne ka socho.")
            st.balloons()
        if alert_low>0 and curr<alert_low:
            st.error(f"🔔 ALERT: {main_symbol} ₹{curr:.2f} tumhare stop-loss ₹{alert_low} ke NEECHE hai! Savdhaan.")

        c1,c2,c3=st.columns(3)
        c1.metric("Price",f"₹{curr:.2f}"); c2.metric("Support",f"₹{sup:.2f}"); c3.metric("Resistance",f"₹{res:.2f}")

        st.subheader("🤖 2. AI Buy/Sell Signal")
        rsi_v=df['RSI'].iloc[-1]; macd_v=df['MACD'].iloc[-1]; sig_v=df['Signal'].iloc[-1]; ema20_v=df['EMA20'].iloc[-1]
        score=ai_signal_row(rsi_v,macd_v,sig_v,curr,ema20_v)
        signal="HOLD 🟡"
        if score>=2: signal="STRONG BUY 🟢"
        elif score==1: signal="BUY 🟢"
        elif score==-1: signal="SELL 🔴"
        elif score<=-2: signal="STRONG SELL 🔴"
        if "BUY" in signal: st.success(f"## {signal}")
        elif "SELL" in signal: st.error(f"## {signal}")
        else: st.warning(f"## {signal}")
        st.write(f"- RSI: {rsi_v:.1f}")
        st.write(f"- MACD: {'Bullish' if macd_v>sig_v else 'Bearish'}")
        st.write(f"- Price vs EMA20: {'Upar' if curr>ema20_v else 'Neeche'}")

        st.subheader("📰 4. News Sentiment")
        pos,neg,titles=get_news_sentiment(main_symbol)
        if titles:
            col1,col2=st.columns(2); col1.metric("Positive",pos); col2.metric("Negative",neg)
            if pos>neg: st.success("Sentiment: Positive 🟢")
            elif neg>pos: st.error("Sentiment: Negative 🔴")
            else: st.warning("Sentiment: Neutral 🟡")
            with st.expander("Headlines"):
                for t in titles[:8]: st.write("- "+t)

        # --- 6. Backtesting ---
        st.subheader("🧪 6. Backtesting (AI Strategy)")
        df_bt=df.copy().dropna()
        cash=100000; holding=0
        for i in range(1,len(df_bt)):
            r=df_bt['RSI'].iloc[i]; m=df_bt['MACD'].iloc[i]; s=df_bt['Signal'].iloc[i]
            p=df_bt['Close'].iloc[i]; e=df_bt['EMA20'].iloc[i]
            sc=ai_signal_row(r,m,s,p,e)
            if sc>=1 and holding==0:
                holding=cash/p; cash=0
            elif sc<=-1 and holding>0:
                cash=holding*p; holding=0
        final_val=cash if cash>0 else holding*df_bt['Close'].iloc[-1]
        pnl=(final_val-100000)/100000*100
        buy_hold=(df_bt['Close'].iloc[-1]-df_bt['Close'].iloc[0])/df_bt['Close'].iloc[0]*100
        b1,b2,b3=st.columns(3)
        b1.metric("AI Strategy Return",f"{pnl:.2f}%")
        b2.metric("Buy & Hold Return",f"{buy_hold:.2f}%")
        b3.metric("Winner", "AI 🤖" if pnl>buy_hold else "Buy&Hold")
        if pnl>buy_hold: st.success("AI ne market ko beat kiya!")
        else: st.info("Is timeframe me Buy & Hold better raha.")

        st.subheader("📉 1. RSI & MACD Chart + Support/Resistance")
        fig=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.05,row_heights=[0.6,0.2,0.2])
        fig.add_trace(go.Candlestick(x=df.index,open=df['Open'],high=df['High'],low=df['Low'],close=df['Close'],name="Price"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['EMA20'],line=dict(color='orange',width=1),name='EMA20'),row=1,col=1)
        # Support Resistance auto lines
        fig.add_hline(y=res, line_dash="dash", line_color="red", annotation_text=f"Res {res:.0f}", row=1, col=1)
        fig.add_hline(y=sup, line_dash="dash", line_color="green", annotation_text=f"Sup {sup:.0f}", row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['RSI'],line=dict(color='purple'),name='RSI'),row=2,col=1)
        fig.add_hline(y=70,line_dash="dash",line_color="red",row=2,col=1); fig.add_hline(y=30,line_dash="dash",line_color="green",row=2,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['MACD'],line=dict(color='blue'),name='MACD'),row=3,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['Signal'],line=dict(color='red'),name='Signal'),row=3,col=1)
        fig.update_layout(height=700,xaxis_rangeslider_visible=False,template="plotly_dark",margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig,use_container_width=True)

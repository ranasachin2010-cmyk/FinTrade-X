import streamlit as st, yfinance as yf, pandas as pd, ta
from concurrent.futures import ThreadPoolExecutor
from textblob import TextBlob
import plotly.graph_objects as go

st.set_page_config(page_title="FinTrade X - Nifty 500 + Search", layout="wide", page_icon="🧠")
st.title("🧠 FinTrade X - Nifty 500 AI + Stock Search")

# --- SEARCH BAR - SABSE UPAR ---
search_sym = st.text_input("🔍 Koi bhi NSE Stock Search Karo (ex: RELIANCE, SUZLON, PAYTM, TATAMOTORS):", "").upper().strip()

def analyze_single(sym, hist_days="1y"):
    try:
        t = yf.Ticker(sym+".NS" if not sym.endswith(".NS") else sym)
        hist = t.history(period=hist_days)
        if len(hist) < 50: return None
        curr = hist['Close'].iloc[-1]

        # Indicators
        rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        sma50 = hist['Close'].rolling(50).mean().iloc[-1]
        sma200 = hist['Close'].rolling(200).mean().iloc[-1]
        atr = ta.volatility.AverageTrueRange(hist['High'], hist['Low'], hist['Close']).average_true_range().iloc[-1]
        vwap = ((hist['Close']*hist['Volume']).rolling(20).sum() / hist['Volume'].rolling(20).sum()).iloc[-1]
        sup = hist['Low'].tail(50).min(); res = hist['High'].tail(50).max()

        # Candle
        last = hist.iloc[-1]; prev = hist.iloc[-2]; body = abs(last['Close']-last['Open'])
        pattern="Normal"
        if last['Close'] > last['Open'] and last['Low'] < last['Open'] - body*1.5: pattern="Hammer 🟢 Bullish"
        elif last['Close'] < last['Open'] and last['High'] > last['Open'] + body*1.5: pattern="Shooting Star 🔴 Bearish"
        elif last['Close'] > prev['Open'] and last['Open'] < prev['Close']: pattern="Bullish Engulfing 🟢"
        elif last['Close'] < prev['Open'] and last['Open'] > prev['Close']: pattern="Bearish Engulfing 🔴"

        # Fundamental + News
        info = t.info
        pe = info.get('trailingPE',0) or 0; roe = info.get('returnOnEquity',0) or 0; de = info.get('debtToEquity',0) or 0
        try:
            news_list = t.news[:5]
            senti_score = sum([TextBlob(n['title']).sentiment.polarity for n in news_list])/len(news_list) if news_list else 0
            news_titles = [n['title'] for n in news_list]
        except: senti_score=0; news_titles=[]
        news_label = "Bullish 🟢" if senti_score>0.15 else "Bearish 🔴" if senti_score<-0.15 else "Neutral 🟡"

        # AI Score & Decision
        score=50
        if curr>sma20: score+=8
        if curr>sma50: score+=10
        if curr>sma200: score+=10
        if curr>vwap: score+=5
        if 35<rsi<65: score+=8
        if rsi<32: score+=10
        if rsi>75: score-=10
        if pe>0 and pe<25: score+=7
        if roe>0.18: score+=7
        if senti_score>0.15: score+=8
        if senti_score<-0.15: score-=8
        if "🟢" in pattern: score+=7
        if "🔴" in pattern: score-=7
        score=max(0,min(100,score))

        decision = "STRONG BUY 🟢" if score>=75 else "BUY 🟢" if score>=60 else "SELL 🔴" if score<=35 else "STRONG SELL 🔴" if score<=25 else "HOLD 🟡"

        # SL & Target (ATR Based)
        sl = round(curr - atr*1.5,2) if score>=60 else round(curr + atr*1.5,2)
        target1 = round(curr + (curr-sl)*1.5,2) if score>=60 else round(curr - (sl-curr)*1.5,2) if score<=40 else round(res,2)
        target2 = round(curr + (curr-sl)*2.5,2) if score>=60 else round(curr - (sl-curr)*2.5,2) if score<=40 else round(res*1.02,2)

        return {
            "SYMBOL": sym.replace(".NS",""), "PRICE": round(curr,2), "AI_SCORE": int(score), "DECISION": decision,
            "SL": sl, "TARGET1": target1, "TARGET2": target2, "RSI": round(rsi,1), "ATR": round(atr,2),
            "AVG20": round(sma20,1), "AVG50": round(sma50,1), "AVG200": round(sma200,1), "VWAP": round(vwap,1),
            "SUPPORT": round(sup,1), "RESISTANCE": round(res,1), "P/E": round(pe,1), "ROE": f"{roe*100:.1f}%",
            "DE": round(de,2), "NEWS": news_label, "SENTI_SCORE": round(senti_score,2), "CANDLE": pattern,
            "NEWS_TITLES": news_titles, "hist": hist.tail(180)
        }
    except Exception as e: return None

# --- IF USER SEARCHED ---
if search_sym:
    with st.spinner(f"🔍 {search_sym} ka full analysis ho raha hai..."):
        data = analyze_single(search_sym)
    if not data:
        st.error(f"{search_sym} nahi mila. Sahi NSE symbol likho (ex: SUZLON)")
    else:
        st.success(f"Found: {data['SYMBOL']}")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Price", data['PRICE']); c2.metric("AI Score", f"{data['AI_SCORE']}/100"); c3.metric("Decision", data['DECISION']); c4.metric("SL", data['SL']); c5.metric("Target 1/2", f"{data['TARGET1']} / {data['TARGET2']}")

        t1,t2,t3 = st.tabs(["📈 Chart + Candle", "📰 News + Sentiment", "📊 Fundamental + Technical"])
        with t1:
            fig = go.Figure(data=[go.Candlestick(x=data['hist'].index, open=data['hist']['Open'], high=data['hist']['High'], low=data['hist']['Low'], close=data['hist']['Close'], name="Candle")])
            fig.add_hline(y=data['SUPPORT'], line_dash="dash", line_color="green", annotation_text="Support")
            fig.add_hline(y=data['RESISTANCE'], line_dash="dash", line_color="red", annotation_text="Resistance")
            fig.add_hline(y=data['SL'], line_color="red", annotation_text="SL")
            fig.update_layout(height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"Candle Pattern: **{data['CANDLE']}** | RSI: {data['RSI']} | ATR: {data['ATR']}")
        with t2:
            st.metric("News Sentiment", f"{data['NEWS']} ({data['SENTI_SCORE']})")
            for title in data['NEWS_TITLES']: st.write(f"- {title}")
        with t3:
            st.json({k:v for k,v in data.items() if k not in ['hist','NEWS_TITLES']})

    st.divider()

# --- NIFTY 500 BACKGROUND SCAN ---
st.subheader("⚡ Nifty 500 Auto Top 10")
@st.cache_data(ttl=86400)
def get_nifty500_list():
    try:
        df = pd.read_csv("https://archives.nseindia.com/content/indices/ind_nifty500list.csv")
        return df['Symbol'].tolist()[:500]
    except: return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","BHARTIARTL","ITC","LT","KOTAKBANK","BAJFINANCE","ASIANPAINT","AXISBANK","MARUTI","WIPRO","HCLTECH","TITAN","SUNPHARMA","ONGC","NTPC"]*25

NIFTY500 = get_nifty500_list()

if st.button("🚀 Nifty 500 Scan Karo (2 min lagega)"):
    progress = st.progress(0)
    results=[]
    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(analyze_single, s): s for s in NIFTY500}
        for i,f in enumerate(futs):
            r=f.result()
            if r: results.append(r)
            if i%20==0: progress.progress((i+1)/len(NIFTY500), text=f"{i+1}/{len(NIFTY500)} {futs[f]}")
    progress.empty()
    if results:
        df = pd.DataFrame([{k:v for k,v in r.items() if k not in ['hist','NEWS_TITLES']} for r in results]).sort_values("AI_SCORE", ascending=False)
        st.session_state['scan_df']=df
        st.session_state['scan_results']=results

if 'scan_df' in st.session_state:
    df = st.session_state['scan_df']
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### ✅ TOP 10 BUY")
        st.dataframe(df.head(10)[["SYMBOL","PRICE","AI_SCORE","DECISION","SL","TARGET1","RSI","CANDLE"]], hide_index=True, use_container_width=True)
    with c2:
        st.markdown("#### ❌ TOP 10 SELL")
        st.dataframe(df.tail(10).sort_values("AI_SCORE")[["SYMBOL","PRICE","AI_SCORE","DECISION","SL","TARGET1","RSI","CANDLE"]], hide_index=True, use_container_width=True)

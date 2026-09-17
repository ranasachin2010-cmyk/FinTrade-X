import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
import numpy as np

st.set_page_config(page_title="AI Stock Analyzer Pro", layout="wide")
st.title("🤖 AI Stock Analyzer Pro - Backtest + Scanner + ML")

st.sidebar.header("Settings")
mode = st.sidebar.radio("Mode", ["Single Stock", "Nifty 50 Scanner"])
timeframe = st.sidebar.selectbox("Timeframe", ["6mo","1y","2y"], index=1)

def rsi_calc(s, l=14):
    d=s.diff(); g=d.where(d>0,0); lo=-d.where(d<0,0)
    ag=g.ewm(com=l-1,min_periods=l).mean(); al=lo.ewm(com=l-1,min_periods=l).mean()
    return 100-(100/(1+ag/al))

def macd_calc(s):
    e12=s.ewm(span=12,adjust=False).mean(); e26=s.ewm(span=26,adjust=False).mean()
    m=e12-e26; sig=m.ewm(span=9,adjust=False).mean(); return m,sig

def get_signal(df):
    last=df.iloc[-1]; rsi=float(last['RSI'])
    score=0
    if rsi<30: score+=2
    elif rsi<50: score+=1
    elif rsi>70: score-=2
    if float(last['MACD'])>float(last['MACDs']): score+=2
    else: score-=1
    if float(last['Close'])>float(last['EMA20']): score+=1
    else: score-=1
    if score>=3: return "STRONG BUY 🟢",score
    elif score>=1: return "BUY 🟢",score
    elif score<=-2: return "STRONG SELL 🔴",score
    elif score<0: return "SELL 🔴",score
    else: return "HOLD 🟡",score

def analyze_df(df):
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df['RSI']=rsi_calc(df['Close'])
    df['MACD'],df['MACDs']=macd_calc(df['Close'])
    df['EMA20']=df['Close'].ewm(span=20,adjust=False).mean()
    df['EMA50']=df['Close'].ewm(span=50,adjust=False).mean()
    return df

def ml_predict(df):
    try:
        d=df.copy(); d['Target']=d['Close'].shift(-1); d=d.dropna()
        if len(d)<60: return None,None
        feats=['Close','RSI','MACD','MACDs','EMA20','EMA50','Volume']
        X=d[feats].fillna(0); y=d['Target']
        m=RandomForestRegressor(n_estimators=100,random_state=42,n_jobs=-1)
        m.fit(X.iloc[:-1],y.iloc[:-1])
        pred=float(m.predict(X.iloc[-1:].values)[0])
        acc=round(float(m.score(X.iloc[-21:-1],y.iloc[-21:-1]))*100,1)
        return round(pred,2),acc
    except: return None,None

def backtest(df):
    trades=[]; pos=False; buy=0
    for i in range(1,len(df)):
        r=df['RSI'].iloc[i]
        p=float(df['Close'].iloc[i])
        if not pos and r<30:
            pos=True; buy=p
        elif pos and r>70:
            pos=False; trades.append((p-buy)/buy*100)
    if not trades: return 0,0,0
    win=sum(1 for t in trades if t>0)/len(trades)*100
    return len(trades), round(win,1), round(sum(trades),1)

def get_fundamentals(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        info = t.info
        return {"pe": info.get("trailingPE","N/A"), "high52": info.get("fiftyTwoWeekHigh","N/A"), "low52": info.get("fiftyTwoWeekLow","N/A"), "div": info.get("dividendYield","N/A")}
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
            prov_dict = c.get('provider') or {}
            provider = prov_dict.get('displayName','') if isinstance(prov_dict, dict) else ''
            out.append({"title":title,"link":link,"provider":provider})
        return out
    except:
        return []

def plot_chart(df,res,sup):
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,row_heights=[0.6,0.2,0.2],vertical_spacing=0.05,
        subplot_titles=("Price + EMA + S/R","RSI","MACD"))
    fig.add_trace(go.Candlestick(x=df.index,open=df['Open'],high=df['High'],low=df['Low'],close=df['Close'],name="Price"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['EMA20'],line=dict(color='orange'),name="EMA20"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['EMA50'],line=dict(color='blue'),name="EMA50"),row=1,col=1)
    fig.add_hline(y=res,line_dash="dot",line_color="red",annotation_text=f"R:{res:.2f}", row=1,col=1)
    fig.add_hline(y=sup,line_dash="dot",line_color="green",annotation_text=f"S:{sup:.2f}", row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['RSI'],line=dict(color='purple'),name="RSI"),row=2,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="red",row=2,col=1)
    fig.add_hline(y=30,line_dash="dash",line_color="green",row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['MACD'],line=dict(color='blue'),name="MACD"),row=3,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['MACDs'],line=dict(color='red'),name="Signal"),row=3,col=1)
    fig.update_layout(height=700,xaxis_rangeslider_visible=False,showlegend=False)
    return fig

NIFTY50=["RELIANCE","HDFCBANK","TCS","INFY","ICICIBANK","SBIN","TATAMOTORS","LT","AXISBANK","KOTAKBANK","NTPC","ONGC","POWERGRID","TITAN","SUNPHARMA","ULTRACEMCO","MARUTI","BAJFINANCE","HINDUNILVR","ADANIENT"]

if mode=="Nifty 50 Scanner":
    st.header("🔍 Nifty 50 Swing Scanner")
    if st.button("Scan Now"):
        results=[]
        bar=st.progress(0)
        for i,sym in enumerate(NIFTY50):
            try:
                df=yf.download(sym+".NS",period=timeframe,progress=False)
                if df.empty or len(df)<60: continue
                df=analyze_df(df)
                sig,score=get_signal(df)
                price=float(df['Close'].iloc[-1]); rsi=float(df['RSI'].iloc[-1])
                pred,_=ml_predict(df)
                results.append({"Symbol":sym,"Price":round(price,2),"RSI":round(rsi,1),"Signal":sig,"Score":score,"ML_Pred":pred})
            except: pass
            bar.progress((i+1)/len(NIFTY50))
        rdf=pd.DataFrame(results).sort_values("Score",ascending=False)
        st.dataframe(rdf,use_container_width=True)
        st.success(f"Top Pick: {rdf.iloc[0]['Symbol']} - {rdf.iloc[0]['Signal']}") if not rdf.empty else st.warning("No data")
else:
    sym=st.sidebar.text_input("NSE Symbol","HUDCO").strip().upper()
    df=yf.download(sym+".NS",period=timeframe,progress=False)
    if df.empty or len(df)<60:
        st.error("Data nahi mila"); st.stop()
    df=analyze_df(df)
    sig,score=get_signal(df)
    price=float(df['Close'].iloc[-1]); rsi=float(df['RSI'].iloc[-1])
    res=float(df['High'].tail(30).max()); sup=float(df['Low'].tail(30).min())
    target=res; stoploss=sup
    pred,acc=ml_predict(df)
    n_trades,win_rate,total_ret=backtest(df)

    st.header(f"📊 {sym}")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Price",f"₹{price:.2f}"); c2.metric("RSI",f"{rsi:.1f}")
    c3.metric("Signal",sig); c4.metric("ML Pred",f"₹{pred}" if pred else "N/A")
    if pred: st.info(f"ML Next Day: ₹{pred} ({(pred-price)/price*100:+.2f}%) | Acc: {acc}%")

    st.success(f"🎯 Target: ₹{target:.2f} | 🛑 Stop-Loss: ₹{stoploss:.2f}")
    st.warning(f"🟥 Resistance: ₹{res:.2f} | 🟩 Support: ₹{sup:.2f}")

    fund = get_fundamentals(sym)
    st.subheader("💰 Fundamentals")
    f1,f2,f3,f4 = st.columns(4)
    f1.write(f"P/E: {fund.get('pe')}")
    f2.write(f"52W High: {fund.get('high52')}")
    f3.write(f"52W Low: {fund.get('low52')}")
    f4.write(f"Div Yield: {fund.get('div')}")

    st.subheader("📰 Latest News")
    news_list = get_news(sym)
    if news_list:
        for n in news_list:
            prov = "("+n['provider']+")" if n['provider'] else ""
            st.write(f"- [{n['title']}]({n['link']}) {prov}")
    else:
        st.write("News nahi mili")

    st.subheader("📊 Backtest (RSI<30 Buy, RSI>70 Sell)")
    b1,b2,b3=st.columns(3)
    b1.metric("Total Trades",n_trades); b2.metric("Win Rate",f"{win_rate}%"); b3.metric("Total Return",f"{total_ret}%")

    st.subheader("📈 Chart with RSI + MACD")
    st.plotly_chart(plot_chart(df,res,sup),use_container_width=True)

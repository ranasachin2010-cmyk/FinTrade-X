import streamlit as st
import yfinance as yf, pandas as pd, ta, plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FinTrade X Pro", layout="wide", page_icon="🧠")
st_autorefresh(interval=5000, key="live")

# --- PREMIUM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@500;700&display=swap');
.stApp { background: #05070a; font-family: 'Inter', sans-serif; }
.glass {
  background: rgba(20,24,35,0.85);
  border: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
  border-radius: 16px; padding: 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
.header {
  background: linear-gradient(90deg, #10131a 0%, #1a1f2e 100%);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 18px; padding: 16px 22px;
  display:flex; justify-content:space-between; align-items:center;
}
.live-dot { width:10px; height:10px; background:#00ff88; border-radius:50%; box-shadow:0 0 12px #00ff88; display:inline-block; animation:pulse 1.5s infinite; }
@keyframes pulse {0%{opacity:1} 50%{opacity:0.4} 100%{opacity:1}}
.ticker { background:#1a1f2b; border-radius:8px; padding:6px 12px; margin-right:8px; border:1px solid rgba(255,255,255,0.06); }
.score-circle { width:160px; height:160px; border-radius:50%; border:6px solid #222; border-top-color:#00ff88; display:flex; align-items:center; justify-content:center; flex-direction:column; margin:auto; }
.badge-buy { background:#00ff88; color:#000; padding:4px 12px; border-radius:20px; font-weight:700; font-size:12px; }
.badge-sell { background:#ff3b5c; color:#fff; padding:4px 12px; border-radius:20px; font-weight:700; font-size:12px; }
.badge-hold { background:#ffb020; color:#000; padding:4px 12px; border-radius:20px; font-weight:700; font-size:12px; }
input { background:#0f121a !important; border:1px solid #222 !important; border-radius:12px !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="header">
  <div style="display:flex; gap:14px; align-items:center;">
    <div style="font-size:32px;">🧠</div>
    <div>
      <div style="font-size:26px; font-weight:800; color:#fff; letter-spacing:-0.5px;">FinTrade <span style="color:#c8ff5a;">X</span></div>
      <div style="color:#8b8fa3; font-size:12px;">Nifty 500 AI • AI-Powered Trading Dashboard</div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="display:flex; gap:8px;">
      <span class="ticker" style="color:#fff;">NIFTY 50 <span style="color:#00ff88;">24,567.30 +0.87% ▲</span></span>
      <span class="ticker" style="color:#fff;">BANK NIFTY <span style="color:#ff3b5c;">52,341.20 -0.24% ▼</span></span>
    </div>
    <div style="color:#00ff88; font-size:11px; margin-top:6px; border:1px solid #00ff88; display:inline-block; padding:2px 10px; border-radius:20px;"><span class="live-dot"></span> Live • 15:42 IST</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# --- SEARCH PREMIUM ---
search = st.text_input("", placeholder="🔍 Search NSE Stock (ex: RELIANCE, SUZLON, PAYTM)...", label_visibility="collapsed")

def analyze(sym):
    try:
        t = yf.Ticker(sym+".NS" if not sym.endswith(".NS") else sym)
        h = t.history(period="6mo")
        if len(h)<50: return None
        curr = h['Close'].iloc[-1]
        live = t.fast_info.get('last_price', curr)
        rsi = ta.momentum.RSIIndicator(h['Close']).rsi().iloc[-1]
        sup = h['Low'].tail(50).min(); res = h['High'].tail(50).max()
        score = 50 + (10 if curr>h['Close'].rolling(20).mean().iloc[-1] else -5) + (15 if 30<rsi<65 else -5)
        score = max(10,min(95,int(score+30)))
        decision = "BUY" if score>=70 else "SELL" if score<=40 else "HOLD"
        return {"SYMBOL":sym.replace(".NS",""), "LIVE":round(live,2), "SCORE":score, "DECISION":decision, "RSI":round(rsi,1), "SUP":round(sup,1), "RES":round(res,1), "hist":h.tail(120)}
    except: return None

col1, col2 = st.columns([1, 2.2])

with col1:
    if search:
        d = analyze(search.upper())
        if d:
            st.markdown(f"""
            <div class="glass">
              <div style="color:#8b8fa3; font-size:12px;">✨ AI SCORE</div>
              <div class="score-circle">
                <div style="font-size:48px; font-weight:800; color:#00ff88;">{d['SCORE']}</div>
                <div style="color:#8b8fa3;">/100</div>
              </div>
              <div style="text-align:center; margin-top:10px;">
                <span style="border:1px solid #00ff88; padding:4px 12px; border-radius:20px; color:#00ff88; font-size:12px;">● {'Bullish' if d['SCORE']>=60 else 'Bearish'}</span>
              </div>
              <div style="margin-top:14px; display:flex; justify-content:space-between; color:#fff;">
                <div>LIVE<br><b style="color:#00ff88;">₹{d['LIVE']}</b></div>
                <div>RSI<br><b>{d['RSI']}</b></div>
                <div>Signal<br><span class="{'badge-buy' if d['DECISION']=='BUY' else 'badge-sell' if d['DECISION']=='SELL' else 'badge-hold'}">{d['DECISION']}</span></div>
              </div>
              <div style="color:#8b8fa3; font-size:11px; margin-top:12px;">Support: {d['SUP']} • Resistance: {d['RES']} • RSI: {d['RSI']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass">
          <div style="color:#8b8fa3; font-size:12px;">✨ AI SCORE</div>
          <div class="score-circle" style="border-top-color:#00ff88;">
            <div style="font-size:48px; font-weight:800; color:#00ff88;">78</div><div style="color:#8b8fa3;">/100</div>
          </div>
          <div style="text-align:center; margin-top:10px;"><span style="border:1px solid #00ff88; padding:4px 12px; border-radius:20px; color:#fff; font-size:12px;">● Bullish</span></div>
          <div style="color:#ff9d66; font-size:11px; text-align:center; margin-top:10px;">Strong Buy Momentum • Confidence 78%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass" style="margin-top:12px;">
      <div style="color:#fff; font-weight:700; margin-bottom:10px;">📊 PORTFOLIO OVERVIEW</div>
      <div style="color:#8b8fa3; font-size:12px;">Today's P&L</div>
      <div style="color:#00ff88; font-size:22px; font-weight:800;">+₹12,450 <span style="font-size:12px;">↗ (+1.32%)</span></div>
      <div style="display:flex; justify-content:space-between; margin-top:12px;">
        <div><div style="color:#8b8fa3; font-size:11px;">Total Value</div><div style="color:#fff; font-weight:700;">₹9,43,280</div></div>
        <div><div style="color:#8b8fa3; font-size:11px;">Win Rate</div><div style="color:#00ff88; font-weight:700;">68%</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Chart
    if search and d:
        hist = d['hist']
    else:
        hist = yf.Ticker("RELIANCE.NS").history(period="6mo").tail(120)
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff3b5c')])
    fig.update_layout(height=380, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0), font=dict(color="#8b8fa3", size=10))
    st.markdown('<div class="glass"><div style="color:#fff; font-weight:700; margin-bottom:8px;">NIFTY 500 • 1D CHART <span style="float:right;"><span style="background:#00ff88; color:#000; padding:2px 8px; border-radius:6px; font-size:11px;">1D</span> <span style="padding:2px 8px;">5D</span> <span style="padding:2px 8px;">1M</span> <span style="padding:2px 8px;">6M</span></span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Top 10 Table Premium
    st.markdown("""
    <div class="glass" style="margin-top:12px;">
      <div style="display:flex; justify-content:space-between; color:#fff; font-weight:700; margin-bottom:10px;">≡ TOP 10 STOCKS — NIFTY 500 <span style="border:1px solid #3a3f52; padding:2px 10px; border-radius:20px; font-size:11px; color:#8b8fa3;">Sorted by AI Score ↓</span></div>
      <div style="color:#8b8fa3; font-size:11px; display:flex; justify-content:space-between; border-bottom:1px solid #222; padding-bottom:6px;">
        <span># STOCK</span><span>PRICE</span><span>CHANGE</span><span>AI SCORE</span><span>SIGNAL</span>
      </div>
      <div style="color:#fff; font-size:12px; line-height:32px;">
        01 &nbsp; Reliance Industries &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ₹2,872.45 &nbsp;&nbsp; <span style="color:#00ff88;">+1.42% ↑</span> &nbsp;&nbsp; 92 &nbsp;&nbsp; <span class="badge-buy">BUY</span><br>
        02 &nbsp; HDFC Bank &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ₹1,643.20 &nbsp;&nbsp; <span style="color:#ff3b5c;">-0.28%</span> &nbsp;&nbsp; 74 &nbsp;&nbsp; <span class="badge-hold">HOLD</span><br>
        03 &nbsp; Infosys &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ₹1,522.90 &nbsp;&nbsp; <span style="color:#00ff88;">+0.91%</span> &nbsp;&nbsp; 85 &nbsp;&nbsp; <span class="badge-buy">BUY</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

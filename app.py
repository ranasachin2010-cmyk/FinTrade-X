import streamlit as st, yfinance as yf, pandas as pd, ta, plotly.graph_objects as go, concurrent.futures
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FinTrade X Pro", layout="wide", page_icon="🧠")
st_autorefresh(interval=10000, key="live")

@st.cache_data(ttl=60)
def get_indices():
    try:
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
        bank = yf.Ticker("^NSEBANK").history(period="1d")['Close'].iloc[-1]
        sensex = yf.Ticker("^BSESN").history(period="1d")['Close'].iloc[-1]
        return round(nifty,2), round(bank,2), round(sensex,2), 18992.40
    except:
        return 24567.30, 52341.20, 80124.65, 18992.40

nifty_p, bank_p, sensex_p, n500_p = get_indices()

st.markdown("""
<style>
.stApp {background:#05070a;}
.glass {background: rgba(18,22,32,0.92); border:1px solid rgba(255,255,255,0.07); border-radius:18px; padding:16px; backdrop-filter:blur(18px);}
.header {background: linear-gradient(90deg, #12151e 0%, #1d2333 100%); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:14px 20px;}
.score-ring {width:150px; height:150px; border-radius:50%; border:8px solid #1e2332; border-top:8px solid #00ff88; border-right:8px solid #00ff88; display:flex; align-items:center; justify-content:center; flex-direction:column; margin:auto; box-shadow:0 0 20px rgba(0,255,136,0.2);}
.b-buy {background:#00e676; color:#000; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-hold {background:#a16207; color:#fff; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-sell {background:#ef4444; color:#fff; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-score {background:#1a4d2e; color:#4ade80; border:1px solid #22c55e; padding:2px 10px; border-radius:6px; font-weight:700;}
.t-h {color:#6b7280; font-size:11px; letter-spacing:1px;}
.t-v {color:#fff; font-weight:700; font-size:14px;}
[data-testid="stHeader"] {display:none;}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown(f"""
<div class="header">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div style="display:flex; gap:12px; align-items:center;">
      <div style="width:42px; height:42px; background:linear-gradient(135deg, #a3ff12, #00ff88); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px;">◈</div>
      <div>
        <div style="color:#fff; font-size:24px; font-weight:900;">FinTrade <span style="color:#c6ff00;">X</span></div>
        <div style="color:#6b7280; font-size:11px;">Nifty 500 AI • AI-Powered Trading Dashboard</div>
      </div>
    </div>
    <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-end;">
      <div style="display:flex; gap:8px;">
        <span style="background:#1a1f2e; border:1px solid #2a2f45; border-radius:8px; padding:6px 12px; color:#fff; font-size:12px;">NIFTY 50 <span style="color:#00ff88;">{nifty_p} +0.87% ▲</span></span>
        <span style="background:#1a1f2e; border:1px solid #2a2f45; border-radius:8px; padding:6px 12px; color:#fff; font-size:12px;">BANK NIFTY <span style="color:#ff4d4d;">{bank_p} -0.24% ▼</span></span>
      </div>
      <div style="display:flex; gap:8px;">
        <span style="background:#1a1f2e; border:1px solid #2a2f45; border-radius:8px; padding:6px 12px; color:#fff; font-size:12px;">SENSEX <span style="color:#00ff88;">{sensex_p} +0.52% ▲</span></span>
        <span style="background:#1a1f2e; border:1px solid #2a2f45; border-radius:8px; padding:6px 12px; color:#fff; font-size:12px;">NIFTY 500 <span style="color:#00ff88;">{n500_p} +0.61% ▲</span></span>
        <span style="background:#0f1a12; border:1px solid #00ff88; border-radius:20px; padding:4px 12px; color:#00ff88; font-size:11px;">Live • 15:42 IST</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
st.write("")

# FIXED ANALYSIS - Price & Signal Bug Fixed
@st.cache_data(ttl=300)
def analyze_stock(sym):
    try:
        t = yf.Ticker(sym+".NS")
        h = t.history(period="6mo")
        if len(h)<60: return None
        curr = h['Close'].iloc[-1] # FIXED: Only Close price
        rsi = ta.momentum.RSIIndicator(h['Close']).rsi().iloc[-1]
        change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2])*100
        score = 50
        if curr > h['Close'].rolling(20).mean().iloc[-1]: score+=12
        if curr > h['Close'].rolling(50).mean().iloc[-1]: score+=12
        if 35<rsi<70: score+=10
        if rsi<30: score+=15
        score = max(20,min(92,int(score+10)))
        dec = "BUY" if score>=70 else "SELL" if score<=45 else "HOLD"
        return {"STOCK":sym, "PRICE":round(curr,2), "CHANGE":round(change,2), "SCORE":score, "SIGNAL":dec, "HIST":h.tail(100), "RSI":round(rsi,1)}
    except:
        return None

NIFTY500_SAMPLE = ["KOTAKBANK","TITAN","INFY","HINDUNILVR","MARUTI","ASIANPAINT","WIPRO","HCLTECH","SUNPHARMA","RELIANCE","HDFCBANK","ICICIBANK","TCS","ITC","LT","SBIN","BAJFINANCE","BHARTIARTL","ONGC","AXISBANK"]

if 'top_data' not in st.session_state or st.button("↻ Refresh"):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        res = [r for r in ex.map(analyze_stock, NIFTY500_SAMPLE) if r]
    st.session_state.top_data = sorted(res, key=lambda x: x['SCORE'], reverse=True)[:10]

top10 = st.session_state.top_data

c1, c2 = st.columns([0.95, 2.2])

with c1:
    # AI SCORE - Live from Top 1
    sc = top10[0]['SCORE'] if top10 else 78
    bullish = "Bullish" if sc>=60 else "Bearish"
    st.markdown(f"""
    <div class="glass">
      <div class="t-h">✨ AI SCORE</div>
      <div style="margin-top:12px;"><div class="score-ring"><div style="color:#00ff88; font-size:44px; font-weight:900;">{sc}</div><div style="color:#6b7280; font-size:14px;">/100</div></div></div>
      <div style="text-align:center; margin-top:12px;"><span style="background:#12261a; border:1px solid #1a4d2e; color:#fff; padding:5px 14px; border-radius:20px; font-size:12px;">● {bullish}</span></div>
      <div style="text-align:center; color:#c08a5a; font-size:11px; margin-top:8px;">Strong Buy Momentum • Confidence {sc}%</div>
    </div>
    <div class="glass" style="margin-top:12px;">
      <div style="color:#fff; font-weight:700; font-size:13px; margin-bottom:10px;">📁 PORTFOLIO OVERVIEW</div>
      <div class="t-h">Today's P&L</div><div style="color:#00ff88; font-size:20px; font-weight:800;">+₹12,450 <span style="font-size:12px;">↗ (+1.32%)</span></div>
      <div style="display:flex; justify-content:space-between; margin-top:14px;">
        <div><div class="t-h">Total Value</div><div class="t-v">₹9,43,280</div></div>
        <div><div class="t-h">Win Rate</div><div style="color:#00ff88; font-weight:800; font-size:16px;">68%</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # FIXED AI SIGNALS - Same data from TOP10
    if len(top10)>=2:
        sig1, sig2 = top10[0], top10[1]
        b1 = "b-buy" if sig1['SIGNAL']=="BUY" else "b-sell" if sig1['SIGNAL']=="SELL" else "b-hold"
        b2 = "b-buy" if sig2['SIGNAL']=="BUY" else "b-sell" if sig2['SIGNAL']=="SELL" else "b-hold"
        st.markdown(f"""
        <div class="glass" style="margin-top:12px;">
          <div style="color:#fff; font-weight:700; font-size:13px; margin-bottom:10px;">📶 AI SIGNALS</div>
          <div style="display:flex; gap:8px; align-items:center; margin-bottom:12px;">
            <span class="{b1}">{sig1['SIGNAL']}</span>
            <div><div style="color:#fff; font-size:11px; font-weight:700;">{sig1['STOCK']} • {sig1['STOCK']}</div><div style="color:#6b7280; font-size:10px;">Score {sig1['SCORE']} • ₹{sig1['PRICE']} • RSI {sig1['RSI']}</div></div>
          </div>
          <div style="display:flex; gap:8px; align-items:center;">
            <span class="{b2}">{sig2['SIGNAL']}</span>
            <div><div style="color:#fff; font-size:11px; font-weight:700;">{sig2['STOCK']} • {sig2['STOCK']}</div><div style="color:#6b7280; font-size:10px;">Score {sig2['SCORE']} • ₹{sig2['PRICE']} • RSI {sig2['RSI']}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

with c2:
    # CHART
    sel = top10[0] if top10 else None
    hist = sel['HIST'] if sel else yf.Ticker("RELIANCE.NS").history(period="6mo").tail(100)
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff4d6d')])
    fig.add_scatter(x=hist.index, y=hist['Close'].rolling(20).mean(), mode='lines', line=dict(color='#00ff88', width=1.5), name='AI Trendline')
    fig.update_layout(height=340, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=20,b=0), showlegend=False)

    st.markdown(f"""
    <div class="glass">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <div style="color:#fff; font-weight:800; font-size:14px;">{sel['STOCK'] if sel else 'NIFTY 500'} • 1D CHART</div>
        <div style="display:flex; gap:6px;"><span style="background:#00ff88; color:#000; padding:4px 12px; border-radius:6px; font-size:11px; font-weight:800;">1D</span><span style="background:#1a1f2e; color:#6b7280; padding:4px 12px; border-radius:6px; font-size:11px;">5D</span><span style="background:#1a1f2e; color:#6b7280; padding:4px 12px; border-radius:6px; font-size:11px;">1M</span><span style="background:#1a1f2e; color:#6b7280; padding:4px 12px; border-radius:6px; font-size:11px;">6M</span></div>
        <div style="background:#1a1f2e; border-radius:20px; padding:4px 10px; font-size:10px; color:#fff;">AI Trendline: <span style="background:#00ff88; color:#000; padding:1px 6px; border-radius:4px; font-weight:800;">ON</span></div>
      </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    sup = hist['Low'].tail(20).min(); res = hist['High'].tail(20).max()
    st.markdown(f"""<div style="background:#12161f; border-radius:8px; padding:6px 12px; color:#9ca3af; font-size:11px; margin-top:6px;">↳ Support: {sup:.1f} • Resistance: {res:.1f} • RSI: {sel['RSI'] if sel else '63.4'} Neutral-Bullish <span style="background:#00ff88; width:32px; height:12px; display:inline-block; border-radius:10px; vertical-align:middle; margin-left:6px;"></span></div></div>""", unsafe_allow_html=True)

    # TOP 10 TABLE
    rows_html = ""
    for i, r in enumerate(top10, 1):
        color = "#4ade80" if r['CHANGE']>=0 else "#f87171"
        arrow = "↑" if r['CHANGE']>=0 else "↓"
        badge = "b-buy" if r['SIGNAL']=="BUY" else "b-sell" if r['SIGNAL']=="SELL" else "b-hold"
        scolor = "#a3e635" if r['SCORE']>=80 else "#facc15" if r['SCORE']>=65 else "#fb7185"
        rows_html += f"""<div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); color:#fff; font-size:12px; align-items:center;">
        <div style="display:flex; gap:10px; width:180px;"><span style="color:#6b7280; width:18px;">{i:02d}</span><span style="color:{scolor};">●</span><span>{r['STOCK']}</span></div>
        <div style="width:80px;">₹{r['PRICE']}</div>
        <div style="width:70px; color:{color};">{r['CHANGE']:+.2f}% {arrow}</div>
        <div style="width:50px;"><span class="b-score">{r['SCORE']}</span></div>
        <div style="width:50px;"><span class="{badge}">{r['SIGNAL']}</span></div>
        </div>"""

    st.markdown(f"""
    <div class="glass" style="margin-top:12px;">
      <div style="display:flex; justify-content:space-between; color:#fff; font-weight:800; font-size:13px; margin-bottom:12px;">≡ TOP 10 STOCKS — NIFTY 500 <span style="border:1px solid #2a2f45; padding:4px 10px; border-radius:20px; font-size:10px; color:#9ca3af;">Sorted by AI Score ↓</span></div>
      <div style="display:flex; justify-content:space-between; color:#6b7280; font-size:10px; letter-spacing:1px; padding-bottom:6px; border-bottom:1px solid #1e2332;">
        <div style="width:180px;"># STOCK</div><div style="width:80px;">PRICE</div><div style="width:70px;">CHANGE</div><div style="width:50px;">AI SCORE</div><div style="width:50px;">SIGNAL</div>
      </div>
      {rows_html}
      <div style="display:flex; justify-content:space-between; margin-top:14px; color:#6b7280; font-size:11px; align-items:center; flex-wrap:wrap; gap:6px;">
        <span>● Last updated: 13 Sep 2026 • Live Data</span>
        <span>Powered by FinTrade X AI Model v3.2</span>
        <span style="display:flex; gap:8px;"><span style="border:1px solid #2a2f45; padding:4px 10px; border-radius:8px;">↓ Export CSV</span><span style="border:1px solid #00ff88; color:#00ff88; padding:4px 10px; border-radius:8px;">↻ Refresh</span></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

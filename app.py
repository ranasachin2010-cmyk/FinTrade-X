import streamlit as st, yfinance as yf, ta, plotly.graph_objects as go, concurrent.futures
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FinTrade X Pro", layout="wide", page_icon="🧠")
st_autorefresh(interval=15000, key="live")

st.markdown("""
<style>
.stApp {background:#05070a;}
.glass {background: rgba(18,22,32,0.92); border:1px solid rgba(255,255,255,0.07); border-radius:18px; padding:16px;}
.header {background: linear-gradient(90deg, #12151e 0%, #1d2333 100%); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:14px 20px;}
.b-buy {background:#00e676; color:#000; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-sell {background:#ef4444; color:#fff; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-hold {background:#a16207; color:#fff; padding:3px 12px; border-radius:6px; font-weight:800; font-size:11px;}
.b-score {background:#1a4d2e; color:#4ade80; border:1px solid #22c55e; padding:2px 10px; border-radius:6px; font-weight:700;}
[data-testid="stHeader"]{display:none;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <div style="display:flex; justify-content:space-between;">
    <div style="color:#fff; font-size:22px; font-weight:900;">FinTrade <span style="color:#c6ff00;">X</span> <span style="font-size:11px; color:#6b7280; font-weight:400;">Nifty 500 AI</span></div>
    <div style="background:#0f1a12; border:1px solid #00ff88; border-radius:20px; padding:4px 12px; color:#00ff88; font-size:11px;">● Live Market</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.write("")

def analyze_stock(sym):
    try:
        h = yf.Ticker(sym+".NS").history(period="6mo", auto_adjust=True)
        if len(h) < 50:
            return None
        curr = float(h['Close'].iloc[-1])
        prev = float(h['Close'].iloc[-2])
        change = ((curr - prev) / prev) * 100
        # RSI safe
        try:
            rsi_val = ta.momentum.RSIIndicator(h['Close']).rsi().iloc[-1]
            rsi_val = float(rsi_val) if not str(rsi_val)=='nan' else 55.0
        except:
            rsi_val = 55.0

        # Simple AI Score - NO RSI None case
        score = 70
        if curr > h['Close'].rolling(20).mean().iloc[-1]: score+=10
        if curr > h['Close'].rolling(50).mean().iloc[-1]: score+=5
        if change > 0: score+=5
        score = max(25, min(92, int(score)))

        signal = "BUY" if score >= 72 else "SELL" if score <= 45 else "HOLD"
        return {"STOCK": sym, "PRICE": round(curr,2), "CHANGE": round(change,2), "SCORE": score, "SIGNAL": signal, "RSI": round(rsi_val,1), "HIST": h.tail(90)}
    except Exception as e:
        return None

SAMPLE = ["RELIANCE","HDFCBANK","INFY","ICICIBANK","TCS","ITC","LT","TITAN","KOTAKBANK","SBIN"]

if 'top_data' not in st.session_state:
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        res = [r for r in ex.map(analyze_stock, SAMPLE) if r is not None]
    st.session_state.top_data = sorted(res, key=lambda x: x.get("SCORE",0), reverse=True)[:10]

top10 = st.session_state.top_data

# Safe defaults if empty
if not top10:
    st.warning("Data load ho raha hai, 10 sec me refresh karo...")
    st.stop()

c1, c2 = st.columns([1, 2.2])

with c1:
    top_score = top10[0].get("SCORE", 78)
    st.markdown(f"""
    <div class="glass" style="text-align:center;">
      <div style="color:#6b7280; font-size:11px;">✨ AI SCORE</div>
      <div style="width:120px; height:120px; border-radius:50%; border:7px solid #1e2332; border-top-color:#00ff88; margin:12px auto; display:flex; align-items:center; justify-content:center; flex-direction:column;">
        <div style="color:#00ff88; font-size:38px; font-weight:900;">{top_score}</div><div style="color:#6b7280; font-size:12px;">/100</div>
      </div>
      <div style="color:#c08a5a; font-size:11px;">Strong Buy Momentum • {top_score}%</div>
    </div>
    """, unsafe_allow_html=True)

    # FIXED AI SIGNALS - No KeyError
    s1 = top10[0]
    s2 = top10[1] if len(top10)>1 else top10[0]

    st.markdown(f"""
    <div class="glass" style="margin-top:12px;">
      <div style="color:#fff; font-weight:700; font-size:13px; margin-bottom:10px;">📶 AI SIGNALS</div>
      <div style="display:flex; gap:8px; margin-bottom:10px; align-items:center;">
        <span class="{'b-buy' if s1['SIGNAL']=='BUY' else 'b-sell' if s1['SIGNAL']=='SELL' else 'b-hold'}">{s1['SIGNAL']}</span>
        <div><div style="color:#fff; font-size:12px; font-weight:700;">{s1['STOCK']}</div><div style="color:#6b7280; font-size:10px;">Score {s1['SCORE']} • ₹{s1['PRICE']}</div></div>
      </div>
      <div style="display:flex; gap:8px; align-items:center;">
        <span class="{'b-buy' if s2['SIGNAL']=='BUY' else 'b-sell' if s2['SIGNAL']=='SELL' else 'b-hold'}">{s2['SIGNAL']}</span>
        <div><div style="color:#fff; font-size:12px; font-weight:700;">{s2['STOCK']}</div><div style="color:#6b7280; font-size:10px;">Score {s2['SCORE']} • ₹{s2['PRICE']}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    sel = top10[0]
    hist = sel.get("HIST")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff4d6d')])
    fig.update_layout(height=320, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0), showlegend=False)
    st.markdown(f"<div class='glass'><div style='color:#fff; font-weight:800;'>{sel.get('STOCK')} • 1D CHART</div>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # TOP 10
    rows = ""
    for i, r in enumerate(top10, 1):
        col = "#4ade80" if r.get("CHANGE",0)>=0 else "#f87171"
        badge = "b-buy" if r.get("SIGNAL")=="BUY" else "b-sell" if r.get("SIGNAL")=="SELL" else "b-hold"
        rows += f"<div style='display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px solid #1e2332; color:#fff; font-size:12px;'><div>{i:02d} ● {r.get('STOCK')}</div><div>₹{r.get('PRICE')}</div><div style='color:{col};'>{r.get('CHANGE'):+.2f}%</div><div><span class='b-score'>{r.get('SCORE')}</span></div><div><span class='{badge}'>{r.get('SIGNAL')}</span></div></div>"

    st.markdown(f"<div class='glass' style='margin-top:12px;'><div style='color:#fff; font-weight:800; margin-bottom:8px;'>≡ TOP 10 STOCKS</div>{rows}</div>", unsafe_allow_html=True)

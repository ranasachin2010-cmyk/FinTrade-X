# pip install fastapi uvicorn yfinance pandas numpy
from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()

def detect_patterns(df):
    # df me Open, High, Low, Close hona chahiye
    patterns = []
    o, h, l, c = df['Open'].iloc[-1], df['High'].iloc[-1], df['Low'].iloc[-1], df['Close'].iloc[-1]
    body = abs(c - o)
    candle_range = h - l
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    # 1. Doji
    if body <= candle_range * 0.1:
        patterns.append({"pattern": "Doji", "signal": "Indecision", "confidence": 85})
    # 2. Hammer
    if lower_wick > body * 2 and upper_wick < body * 0.5 and candle_range > 0:
        patterns.append({"pattern": "Hammer", "signal": "Bullish Reversal", "confidence": 78})
    # 3. Bullish Engulfing (last 2 candles)
    if len(df) > 1:
        o1, c1 = df['Open'].iloc[-2], df['Close'].iloc[-2]
        if c1 < o1 and c > o and c > o1 and o < c1:
            patterns.append({"pattern": "Bullish Engulfing", "signal": "Strong Bullish", "confidence": 82})

    return patterns

@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    # NSE ke liye.NS lagao, ex: RELIANCE.NS
    ticker = yf.Ticker(symbol + ".NS" if ".NS" not in symbol else symbol)
    df = ticker.history(period="3mo", interval="1d")
    df = df.dropna()

    patterns = detect_patterns(df)

    # Support/Resistance
    recent_high = float(df['High'].tail(20).max())
    recent_low = float(df['Low'].tail(20).min())
    current_price = float(df['Close'].iloc[-1])

    return {
        "symbol": symbol,
        "price": current_price,
        "support": recent_low,
        "resistance": recent_high,
        "patterns": patterns,
        "candles": df.tail(60).reset_index().to_dict(orient="records")
    }

# Run: uvicorn app:app --reload

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd

# Auto-refresh every 60 seconds (60000 milliseconds)
st_autorefresh(interval=60000, limit=None, key="futures_autorefresh")

# Inject custom CSS for dark green and gold theme styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0B3D0B;
        color: #D4AF37;
    }
    .sidebar .sidebar-content {
        background-color: #154b14;
        color: #D4AF37;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37;
    }
    .stButton>button {
        background-color: #154b14;
        color: #D4AF37;
        border: none;
    }
    .css-1d391kg, .stMarkdown {
        color: #D4AF37;
    }
    </style>
""", unsafe_allow_html=True)

# Cache data for 60 seconds to reduce API calls.
@st.cache_data(ttl=60)
def get_data(ticker: str) -> pd.DataFrame:
    """
    Fetch historical data for the given ticker.
    Using period="2d" and interval="1m" allows us to compare the previous day’s close with today’s latest price.
    """
    try:
        df = yf.Ticker(ticker).history(period="2d", interval="1m")
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def compute_change(df: pd.DataFrame):
    """
    Computes the percentage change from the previous day's close to the latest price.
    If only one day's data is available, it computes the change from the day's open.
    Returns (change percentage, reference price, latest price)
    """
    if df.empty:
        return None, None, None

    days = sorted(set(df.index.date))
    if len(days) >= 2:
        prev_day = days[-2]
        current_day = days[-1]
        try:
            prev_close = df[df.index.date == prev_day]['Close'].iloc[-1]
            current_latest = df[df.index.date == current_day]['Close'].iloc[-1]
            change = (current_latest - prev_close) / prev_close * 100
            return change, prev_close, current_latest
        except IndexError:
            return None, None, None
    else:
        open_price = df['Close'].iloc[0]
        latest_price = df['Close'].iloc[-1]
        change = (latest_price - open_price) / open_price * 100
        return change, open_price, latest_price

def generate_chart(df: pd.DataFrame):
    """
    Displays a line chart of the 'Close' prices from the provided DataFrame.
    """
    if df.empty:
        st.write("Data not available.")
    else:
        st.line_chart(df['Close'])

def analyze_market(changes: dict):
    """
    Analyzes the futures changes to provide a prediction for market hour price movements.
    It uses simple heuristics based on:
      - Bullish sentiment: S&P 500 and Nasdaq rising with falling 10-Year Treasury yields.
      - Bearish sentiment: Broad declines in equity futures with rising volatility or safe-haven assets.
      - Defensive rotation: Stable S&P 500 but weakness in tech and small-cap futures.
      - Inflation concerns: Falling S&P 500 with rising crude oil prices and a stronger dollar.
    """
    signals = []
    es = changes.get("ES=F")
    nq = changes.get("NQ=F")
    ym = changes.get("YM=F")
    rty = changes.get("RTY=F")
    zn = changes.get("ZN=F")
    vx = changes.get("VX=F")
    cl = changes.get("CL=F")
    gc = changes.get("GC=F")
    dxy = changes.get("DX-Y.NYB")

    # Bullish scenario: ES and NQ up with falling 10-Year yields
    if es is not None and nq is not None and zn is not None:
        if es > 0 and nq > 0 and zn < 0:
            signals.append("Bullish: S&P 500 and Nasdaq rising with falling 10-Year Treasury yields indicate strong market sentiment.")

    # Bearish scenario: Broad declines in equities with rising volatility/safe-havens
    if es is not None and nq is not None and rty is not None and vx is not None and gc is not None and zn is not None:
        if es < 0 and nq < 0 and rty < 0 and (vx > 0 or gc > 0 or zn > 0):
            signals.append("Bearish: Declines across equity futures combined with rising volatility or safe-haven assets suggest a risk-off environment.")

    # Defensive rotation scenario
    if es is not None and nq is not None and rty is not None:
        if abs(es) < 0.5 and nq < 0 and rty < 0:
            signals.append("Defensive Rotation: Stable S&P 500 but weakness in Nasdaq and Russell 2000 implies investors may be shifting toward blue-chip stocks.")

    # Inflation concerns scenario
    if es is not None and cl is not None and dxy is not None:
        if es < 0 and cl > 0 and dxy > 0:
            signals.append("Inflation Concerns: A falling S&P 500 alongside rising crude oil and a stronger dollar may point to inflationary pressures.")

    if not signals:
        signals.append("No dominant signal detected; the market could trade sideways or await further catalysts.")

    return signals

def main():
    st.title("Overnight Futures Analysis Dashboard (Live Data)")
    st.markdown("This dashboard displays live overnight futures data and automatically analyzes the situation to predict near-term market movements.")

    # Define the futures tickers and their friendly names
    tickers = {
        "ES=F": "S&P 500 Futures (ES)",
        "NQ=F": "Nasdaq 100 Futures (NQ)",
        "YM=F": "Dow Jones Futures (YM)",
        "RTY=F": "Russell 2000 Futures (RTY)",
        "VX=F": "VIX Futures (VX)",
        "ZN=F": "10-Year Treasury Note Futures (ZN)",
        "ZB=F": "30-Year Bond Futures (ZB)",
        "CL=F": "Crude Oil Futures (CL)",
        "GC=F": "Gold Futures (GC)",
        "HG=F": "Copper Futures (HG)",
        "DX-Y.NYB": "U.S. Dollar Index",
        "6E=F": "Euro Futures (6E)",
        "6J=F": "Japanese Yen Futures (6J)"
    }

    # Dictionary to store each ticker's data, change, and prices.
    data_dict = {}
    changes = {}

    # Retrieve data and compute changes for each ticker
    for ticker, name in tickers.items():
        df = get_data(ticker)
        change, ref, latest = compute_change(df)
        changes[ticker] = change
        data_dict[ticker] = {
            "name": name,
            "data": df,
            "change": change,
            "ref": ref,
            "latest": latest
        }

    # Market analysis based on computed changes
    signals = analyze_market(changes)
    st.header("Market Analysis")
    for signal in signals:
        st.write(f"- {signal}")

    st.header("Overnight Futures Data")

    # --- Index Futures ---
    st.subheader("Index Futures")
    index_tickers = ["ES=F", "NQ=F", "YM=F", "RTY=F"]
    cols = st.columns(2)
    for i, ticker in enumerate(index_tickers):
        with cols[i % 2]:
            info = data_dict[ticker]
            st.markdown(f"**{info['name']}**")
            if info['change'] is not None:
                st.write(f"Change: {info['change']:.2f}%")
                st.write(f"From: {info['ref']:.2f}  →  To: {info['latest']:.2f}")
            else:
                st.write("Data unavailable")
            generate_chart(info['data'])

    # --- Volatility Futures ---
    st.subheader("Volatility Futures")
    info = data_dict["VX=F"]
    st.markdown(f"**{info['name']}**")
    if info['change'] is not None:
        st.write(f"Change: {info['change']:.2f}%")
        st.write(f"From: {info['ref']:.2f}  →  To: {info['latest']:.2f}")
    else:
        st.write("Data unavailable")
    generate_chart(info['data'])

    # --- Bond Futures ---
    st.subheader("Bond Futures")
    bond_tickers = ["ZN=F", "ZB=F"]
    cols = st.columns(2)
    for i, ticker in enumerate(bond_tickers):
        with cols[i]:
            info = data_dict[ticker]
            st.markdown(f"**{info['name']}**")
            if info['change'] is not None:
                st.write(f"Change: {info['change']:.2f}%")
                st.write(f"From: {info['ref']:.2f}  →  To: {info['latest']:.2f}")
            else:
                st.write("Data unavailable")
            generate_chart(info['data'])

    # --- Commodity Futures ---
    st.subheader("Commodity Futures")
    commodity_tickers = ["CL=F", "GC=F", "HG=F"]
    cols = st.columns(3)
    for i, ticker in enumerate(commodity_tickers):
        with cols[i]:
            info = data_dict[ticker]
            st.markdown(f"**{info['name']}**")
            if info['change'] is not None:
                st.write(f"Change: {info['change']:.2f}%")
                st.write(f"From: {info['ref']:.2f}  →  To: {info['latest']:.2f}")
            else:
                st.write("Data unavailable")
            generate_chart(info['data'])

    # --- Currency Futures ---
    st.subheader("Currency Futures")
    currency_tickers = ["DX-Y.NYB", "6E=F", "6J=F"]
    cols = st.columns(3)
    for i, ticker in enumerate(currency_tickers):
        with cols[i]:
            info = data_dict[ticker]
            st.markdown(f"**{info['name']}**")
            if info['change'] is not None:
                st.write(f"Change: {info['change']:.2f}%")
                st.write(f"From: {info['ref']:.2f}  →  To: {info['latest']:.2f}")
            else:
                st.write("Data unavailable")
            generate_chart(info['data'])

if __name__ == "__main__":
    main()

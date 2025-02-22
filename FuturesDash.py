import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd

# Auto-refresh the app every 60 seconds (60000 milliseconds)
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

# Cache data for 60 seconds to reduce API calls
@st.cache_data(ttl=60)
def get_data(ticker: str) -> pd.DataFrame:
    """
    Fetch historical data for the given ticker for the current trading day with 1-minute intervals.
    """
    try:
        df = yf.Ticker(ticker).history(period="1d", interval="1m")
        if df.empty:
            st.warning(f"No data returned for {ticker}.")
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def display_future(title: str, ticker: str, description: str):
    """
    Display a subheader, description, latest price, and a line chart for the futures ticker.
    """
    st.subheader(title)
    if description:
        st.write(description)
    data = get_data(ticker)
    if not data.empty:
        latest_price = data['Close'].iloc[-1]
        st.write(f"**Latest Price:** {latest_price:.2f}")
        st.line_chart(data['Close'])
    else:
        st.write("Data not available.")

def main():
    st.title("Overnight Futures Movement Dashboard (Live Data)")
    st.markdown(
        """
        This dashboard examines overnight futures movements using live data from Yahoo Finance.
        The app auto-refreshes every minute so you can see up-to-date price movements.
        """
    )
    
    st.sidebar.header("Select Futures Category")
    category = st.sidebar.selectbox(
        "Futures Category",
        ["Index Futures", "Volatility Futures", "Bond Futures", "Commodity Futures", "Currency Futures"]
    )
    
    if category == "Index Futures":
        st.header("Index Futures (Equity Market Sentiment)")
        display_future(
            "S&P 500 Futures (ES)",
            "ES=F",
            "Primary indicator for U.S. large-cap stocks. Reflects market sentiment overnight before the SPX cash opens."
        )
        display_future(
            "Nasdaq 100 Futures (NQ)",
            "NQ=F",
            "Tech-heavy index gauging the sentiment of growth stocks. A drop in NQ relative to ES could indicate a tech-led sell-off, whereas better performance may suggest rotation into tech stocks."
        )
        display_future(
            "Dow Jones Futures (YM)",
            "YM=F",
            "Reflects industrials and blue-chip stocks. Typically less volatile than the Nasdaq and useful for spotting rotations into defensive stocks."
        )
        display_future(
            "Russell 2000 Futures (RTY)",
            "RTY=F",
            "Tracks small-cap stocks—great for measuring risk appetite. A drop in RTY while ES remains stable signals rising risk aversion; an upward move suggests speculative sentiment."
        )
    
    elif category == "Volatility Futures":
        st.header("Volatility Futures (Fear & IV Sentiment)")
        display_future(
            "VIX Futures (VX)",
            "VX=F",
            "Tracks the implied volatility of SPX options. A spike in VIX may signal market turbulence and increased implied volatility, while flat or declining VIX in a weak market may indicate a controlled sell-off."
        )
    
    elif category == "Bond Futures":
        st.header("Bond Futures (Interest Rate & Macro Risk)")
        display_future(
            "10-Year Treasury Note Futures (ZN)",
            "ZN=F",
            "If ZN rises (yields falling), it suggests a flight to safety (bearish for stocks). Conversely, falling ZN (rising yields) may hurt growth stocks."
        )
        display_future(
            "30-Year Bond Futures (ZB)",
            "ZB=F",
            "Similar to ZN but reflects long-term rates. A rising ZB suggests a risk-off environment as investors move into bonds."
        )
    
    elif category == "Commodity Futures":
        st.header("Commodity Futures (Inflation & Macro Trends)")
        display_future(
            "Crude Oil Futures (CL)",
            "CL=F",
            "Strongly correlated with economic activity and inflation. Rising oil prices can indicate inflation fears and higher energy costs, while falling prices may signal weak demand."
        )
        display_future(
            "Gold Futures (GC)",
            "GC=F",
            "A safe-haven asset that typically rises when markets fear uncertainty. A surge in gold during equity declines indicates a risk-off sentiment."
        )
        display_future(
            "Copper Futures (HG)",
            "HG=F",
            "A leading indicator of economic growth, particularly in manufacturing. Declining copper prices can signal fears of a global economic slowdown."
        )
    
    elif category == "Currency Futures":
        st.header("Currency Futures (Global Market Influence)")
        display_future(
            "U.S. Dollar Index",
            "DX-Y.NYB",
            "A rising dollar may pressure equities and other risk assets, while a weakening dollar supports stocks, commodities, and emerging markets."
        )
        st.subheader("Euro & Japanese Yen Futures")
        st.write(
            "**Euro Futures (6E):** Euro strength often signifies a risk-on environment.\n\n"
            "**Japanese Yen Futures (6J):** Yen strength can suggest risk-off sentiment; spikes in yen futures may indicate a flight to safety."
        )
        col1, col2 = st.columns(2)
        with col1:
            display_future("Euro Futures (6E)", "6E=F", "")
        with col2:
            display_future("Japanese Yen Futures (6J)", "6J=F", "")
    
    st.markdown("## How to Use These Futures Together")
    st.write(
        """
        1. **Bullish Scenario:** If S&P 500 and Nasdaq 100 futures are rising while 10-Year Treasury futures fall, it is bullish for stocks.  
        2. **Risk-Off Scenario:** If S&P 500, Nasdaq 100, and Russell 2000 futures all drop while VIX, Gold, and 10-Year Treasury futures rise, it signals a risk-off sentiment.  
        3. **Defensive Rotation:** If the S&P 500 is stable but the Nasdaq 100 and Russell 2000 are weak, investors may be rotating into blue chips.  
        4. **Inflation Concerns:** If Crude Oil and the U.S. Dollar Index are rising while the S&P 500 falls, inflation fears may be pressuring the market.
        """
    )

if __name__ == "__main__":
    main()

import yfinance as yf
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# Top 20 Nifty stocks
STOCKS = [
    "^NSEI",          # Nifty 50 Index
    "RELIANCE.NS",    # Reliance
    "TCS.NS",         # TCS
    "HDFCBANK.NS",    # HDFC Bank
    "INFY.NS",        # Infosys
    "ICICIBANK.NS",   # ICICI Bank
    "HINDUNILVR.NS",  # HUL
    "SBIN.NS",        # SBI
    "BHARTIARTL.NS",  # Airtel
    "BAJFINANCE.NS",  # Bajaj Finance
    "WIPRO.NS",       # Wipro
    "ADANIENT.NS",    # Adani Enterprises
    "TATASTEEL.NS",  # TATASTEEL
    "MARUTI.NS",      # Maruti
    "SUNPHARMA.NS",   # Sun Pharma
    "AXISBANK.NS",    # Axis Bank
    "KOTAKBANK.NS",   # Kotak Bank
    "LT.NS",          # L&T
    "TITAN.NS",       # Titan
    "ONGC.NS",        # ONGC
]

# Store previous prices to detect movement
previous_prices = {}

def fetch_prices():
    print(f"\n🔄 Fetching prices at {datetime.now().strftime('%H:%M:%S')}...")
    
    for symbol in STOCKS:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.fast_info
            current_price = data.last_price

            if current_price is None:
                print(f"⚠️ No price for {symbol}")
                continue

            print(f"📈 {symbol}: ₹{current_price:.2f}")

            # Check for >0.5% movement
            if symbol in previous_prices:
                prev = previous_prices[symbol]
                change_pct = ((current_price - prev) / prev) * 100

                if abs(change_pct) >= 0.5:
                    direction = "🔺 UP" if change_pct > 0 else "🔻 DOWN"
                    print(f"🚨 SIGNAL! {symbol} moved {change_pct:.2f}% {direction}")

                    # Save signal to Supabase
                    supabase.table("signals").insert({
                        "symbol": symbol,
                        "signal_type": "PRICE_MOVE",
                        "confidence": min(abs(change_pct) / 5, 1.0),
                        "source": "yfinance",
                        "message": f"{symbol} moved {change_pct:.2f}% {direction}"
                    }).execute()

            previous_prices[symbol] = current_price

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")

if __name__ == "__main__":
    print("🚀 MoneyVeda Price Fetcher Started!")
    fetch_prices()
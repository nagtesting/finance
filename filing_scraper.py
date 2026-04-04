from nse import NSE
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

NSE_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "BAJFINANCE", "WIPRO",
    "ADANIENT", "TATASTEEL", "MARUTI", "SUNPHARMA", "AXISBANK",
    "KOTAKBANK", "LT", "TITAN", "ONGC"
]

def run_scraper():
    print(f"\n📰 Scraping NSE filings at {datetime.now().strftime('%H:%M:%S')}...")

    with NSE(download_folder=Path("./")) as nse:
        for symbol in NSE_SYMBOLS:
            try:
                # Get corporate announcements
                announcements = nse.announcements(symbol=symbol)

                if not announcements:
                    print(f"⚠️ No announcements for {symbol}")
                    continue

                # Process latest 3
                for ann in announcements[:3]:
                    headline = ann.get("desc", ann.get("subject", "No headline"))
                    date = ann.get("an_dt", "")
                    category = ann.get("attchmntType", "General")

                    print(f"📋 {symbol}: {headline[:60]}...")

                    supabase.table("filings").insert({
                        "symbol": symbol,
                        "source": "NSE",
                        "headline": headline,
                        "category": category,
                        "filing_date": date,
                        "raw_data": str(ann)
                    }).execute()

            except Exception as e:
                print(f"❌ Error for {symbol}: {e}")

    print("✅ Scraping complete!")

if __name__ == "__main__":
    run_scraper()
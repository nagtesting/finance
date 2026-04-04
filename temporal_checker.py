from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# Time window — filing and price move must be within 2 hours
CORRELATION_WINDOW_HOURS = 2

def check_temporal_correlation():
    print(f"\n⏱️ Temporal Correlation Checker running at {datetime.now().strftime('%H:%M:%S')}...")

    # Get recent signals from signal engine
    signals = supabase.table("signals")\
        .select("*")\
        .eq("source", "signal_engine")\
        .limit(50)\
        .execute().data

    # Get recent price move signals
    price_signals = supabase.table("signals")\
        .select("*")\
        .eq("source", "yfinance")\
        .limit(50)\
        .execute().data

    if not signals:
        print("⚠️ No signals found!")
        return

    print(f"📊 Checking {len(signals)} filing signals against {len(price_signals)} price signals...\n")

    correlated = 0
    not_correlated = 0

    for signal in signals:
        symbol = signal["symbol"]
        signal_time = signal["created_at"]

        # Find matching price signal for same symbol
        matching_price = [
            p for p in price_signals
            if p["symbol"].replace(".NS", "") == symbol
        ]

        if not matching_price:
            # No price move detected — lower confidence
            supabase.table("signals").update({
                "confidence": round(signal["confidence"] * 0.5, 3),
                "message": signal["message"] + " | NO_PRICE_CORRELATION"
            }).eq("id", signal["id"]).execute()
            not_correlated += 1
            continue

        # Check time difference
        try:
            t1 = datetime.fromisoformat(signal_time.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(
                matching_price[0]["created_at"].replace("Z", "+00:00")
            )
            diff_hours = abs((t1 - t2).total_seconds() / 3600)

            if diff_hours <= CORRELATION_WINDOW_HOURS:
                # Correlated! Boost confidence
                new_confidence = min(signal["confidence"] * 1.5, 1.0)
                supabase.table("signals").update({
                    "confidence": round(new_confidence, 3),
                    "message": signal["message"] + " | PRICE_CORRELATED ✅"
                }).eq("id", signal["id"]).execute()

                print(f"✅ CORRELATED: {symbol}")
                print(f"   ⏱️ Time gap: {diff_hours:.1f} hours")
                print(f"   💯 Confidence boosted to: {new_confidence:.0%}\n")
                correlated += 1
            else:
                # Too far apart — reduce confidence
                new_confidence = round(signal["confidence"] * 0.7, 3)
                supabase.table("signals").update({
                    "confidence": new_confidence,
                    "message": signal["message"] + f" | TIME_GAP_{diff_hours:.0f}H"
                }).eq("id", signal["id"]).execute()
                not_correlated += 1

        except Exception as e:
            print(f"❌ Time parse error for {symbol}: {e}")

    print(f"✅ Temporal check complete!")
    print(f"   ✅ Correlated: {correlated}")
    print(f"   ⚠️ Not correlated: {not_correlated}")

if __name__ == "__main__":
    check_temporal_correlation()
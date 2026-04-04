from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# Signal scoring weights
WEIGHTS = {
    "price_move": 0.4,      # 40% weight
    "sentiment": 0.35,      # 35% weight
    "filing_category": 0.25 # 25% weight
}

# High impact filing categories
HIGH_IMPACT_CATEGORIES = [
    "Acquisition", "Amalgamation/Merger", "Change in Management",
    "Issue of Securities", "Scheme of Arrangement", "Record Date",
    "Bagging/Receiving of orders/contracts", "Press Release"
]

LOW_IMPACT_CATEGORIES = [
    "Trading Window", "General Updates", "Updates",
    "Certificate under SEBI"
]

def get_filing_impact(category):
    if any(h in category for h in HIGH_IMPACT_CATEGORIES):
        return 1.0
    elif any(l in category for l in LOW_IMPACT_CATEGORIES):
        return 0.1
    return 0.5

def get_sentiment_score(sentiment, sentiment_score):
    if sentiment == "positive":
        return sentiment_score
    elif sentiment == "negative":
        return -sentiment_score
    return 0.0

def generate_signals():
    print(f"\n🧠 Signal Fusion Engine running at {datetime.now().strftime('%H:%M:%S')}...")

    # Get recent filings with sentiment
    result = supabase.table("filings")\
        .select("*")\
        .not_.is_("sentiment", "null")\
        .limit(50)\
        .execute()

    filings = result.data

    if not filings:
        print("⚠️ No analyzed filings found!")
        return

    print(f"📋 Processing {len(filings)} filings...\n")

    signals_generated = 0

    for filing in filings:
        symbol = filing["symbol"]
        headline = filing["headline"]
        category = filing.get("category", "")
        sentiment = filing.get("sentiment", "neutral")
        sentiment_score = filing.get("sentiment_score", 0.5)

        # Calculate scores
        filing_impact = get_filing_impact(category)
        sentiment_value = get_sentiment_score(sentiment, sentiment_score)

        # Combined confidence score
        confidence = (
            WEIGHTS["sentiment"] * abs(sentiment_value) +
            WEIGHTS["filing_category"] * filing_impact
        )

        # Determine signal type
        if filing_impact >= 0.8:
            if sentiment_value >= 0:
                signal_type = "BULLISH"
                emoji = "🟢"
            else:
                signal_type = "BEARISH"
                emoji = "🔴"
        elif filing_impact >= 0.5:
            signal_type = "WATCH"
            emoji = "🟡"
        else:
            signal_type = "NEUTRAL"
            emoji = "⚪"

        # Only save meaningful signals
        if signal_type in ["BULLISH", "BEARISH", "WATCH"]:
            print(f"{emoji} {symbol}: {signal_type}")
            print(f"   📋 Filing: {headline[:50]}...")
            print(f"   📊 Category impact: {filing_impact:.0%}")
            print(f"   🤖 Sentiment: {sentiment} ({sentiment_score:.0%})")
            print(f"   💯 Confidence: {confidence:.0%}\n")

            # Save signal to Supabase
            supabase.table("signals").insert({
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": round(confidence, 3),
                "source": "signal_engine",
                "message": f"{signal_type}: {headline[:100]} | Category: {category} | Sentiment: {sentiment}"
            }).execute()

            signals_generated += 1

    print(f"✅ Signal engine complete! Generated {signals_generated} signals.")

if __name__ == "__main__":
    generate_signals()
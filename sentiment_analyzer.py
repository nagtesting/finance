from transformers import pipeline
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

print("🤖 Loading FinBERT model... (first time takes 2-3 mins to download)")

# Load FinBERT - financial sentiment AI model
sentiment_pipeline = pipeline(
    "text-classification",
    model="ProsusAI/finbert"
)

print("✅ FinBERT loaded!")

def analyze_sentiment(text):
    try:
        result = sentiment_pipeline(text[:512])[0]
        label = result["label"]   # positive / negative / neutral
        score = result["score"]   # confidence 0.0 to 1.0
        return label, score
    except Exception as e:
        print(f"❌ Sentiment error: {e}")
        return "neutral", 0.5

def run_sentiment_analysis():
    print("\n🔍 Fetching filings from Supabase...")

    # Get filings that haven't been analyzed yet
    result = supabase.table("filings")\
        .select("*")\
        .is_("sentiment", "null")\
        .limit(20)\
        .execute()

    filings = result.data

    if not filings:
        print("⚠️ No filings to analyze!")
        return

    print(f"📋 Analyzing {len(filings)} filings...\n")

    for filing in filings:
        headline = filing["headline"]
        label, score = analyze_sentiment(headline)

        emoji = "😊" if label == "positive" else "😟" if label == "negative" else "😐"
        print(f"{emoji} {filing['symbol']}: {headline[:50]}...")
        print(f"   → {label.upper()} ({score:.2%} confidence)\n")

        # Save sentiment back to Supabase
        supabase.table("filings").update({
            "sentiment": label,
            "sentiment_score": score
        }).eq("id", filing["id"]).execute()

    print("✅ Sentiment analysis complete!")

if __name__ == "__main__":
    run_sentiment_analysis()
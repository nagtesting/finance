from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

# Confidence thresholds
PUBLISH_THRESHOLD = 0.70    # Above this → publish
REVIEW_THRESHOLD = 0.40     # Above this → queue for review
# Below 0.40 → discard

def run_publishing_gate():
    print(f"\n🚦 Publishing Gate running at {datetime.now().strftime('%H:%M:%S')}...")

    # Get all unprocessed signals
    result = supabase.table("signals")\
        .select("*")\
        .not_.like("message", "%PUBLISHED%")\
        .not_.like("message", "%QUEUED%")\
        .not_.like("message", "%DISCARDED%")\
        .limit(100)\
        .execute()

    signals = result.data

    if not signals:
        print("⚠️ No new signals to process!")
        return

    print(f"📊 Processing {len(signals)} signals...\n")

    published = 0
    queued = 0
    discarded = 0

    for signal in signals:
        symbol = signal["symbol"]
        confidence = signal["confidence"] or 0
        signal_type = signal["signal_type"]
        message = signal["message"] or ""

        if confidence >= PUBLISH_THRESHOLD:
            # ✅ PUBLISH
            status = "PUBLISHED"
            emoji = "✅"
            published += 1

        elif confidence >= REVIEW_THRESHOLD:
            # 🟡 QUEUE
            status = "QUEUED"
            emoji = "🟡"
            queued += 1

        else:
            # ❌ DISCARD
            status = "DISCARDED"
            emoji = "❌"
            discarded += 1

        print(f"{emoji} {symbol}: {signal_type} ({confidence:.0%}) → {status}")

        # Update signal status in Supabase
        supabase.table("signals").update({
            "message": message + f" | {status}",
            "confidence": confidence
        }).eq("id", signal["id"]).execute()

    print(f"\n📊 Publishing Gate Summary:")
    print(f"   ✅ Published:  {published}")
    print(f"   🟡 Queued:     {queued}")
    print(f"   ❌ Discarded:  {discarded}")
    print(f"\n✅ Publishing gate complete!")

if __name__ == "__main__":
    run_publishing_gate()
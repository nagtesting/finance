import sys
from datetime import datetime, timezone
from supabase import create_client

def get_verified_daily_token():
    """
    Ensures the token in Supabase was updated today.
    Prevents the script from recycling yesterday's expired session credentials.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    
    # Query your tracking session record
    response = supabase.table("api_sessions").select("session_token, updated_at").eq("id", "icici_breeze").execute()
    
    if not response.data:
        raise Exception("Database configuration target missing row entry.")
        
    record = response.data[0]
    token = record["session_token"]
    updated_at_str = record["updated_at"]
    
    # Parse the timestamp safely to match global synchronization layers
    # (Supabase stores timestamps in ISO string formats with UTC designations)
    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
    today_utc = datetime.now(timezone.utc).date()
    
    if updated_at.date() < today_utc:
        # The script halts safely because it caught an old token from a previous date
        print("⚠️ [Stall Alert]: The token found in Supabase is from a past trading session.")
        print("⏭️ Render automated pre-market loop suspended. Awaiting phone manual sync activation...")
        sys.exit(0) # Exits cleanly with zero so your Render failure emails don't trigger unnecessarily
        
    return token

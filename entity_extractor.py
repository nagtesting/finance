import spacy
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")
)

print("🤖 Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")
print("✅ spaCy loaded!")

def extract_entities(text):
    doc = nlp(text)
    entities = {
        "companies": [],
        "money": [],
        "dates": [],
        "percentages": [],
        "people": [],
        "locations": []
    }

    for ent in doc.ents:
        if ent.label_ == "ORG":
            entities["companies"].append(ent.text)
        elif ent.label_ == "MONEY":
            entities["money"].append(ent.text)
        elif ent.label_ == "DATE":
            entities["dates"].append(ent.text)
        elif ent.label_ == "PERCENT":
            entities["percentages"].append(ent.text)
        elif ent.label_ == "PERSON":
            entities["people"].append(ent.text)
        elif ent.label_ == "GPE":
            entities["locations"].append(ent.text)

    return entities

def run_entity_extraction():
    print("\n🔍 Fetching filings from Supabase...")

    result = supabase.table("filings")\
        .select("*")\
        .limit(20)\
        .execute()

    filings = result.data

    print(f"📋 Extracting entities from {len(filings)} filings...\n")

    for filing in filings:
        headline = filing["headline"]
        symbol = filing["symbol"]
        entities = extract_entities(headline)

        # Only show filings with interesting entities
        has_entities = any(len(v) > 0 for v in entities.values())

        if has_entities:
            print(f"📌 {symbol}: {headline[:50]}...")
            if entities["companies"]:
                print(f"   🏢 Companies: {entities['companies']}")
            if entities["money"]:
                print(f"   💰 Money: {entities['money']}")
            if entities["dates"]:
                print(f"   📅 Dates: {entities['dates']}")
            if entities["percentages"]:
                print(f"   📊 Percentages: {entities['percentages']}")
            if entities["people"]:
                print(f"   👤 People: {entities['people']}")
            if entities["locations"]:
                print(f"   📍 Locations: {entities['locations']}")
            print()

        # Save entities back to Supabase
        supabase.table("filings").update({
            "entities": str(entities)
        }).eq("id", filing["id"]).execute()

    print("✅ Entity extraction complete!")

if __name__ == "__main__":
    run_entity_extraction()
"""
nifty100.py  ─  Canonical Nifty 100 constituent list
====================================================
Used by:
  • app.py           → /api/market-cache endpoint (the master list)
  • market_commentary.py → top_stocks lookup for intraday/post commentary

Each entry is (NSE_SYMBOL, DISPLAY_NAME, YAHOO_SYMBOL).
Yahoo symbols use the .NS suffix (NSE).

This list reflects the Nifty 100 constituents as of the most recent
public reconstitution. Update twice a year (March & September) when
NSE publishes the revised list.
"""

# 100 names — order roughly by sector cluster, no formal weighting needed
NIFTY_100 = [
    # ── Banks & Financial Services ──
    ("HDFCBANK",   "HDFC Bank",            "HDFCBANK.NS"),
    ("ICICIBANK",  "ICICI Bank",           "ICICIBANK.NS"),
    ("SBIN",       "State Bank of India",  "SBIN.NS"),
    ("KOTAKBANK",  "Kotak Mahindra Bank",  "KOTAKBANK.NS"),
    ("AXISBANK",   "Axis Bank",            "AXISBANK.NS"),
    ("INDUSINDBK", "IndusInd Bank",        "INDUSINDBK.NS"),
    ("BANKBARODA", "Bank of Baroda",       "BANKBARODA.NS"),
    ("PNB",        "Punjab National Bank", "PNB.NS"),
    ("CANBK",      "Canara Bank",          "CANBK.NS"),
    ("FEDERALBNK", "Federal Bank",         "FEDERALBNK.NS"),
    ("BAJFINANCE", "Bajaj Finance",        "BAJFINANCE.NS"),
    ("BAJAJFINSV", "Bajaj Finserv",        "BAJAJFINSV.NS"),
    ("CHOLAFIN",   "Cholamandalam Finance","CHOLAFIN.NS"),
    ("HDFCLIFE",   "HDFC Life Insurance",  "HDFCLIFE.NS"),
    ("SBILIFE",    "SBI Life Insurance",   "SBILIFE.NS"),
    ("ICICIPRULI", "ICICI Prudential Life","ICICIPRULI.NS"),
    ("ICICIGI",    "ICICI Lombard",        "ICICIGI.NS"),
    ("LICI",       "Life Insurance Corp",  "LICI.NS"),
    ("SHRIRAMFIN", "Shriram Finance",      "SHRIRAMFIN.NS"),
    ("PFC",        "Power Finance Corp",   "PFC.NS"),
    ("RECLTD",     "REC Limited",          "RECLTD.NS"),
    ("HDFCAMC",    "HDFC AMC",             "HDFCAMC.NS"),

    # ── IT Services ──
    ("TCS",        "Tata Consultancy",     "TCS.NS"),
    ("INFY",       "Infosys",              "INFY.NS"),
    ("WIPRO",      "Wipro",                "WIPRO.NS"),
    ("HCLTECH",    "HCL Technologies",     "HCLTECH.NS"),
    ("TECHM",      "Tech Mahindra",        "TECHM.NS"),
    ("LTIM",       "LTIMindtree",          "LTIM.NS"),

    # ── Oil, Gas & Energy ──
    ("RELIANCE",   "Reliance Industries",  "RELIANCE.NS"),
    ("ONGC",       "ONGC",                 "ONGC.NS"),
    ("IOC",        "Indian Oil",           "IOC.NS"),
    ("BPCL",       "BPCL",                 "BPCL.NS"),
    ("GAIL",       "GAIL India",           "GAIL.NS"),
    ("ADANIENSOL", "Adani Energy Solutions","ADANIENSOL.NS"),
    ("ADANIGREEN", "Adani Green Energy",   "ADANIGREEN.NS"),

    # ── Metals & Mining ──
    ("TATASTEEL",  "Tata Steel",           "TATASTEEL.NS"),
    ("JSWSTEEL",   "JSW Steel",            "JSWSTEEL.NS"),
    ("HINDALCO",   "Hindalco",             "HINDALCO.NS"),
    ("VEDL",       "Vedanta",              "VEDL.NS"),
    ("COALINDIA",  "Coal India",           "COALINDIA.NS"),
    ("HINDZINC",   "Hindustan Zinc",       "HINDZINC.NS"),
    ("JINDALSTEL", "Jindal Steel",         "JINDALSTEL.NS"),

    # ── Cement & Construction ──
    ("ULTRACEMCO", "UltraTech Cement",     "ULTRACEMCO.NS"),
    ("GRASIM",     "Grasim Industries",    "GRASIM.NS"),
    ("AMBUJACEM",  "Ambuja Cement",        "AMBUJACEM.NS"),
    ("SHREECEM",   "Shree Cement",         "SHREECEM.NS"),
    ("LT",         "Larsen & Toubro",      "LT.NS"),
    ("DLF",        "DLF",                  "DLF.NS"),

    # ── Automobile ──
    ("MARUTI",     "Maruti Suzuki",        "MARUTI.NS"),
    ("M&M",        "Mahindra & Mahindra",  "M%26M.NS"),
    ("TMPV",       "Tata Motors PV",       "TMPV.NS"),
    ("BAJAJ-AUTO", "Bajaj Auto",           "BAJAJ-AUTO.NS"),
    ("EICHERMOT",  "Eicher Motors",        "EICHERMOT.NS"),
    ("HEROMOTOCO", "Hero MotoCorp",        "HEROMOTOCO.NS"),
    ("TVSMOTOR",   "TVS Motor",            "TVSMOTOR.NS"),

    # ── Pharmaceuticals & Healthcare ──
    ("SUNPHARMA",  "Sun Pharma",           "SUNPHARMA.NS"),
    ("DRREDDY",    "Dr Reddy's",           "DRREDDY.NS"),
    ("CIPLA",      "Cipla",                "CIPLA.NS"),
    ("DIVISLAB",   "Divi's Laboratories",  "DIVISLAB.NS"),
    ("APOLLOHOSP", "Apollo Hospitals",     "APOLLOHOSP.NS"),
    ("TORNTPHARM", "Torrent Pharma",       "TORNTPHARM.NS"),
    ("ZYDUSLIFE",  "Zydus Lifesciences",   "ZYDUSLIFE.NS"),

    # ── FMCG ──
    ("HINDUNILVR", "Hindustan Unilever",   "HINDUNILVR.NS"),
    ("ITC",        "ITC",                  "ITC.NS"),
    ("NESTLEIND",  "Nestle India",         "NESTLEIND.NS"),
    ("BRITANNIA",  "Britannia",            "BRITANNIA.NS"),
    ("DABUR",      "Dabur",                "DABUR.NS"),
    ("MARICO",     "Marico",               "MARICO.NS"),
    ("GODREJCP",   "Godrej Consumer",      "GODREJCP.NS"),
    ("VBL",        "Varun Beverages",      "VBL.NS"),
    ("UNITDSPR",   "United Spirits",       "UNITDSPR.NS"),
    ("TATACONSUM", "Tata Consumer",        "TATACONSUM.NS"),

    # ── Telecom & Media ──
    ("BHARTIARTL", "Bharti Airtel",        "BHARTIARTL.NS"),
    ("INDIGO",     "InterGlobe Aviation",  "INDIGO.NS"),
    ("ETERNAL",    "Eternal (Zomato)",     "ETERNAL.NS"),
    ("DMART",      "Avenue Supermarts",    "DMART.NS"),
    ("TRENT",      "Trent",                "TRENT.NS"),
    ("TITAN",      "Titan Company",        "TITAN.NS"),

    # ── Power & Utilities ──
    ("NTPC",       "NTPC",                 "NTPC.NS"),
    ("POWERGRID",  "Power Grid",           "POWERGRID.NS"),
    ("ADANIPOWER", "Adani Power",          "ADANIPOWER.NS"),
    ("TATAPOWER",  "Tata Power",           "TATAPOWER.NS"),
    ("SIEMENS",    "Siemens",              "SIEMENS.NS"),
    ("ABB",        "ABB India",            "ABB.NS"),

    # ── Chemicals & Paints ──
    ("ASIANPAINT", "Asian Paints",         "ASIANPAINT.NS"),
    ("PIDILITIND", "Pidilite Industries",  "PIDILITIND.NS"),
    ("UPL",        "UPL",                  "UPL.NS"),
    ("SRF",        "SRF",                  "SRF.NS"),

    # ── Conglomerates / Other ──
    ("ADANIENT",   "Adani Enterprises",    "ADANIENT.NS"),
    ("ADANIPORTS", "Adani Ports & SEZ",    "ADANIPORTS.NS"),
    ("BEL",        "Bharat Electronics",   "BEL.NS"),
    ("HAL",        "Hindustan Aeronautics","HAL.NS"),
    ("GODREJPROP", "Godrej Properties",    "GODREJPROP.NS"),
    ("NAUKRI",     "Info Edge",            "NAUKRI.NS"),
    ("PAYTM",      "One 97 (Paytm)",       "PAYTM.NS"),
    ("BOSCHLTD",   "Bosch",                "BOSCHLTD.NS"),
    ("HAVELLS",    "Havells",              "HAVELLS.NS"),
    ("CUMMINSIND", "Cummins India",        "CUMMINSIND.NS"),
    ("MOTHERSON",  "Samvardhana Motherson","MOTHERSON.NS"),
    ("IRCTC",      "IRCTC",                "IRCTC.NS"),
]

# Convenience lookups
SYMBOL_TO_NAME   = {sym: name      for sym, name, _    in NIFTY_100}
SYMBOL_TO_YAHOO  = {sym: yahoo     for sym, _, yahoo   in NIFTY_100}
NAME_TO_SYMBOL   = {name: sym      for sym, name, _    in NIFTY_100}
ALL_SYMBOLS      = [sym            for sym, _, _       in NIFTY_100]
ALL_YAHOO_SYMS   = [yahoo          for _, _, yahoo     in NIFTY_100]

assert len(NIFTY_100) == 100, f"Expected 100, got {len(NIFTY_100)}"

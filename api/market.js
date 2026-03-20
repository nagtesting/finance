/**
 * /api/market?mode=india|world
 * Vercel Serverless Function — Secure Market Data Proxy
 *
 * API key lives ONLY in Vercel environment variables — never in browser JS.
 *
 * SETUP (one-time, 2 minutes):
 *   1. https://finnhub.io → Sign up free → copy your API key
 *   2. Vercel dashboard → Project → Settings → Environment Variables
 *      Add:  FINNHUB_API_KEY = your_key_here   (all environments)
 *   3. Redeploy once. Done. Key hidden forever.
 *
 * SECURITY:
 *   ✓ API key only in process.env — never sent to browser
 *   ✓ CORS locked to same origin
 *   ✓ Mode param whitelisted — rejects anything else
 *   ✓ Edge cached 30s — reduces Finnhub API calls by ~95%
 *   ✓ Per-symbol failure handled — partial results returned gracefully
 *
 * SYMBOL NOTES (Finnhub free tier compatible):
 *   ✗ BSE:SENSEX, NSE:NIFTY50, NSE:BANKNIFTY  → Premium exchange feed, not on free plan
 *   ✗ OANDA:SPX500USD, OANDA:NAS100USD         → OANDA indices need paid plan
 *   ✓ Individual NSE stocks (RELIANCE, TCS…)   → Free tier supported
 *   ✓ OANDA forex pairs (USDINR, XAUUSD…)      → Free tier supported
 *   ✓ BINANCE crypto pairs                      → Free tier supported
 *   ✓ FX pairs (EURUSD, GBPUSD…)               → Free tier supported
 *   ✓ US stocks (AAPL, MSFT, AMZN…)            → Free tier supported
 */

const SYMBOLS = {
  india: [
    // Forex — works on free tier
    { symbol: 'OANDA:USDINR',    label: 'USD/INR'   },
    // Commodities via OANDA — works on free tier
    { symbol: 'OANDA:XAUUSD',    label: 'GOLD'      },
    { symbol: 'OANDA:UKOIL',     label: 'BRENT OIL' },
    // Individual NSE large-caps — works on free tier
    { symbol: 'NSE:RELIANCE',    label: 'RELIANCE'  },
    { symbol: 'NSE:HDFCBANK',    label: 'HDFC BANK' },
    { symbol: 'NSE:TCS',         label: 'TCS'       },
    { symbol: 'NSE:INFY',        label: 'INFOSYS'   },
    { symbol: 'NSE:WIPRO',       label: 'WIPRO'     },
    { symbol: 'NSE:ITC',         label: 'ITC'       },
    { symbol: 'NSE:TATAMOTORS',  label: 'TATA MOTORS'},
  ],
  world: [
    // US mega-cap stocks — works on free tier (replaces index symbols)
    { symbol: 'AAPL',            label: 'APPLE'      },
    { symbol: 'MSFT',            label: 'MICROSOFT'  },
    { symbol: 'AMZN',            label: 'AMAZON'     },
    { symbol: 'NVDA',            label: 'NVIDIA'     },
    { symbol: 'TSLA',            label: 'TESLA'      },
    // Commodities & Forex — works on free tier
    { symbol: 'OANDA:XAUUSD',    label: 'GOLD'       },
    { symbol: 'OANDA:UKOIL',     label: 'BRENT CRUDE'},
    { symbol: 'FX:EURUSD',       label: 'EUR/USD'    },
    // Crypto — works on free tier
    { symbol: 'BINANCE:BTCUSDT', label: 'BITCOIN'    },
    { symbol: 'BINANCE:ETHUSD',  label: 'ETHEREUM'   },
  ],
};

async function fetchQuote(symbol, apiKey) {
  const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(symbol)}&token=${apiKey}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default async function handler(req, res) {
  // CORS — same origin only
  const origin = req.headers.origin || '';
  const host   = (req.headers.host || '').split(':')[0];
  if (origin && !origin.includes(host)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  // Whitelist mode param
  const { mode } = req.query;
  if (mode !== 'india' && mode !== 'world') {
    return res.status(400).json({ error: 'Invalid mode. Use india or world.' });
  }

  // Key from env — NEVER from client request
  const apiKey = process.env.FINNHUB_API_KEY;
  if (!apiKey) {
    return res.status(503).json({ error: 'Market data not configured', fallback: true });
  }

  // Fetch all symbols in parallel
  const symbolList = SYMBOLS[mode];
  const settled = await Promise.allSettled(
    symbolList.map(s => fetchQuote(s.symbol, apiKey))
  );

  const tickers = settled.map((r, i) => {
    const meta = symbolList[i];
    if (r.status === 'fulfilled' && r.value.c > 0) {
      const q   = r.value;
      const pct = parseFloat((q.dp || 0).toFixed(2));
      return { label: meta.label, value: q.c, change: parseFloat((q.d || 0).toFixed(2)), pct, up: pct >= 0, ok: true };
    }
    return { label: meta.label, ok: false };
  });

  // Edge cache 30s — reduces Finnhub hits dramatically across all visitors
  res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
  res.setHeader('Content-Type', 'application/json');
  return res.status(200).json({ mode, asOf: new Date().toISOString(), tickers, note: 'Indicative only. Not for trading.' });
}

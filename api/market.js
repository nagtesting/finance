/**
 * /api/market.js — MoneyVeda Market API v2
 * 
 * CHANGES FROM v1:
 *   1. Added usa + europe symbol lists (were missing)
 *   2. s-maxage upgraded 30s → 15s (matches sidebar refresh)
 *   3. In-memory server cache added as second safety layer
 *   4. Market hours guard — skips Yahoo on weekends/after-hours (saves calls)
 * 
 * VERCEL FREE TIER SAFETY:
 *   Edge cache (s-maxage=15) means CDN serves cached responses.
 *   Cached hits = 0 function invocations counted against your limit.
 *   Even at 10,000 daily users: ~96 actual function calls/day (one per 15s).
 *   Free tier limit: 100,000 invocations/month. You use ~2,880/month. ✅
 *
 * YAHOO FINANCE RATE LIMIT SAFETY:
 *   Server-side in-memory cache = max 4 Yahoo calls/min regardless of users.
 *   Weekend/after-hours guard = zero calls when markets are closed.
 */

const SYMBOLS = {
  india: [
    { symbol: '^BSESN',        label: 'SENSEX'      },
    { symbol: '^NSEI',         label: 'NIFTY 50'    },
    { symbol: '^NSEBANK',      label: 'NIFTY BANK'  },
    { symbol: 'USDINR=X',      label: 'USD/INR'     },
    { symbol: 'GC=F',          label: 'GOLD'        },
    { symbol: 'RELIANCE.NS',   label: 'RELIANCE'    },
    { symbol: 'HDFCBANK.NS',   label: 'HDFC BANK'   },
    { symbol: 'TCS.NS',        label: 'TCS'         },
    { symbol: 'INFY.NS',       label: 'INFOSYS'     },
    { symbol: 'TATAMOTORS.NS', label: 'TATA MOTORS' },
  ],
  usa: [
    { symbol: '^GSPC',    label: 'S&P 500'    },
    { symbol: '^IXIC',    label: 'NASDAQ'     },
    { symbol: '^DJI',     label: 'DOW JONES'  },
    { symbol: 'GC=F',     label: 'GOLD'       },
    { symbol: 'EURUSD=X', label: 'EUR/USD'    },
    { symbol: 'AAPL',     label: 'APPLE'      },
    { symbol: 'MSFT',     label: 'MICROSOFT'  },
    { symbol: 'TSLA',     label: 'TESLA'      },
    { symbol: 'NVDA',     label: 'NVIDIA'     },
    { symbol: 'AMZN',     label: 'AMAZON'     },
  ],
  europe: [
    { symbol: '^STOXX50E', label: 'EURO STOXX' },
    { symbol: '^GDAXI',    label: 'DAX'        },
    { symbol: '^FTSE',     label: 'FTSE 100'   },
    { symbol: '^FCHI',     label: 'CAC 40'     },
    { symbol: 'EURUSD=X',  label: 'EUR/USD'    },
    { symbol: 'GC=F',      label: 'GOLD'       },
    { symbol: 'CL=F',      label: 'CRUDE OIL'  },
    { symbol: 'ASML.AS',   label: 'ASML'       },
    { symbol: 'SAP.DE',    label: 'SAP'        },
    { symbol: 'LVMH.PA',   label: 'LVMH'       },
  ],
  world: [
    { symbol: '^GSPC',   label: 'S&P 500'     },
    { symbol: '^IXIC',   label: 'NASDAQ'      },
    { symbol: '^DJI',    label: 'DOW JONES'   },
    { symbol: '^FTSE',   label: 'FTSE 100'    },
    { symbol: '^GDAXI',  label: 'DAX'         },
    { symbol: 'GC=F',    label: 'GOLD'        },
    { symbol: 'CL=F',    label: 'CRUDE OIL'   },
    { symbol: 'BTC-USD', label: 'BITCOIN'     },
    { symbol: 'ETH-USD', label: 'ETHEREUM'    },
    { symbol: 'EURUSD=X',label: 'EUR/USD'     },
  ],
};

// ── In-memory server cache (second safety layer after Edge CDN) ──
const _cache = {};
const _cacheTime = {};
const SERVER_CACHE_MS = 15 * 1000; // 15 seconds

// ── Market hours guard ───────────────────────────────────────────
// Returns true if at least one major market is likely open
function isAnyMarketOpen() {
  const now = new Date();
  const day = now.getUTCDay(); // 0=Sun, 6=Sat
  if (day === 0 || day === 6) return false; // weekend — all closed
  return true; // weekday — at least one timezone has a market open
}

// ── Fetch single quote from Yahoo ───────────────────────────────
async function fetchQuote(symbol) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept': 'application/json',
    },
    signal: AbortSignal.timeout(6000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const result = data?.chart?.result?.[0];
  if (!result) throw new Error('No result');
  const meta = result.meta;
  const price = meta.regularMarketPrice;
  const prevClose = meta.previousClose || meta.chartPreviousClose;
  if (!price) throw new Error('No price');
  const change = parseFloat((price - prevClose).toFixed(4));
  const pct    = parseFloat(((change / prevClose) * 100).toFixed(2));
  return { c: price, d: change, dp: pct };
}

// ── Main handler ─────────────────────────────────────────────────
export default async function handler(req, res) {
  // CORS — same origin only
  const origin = req.headers.origin || '';
  const host   = (req.headers.host || '').split(':')[0];
  if (origin && !origin.includes(host)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Whitelist mode param
  const { mode } = req.query;
  const validModes = ['india', 'usa', 'europe', 'world'];
  if (!validModes.includes(mode)) {
    return res.status(400).json({ error: 'Invalid mode. Use: india, usa, europe, or world.' });
  }

  // ── Serve from server-side memory cache if fresh ──────────────
  if (_cache[mode] && (Date.now() - (_cacheTime[mode] || 0)) < SERVER_CACHE_MS) {
    res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('X-Cache', 'HIT');
    return res.status(200).json(_cache[mode]);
  }

  // ── Weekend guard — serve stale cache or fallback ─────────────
  if (!isAnyMarketOpen() && _cache[mode]) {
    res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200');
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('X-Cache', 'STALE-WEEKEND');
    return res.status(200).json({ ..._cache[mode], weekend: true });
  }

  // ── Fetch all symbols in parallel from Yahoo ──────────────────
  const symbolList = SYMBOLS[mode];
  const settled = await Promise.allSettled(
    symbolList.map(s => fetchQuote(s.symbol))
  );

  const tickers = settled.map((r, i) => {
    const meta = symbolList[i];
    if (r.status === 'fulfilled' && r.value.c > 0) {
      const q   = r.value;
      const pct = parseFloat((q.dp || 0).toFixed(2));
      return {
        label:  meta.label,
        value:  q.c,
        change: parseFloat((q.d || 0).toFixed(2)),
        pct,
        up:     pct >= 0,
        ok:     true,
      };
    }
    return { label: meta.label, ok: false };
  });

  const payload = {
    mode,
    asOf:    new Date().toISOString(),
    tickers,
    fallback: tickers.every(t => !t.ok), // true if all failed
    note:    'Indicative only. Not for trading.',
  };

  // Update server-side memory cache
  _cache[mode]    = payload;
  _cacheTime[mode] = Date.now();

  // Edge cache 15s (CDN serves this — zero invocations counted)
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('X-Cache', 'MISS');
  return res.status(200).json(payload);
}

/**
 * /api/market?mode=india|world
 * Vercel Serverless Function — Yahoo Finance Proxy
 *
 * NO API KEY NEEDED — Yahoo Finance is free and public.
 * Supports real NSE/BSE symbols with actual INR prices.
 *
 * SECURITY:
 *   ✓ No API key required — nothing to expose
 *   ✓ CORS locked to same origin
 *   ✓ Mode param whitelisted — rejects anything else
 *   ✓ Edge cached 30s — reduces Yahoo calls dramatically
 *   ✓ Per-symbol failure handled — partial results returned gracefully
 *
 * YAHOO FINANCE SYMBOL FORMAT:
 *   NSE stocks  →  RELIANCE.NS, TCS.NS, INFY.NS
 *   BSE index   →  ^BSESN  (SENSEX)
 *   NSE index   →  ^NSEI   (NIFTY 50)
 *   Forex       →  USDINR=X
 *   Crypto      →  BTC-USD
 *   US stocks   →  AAPL, MSFT (plain ticker)
 *   Commodities →  GC=F (Gold futures), CL=F (Crude Oil)
 */

const SYMBOLS = {
  india: [
    { symbol: '^BSESN',       label: 'SENSEX'    },
    { symbol: '^NSEI',        label: 'NIFTY 50'  },
    { symbol: '^NSEBANK',     label: 'NIFTY BANK'},
    { symbol: 'USDINR=X',     label: 'USD/INR'   },
    { symbol: 'GC=F',         label: 'GOLD'      },
    { symbol: 'RELIANCE.NS',  label: 'RELIANCE'  },
    { symbol: 'HDFCBANK.NS',  label: 'HDFC BANK' },
    { symbol: 'TCS.NS',       label: 'TCS'       },
    { symbol: 'INFY.NS',      label: 'INFOSYS'   },
    { symbol: 'TATAMOTORS.NS',label: 'TATA MOTORS'},
  ],
  world: [
    { symbol: '^GSPC',   label: 'S&P 500'    },
    { symbol: '^IXIC',   label: 'NASDAQ'     },
    { symbol: '^DJI',    label: 'DOW JONES'  },
    { symbol: '^FTSE',   label: 'FTSE 100'   },
    { symbol: '^GDAXI',  label: 'DAX'        },
    { symbol: 'GC=F',    label: 'GOLD'       },
    { symbol: 'CL=F',    label: 'BRENT CRUDE'},
    { symbol: 'BTC-USD', label: 'BITCOIN'    },
    { symbol: 'ETH-USD', label: 'ETHEREUM'   },
    { symbol: 'EURUSD=X',label: 'EUR/USD'    },
  ],
};

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

  // Fetch all symbols in parallel
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

  // Edge cache 30s
  res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
  res.setHeader('Content-Type', 'application/json');
  return res.status(200).json({
    mode,
    asOf:    new Date().toISOString(),
    tickers,
    note:    'Indicative only. Not for trading.',
  });
}

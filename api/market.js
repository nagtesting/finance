/**
 * /api/market.js — MoneyVeda Market API v3
 *
 * CHANGES FROM v2  (audit fixes applied):
 *
 *   ISS-01 — Dynamic Holiday Calendar
 *     - isAnyMarketOpen() now fetches and caches the NSE holiday list
 *       so exchange holidays on weekdays are correctly identified as
 *       closed days. Falls back to weekday-only logic if the calendar
 *       fetch fails (fail-open: better to make a Yahoo call than to
 *       silently suppress live data).
 *     - isNSEHoliday(dateStr) performs a fast O(1) Set lookup after
 *       the calendar is loaded once per calendar year.
 *     - Muhurat trading override: if MUHURAT_DATE env var is set to
 *       "YYYY-MM-DD", the evening window (6:00–7:00 PM IST) is
 *       treated as market-open on that date regardless of holiday status.
 *
 *   ISS-05 — Race-and-Serve Partial Hydration
 *     - fetchAllWithRaceServe() returns partial results after a 2-second
 *       soft timeout and continues fetching remaining symbols in the
 *       background, updating the in-memory cache when they arrive.
 *     - Slow or missing symbols are returned with ok:false immediately;
 *       subsequent requests within the 15-second CDN window will get the
 *       fully hydrated cache.
 *
 * VERCEL FREE TIER SAFETY (unchanged from v2):
 *   Edge cache (s-maxage=15) means CDN serves cached responses.
 *   Cached hits = 0 function invocations counted against your limit.
 *   Even at 10,000 daily users: ~96 actual function calls/day (one per 15s).
 *   Free tier limit: 100,000 invocations/month. You use ~2,880/month. ✅
 *
 * YAHOO FINANCE RATE LIMIT SAFETY (unchanged from v2):
 *   Server-side in-memory cache = max 4 Yahoo calls/min regardless of users.
 *   Weekend/holiday guard = zero calls when all markets are closed.
 */

// ─────────────────────────────────────────────────────────────────────────────
// SYMBOL LISTS (unchanged from v2)
// ─────────────────────────────────────────────────────────────────────────────
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
    { symbol: '^GSPC',    label: 'S&P 500'     },
    { symbol: '^IXIC',    label: 'NASDAQ'      },
    { symbol: '^DJI',     label: 'DOW JONES'   },
    { symbol: '^FTSE',    label: 'FTSE 100'    },
    { symbol: '^GDAXI',   label: 'DAX'         },
    { symbol: 'GC=F',     label: 'GOLD'        },
    { symbol: 'CL=F',     label: 'CRUDE OIL'   },
    { symbol: 'BTC-USD',  label: 'BITCOIN'     },
    { symbol: 'ETH-USD',  label: 'ETHEREUM'    },
    { symbol: 'EURUSD=X', label: 'EUR/USD'     },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// IN-MEMORY CACHES
// ─────────────────────────────────────────────────────────────────────────────
const _cache     = {};
const _cacheTime = {};
const SERVER_CACHE_MS = 15 * 1000; // 15 seconds

// ─────────────────────────────────────────────────────────────────────────────
// ISS-01 FIX — HOLIDAY CALENDAR
// ─────────────────────────────────────────────────────────────────────────────

/**
 * In-memory holiday set: keys are "YYYY-MM-DD" strings (IST date).
 * Populated once per calendar year from the NSE holiday API, then reused.
 */
let _holidaySet       = new Set();
let _holidayYear      = null;   // which calendar year the set covers
let _holidayFetchedAt = 0;      // epoch ms of last successful fetch

const HOLIDAY_TTL_MS  = 24 * 60 * 60 * 1000; // refresh once per day

/**
 * Returns the ISO date string "YYYY-MM-DD" in IST for a given Date object.
 */
function toISTDateString(date) {
  const ist = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const y   = ist.getFullYear();
  const m   = String(ist.getMonth() + 1).padStart(2, '0');
  const d   = String(ist.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/**
 * Fetches the NSE holiday list for the given year and populates _holidaySet.
 * NSE publishes a JSON endpoint listing CM (Capital Markets) segment holidays.
 * Falls back silently — the caller degrades to weekend-only logic on failure.
 */
async function refreshHolidayCalendar(year) {
  try {
    const url = `https://www.nseindia.com/api/holiday-master?type=trading`;
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept':     'application/json',
        'Referer':    'https://www.nseindia.com/',
      },
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) throw new Error(`NSE holiday API HTTP ${res.status}`);

    const data = await res.json();

    // NSE returns { CM: [ { tradingDate: "DD-Mon-YYYY", ... }, ... ], ... }
    const cmHolidays = data?.CM ?? [];
    const newSet     = new Set();

    for (const entry of cmHolidays) {
      // Normalise "01-Jan-2025" → "2025-01-01"
      const parsed = new Date(entry.tradingDate);
      if (!isNaN(parsed)) {
        // Use IST representation for consistency
        newSet.add(toISTDateString(parsed));
      }
    }

    _holidaySet       = newSet;
    _holidayYear      = year;
    _holidayFetchedAt = Date.now();
    console.log(`[Holiday] Loaded ${newSet.size} NSE trading holidays for ${year}`);

  } catch (err) {
    // Non-fatal — log and continue. isAnyMarketOpen() falls back to weekday logic.
    console.warn(`[Holiday] Calendar fetch failed (${err.message}). Falling back to weekday-only guard.`);
  }
}

/**
 * Returns true if the given IST date string is a known NSE trading holiday.
 * Ensures the holiday set is populated for the current calendar year.
 */
async function isNSEHoliday(istDateStr) {
  const year = parseInt(istDateStr.slice(0, 4), 10);

  // Refresh if: wrong year loaded, or TTL expired
  const needsRefresh = (_holidayYear !== year)
    || (Date.now() - _holidayFetchedAt > HOLIDAY_TTL_MS);

  if (needsRefresh) {
    await refreshHolidayCalendar(year);
  }

  return _holidaySet.has(istDateStr);
}

/**
 * Muhurat trading override.
 * Set env var MUHURAT_DATE="YYYY-MM-DD" (IST) on the Diwali evening session.
 * The session window is 6:00 PM – 7:00 PM IST (hard-coded; NSE announces exact
 * timing each year — adjust MUHURAT_START_MIN / MUHURAT_END_MIN as needed).
 */
const MUHURAT_DATE      = process.env.MUHURAT_DATE ?? null;
const MUHURAT_START_MIN = 18 * 60;      // 6:00 PM IST in minutes
const MUHURAT_END_MIN   = 19 * 60;      // 7:00 PM IST in minutes

function isMuhuratSessionActive(istDateStr, totalMinsIST) {
  if (!MUHURAT_DATE) return false;
  return istDateStr === MUHURAT_DATE
    && totalMinsIST >= MUHURAT_START_MIN
    && totalMinsIST <= MUHURAT_END_MIN;
}

/**
 * ISS-01 FIX: Full market-open check — weekend, exchange holiday, and
 * optional Muhurat session aware.
 *
 * For the broader server API (isAnyMarketOpen), we check IST-specific
 * conditions (NSE/BSE) as the primary gate. Global markets (US/EU) are
 * always open on non-Indian weekdays, so we only skip calls if ALL
 * markets — including NSE — are closed.
 *
 * For India mode: a holiday or weekend = closed.
 * For USA/Europe/World mode: only weekends (UTC Sat/Sun) close all markets.
 */
async function isAnyMarketOpen(mode = 'world') {
  const now = new Date();
  const utcDay = now.getUTCDay(); // 0=Sun, 6=Sat

  // Hard weekend gate — all global markets closed
  if (utcDay === 0 || utcDay === 6) return false;

  // For India mode: additionally check NSE trading calendar
  if (mode === 'india') {
    const istDateStr    = toISTDateString(now);
    const istObj        = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    const totalMinsIST  = istObj.getHours() * 60 + istObj.getMinutes();

    // Allow Muhurat session even on holidays
    if (isMuhuratSessionActive(istDateStr, totalMinsIST)) return true;

    const holiday = await isNSEHoliday(istDateStr);
    if (holiday) return false; // NSE/BSE holiday — skip Yahoo calls for India mode
  }

  // Weekday, not an India holiday (or non-India mode): at least one market open
  return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// FETCH SINGLE QUOTE (unchanged from v2)
// ─────────────────────────────────────────────────────────────────────────────
async function fetchQuote(symbol) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept':     'application/json',
    },
    signal: AbortSignal.timeout(6000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const result = data?.chart?.result?.[0];
  if (!result) throw new Error('No result');
  const meta      = result.meta;
  const price     = meta.regularMarketPrice;
  const prevClose = meta.previousClose || meta.chartPreviousClose;
  if (!price) throw new Error('No price');
  const change = parseFloat((price - prevClose).toFixed(4));
  const pct    = parseFloat(((change / prevClose) * 100).toFixed(2));
  return { c: price, d: change, dp: pct };
}

// ─────────────────────────────────────────────────────────────────────────────
// ISS-05 FIX — RACE-AND-SERVE PARTIAL HYDRATION
// ─────────────────────────────────────────────────────────────────────────────

const SOFT_TIMEOUT_MS = 2000; // Return partial results after 2s; keep fetching in background

/**
 * Fetches all symbols in parallel. After SOFT_TIMEOUT_MS, returns whatever
 * has resolved so far (partial payload). Remaining promises continue running
 * in the background and update _cache[mode] when they settle.
 *
 * This prevents one slow Yahoo shard from blocking the entire response.
 */
async function fetchAllWithRaceServe(symbolList, mode) {
  // Create per-symbol promise wrappers that record their result index
  const resolved = new Array(symbolList.length).fill(null); // null = pending

  const symbolPromises = symbolList.map((s, i) =>
    fetchQuote(s.symbol)
      .then(q  => { resolved[i] = { status: 'fulfilled', value: q }; })
      .catch(e => { resolved[i] = { status: 'rejected',  reason: e }; })
  );

  // Wait for either all symbols OR the soft timeout, whichever comes first
  await Promise.race([
    Promise.allSettled(symbolPromises),
    new Promise(res => setTimeout(res, SOFT_TIMEOUT_MS)),
  ]);

  // Build partial payload from whatever has resolved so far
  const partialTickers = buildTickers(symbolList, resolved);

  const pendingCount = resolved.filter(r => r === null).length;
  const partial      = pendingCount > 0;

  // Background continuation: update cache when remaining symbols resolve
  if (partial) {
    Promise.allSettled(symbolPromises).then(() => {
      const fullTickers = buildTickers(symbolList, resolved);
      _cache[mode] = {
        mode,
        asOf:    new Date().toISOString(),
        tickers: fullTickers,
        partial: false,
        fallback: fullTickers.every(t => !t.ok),
        note:    'Indicative only. Not for trading.',
      };
      _cacheTime[mode] = Date.now();
    });
  }

  return { tickers: partialTickers, partial, pendingCount };
}

/** Maps the resolved array into the standard ticker format. */
function buildTickers(symbolList, resolved) {
  return symbolList.map((meta, i) => {
    const r = resolved[i];
    if (r && r.status === 'fulfilled' && r.value.c > 0) {
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
    // null = still pending; rejected = failed
    return { label: meta.label, ok: false, pending: r === null };
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN HANDLER
// ─────────────────────────────────────────────────────────────────────────────
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

  // ── ISS-01: Holiday-aware market guard ────────────────────────
  const marketOpen = await isAnyMarketOpen(mode);

  if (!marketOpen && _cache[mode]) {
    res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200');
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('X-Cache', 'STALE-CLOSED');
    // Tag as holiday or weekend so consumers can show appropriate UI
    const now        = new Date();
    const istDateStr = toISTDateString(now);
    const isHol      = _holidaySet.has(istDateStr);
    return res.status(200).json({
      ..._cache[mode],
      marketClosed: true,
      closedReason: isHol ? 'exchange-holiday' : 'weekend',
    });
  }

  // ── ISS-05: Race-and-serve parallel fetch ─────────────────────
  const symbolList = SYMBOLS[mode];
  const { tickers, partial, pendingCount } = await fetchAllWithRaceServe(symbolList, mode);

  const payload = {
    mode,
    asOf:        new Date().toISOString(),
    tickers,
    partial,     // true if some symbols are still resolving in background
    pendingCount: partial ? pendingCount : 0,
    fallback:    tickers.every(t => !t.ok),
    note:        'Indicative only. Not for trading.',
  };

  // Update server-side memory cache (may be partial; background task will overwrite with full)
  _cache[mode]     = payload;
  _cacheTime[mode] = Date.now();

  // Edge cache 15s
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('X-Cache', partial ? 'MISS-PARTIAL' : 'MISS');
  return res.status(200).json(payload);
}

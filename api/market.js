
/**
 * /api/market.js — MoneyVeda Market API v3 (Protected Edition)
 *
 * MOVED SERVER-SIDE (no longer in index.html):
 *   • STATIC_FALLBACK data for all regions + sidebar variants
 *   • modeColors + modeFlags display config
 *   • Ticker HTML string assembly (badge + item HTML)
 *   • Sidebar HTML string assembly
 *   • Fallback ticker/sidebar rendering logic
 *
 * CLIENT RECEIVES ready-to-inject HTML:
 *   ?view=ticker  → { tickerHtml, mode, weekend, fallback }
 *   ?view=sidebar → { sidebarHtml, live, updatedTime, mode }
 *   (no ?view)    → raw tickers JSON (backward compat)
 *
 * VERCEL FREE TIER: s-maxage=15 edge cache → ~2,880 invocations/month ✅
 * YAHOO RATE LIMIT: server-side 15s cache → max 4 Yahoo calls/min ✅
 */

const SYMBOLS = {
  india: [
    { symbol: '^BSESN',        label: 'SENSEX'        },
    { symbol: '^NSEI',         label: 'NIFTY 50'      },
    { symbol: '^NSEBANK',      label: 'NIFTY BANK'    },
    { symbol: '^CNXIT',        label: 'NIFTY IT'      },
    { symbol: '^CNXAUTO',      label: 'NIFTY AUTO'    },
    { symbol: '^CNXPHARMA',    label: 'NIFTY PHARMA'  },
    { symbol: '^CNXFMCG',      label: 'NIFTY FMCG'   },
    { symbol: 'USDINR=X',      label: 'USD/INR'       },
    { symbol: 'GC=F',          label: 'GOLD'          },
    { symbol: 'CL=F',          label: 'CRUDE OIL'     },
    { symbol: 'SI=F',          label: 'SILVER'        },
    { symbol: 'RELIANCE.NS',   label: 'RELIANCE'      },
    { symbol: 'HDFCBANK.NS',   label: 'HDFC BANK'     },
    { symbol: 'TCS.NS',        label: 'TCS'           },
    { symbol: 'INFY.NS',       label: 'INFOSYS'       },
    { symbol: 'TATAMOTORS.NS', label: 'TATA MOTORS'   },
    { symbol: 'ICICIBANK.NS',  label: 'ICICI BANK'    },
    { symbol: 'WIPRO.NS',      label: 'WIPRO'         },
    { symbol: 'AXISBANK.NS',   label: 'AXIS BANK'     },
    { symbol: 'SBIN.NS',       label: 'SBI'           },
    { symbol: 'MARUTI.NS',     label: 'MARUTI'        },
    { symbol: 'SUNPHARMA.NS',  label: 'SUN PHARMA'    },
    { symbol: 'BAJFINANCE.NS', label: 'BAJAJ FIN'     },
    { symbol: 'HINDUNILVR.NS', label: 'HUL'           },
    { symbol: 'LT.NS',         label: 'L&T'           },
    { symbol: 'KOTAKBANK.NS',  label: 'KOTAK BANK'    },
    { symbol: 'ITC.NS',        label: 'ITC'           },
    { symbol: 'BHARTIARTL.NS', label: 'AIRTEL'        },
    { symbol: 'ASIANPAINT.NS', label: 'ASIAN PAINTS'  },
    { symbol: 'TITAN.NS',      label: 'TITAN'         },
    { symbol: 'ULTRACEMCO.NS', label: 'ULTRATECH CEM' },
    { symbol: 'NESTLEIND.NS',  label: 'NESTLE INDIA'  },
    { symbol: 'POWERGRID.NS',  label: 'POWER GRID'    },
    { symbol: 'NTPC.NS',       label: 'NTPC'          },
    { symbol: 'ONGC.NS',       label: 'ONGC'          },
    { symbol: 'ADANIENT.NS',   label: 'ADANI ENT'     },
  ],
  usa: [
    { symbol: '^GSPC',    label: 'S&P 500'      },
    { symbol: '^IXIC',    label: 'NASDAQ'       },
    { symbol: '^DJI',     label: 'DOW JONES'    },
    { symbol: '^RUT',     label: 'RUSSELL 2000' },
    { symbol: '^VIX',     label: 'VIX'          },
    { symbol: 'GC=F',     label: 'GOLD'         },
    { symbol: 'CL=F',     label: 'CRUDE OIL'    },
    { symbol: 'SI=F',     label: 'SILVER'       },
    { symbol: 'EURUSD=X', label: 'EUR/USD'      },
    { symbol: 'DX-Y.NYB', label: 'US DOLLAR'    },
    { symbol: 'BTC-USD',  label: 'BITCOIN'      },
    { symbol: 'ETH-USD',  label: 'ETHEREUM'     },
    { symbol: 'AAPL',     label: 'APPLE'        },
    { symbol: 'MSFT',     label: 'MICROSOFT'    },
    { symbol: 'TSLA',     label: 'TESLA'        },
    { symbol: 'NVDA',     label: 'NVIDIA'       },
    { symbol: 'AMZN',     label: 'AMAZON'       },
    { symbol: 'GOOGL',    label: 'ALPHABET'     },
    { symbol: 'META',     label: 'META'         },
    { symbol: 'NFLX',     label: 'NETFLIX'      },
    { symbol: 'JPM',      label: 'JPMORGAN'     },
    { symbol: 'BAC',      label: 'BANK OF AM.'  },
    { symbol: 'BRK-B',    label: 'BERKSHIRE'    },
    { symbol: 'UNH',      label: 'UNITEDHEALTH' },
    { symbol: 'V',        label: 'VISA'         },
  ],
  europe: [
    { symbol: '^STOXX50E', label: 'EURO STOXX'    },
    { symbol: '^GDAXI',    label: 'DAX'           },
    { symbol: '^FTSE',     label: 'FTSE 100'      },
    { symbol: '^FCHI',     label: 'CAC 40'        },
    { symbol: '^IBEX',     label: 'IBEX 35'       },
    { symbol: '^SSMI',     label: 'SMI'           },
    { symbol: '^AEX',      label: 'AEX'           },
    { symbol: 'EURUSD=X',  label: 'EUR/USD'       },
    { symbol: 'GBPUSD=X',  label: 'GBP/USD'       },
    { symbol: 'GC=F',      label: 'GOLD'          },
    { symbol: 'CL=F',      label: 'CRUDE OIL'     },
    { symbol: 'NG=F',      label: 'NAT. GAS'      },
    { symbol: 'ASML.AS',   label: 'ASML'          },
    { symbol: 'SAP.DE',    label: 'SAP'           },
    { symbol: 'LVMH.PA',   label: 'LVMH'          },
    { symbol: 'SIE.DE',    label: 'SIEMENS'       },
    { symbol: 'NOVO-B.CO', label: 'NOVO NORDISK'  },
    { symbol: 'NESN.SW',   label: 'NESTLE'        },
    { symbol: 'ROG.SW',    label: 'ROCHE'         },
    { symbol: 'MC.PA',     label: 'MOET HENNESSY' },
    { symbol: 'TTE.PA',    label: 'TOTALENERGIES' },
    { symbol: 'SHELL.AS',  label: 'SHELL'         },
    { symbol: 'ULVR.L',    label: 'UNILEVER'      },
    { symbol: 'AZN.L',     label: 'ASTRAZENECA'   },
    { symbol: 'HSBA.L',    label: 'HSBC'          },
  ],
  world: [
    { symbol: '^GSPC',     label: 'S&P 500'    },
    { symbol: '^IXIC',     label: 'NASDAQ'     },
    { symbol: '^DJI',      label: 'DOW JONES'  },
    { symbol: '^FTSE',     label: 'FTSE 100'   },
    { symbol: '^GDAXI',    label: 'DAX'        },
    { symbol: '^BSESN',    label: 'SENSEX'     },
    { symbol: '^NSEI',     label: 'NIFTY 50'   },
    { symbol: '^N225',     label: 'NIKKEI 225' },
    { symbol: '^HSI',      label: 'HANG SENG'  },
    { symbol: '^STOXX50E', label: 'EURO STOXX' },
    { symbol: '^AXJO',     label: 'ASX 200'    },
    { symbol: '^KS11',     label: 'KOSPI'      },
    { symbol: 'GC=F',      label: 'GOLD'       },
    { symbol: 'CL=F',      label: 'CRUDE OIL'  },
    { symbol: 'SI=F',      label: 'SILVER'     },
    { symbol: 'NG=F',      label: 'NAT. GAS'   },
    { symbol: 'BTC-USD',   label: 'BITCOIN'    },
    { symbol: 'ETH-USD',   label: 'ETHEREUM'   },
    { symbol: 'BNB-USD',   label: 'BNB'        },
    { symbol: 'EURUSD=X',  label: 'EUR/USD'    },
    { symbol: 'GBPUSD=X',  label: 'GBP/USD'   },
    { symbol: 'USDINR=X',  label: 'USD/INR'    },
    { symbol: 'USDJPY=X',  label: 'USD/JPY'    },
    { symbol: 'USDCNY=X',  label: 'USD/CNY'    },
    { symbol: 'DX-Y.NYB',  label: 'US DOLLAR'  },
  ],
};

// ── Mode display config (was modeColors + modeFlags in client JS) ─
const MODE_META = {
  india:  { color: '#C9A84C', flag: '🇮🇳', sidebarLabels: ['SENSEX',     'NIFTY 50'] },
  usa:    { color: '#60a5fa', flag: '🇺🇸', sidebarLabels: ['S&P 500',    'NASDAQ']   },
  europe: { color: '#a5b4fc', flag: '🇪🇺', sidebarLabels: ['EURO STOXX', 'DAX']      },
  world:  { color: '#4ade80', flag: '🌍', sidebarLabels: ['S&P 500',    'NIFTY 50'] },
};

// ── Static fallback data (was STATIC_FALLBACK in client JS) ──
const STATIC_FALLBACK = {
  india: [
    { label: 'SENSEX',     value: 74532,  pct:  0.44, up: true  },
    { label: 'NIFTY 50',   value: 23114,  pct:  0.49, up: true  },
    { label: 'NIFTY BANK', value: 54018,  pct: -2.36, up: false },
    { label: 'GOLD',       value: 6842,   pct:  0.43, up: true  },
    { label: 'USD/INR',    value: 93.75,  pct: -0.12, up: false },
  ],
  usa: [
    { label: 'S&P 500',  value: 6606,   pct: -0.27, up: false },
    { label: 'NASDAQ',   value: 22090,  pct: -0.28, up: false },
    { label: 'DOW',      value: 43215,  pct: -0.15, up: false },
    { label: 'GOLD',     value: 4617,   pct:  0.31, up: true  },
    { label: 'EUR/USD',  value: 0.9241, pct:  0.12, up: true  },
  ],
  europe: [
    { label: 'EURO STOXX', value: 5372,   pct: -1.62, up: false },
    { label: 'DAX',        value: 22391,  pct: -1.45, up: false },
    { label: 'FTSE 100',   value: 8673,   pct: -2.35, up: false },
    { label: 'GOLD',       value: 4263,   pct:  0.21, up: true  },
    { label: 'EUR/USD',    value: 1.0823, pct: -0.12, up: false },
  ],
  world: [
    { label: 'S&P 500',   value: 6606,  pct: -0.27, up: false },
    { label: 'NIFTY 50',  value: 23114, pct:  0.49, up: true  },
    { label: 'BITCOIN',   value: 84200, pct: -1.80, up: false },
    { label: 'GOLD',      value: 4617,  pct:  0.31, up: true  },
    { label: 'CRUDE OIL', value: 68.40, pct: -0.90, up: false },
  ],
};

// ── In-memory cache ───────────────────────────────────────────
const _cache     = {};
const _cacheTime = {};
const SERVER_CACHE_MS = 15 * 1000;

// ── Per-region market hours (UTC) ────────────────────────────
// Returns { open: bool, label: string, nextOpen: string }
function getMarketStatus(mode) {
  const now  = new Date();
  const day  = now.getUTCDay();   // 0=Sun, 6=Sat
  const hour = now.getUTCHours();
  const min  = now.getUTCMinutes();
  const t    = hour * 60 + min;   // minutes since UTC midnight

  // Weekend check (universal)
  const isWeekend = day === 0 || day === 6;

  const schedules = {
    // NSE/BSE: Mon-Fri 03:45–10:00 UTC (09:15–15:30 IST)
    india:  { open: 3*60+45,  close: 10*60,     tz: 'IST',  exchange: 'NSE/BSE',  local: '9:15–15:30 IST'  },
    // NYSE/NASDAQ: Mon-Fri 13:30–20:00 UTC (9:30–16:00 ET)
    usa:    { open: 13*60+30, close: 20*60,      tz: 'ET',   exchange: 'NYSE',     local: '9:30–16:00 ET'   },
    // Euronext/Frankfurt: Mon-Fri 07:00–15:30 UTC (8:00–16:30 CET)
    europe: { open: 7*60,     close: 15*60+30,   tz: 'CET',  exchange: 'XETRA',   local: '8:00–16:30 CET'  },
    // World: use NYSE as primary reference
    world:  { open: 13*60+30, close: 20*60,      tz: 'ET',   exchange: 'NYSE',     local: '9:30–16:00 ET'   },
  };

  const s = schedules[mode] || schedules.india;
  const isOpen = !isWeekend && t >= s.open && t < s.close;

  let statusLabel, statusColor;
  if (isWeekend) {
    statusLabel = `${s.exchange} closed (weekend) · Opens Mon ${s.local}`;
    statusColor = '#f59e0b';
  } else if (!isOpen && t < s.open) {
    const minsTo = s.open - t;
    const hTo = Math.floor(minsTo / 60), mTo = minsTo % 60;
    statusLabel = `${s.exchange} pre-market · Opens in ${hTo}h ${mTo}m (${s.local})`;
    statusColor = '#f59e0b';
  } else if (!isOpen && t >= s.close) {
    statusLabel = `${s.exchange} closed · Opens tomorrow ${s.local}`;
    statusColor = '#9090A8';
  } else {
    statusLabel = `${s.exchange} live · ${s.local}`;
    statusColor = '#4ade80';
  }

  return { isOpen, isWeekend, statusLabel, statusColor, exchange: s.exchange };
}

function isAnyMarketOpen() {
  const day = new Date().getUTCDay();
  return day !== 0 && day !== 6;
}

async function fetchQuote(symbol) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept': 'application/json',
    },
    signal: (() => { try { return AbortSignal.timeout(6000); } catch(e) { const c = new AbortController(); setTimeout(() => c.abort(), 6000); return c.signal; } })(),
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

// ── HTML builders (moved fully from client renderTickerItems / renderSidebar) ──

function buildTickerItemHtml(t) {
  const up    = t.up;
  const color = up ? '#22C55E' : '#EF4444';
  const arrow = up ? '&#9650;' : '&#9660;';
  const val   = typeof t.value === 'number'
    ? t.value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    : String(t.value);
  const sign  = t.pct >= 0 ? '+' : '';
  return `<div style="display:inline-flex;align-items:center;padding:0 18px 0 16px;border-right:1px solid rgba(255,255,255,.05);height:44px;">` +
    `<span style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#6b7280;margin-right:9px;">${t.label}</span>` +
    `<span style="font-size:13px;font-weight:600;color:#F0EDE6;font-family:'DM Mono',monospace;margin-right:7px;">${val}</span>` +
    `<span style="display:inline-flex;align-items:center;gap:2px;background:${up ? 'rgba(34,197,94,.1)' : 'rgba(239,68,68,.1)'};` +
      `border:1px solid ${up ? 'rgba(34,197,94,.25)' : 'rgba(239,68,68,.25)'};border-radius:4px;padding:2px 7px;">` +
      `<span style="font-size:7px;color:${color};">${arrow}</span>` +
      `<span style="font-size:10px;font-weight:700;color:${color};font-family:'DM Mono',monospace;">${sign}${t.pct}%</span>` +
    `</span></div>`;
}

function buildBadgeHtml(mode, marketStatus) {
  const m   = MODE_META[mode];
  const ms  = marketStatus || { isOpen: true, statusColor: '#4ade80', statusLabel: 'LIVE' };
  const dot = `<span style="display:inline-block;width:6px;height:6px;border-radius:50%;` +
    `background:${ms.statusColor};margin-right:6px;flex-shrink:0;` +
    `${ms.isOpen ? 'box-shadow:0 0 6px ' + ms.statusColor + ';' : ''}"></span>`;
  const liveText = ms.isOpen ? 'LIVE' : 'CLOSED';
  return `<div style="display:inline-flex;align-items:center;padding:0 14px;height:44px;` +
    `border-right:1px solid rgba(201,168,76,.2);flex-shrink:0;gap:0;">` +
    `${dot}<span style="font-size:9px;font-weight:800;letter-spacing:2px;color:${m.color};` +
    `font-family:'DM Sans',sans-serif;margin-right:8px;">${m.flag} ${liveText}</span>` +
    // Scrolling status text if market closed
    (!ms.isOpen ? `<span style="font-size:8px;color:${ms.statusColor};font-family:'DM Mono',monospace;` +
      `letter-spacing:0.5px;max-width:220px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">` +
      `${ms.statusLabel}</span>` : '') +
    `</div>`;
}

function buildSidebarItemHtml(t) {
  const c     = t.up === true ? '#4ade80' : t.up === false ? '#f87171' : 'var(--muted)';
  const arrow = t.up === true ? '&#9650;' : t.up === false ? '&#9660;' : '';
  const val   = typeof t.value === 'number'
    ? t.value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    : String(t.value);
  const sign  = t.pct >= 0 ? '+' : '';
  return `<div style="display:flex;justify-content:space-between;align-items:center;` +
    `padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);">` +
    `<span style="font-size:10px;color:var(--muted);">${t.label}</span>` +
    `<div style="text-align:right;">` +
      `<span style="font-size:12px;font-family:'DM Mono',monospace;font-weight:600;color:var(--cream);display:block;">${val}</span>` +
      `<span style="font-size:9px;color:${c};">${arrow} ${sign}${t.pct}%</span>` +
    `</div></div>`;
}

function resolveTickerItems(mode, tickers) {
  const live = tickers ? tickers.filter(t => t.ok) : [];
  return live.length > 0 ? live : STATIC_FALLBACK[mode].map(t => ({ ...t, ok: true }));
}

function resolveSidebarItems(mode, tickers) {
  const preferred = MODE_META[mode].sidebarLabels;
  if (tickers) {
    const matched = preferred.map(lbl => tickers.find(t => t.ok && t.label === lbl)).filter(Boolean);
    if (matched.length === 2) return { items: matched, live: true };
    const top2 = tickers.filter(t => t.ok).slice(0, 2);
    if (top2.length === 2) return { items: top2, live: true };
  }
  return { items: STATIC_FALLBACK[mode].slice(0, 2), live: false };
}

// ── Main handler ──────────────────────────────────────────────
export default async function handler(req, res) {
  const origin = req.headers.origin || '';
  const host   = (req.headers.host || '').split(':')[0];
  if (origin && !origin.includes(host)) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { mode, view } = req.query;
  const validModes = ['india', 'usa', 'europe', 'world'];
  if (!validModes.includes(mode)) {
    return res.status(400).json({ error: 'Invalid mode. Use: india, usa, europe, or world.' });
  }

  let isWeekend = false;
  let tickers   = null;

  // Serve from in-memory cache if fresh
  if (_cache[mode] && (Date.now() - (_cacheTime[mode] || 0)) < SERVER_CACHE_MS) {
    tickers = _cache[mode].tickers;
  }
  // Weekend: use stale cache
  else if (!isAnyMarketOpen() && _cache[mode]) {
    tickers   = _cache[mode].tickers;
    isWeekend = true;
  }
  // Fetch fresh from Yahoo
  else {
    const symbolList = SYMBOLS[mode];
    const settled = await Promise.allSettled(
      symbolList.map(s => fetchQuote(s.symbol))
    );
    tickers = settled.map((r, i) => {
      const meta = symbolList[i];
      if (r.status === 'fulfilled' && r.value.c > 0) {
        const q   = r.value;
        const pct = parseFloat((q.dp || 0).toFixed(2));
        return { label: meta.label, value: q.c, change: parseFloat((q.d || 0).toFixed(2)), pct, up: pct >= 0, ok: true };
      }
      return { label: meta.label, ok: false };
    });
    _cache[mode]     = { mode, asOf: new Date().toISOString(), tickers, note: 'Indicative only. Not for trading.' };
    _cacheTime[mode] = Date.now();
  }

  const cacheControl = isWeekend
    ? 's-maxage=3600, stale-while-revalidate=7200'
    : 's-maxage=15, stale-while-revalidate=30';

  res.setHeader('Cache-Control', cacheControl);
  res.setHeader('Content-Type', 'application/json');

  // ── ?view=ticker ─────────────────────────────────────────
  // Returns ready-to-inject HTML for #ticker-track.
  // Client does: track.innerHTML = data.tickerHtml; startScroll(track);
  if (view === 'ticker') {
    const ms         = getMarketStatus(mode);
    const items      = resolveTickerItems(mode, tickers);
    const badge      = buildBadgeHtml(mode, ms);
    const itemsHtml  = items.map(buildTickerItemHtml).join('');
    const tickerHtml = badge + itemsHtml + badge + itemsHtml; // doubled for seamless loop
    return res.status(200).json({ tickerHtml, mode, weekend: ms.isWeekend, marketOpen: ms.isOpen, marketStatus: ms.statusLabel });
  }

  // ── ?view=sidebar ────────────────────────────────────────
  // Returns ready-to-inject sidebar HTML + live/time metadata.
  // Client does: el.innerHTML = data.sidebarHtml; updateDot(data.live);
  if (view === 'sidebar') {
    const { items, live } = resolveSidebarItems(mode, tickers);
    const sidebarHtml     = items.map(buildSidebarItemHtml).join('');
    const updatedTime     = live
      ? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : 'Snapshot';
    return res.status(200).json({ sidebarHtml, live, updatedTime, mode, weekend: isWeekend });
  }

  // ── default: raw JSON (backward compat) ──────────────────
  return res.status(200).json({ ..._cache[mode], weekend: isWeekend });
}

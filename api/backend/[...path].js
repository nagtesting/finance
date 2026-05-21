// api/backend/[...path].js
//
// Same-origin proxy from www.moneyveda.org → the Render backend.
// This is what the market-pulse.html v2 patches call instead of hitting
// moneyveda-backend.onrender.com directly from the browser.
//
// WHY THIS EXISTS
// ===============
// 1. CORS: the browser refuses to read responses from onrender.com because
//    that host doesn't send Access-Control-Allow-Origin. By proxying through
//    our own origin, every browser request is same-origin — no CORS at all.
// 2. Performance: Vercel edge-caches every response based on the
//    Cache-Control header we set below. Once the edge has a hot entry, the
//    browser gets it in ~30 ms — masking Render's 300–800 ms (or 10+ s when
//    it cold-starts from sleep).
// 3. Security / abuse control: the Render URL is no longer visible in the
//    page source. Render can be locked down further by checking the
//    x-proxy-secret header below — anyone hitting Render directly without
//    that header gets refused.
//
// REQUIRED VERCEL ENV VARS (set in the Vercel dashboard, not committed)
// ====================================================================
//   RENDER_BACKEND_URL   — e.g. https://moneyveda-backend.onrender.com
//   RENDER_PROXY_SECRET  — any long random string; pass the same value to
//                          Render and have Render reject requests where
//                          x-proxy-secret doesn't match.
//
// ROUTING
// =======
// Filename `api/backend/[...path].js` is Vercel's catch-all pattern: any
// request to `/api/backend/anything/here?x=1` lands here with
// req.query.path = ['anything', 'here'].
//
// ENDPOINT ALLOWLIST
// ==================
// We deliberately enumerate the endpoints the frontend uses. Anything not
// in the list returns 404 — no surprises if the Render backend exposes
// internal routes we don't want to surface.

const RENDER_BASE   = process.env.RENDER_BACKEND_URL  || 'https://moneyveda-backend.onrender.com';
const PROXY_SECRET  = process.env.RENDER_PROXY_SECRET || '';

// path → seconds at the Vercel edge. Browser-side localStorage SWR has its
// own (shorter) TTLs; this layer is purely about Vercel edge cache.
const EDGE_TTL = {
  'market-commentary':    60,         // commentary updates every 30 min
  'market-cache':         30,         // live prices
  'market-cache/symbols': 24 * 3600,  // static catalog
  'summary':              60,
  'signals':              60,
  'filings':              60,
  'prices':               30,
  'commentary':           300,        // LLM-generated per-symbol commentary
};

const ALLOWED = new Set(Object.keys(EDGE_TTL));

// Lightweight per-IP rate limit (best-effort, in-memory; resets per cold
// start). Real protection sits behind RENDER_PROXY_SECRET, but this stops
// a single bad actor from spamming the proxy.
const RATE = new Map();   // ip → { count, resetAt }
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 120;     // 2 req/sec per IP per minute, plenty for a UI

function clientIp(req) {
  const xf = req.headers['x-forwarded-for'];
  return (xf && xf.split(',')[0].trim()) || req.socket?.remoteAddress || 'anon';
}

function rateLimited(ip) {
  const now = Date.now();
  let rec = RATE.get(ip);
  if (!rec || rec.resetAt < now) {
    rec = { count: 0, resetAt: now + RATE_WINDOW_MS };
    RATE.set(ip, rec);
  }
  rec.count += 1;
  return rec.count > RATE_MAX;
}

module.exports = async (req, res) => {
  // Only GET is supported — every endpoint we proxy is read-only.
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.setHeader('Allow', 'GET, HEAD');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Build the target path from the catch-all segments.
  const segs = req.query.path;
  const path = Array.isArray(segs) ? segs.join('/') : (segs || '');

  if (!ALLOWED.has(path)) {
    return res.status(404).json({ error: 'Unknown endpoint', path });
  }

  if (rateLimited(clientIp(req))) {
    res.setHeader('Retry-After', '60');
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  // Forward all query params except the routing `path` itself.
  const target = new URL(`${RENDER_BASE}/api/${path}`);
  for (const [k, v] of Object.entries(req.query)) {
    if (k === 'path') continue;
    target.searchParams.set(k, Array.isArray(v) ? v[0] : v);
  }

  // Auth header for Render. Render-side: check `x-proxy-secret` equals the
  // same env var and 401 anything else. That cuts the Render endpoint off
  // from direct public access.
  const headers = { accept: 'application/json' };
  if (PROXY_SECRET) headers['x-proxy-secret'] = PROXY_SECRET;

  // AbortController gives us a hard timeout — Render free dynos that fail
  // to wake within 15 s shouldn't hang our function.
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15_000);

  let upstream;
  try {
    upstream = await fetch(target.toString(), { headers, signal: ctrl.signal });
  } catch (err) {
    clearTimeout(timer);
    const reason = err && err.name === 'AbortError' ? 'timeout' : (err && err.message) || 'unknown';
    return res.status(502).json({ error: 'Backend unreachable', reason });
  }
  clearTimeout(timer);

  const body = await upstream.text();

  // Edge cache: cache the response for EDGE_TTL[path] seconds, and serve a
  // stale copy for up to 10× that while fresh data fetches.
  const ttl = EDGE_TTL[path] || 60;
  res.setHeader('Cache-Control', `public, s-maxage=${ttl}, stale-while-revalidate=${ttl * 10}`);
  // Mirror upstream content type when present; default to JSON.
  const ct = upstream.headers.get('content-type') || 'application/json; charset=utf-8';
  res.setHeader('Content-Type', ct);

  return res.status(upstream.status).send(body);
};

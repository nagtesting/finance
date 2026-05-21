// api/backend/[...path].js
//
// Same-origin proxy from www.moneyveda.org → the Render Flask backend.
// This is what market-pulse.html v2 calls instead of hitting the Render URL
// from the browser directly. Solves CORS, edge-caches every response, hides
// the Render URL, and (with the matching env var) authenticates to Render so
// direct public access can be blocked.
//
// CHANGELOG
// ─────────
// v2 — Parse the backend path from req.url directly. Earlier version relied
//      on req.query.path being populated from the [...path] catch-all bracket
//      filename, which Vercel (without Next.js) does not actually populate
//      reliably — the function received an empty path on every request and
//      returned {"error":"Unknown endpoint","path":""} for everything.
//      Reading req.url avoids the catch-all-routing assumption entirely.
//
// ENV VARS (set in Vercel dashboard, NOT committed)
//   RENDER_BACKEND_URL    https://moneyveda-backend.onrender.com
//   RENDER_PROXY_SECRET   <long random string; same value in Render>

const RENDER_BASE  = process.env.RENDER_BACKEND_URL  || 'https://moneyveda-backend.onrender.com';
const PROXY_SECRET = process.env.RENDER_PROXY_SECRET || '';

// Edge cache TTLs (seconds). Browser-side localStorage SWR layers a separate
// cache on top — this is purely about Vercel's global edge cache.
const EDGE_TTL = {
  'market-commentary':    60,
  'market-cache':         30,
  'market-cache/symbols': 24 * 3600,
  'summary':              60,
  'signals':              60,
  'filings':              60,
  'prices':               30,
  'commentary':           300,
};

const ALLOWED = new Set(Object.keys(EDGE_TTL));

// Best-effort in-memory rate limit (per Vercel function instance).
const RATE = new Map();
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 120;
function clientIp(req) {
  const xf = req.headers['x-forwarded-for'];
  return (xf && xf.split(',')[0].trim()) || req.socket?.remoteAddress || 'anon';
}
function rateLimited(ip) {
  const now = Date.now();
  let rec = RATE.get(ip);
  if (!rec || rec.resetAt < now) { rec = { count: 0, resetAt: now + RATE_WINDOW_MS }; RATE.set(ip, rec); }
  rec.count += 1;
  return rec.count > RATE_MAX;
}

module.exports = async (req, res) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.setHeader('Allow', 'GET, HEAD');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // ── Parse path from req.url directly (the v2 fix) ────────────────────────
  // req.url looks like `/api/backend/market-cache?foo=bar` — we strip the
  // `/api/backend/` prefix to get the backend endpoint name, then forward
  // any query string to Render. No reliance on req.query.path.
  let urlObj;
  try {
    urlObj = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  } catch (e) {
    return res.status(400).json({ error: 'Bad request URL', detail: req.url });
  }

  const PREFIX = '/api/backend/';
  let path = urlObj.pathname;
  if (path.startsWith(PREFIX)) {
    path = path.slice(PREFIX.length).replace(/\/+$/, '');
  } else if (path === '/api/backend') {
    path = '';
  }

  if (!ALLOWED.has(path)) {
    // Include the URL we actually saw — makes diagnosis trivial if this fires.
    return res.status(404).json({
      error: 'Unknown endpoint',
      path,
      received_pathname: urlObj.pathname,
      allowed: [...ALLOWED],
    });
  }

  if (rateLimited(clientIp(req))) {
    res.setHeader('Retry-After', '60');
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  // ── Build the upstream URL and forward query params ─────────────────────
  const target = new URL(`${RENDER_BASE}/api/${path}`);
  urlObj.searchParams.forEach((v, k) => target.searchParams.set(k, v));

  const headers = { accept: 'application/json' };
  if (PROXY_SECRET) headers['x-proxy-secret'] = PROXY_SECRET;

  // Hard 15 s timeout — protects against Render free dynos that fail to wake.
  const ctrl  = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15_000);

  let upstream;
  try {
    upstream = await fetch(target.toString(), { headers, signal: ctrl.signal });
  } catch (err) {
    clearTimeout(timer);
    const reason = err && err.name === 'AbortError' ? 'timeout' : (err && err.message) || 'unknown';
    return res.status(502).json({ error: 'Backend unreachable', reason, target: target.toString() });
  }
  clearTimeout(timer);

  const body = await upstream.text();

  // Edge cache — TTL per endpoint, plus a generous stale-while-revalidate.
  const ttl = EDGE_TTL[path] || 60;
  res.setHeader('Cache-Control', `public, s-maxage=${ttl}, stale-while-revalidate=${ttl * 10}`);
  res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json; charset=utf-8');

  return res.status(upstream.status).send(body);
};

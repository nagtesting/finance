// api/proxy.js
//
// Same-origin proxy from www.moneyveda.org/api/backend/* → the Render Flask
// backend. Solves CORS, edge-caches every response, hides the Render URL,
// and (with the matching env var) authenticates to Render so direct public
// access can be blocked.
//
// ROUTING
// =======
// This file is reached via a vercel.json rewrite — NOT via filename-based
// catch-all routing. The rewrite is:
//
//   { "source": "/api/backend/:path*", "destination": "/api/proxy?_path=:path*" }
//
// So a browser request to `/api/backend/api/summary?limit=50` gets
// rewritten internally to `/api/proxy?_path=api/summary&limit=50`, and
// this function reads `req.query._path` to know which backend endpoint
// the browser actually wanted.
//
// WHY NOT api/backend/[...path].js?
//   Plain Vercel projects (without Next.js) do NOT support the
//   `[...catchall].js` filename spread syntax. That filename only matches
//   single-segment paths, returning Vercel's framework 404 for any URL
//   with two or more segments after the prefix. The vercel.json rewrite
//   above avoids the issue entirely — works on every Vercel project.
//
// ENV VARS (set in Vercel dashboard, NOT committed)
//   RENDER_BACKEND_URL    https://moneyveda-backend.onrender.com
//   RENDER_PROXY_SECRET   <long random string; same value in Render>

const RENDER_BASE  = process.env.RENDER_BACKEND_URL  || 'https://moneyveda-backend.onrender.com';
const PROXY_SECRET = process.env.RENDER_PROXY_SECRET || '';

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

  // ── Resolve the backend endpoint path ───────────────────────────────────
  // Primary source: the _path query param set by the vercel.json rewrite.
  // Fallback: parse from req.url, in case someone hits /api/proxy directly
  // or the rewrite isn't yet active.
  let path = req.query._path;
  if (Array.isArray(path)) path = path[0];
  path = (path || '').toString();

  if (!path) {
    try {
      const urlObj = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
      if (urlObj.pathname.startsWith('/api/backend/')) {
        path = urlObj.pathname.slice('/api/backend/'.length);
      }
    } catch (_) {}
  }
  path = path.replace(/\/+$/, '');

  // Tolerate the doubled `api/` from `API_BASE + '/api/summary'` in the HTML.
  if (path.startsWith('api/')) path = path.slice(4);

  if (!ALLOWED.has(path)) {
    return res.status(404).json({
      error: 'Unknown endpoint',
      resolved_path: path,
      received_query: req.query,
      received_url:   req.url,
      allowed: [...ALLOWED],
    });
  }

  if (rateLimited(clientIp(req))) {
    res.setHeader('Retry-After', '60');
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  // ── Build upstream URL and forward query params (except _path) ──────────
  const target = new URL(`${RENDER_BASE}/api/${path}`);
  for (const [k, v] of Object.entries(req.query || {})) {
    if (k === '_path') continue;
    target.searchParams.set(k, Array.isArray(v) ? v[0] : v);
  }

  const headers = { accept: 'application/json' };
  if (PROXY_SECRET) headers['x-proxy-secret'] = PROXY_SECRET;

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
  const ttl  = EDGE_TTL[path] || 60;
  res.setHeader('Cache-Control', `public, s-maxage=${ttl}, stale-while-revalidate=${ttl * 10}`);
  res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json; charset=utf-8');
  return res.status(upstream.status).send(body);
};

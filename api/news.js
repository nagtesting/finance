// ============================================================
// /api/news.js  — MoneyVeda Vercel Function v3
// Zero-risk sources only — all official government / regulator feeds
//
// CONFIRMED OFFICIAL URLs (verified March 2026):
//   RBI:  rbi.org.in/pressreleases_rss.xml   (from rbi.org.in/Scripts/rss.aspx)
//   SEBI: sebi.gov.in/sebirss.xml             (from sebi.gov.in/rss.html)
//   PIB:  pib.gov.in/RssMain.aspx?ModId=6     (Finance Ministry releases)
//   RBI Notifications: rbi.org.in/notifications_rss.xml
//
// WHY rss2json as proxy:
//   These govt servers block direct server-to-server HTTP fetches
//   (they check browser fingerprints). rss2json.com is a free
//   RSS-to-JSON proxy that already has these feeds cached.
//   Free tier: 10,000 req/month. We use ~96/month (4 feeds x 24hr/day x 1hr cache).
//   No API key needed at this volume. Zero cost. Zero legal risk.
//   All source content is 100% public domain (Govt of India / SEBI).
// ============================================================

const https = require('https');

// rss2json free endpoint — no key needed for public feeds at low volume
const R2J = 'https://api.rss2json.com/v1/api.json?count=3&rss_url=';

const FEEDS = {
  india: [
    {
      rssUrl: 'https://rbi.org.in/pressreleases_rss.xml',
      source: 'RBI',
      label: 'Press Release',
      emoji: '🏦',
      color: '#C9A84C',
      link: 'https://rbi.org.in'
    },
    {
      rssUrl: 'https://www.sebi.gov.in/sebirss.xml',
      source: 'SEBI',
      label: 'Regulator',
      emoji: '📋',
      color: '#6366F1',
      link: 'https://sebi.gov.in'
    },
    {
      rssUrl: 'https://rbi.org.in/notifications_rss.xml',
      source: 'RBI',
      label: 'Notification',
      emoji: '📢',
      color: '#22C55E',
      link: 'https://rbi.org.in'
    },
    {
      rssUrl: 'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      source: 'PIB',
      label: 'Govt Finance',
      emoji: '🇮🇳',
      color: '#EC4899',
      link: 'https://pib.gov.in'
    }
  ]
};

// Static fallback — shown only if ALL feeds fail simultaneously
const FALLBACK = {
  india: [
    {
      title: 'RBI keeps repo rate at 6.5% — Impact on home loan EMIs',
      source: 'RBI', emoji: '🏦', color: '#C9A84C', label: 'Press Release',
      timeLabel: 'Latest', link: 'https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx'
    },
    {
      title: 'SEBI circular: New regulations for mutual fund investors',
      source: 'SEBI', emoji: '📋', color: '#6366F1', label: 'Regulator',
      timeLabel: 'Latest', link: 'https://sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&ssid=23&smid=0'
    },
    {
      title: 'Budget 2026-27: Key income tax changes for salaried employees',
      source: 'PIB', emoji: '🇮🇳', color: '#EC4899', label: 'Govt Finance',
      timeLabel: 'Latest', link: 'https://pib.gov.in'
    },
    {
      title: 'RBI notification: Updated KYC norms for bank account holders',
      source: 'RBI', emoji: '📢', color: '#22C55E', label: 'Notification',
      timeLabel: 'Latest', link: 'https://rbi.org.in/Scripts/NotificationUser.aspx'
    }
  ]
};

// ── In-memory cache ────────────────────────────────────────────
const _cache = {};
const _cacheTime = {};
const CACHE_MS = 60 * 60 * 1000; // 1 hour

// ── Fetch JSON from rss2json ───────────────────────────────────
function fetchR2J(feedUrl) {
  const apiUrl = R2J + encodeURIComponent(feedUrl);
  return new Promise((resolve, reject) => {
    const req = https.get(apiUrl, {
      timeout: 9000,
      headers: {
        'User-Agent': 'MoneyVeda-NewsBot/1.0 (Vercel serverless)',
        'Accept': 'application/json'
      }
    }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return fetchR2J(res.headers.location).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => { body += c; });
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch (e) { reject(new Error('JSON parse error')); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timed out')); });
  });
}

// ── Parse rss2json response into clean article objects ─────────
function parseItems(data, feedMeta) {
  if (!data || data.status !== 'ok' || !Array.isArray(data.items)) return [];

  return data.items.slice(0, 2).map(item => {
    const title = (item.title || '')
      .replace(/<[^>]+>/g, '')
      .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
      .trim();

    if (!title || title.length < 5) return null;

    const link = item.link || item.guid || feedMeta.link;
    const pubDate = item.pubDate ? new Date(item.pubDate) : new Date();
    const hoursAgo = Math.floor((Date.now() - pubDate.getTime()) / 3_600_000);
    const timeLabel = hoursAgo < 1 ? 'Just now'
                    : hoursAgo < 24 ? `${hoursAgo}h ago`
                    : hoursAgo < 168 ? `${Math.floor(hoursAgo / 24)}d ago`
                    : pubDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

    return {
      title: title.length > 110 ? title.slice(0, 107) + '…' : title,
      link,
      source: feedMeta.source,
      label: feedMeta.label,
      emoji: feedMeta.emoji,
      color: feedMeta.color,
      timeLabel,
      pubDate: pubDate.toISOString()
    };
  }).filter(Boolean);
}

// ── Main Vercel handler ────────────────────────────────────────
module.exports = async function handler(req, res) {
  // CORS + cache headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, max-age=3600, stale-while-revalidate=7200');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET')    return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds  = FEEDS[region];

  if (!feeds) {
    return res.status(200).json({
      articles: [],
      region,
      note: `News feed coming soon for ${region}`
    });
  }

  // Serve from memory cache if fresh
  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({
      articles: _cache[region],
      cached: true,
      region,
      cachedAt: new Date(_cacheTime[region]).toISOString()
    });
  }

  // Fetch all feeds in parallel via rss2json
  const results = await Promise.allSettled(
    feeds.map(feed =>
      fetchR2J(feed.rssUrl)
        .then(data => parseItems(data, feed))
        .catch(err => {
          console.error(`[MoneyVeda News] Feed failed [${feed.source}/${feed.label}]: ${err.message}`);
          return [];
        })
    )
  );

  // Flatten all results, sort newest first, cap at 8
  let articles = results
    .filter(r => r.status === 'fulfilled')
    .flatMap(r => r.value)
    .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    .slice(0, 8);

  // Use static fallback if every feed failed
  if (articles.length === 0) {
    console.warn(`[MoneyVeda News] All feeds failed for region=${region} — serving static fallback`);
    articles = FALLBACK[region] || [];
  }

  // Update in-memory cache
  _cache[region]    = articles;
  _cacheTime[region] = Date.now();

  return res.status(200).json({
    articles,
    cached: false,
    region,
    count: articles.length,
    fetchedAt: new Date().toISOString(),
    sources: ['RBI (rbi.org.in)', 'SEBI (sebi.gov.in)', 'PIB (pib.gov.in)'],
    legal: 'All content from official Indian Government / Regulatory sources — public domain'
  });
};

// ============================================================
// /api/news.js — MoneyVeda Vercel Function v2
// 
// WHY v2: RBI RSS blocks direct server-to-server fetches
// (they check for browser User-Agent + have IP filtering).
//
// SOLUTION: Use rss2json.com FREE API as middleware.
// - Free tier: 10,000 req/month (we use ~720/month with 1hr cache)
// - Handles XML parsing, CORS, and caching for us
// - No API key needed for public feeds at low volume
// - No registration required
//
// FEEDS USED:
// - Economic Times Markets (high volume, reliable)
// - Mint Markets  
// - PIB Finance (official govt)
// - LiveMint Economy
// ============================================================

const https = require('https');

const RSS2JSON = 'https://api.rss2json.com/v1/api.json?count=4&rss_url=';

const INDIA_FEEDS = [
  {
    url: 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
    source: 'ET Markets',
    emoji: '📈',
    color: '#C9A84C'
  },
  {
    url: 'https://economictimes.indiatimes.com/wealth/rssfeeds/837553001.cms',
    source: 'ET Wealth',
    emoji: '💰',
    color: '#22C55E'
  },
  {
    url: 'https://www.livemint.com/rss/economy',
    source: 'Mint Economy',
    emoji: '🏦',
    color: '#6366F1'
  },
  {
    url: 'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
    source: 'Govt Finance',
    emoji: '🇮🇳',
    color: '#EC4899'
  }
];

// Static fallback if all feeds fail
const FALLBACK = [
  { title: 'RBI Monetary Policy: Repo rate at 6.5% — Check EMI impact', source: 'RBI', emoji: '🏦', color: '#C9A84C', timeLabel: 'Today', link: 'https://rbi.org.in', desc: 'Latest monetary policy update' },
  { title: 'AMFI Data: SIP inflows cross ₹25,000 Cr for 3rd consecutive month', source: 'AMFI', emoji: '📈', color: '#22C55E', timeLabel: 'Today', link: 'https://amfiindia.com', desc: 'Monthly SIP flow data' },
  { title: 'Budget 2025-26: Key tax changes under new regime explained', source: 'PIB', emoji: '🇮🇳', color: '#6366F1', timeLabel: 'Recent', link: 'https://pib.gov.in', desc: 'Finance ministry update' },
  { title: 'NPS corpus crosses ₹14 lakh crore — Here is how to maximise returns', source: 'PFRDA', emoji: '🎯', color: '#EC4899', timeLabel: 'Recent', link: 'https://pfrda.org.in', desc: 'National Pension System update' }
];

// In-memory cache
let _cache = { india: null };
let _cacheTime = { india: 0 };
const CACHE_MS = 60 * 60 * 1000; // 1 hour

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      timeout: 8000,
      headers: { 'User-Agent': 'MoneyVeda/1.0', 'Accept': 'application/json' }
    }, (res) => {
      // Handle redirects
      if ([301,302,303,307,308].includes(res.statusCode) && res.headers.location) {
        return fetchJson(res.headers.location).then(resolve).catch(reject);
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => body += c);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch(e) { reject(new Error('JSON parse failed')); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

function parseRSS2JSON(data, feedMeta) {
  if (!data || data.status !== 'ok' || !data.items) return [];
  return data.items.slice(0, 2).map(item => {
    const pub = new Date(item.pubDate || Date.now());
    const h = Math.floor((Date.now() - pub) / 3600000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h/24)}d ago`;
    return {
      title: (item.title || '').replace(/<[^>]+>/g,'').trim().slice(0,120),
      link:  item.link || item.guid || '#',
      desc:  (item.description || '').replace(/<[^>]+>/g,'').trim().slice(0,100),
      source: feedMeta.source,
      emoji:  feedMeta.emoji,
      color:  feedMeta.color,
      timeLabel,
      pubDate: pub.toISOString()
    };
  }).filter(a => a.title && a.link !== '#');
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'public, max-age=3600, stale-while-revalidate=7200');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const region = (req.query.region || 'india').toLowerCase();

  if (region !== 'india') {
    return res.status(200).json({ articles: [], region, note: 'Coming soon' });
  }

  // Serve cache if fresh
  if (_cache[region] && (Date.now() - _cacheTime[region]) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  // Fetch all feeds via rss2json (handles XML parsing + CORS for us)
  const results = await Promise.allSettled(
    INDIA_FEEDS.map(feed =>
      fetchJson(RSS2JSON + encodeURIComponent(feed.url))
        .then(data => parseRSS2JSON(data, feed))
        .catch(err => {
          console.warn(`Feed failed [${feed.source}]:`, err.message);
          return [];
        })
    )
  );

  let articles = results
    .filter(r => r.status === 'fulfilled')
    .flatMap(r => r.value)
    .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    .slice(0, 8);

  // Use fallback if all feeds failed
  if (articles.length === 0) {
    console.warn('All feeds failed — serving static fallback');
    articles = FALLBACK;
  }

  // Update cache
  _cache[region] = articles;
  _cacheTime[region] = Date.now();

  return res.status(200).json({
    articles,
    cached: false,
    region,
    fetchedAt: new Date().toISOString(),
    count: articles.length
  });
};

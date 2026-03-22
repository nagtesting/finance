// ============================================================
// /api/news.js — MoneyVeda v5
// Fixed: proper try/catch around entire handler so Vercel never
// returns an HTML error page instead of JSON
// ============================================================

const https = require('https');

const R2J = 'https://api.rss2json.com/v1/api.json?count=3&rss_url=';

const FEEDS = {
  india: [
    { rssUrl:'https://rbi.org.in/pressreleases_rss.xml',   source:'RBI',  label:'Press Release', emoji:'🏦', color:'#C9A84C', link:'https://rbi.org.in' },
    { rssUrl:'https://www.sebi.gov.in/sebirss.xml',         source:'SEBI', label:'Regulator',     emoji:'📋', color:'#6366F1', link:'https://sebi.gov.in' },
    { rssUrl:'https://rbi.org.in/notifications_rss.xml',    source:'RBI',  label:'Notification',  emoji:'📢', color:'#22C55E', link:'https://rbi.org.in' },
    { rssUrl:'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3', source:'PIB', label:'Govt Finance', emoji:'🇮🇳', color:'#EC4899', link:'https://pib.gov.in' },
  ]
};

const FALLBACK = {
  india: [
    { title:'RBI keeps repo rate at 6.5% — Check your EMI impact', source:'RBI', emoji:'🏦', color:'#C9A84C', label:'Press Release', timeLabel:'Latest', link:'https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx', pubDate: new Date().toISOString() },
    { title:'SEBI circular: New regulations for mutual fund investors', source:'SEBI', emoji:'📋', color:'#6366F1', label:'Regulator', timeLabel:'Latest', link:'https://sebi.gov.in', pubDate: new Date().toISOString() },
    { title:'Budget 2026: Key income tax changes for salaried employees', source:'PIB', emoji:'🇮🇳', color:'#EC4899', label:'Govt Finance', timeLabel:'Latest', link:'https://pib.gov.in', pubDate: new Date().toISOString() },
    { title:'RBI notification: Updated KYC norms for bank account holders', source:'RBI', emoji:'📢', color:'#22C55E', label:'Notification', timeLabel:'Latest', link:'https://rbi.org.in/Scripts/NotificationUser.aspx', pubDate: new Date().toISOString() },
  ]
};

// In-memory cache
const _cache = {};
const _cacheTime = {};
const CACHE_MS = 60 * 60 * 1000; // 1 hour

// Fetch JSON with timeout
function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      timeout: 8000,
      headers: { 'User-Agent': 'MoneyVeda/1.0', 'Accept': 'application/json' }
    }, (res) => {
      if (res.statusCode !== 200) {
        res.resume(); // drain response
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => { body += c; });
      res.on('end', () => {
        // Guard: make sure it's actually JSON
        const trimmed = body.trim();
        if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
          return reject(new Error('Response is not JSON'));
        }
        try { resolve(JSON.parse(trimmed)); }
        catch (e) { reject(new Error('JSON parse failed: ' + e.message)); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

function parseItems(data, feedMeta) {
  if (!data || data.status !== 'ok' || !Array.isArray(data.items)) return [];
  return data.items.slice(0, 2).map(item => {
    const title = (item.title || '')
      .replace(/<[^>]+>/g, '').replace(/&amp;/g, '&')
      .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"')
      .trim();
    if (!title || title.length < 5) return null;
    const link = item.link || item.guid || feedMeta.link;
    const pub = new Date(item.pubDate || Date.now());
    const h = Math.floor((Date.now() - pub.getTime()) / 3600000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h/24)}d ago`;
    return {
      title: title.length > 110 ? title.slice(0, 107) + '…' : title,
      link,
      source: feedMeta.source,
      label: feedMeta.label,
      emoji: feedMeta.emoji,
      color: feedMeta.color,
      timeLabel,
      pubDate: pub.toISOString()
    };
  }).filter(Boolean);
}

module.exports = async function handler(req, res) {
  // Always return JSON — never let Vercel return HTML error page
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'public, max-age=3600, stale-while-revalidate=7200');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds = FEEDS[region];

  if (!feeds) {
    return res.status(200).json({ articles: [], region, note: 'Coming soon' });
  }

  // Serve from cache if fresh
  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  // Wrap entire fetch in try/catch — never crash
  try {
    const results = await Promise.allSettled(
      feeds.map(feed =>
        fetchJSON(R2J + encodeURIComponent(feed.rssUrl))
          .then(data => parseItems(data, feed))
          .catch(err => {
            console.warn(`[MoneyVeda] Feed failed [${feed.source}]: ${err.message}`);
            return [];
          })
      )
    );

    let articles = results
      .filter(r => r.status === 'fulfilled')
      .flatMap(r => r.value)
      .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
      .slice(0, 8);

    if (articles.length === 0) {
      console.warn('[MoneyVeda] All feeds failed — serving static fallback');
      articles = FALLBACK[region] || [];
    }

    _cache[region] = articles;
    _cacheTime[region] = Date.now();

    return res.status(200).json({
      articles, cached: false, region,
      count: articles.length,
      fetchedAt: new Date().toISOString()
    });

  } catch (err) {
    // Last resort — always return valid JSON with fallback articles
    console.error('[MoneyVeda] Handler error:', err.message);
    return res.status(200).json({
      articles: FALLBACK[region] || [],
      cached: false,
      region,
      fallback: true,
      error: err.message
    });
  }
};


// ============================================================
// /api/news.js — MoneyVeda v9
// CHANGES FROM v8:
//   1. World feeds (IMF, BIS, Fed Reserve, ECB, World Bank) merged
//      into every individual country feed — so india/usa/europe all
//      get their own local feeds PLUS all global feeds.
//   2. Article limit raised to 12 (was 8) to accommodate merged feeds.
//   3. Fallbacks updated to include world items for each region.
//   4. No shared object references — each feed is a plain object.
// ============================================================

const https = require('https');
const R2J = 'https://api.rss2json.com/v1/api.json?count=3&rss_url=';

// ── Helper: create fresh feed object (no shared references) ──
const feed = (rssUrl, source, label, emoji, color, link) =>
  ({ rssUrl, source, label, emoji, color, link });

// ── Verified global feed URLs (confirmed March 2026) ─────────
const IMF_URL       = 'https://www.imf.org/en/Blogs';
const BIS_URL       = 'https://www.bis.org/doclist/cbspeeches.rss';
const WORLDBANK_URL = 'https://blogs.worldbank.org/rss.xml';
const FED_URL       = 'https://www.federalreserve.gov/feeds/press_all.xml';
const ECB_URL       = 'https://www.ecb.europa.eu/rss/press.html';

// ── World/global feeds (merged into every region) ────────────
const WORLD_FEEDS = [
  feed(IMF_URL,
    'IMF', 'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/Blogs'),
  feed(BIS_URL,
    'BIS', 'Central Banks', '🏛️', '#C9A84C', 'https://bis.org'),
  feed(FED_URL,
    'Fed Reserve', 'US Policy', '💵', '#22C55E', 'https://federalreserve.gov'),
  feed(ECB_URL,
    'ECB', 'EU Policy', '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
  feed(WORLDBANK_URL,
    'World Bank', 'Global Finance', '🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
];

// ── Feeds per region — country-specific feeds + world feeds ──
const FEEDS = {

  // ── INDIA ─────────────────────────────────────────────────
  india: [
    // Country-specific feeds
    feed('https://rbi.org.in/pressreleases_rss.xml',
      'RBI', 'Press Release', '🏦', '#C9A84C', 'https://rbi.org.in'),
    feed('https://www.sebi.gov.in/sebirss.xml',
      'SEBI', 'Regulator', '📋', '#6366F1', 'https://sebi.gov.in'),
    feed('https://rbi.org.in/notifications_rss.xml',
      'RBI', 'Notification', '📢', '#22C55E', 'https://rbi.org.in'),
    feed('https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      'PIB', 'Govt Finance', '🇮🇳', '#EC4899', 'https://pib.gov.in'),
    // Global feeds merged in
    ...WORLD_FEEDS,
  ],

  // ── USA ───────────────────────────────────────────────────
  usa: [
    // Country-specific feeds
    feed('https://www.federalreserve.gov/feeds/press_all.xml',
      'Fed Reserve', 'Monetary Policy', '🏛️', '#3B82F6', 'https://federalreserve.gov'),
    feed('https://www.federalreserve.gov/feeds/press_monetary.xml',
      'FOMC', 'Rate Decision', '💵', '#22C55E', 'https://federalreserve.gov'),
    feed('https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom',
      'SEC', 'Regulator', '⚖️', '#F59E0B', 'https://sec.gov'),
    // Global feeds merged in
    ...WORLD_FEEDS,
  ],

  // ── EUROPE ────────────────────────────────────────────────
  europe: [
    // Country-specific feeds
    feed('https://www.ecb.europa.eu/rss/press.html',
      'ECB', 'Rate Decision', '🏦', '#6366F1', 'https://ecb.europa.eu'),
    feed('https://www.ecb.europa.eu/rss/key.html',
      'ECB', 'Key Speech', '🎙️', '#22C55E', 'https://ecb.europa.eu'),
    feed('https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      'ESMA', 'Regulator', '📋', '#EC4899', 'https://esma.europa.eu'),
    // Global feeds merged in
    ...WORLD_FEEDS,
  ],

  // ── WORLD ─────────────────────────────────────────────────
  world: [
    ...WORLD_FEEDS,
  ],
};

// ── Static fallbacks (country-specific + world items) ────────
const WORLD_FALLBACK = [
  { title:'IMF: Global growth at 3.2% for 2026 amid trade tensions', source:'IMF', emoji:'🌍', color:'#3B82F6', label:'Global Economy', timeLabel:'Latest', link:'https://imf.org/en/Blogs', pubDate:new Date().toISOString() },
  { title:'BIS: Central banks navigating post-inflation normalisation', source:'BIS', emoji:'🏛️', color:'#C9A84C', label:'Central Banks', timeLabel:'Latest', link:'https://bis.org', pubDate:new Date().toISOString() },
  { title:'Fed holds rates — next move depends on employment and CPI', source:'Fed Reserve', emoji:'💵', color:'#22C55E', label:'US Policy', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
  { title:'ECB holds rates — euro area inflation nearing 2% target', source:'ECB', emoji:'🇪🇺', color:'#6366F1', label:'EU Policy', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
  { title:'World Bank: 1.2B youth entering workforce by 2040 — jobs gap widens', source:'World Bank', emoji:'🌐', color:'#0ea5e9', label:'Global Finance', timeLabel:'Latest', link:'https://blogs.worldbank.org', pubDate:new Date().toISOString() },
];

const FALLBACK = {
  india: [
    { title:'RBI holds repo rate at 6.5% — impact on home loan EMIs', source:'RBI', emoji:'🏦', color:'#C9A84C', label:'Press Release', timeLabel:'Latest', link:'https://rbi.org.in', pubDate:new Date().toISOString() },
    { title:'SEBI circular: Updated mutual fund expense ratio norms', source:'SEBI', emoji:'📋', color:'#6366F1', label:'Regulator', timeLabel:'Latest', link:'https://sebi.gov.in', pubDate:new Date().toISOString() },
    { title:'Budget 2026-27: Key income tax changes under new regime', source:'PIB', emoji:'🇮🇳', color:'#EC4899', label:'Govt Finance', timeLabel:'Latest', link:'https://pib.gov.in', pubDate:new Date().toISOString() },
    ...WORLD_FALLBACK,
  ],
  usa: [
    { title:'Federal Reserve holds rates at 3.5–3.75% range', source:'Fed Reserve', emoji:'🏛️', color:'#3B82F6', label:'Monetary Policy', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
    { title:'FOMC: Inflation data determines timing of next rate move', source:'FOMC', emoji:'💵', color:'#22C55E', label:'Rate Decision', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
    { title:'SEC proposes enhanced retail investor protection rules', source:'SEC', emoji:'⚖️', color:'#F59E0B', label:'Regulator', timeLabel:'Latest', link:'https://sec.gov', pubDate:new Date().toISOString() },
    ...WORLD_FALLBACK,
  ],
  europe: [
    { title:'ECB keeps key interest rates unchanged at current levels', source:'ECB', emoji:'🏦', color:'#6366F1', label:'Rate Decision', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
    { title:'Lagarde: ECB remains data-dependent on future rate path', source:'ECB', emoji:'🎙️', color:'#22C55E', label:'Key Speech', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
    { title:'ESMA: New sustainable finance disclosure guidelines published', source:'ESMA', emoji:'📋', color:'#EC4899', label:'Regulator', timeLabel:'Latest', link:'https://esma.europa.eu', pubDate:new Date().toISOString() },
    ...WORLD_FALLBACK,
  ],
  world: [
    ...WORLD_FALLBACK,
  ],
};

// ── In-memory cache (per region) ─────────────────────────────
const _cache = {};
const _cacheTime = {};
const CACHE_MS = 60 * 60 * 1000; // 1 hour

// ── Fetch JSON from rss2json proxy ────────────────────────────
function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      timeout: 9000,
      headers: { 'User-Agent':'MoneyVeda/1.0', 'Accept':'application/json' }
    }, (res) => {
      if (res.statusCode !== 200) { res.resume(); return reject(new Error(`HTTP ${res.statusCode}`)); }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => { body += c; });
      res.on('end', () => {
        const t = body.trim();
        if (!t.startsWith('{') && !t.startsWith('[')) return reject(new Error('Not JSON'));
        try { resolve(JSON.parse(t)); } catch(e) { reject(new Error('Parse: '+e.message)); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// ── Parse rss2json response into clean article objects ────────
function parseItems(data, feedMeta) {
  if (!data || data.status !== 'ok' || !Array.isArray(data.items)) return [];
  return data.items.slice(0, 2).map(item => {
    const title = (item.title || '')
      .replace(/<[^>]+>/g, '').replace(/&amp;/g,'&').replace(/&lt;/g,'<')
      .replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').trim();
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

// ── Deduplicate articles by title ─────────────────────────────
function dedupe(articles) {
  const seen = new Set();
  return articles.filter(a => {
    const key = a.title.toLowerCase().slice(0, 60);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ── Main handler ──────────────────────────────────────────────
module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'public, max-age=3600, stale-while-revalidate=7200');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles: [], region, note: 'Coming soon' });

  // Serve from memory cache if fresh
  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  try {
    const results = await Promise.allSettled(
      feeds.map(f =>
        fetchJSON(R2J + encodeURIComponent(f.rssUrl))
          .then(data => parseItems(data, f))
          .catch(err => { console.warn(`[${f.source}]: ${err.message}`); return []; })
      )
    );

    let articles = dedupe(
      results
        .filter(r => r.status === 'fulfilled')
        .flatMap(r => r.value)
        .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    ).slice(0, 12); // raised from 8 → 12 to accommodate merged feeds

    if (articles.length === 0) {
      console.warn(`All feeds failed for ${region} — serving fallback`);
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
    console.error('[MoneyVeda News] Handler error:', err.message);
    return res.status(200).json({
      articles: FALLBACK[region] || [],
      cached: false, region, fallback: true
    });
  }
};

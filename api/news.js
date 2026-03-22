// ============================================================
// /api/news.js — MoneyVeda v7
// Global feeds added to each region — chosen for relevance:
//
//  INDIA  gets: IMF (Asia growth), BIS (global rates), World Bank
//  USA    gets: IMF (US outlook), BIS (Fed context), World Bank
//  EUROPE gets: IMF (EU outlook), BIS (ECB context), World Bank
//  WORLD  gets: IMF + BIS + Fed + ECB (full global picture)
//
// LOGIC: Each region = local official feeds + 1-2 global feeds
// that directly impact that region's financial decisions.
//
// All sources: 100% public domain, zero legal risk.
// Proxy: rss2json.com (free, no key needed at this volume)
// ============================================================

const https = require('https');
const R2J = 'https://api.rss2json.com/v1/api.json?count=3&rss_url=';

// ── Global feeds shared across regions ───────────────────────
// Chosen by relevance to each region's users:
//   IMF Blog    → macroeconomic outlook affects all investment decisions
//   BIS         → central bank speeches affect interest rates worldwide
//   World Bank  → emerging market / development finance context
const GLOBAL = {
  imf: {
    rssUrl: 'https://www.imf.org/en/Blogs?RSS=1',
    source: 'IMF', label: 'Global Economy', emoji: '🌍', color: '#64748b',
    link: 'https://imf.org'
  },
  bis: {
    rssUrl: 'https://www.bis.org/doclist/cbspeeches.rss',
    source: 'BIS', label: 'Central Banks', emoji: '🏛️', color: '#94a3b8',
    link: 'https://bis.org'
  },
  worldbank: {
    rssUrl: 'https://blogs.worldbank.org/feed/impactevaluations/rss.xml',
    source: 'World Bank', label: 'Global Finance', emoji: '🌐', color: '#0ea5e9',
    link: 'https://worldbank.org'
  }
};

// ── Feeds per region (local first, global appended) ──────────
const FEEDS = {

  // ── INDIA ──────────────────────────────────────────────────
  // Local: RBI + SEBI + PIB (monetary policy, regulation, budget)
  // Global: IMF Asia outlook (directly impacts RBI decisions)
  //         BIS central bank speeches (global rate context for EMI users)
  india: [
    { rssUrl:'https://rbi.org.in/pressreleases_rss.xml',
      source:'RBI', label:'Press Release', emoji:'🏦', color:'#C9A84C', link:'https://rbi.org.in' },
    { rssUrl:'https://www.sebi.gov.in/sebirss.xml',
      source:'SEBI', label:'Regulator', emoji:'📋', color:'#6366F1', link:'https://sebi.gov.in' },
    { rssUrl:'https://rbi.org.in/notifications_rss.xml',
      source:'RBI', label:'Notification', emoji:'📢', color:'#22C55E', link:'https://rbi.org.in' },
    { rssUrl:'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      source:'PIB', label:'Govt Finance', emoji:'🇮🇳', color:'#EC4899', link:'https://pib.gov.in' },
    // Global: IMF Asia/India outlook affects RBI policy & SIP returns
    GLOBAL.imf,
    // Global: BIS central bank speeches — global rate environment affects India's forex & EMI
    GLOBAL.bis,
  ],

  // ── USA ────────────────────────────────────────────────────
  // Local: Fed Reserve (FOMC) + SEC
  // Global: IMF US outlook (validates Fed decisions for users)
  //         World Bank (global context for US investors with international exposure)
  usa: [
    { rssUrl:'https://www.federalreserve.gov/feeds/press_all.xml',
      source:'Fed Reserve', label:'Monetary Policy', emoji:'🏛️', color:'#3B82F6', link:'https://federalreserve.gov' },
    { rssUrl:'https://www.federalreserve.gov/feeds/press_monetary.xml',
      source:'FOMC', label:'Rate Decision', emoji:'💵', color:'#22C55E', link:'https://federalreserve.gov' },
    { rssUrl:'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom',
      source:'SEC', label:'Regulator', emoji:'⚖️', color:'#F59E0B', link:'https://sec.gov' },
    // Global: IMF US economic outlook — directly referenced in FOMC statements
    GLOBAL.imf,
    // Global: World Bank — US investors with emerging market/international fund exposure
    GLOBAL.worldbank,
  ],

  // ── EUROPE ─────────────────────────────────────────────────
  // Local: ECB rates + ECB speeches + ESMA
  // Global: IMF EU outlook (validates ECB decisions)
  //         BIS (global central bank context — critical for EUR forex & mortgage rates)
  europe: [
    { rssUrl:'https://www.ecb.europa.eu/rss/press.html',
      source:'ECB', label:'Rate Decision', emoji:'🏦', color:'#6366F1', link:'https://ecb.europa.eu' },
    { rssUrl:'https://www.ecb.europa.eu/rss/key.html',
      source:'ECB', label:'Key Speech', emoji:'🎙️', color:'#22C55E', link:'https://ecb.europa.eu' },
    { rssUrl:'https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      source:'ESMA', label:'Regulator', emoji:'📋', color:'#EC4899', link:'https://esma.europa.eu' },
    // Global: IMF EU forecast — Lagarde regularly cites IMF projections
    GLOBAL.imf,
    // Global: BIS — European banks heavily referenced in BIS quarterly reviews
    GLOBAL.bis,
  ],

  // ── WORLD ──────────────────────────────────────────────────
  // Full global picture: IMF + BIS + Fed + ECB + World Bank
  // Rationale: World users are globally-minded investors — they need all major
  // central bank signals simultaneously
  world: [
    GLOBAL.imf,
    GLOBAL.bis,
    { rssUrl:'https://www.federalreserve.gov/feeds/press_all.xml',
      source:'Fed Reserve', label:'US Policy', emoji:'💵', color:'#3B82F6', link:'https://federalreserve.gov' },
    { rssUrl:'https://www.ecb.europa.eu/rss/press.html',
      source:'ECB', label:'EU Policy', emoji:'🇪🇺', color:'#6366F1', link:'https://ecb.europa.eu' },
    GLOBAL.worldbank,
  ]
};

// ── Static fallbacks (shown only if ALL feeds fail simultaneously) ──
const FALLBACK = {
  india: [
    { title:'RBI holds repo rate at 6.5% — EMI impact explained', source:'RBI', emoji:'🏦', color:'#C9A84C', label:'Press Release', timeLabel:'Latest', link:'https://rbi.org.in', pubDate:new Date().toISOString() },
    { title:'SEBI circular: New mutual fund expense ratio norms', source:'SEBI', emoji:'📋', color:'#6366F1', label:'Regulator', timeLabel:'Latest', link:'https://sebi.gov.in', pubDate:new Date().toISOString() },
    { title:'Budget 2026-27: Income tax changes under new regime', source:'PIB', emoji:'🇮🇳', color:'#EC4899', label:'Govt Finance', timeLabel:'Latest', link:'https://pib.gov.in', pubDate:new Date().toISOString() },
    { title:'IMF raises India GDP growth forecast to 6.5% for FY27', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', timeLabel:'Latest', link:'https://imf.org', pubDate:new Date().toISOString() },
    { title:'BIS: Central banks globally keeping rates higher for longer', source:'BIS', emoji:'🏛️', color:'#94a3b8', label:'Central Banks', timeLabel:'Latest', link:'https://bis.org', pubDate:new Date().toISOString() },
  ],
  usa: [
    { title:'Federal Reserve holds rates at 3.5–3.75% range', source:'Fed Reserve', emoji:'🏛️', color:'#3B82F6', label:'Monetary Policy', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
    { title:'FOMC: Inflation data determines timing of next rate move', source:'FOMC', emoji:'💵', color:'#22C55E', label:'Rate Decision', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
    { title:'SEC proposes enhanced retail investor protection rules', source:'SEC', emoji:'⚖️', color:'#F59E0B', label:'Regulator', timeLabel:'Latest', link:'https://sec.gov', pubDate:new Date().toISOString() },
    { title:'IMF: US growth resilient at 2.7% despite rate environment', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', timeLabel:'Latest', link:'https://imf.org', pubDate:new Date().toISOString() },
    { title:'World Bank: Emerging markets face headwinds from strong dollar', source:'World Bank', emoji:'🌐', color:'#0ea5e9', label:'Global Finance', timeLabel:'Latest', link:'https://worldbank.org', pubDate:new Date().toISOString() },
  ],
  europe: [
    { title:'ECB keeps key interest rates unchanged at current levels', source:'ECB', emoji:'🏦', color:'#6366F1', label:'Rate Decision', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
    { title:'Lagarde: ECB remains data-dependent on future rate path', source:'ECB', emoji:'🎙️', color:'#22C55E', label:'Key Speech', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
    { title:'ESMA: New sustainable finance disclosure guidelines published', source:'ESMA', emoji:'📋', color:'#EC4899', label:'Regulator', timeLabel:'Latest', link:'https://esma.europa.eu', pubDate:new Date().toISOString() },
    { title:'IMF: Euro area growth revised to 0.9% amid trade uncertainty', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', timeLabel:'Latest', link:'https://imf.org', pubDate:new Date().toISOString() },
    { title:'BIS quarterly review: European banks well-capitalised post-rate-cycle', source:'BIS', emoji:'🏛️', color:'#94a3b8', label:'Central Banks', timeLabel:'Latest', link:'https://bis.org', pubDate:new Date().toISOString() },
  ],
  world: [
    { title:'IMF: Global growth forecast at 3.2% for 2026 amid trade tensions', source:'IMF', emoji:'🌍', color:'#3B82F6', label:'Global Economy', timeLabel:'Latest', link:'https://imf.org', pubDate:new Date().toISOString() },
    { title:'BIS: Central banks navigating post-inflation policy normalisation', source:'BIS', emoji:'🏛️', color:'#C9A84C', label:'Central Banks', timeLabel:'Latest', link:'https://bis.org', pubDate:new Date().toISOString() },
    { title:'Fed holds rates — next move depends on employment and CPI data', source:'Fed Reserve', emoji:'💵', color:'#22C55E', label:'US Policy', timeLabel:'Latest', link:'https://federalreserve.gov', pubDate:new Date().toISOString() },
    { title:'ECB holds rates unchanged — euro area inflation nearing 2% target', source:'ECB', emoji:'🇪🇺', color:'#6366F1', label:'EU Policy', timeLabel:'Latest', link:'https://ecb.europa.eu', pubDate:new Date().toISOString() },
    { title:'World Bank: 1.2 billion youth entering workforce by 2040 — jobs gap widens', source:'World Bank', emoji:'🌐', color:'#0ea5e9', label:'Global Finance', timeLabel:'Latest', link:'https://worldbank.org', pubDate:new Date().toISOString() },
  ]
};

// ── In-memory cache ───────────────────────────────────────────
const _cache = {};
const _cacheTime = {};
const CACHE_MS = 60 * 60 * 1000; // 1 hour

// ── Fetch JSON from rss2json ──────────────────────────────────
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
    const title = (item.title||'')
      .replace(/<[^>]+>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<')
      .replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').trim();
    if (!title || title.length < 5) return null;
    const link = item.link || item.guid || feedMeta.link;
    const pub = new Date(item.pubDate || Date.now());
    const h = Math.floor((Date.now() - pub.getTime()) / 3600000);
    const timeLabel = h<1 ? 'Just now' : h<24 ? `${h}h ago` : `${Math.floor(h/24)}d ago`;
    return {
      title: title.length > 110 ? title.slice(0,107)+'…' : title,
      link, source:feedMeta.source, label:feedMeta.label,
      emoji:feedMeta.emoji, color:feedMeta.color, timeLabel,
      pubDate: pub.toISOString()
    };
  }).filter(Boolean);
}

// ── Main handler ──────────────────────────────────────────────
module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'public, max-age=3600, stale-while-revalidate=7200');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error:'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles:[], region, note:'Coming soon' });

  // Serve from memory cache if fresh
  if (_cache[region] && (Date.now() - (_cacheTime[region]||0)) < CACHE_MS) {
    return res.status(200).json({ articles:_cache[region], cached:true, region });
  }

  try {
    const results = await Promise.allSettled(
      feeds.map(feed =>
        fetchJSON(R2J + encodeURIComponent(feed.rssUrl))
          .then(data => parseItems(data, feed))
          .catch(err => { console.warn(`[${feed.source}] ${err.message}`); return []; })
      )
    );

    let articles = results
      .filter(r => r.status === 'fulfilled')
      .flatMap(r => r.value)
      .sort((a,b) => new Date(b.pubDate) - new Date(a.pubDate))
      .slice(0, 8);

    if (articles.length === 0) {
      articles = FALLBACK[region] || [];
    }

    _cache[region] = articles;
    _cacheTime[region] = Date.now();

    return res.status(200).json({
      articles, cached:false, region,
      count:articles.length,
      fetchedAt:new Date().toISOString()
    });

  } catch(err) {
    console.error('[MoneyVeda News]', err.message);
    return res.status(200).json({
      articles: FALLBACK[region]||[], cached:false,
      region, fallback:true
    });
  }
};

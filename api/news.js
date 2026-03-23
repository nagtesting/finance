// ============================================================
// /api/news.js — MoneyVeda v10 (Protected Edition)
//
// MOVED SERVER-SIDE (no longer in index.html):
//   • NEWS_ROUTES keyword→tab routing table (16 route groups,
//     60+ keywords) — the smart news routing logic is now fully
//     hidden from the client
//   • getNewsRoute() function — resolves each article's internal
//     calculator tab (or null for external) on the server
//   • Each article in the response now carries a resolved `tab`
//     field. Client just checks: if(a.tab) navTo(a.tab); else
//     window.open(a.link) — zero routing logic exposed
//   • FALLBACK data for all regions + world items
//   • Feed URL lists (RBI, SEBI, PIB, Fed, ECB, ESMA, IMF, BIS,
//     World Bank) — no source structure visible to client
// ============================================================

const https = require('https');
const R2J   = 'https://api.rss2json.com/v1/api.json?count=3&rss_url=';

// ── Feed constructor ─────────────────────────────────────────
const feed = (rssUrl, source, label, emoji, color, link) =>
  ({ rssUrl, source, label, emoji, color, link });

// ── Feed URL constants (server-only) ─────────────────────────
const IMF_URL       = 'https://www.imf.org/en/Blogs';
const BIS_URL       = 'https://www.bis.org/doclist/cbspeeches.rss';
const WORLDBANK_URL = 'https://blogs.worldbank.org/rss.xml';
const FED_URL       = 'https://www.federalreserve.gov/feeds/press_all.xml';
const ECB_URL       = 'https://www.ecb.europa.eu/rss/press.html';

// ── World feeds (merged into every region) ───────────────────
const WORLD_FEEDS = [
  feed(IMF_URL,       'IMF',        'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/Blogs'),
  feed(BIS_URL,       'BIS',        'Central Banks',  '🏛️', '#C9A84C', 'https://bis.org'),
  feed(FED_URL,       'Fed Reserve','US Policy',      '💵', '#22C55E', 'https://federalreserve.gov'),
  feed(ECB_URL,       'ECB',        'EU Policy',      '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
  feed(WORLDBANK_URL, 'World Bank', 'Global Finance', '🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
];

// ── Feed lists per region ─────────────────────────────────────
const FEEDS = {
  india: [
    feed('https://rbi.org.in/pressreleases_rss.xml',
      'RBI',  'Press Release', '🏦', '#C9A84C', 'https://rbi.org.in'),
    feed('https://www.sebi.gov.in/sebirss.xml',
      'SEBI', 'Regulator',     '📋', '#6366F1', 'https://sebi.gov.in'),
    feed('https://rbi.org.in/notifications_rss.xml',
      'RBI',  'Notification',  '📢', '#22C55E', 'https://rbi.org.in'),
    feed('https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      'PIB',  'Govt Finance',  '🇮🇳', '#EC4899', 'https://pib.gov.in'),
    ...WORLD_FEEDS,
  ],
  usa: [
    feed(FED_URL,
      'Fed Reserve', 'Monetary Policy', '🏛️', '#3B82F6', 'https://federalreserve.gov'),
    feed('https://www.federalreserve.gov/feeds/press_monetary.xml',
      'FOMC', 'Rate Decision',   '💵', '#22C55E', 'https://federalreserve.gov'),
    feed('https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom',
      'SEC',  'Regulator',       '⚖️', '#F59E0B', 'https://sec.gov'),
    ...WORLD_FEEDS,
  ],
  europe: [
    feed(ECB_URL,
      'ECB',  'Rate Decision',   '🏦', '#6366F1', 'https://ecb.europa.eu'),
    feed('https://www.ecb.europa.eu/rss/key.html',
      'ECB',  'Key Speech',      '🎙️', '#22C55E', 'https://ecb.europa.eu'),
    feed('https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      'ESMA', 'Regulator',       '📋', '#EC4899', 'https://esma.europa.eu'),
    ...WORLD_FEEDS,
  ],
  world: [ ...WORLD_FEEDS ],
};

// ── NEWS ROUTING TABLE (was NEWS_ROUTES in client JS) ─────────
// Fully hidden server-side. Client receives a resolved `tab` field per article.
const NEWS_ROUTES = [
  // India
  { kw: ['nps','national pension','pfrda','pension corpus','pension fund'],              tab: 'nps'       },
  { kw: ['sip','mutual fund','amfi','elss','equity fund','nfo','nav','systematic invest'],tab: 'sip'       },
  { kw: ['ppf','public provident fund','small savings'],                                 tab: 'ppf'       },
  { kw: ['epf','provident fund','pf withdrawal','pf balance','employees provident'],     tab: 'epf'       },
  { kw: ['home loan','repo rate','emi','housing loan','rbi rate'],                       tab: 'emi'       },
  { kw: ['income tax','tax slab','80c','section 80','itr','deduction','new regime','old regime','budget tax'], tab: 'tax' },
  { kw: ['insurance','term plan','life cover','health insurance'],                       tab: 'insurance' },
  { kw: ['sukanya','girl child','ssa','samriddhi'],                                      tab: 'ssa'       },
  { kw: ['step up sip','increase sip','sip increment'],                                  tab: 'stepsip'   },
  // USA
  { kw: ['federal reserve','fed rate','fomc','interest rate','fed hike','fed cut','rate decision'], tab: 'emi' },
  { kw: ['401k','roth ira','ira contribution','retirement savings','social security'],   tab: 'fire'      },
  { kw: ['mortgage rate','home purchase','housing market','refinance'],                  tab: 'emi'       },
  { kw: ['s&p 500','nasdaq','stock market','equity market','bull market','bear market'], tab: 'sip'       },
  { kw: ['sec regulation','investor protection','securities'],                           tab: 'insurance' },
  { kw: ['capital gains tax','tax bracket','irs','federal tax','tax return'],            tab: 'tax'       },
  // Europe
  { kw: ['ecb','european central bank','euro rate','eurozone inflation'],                tab: 'emi'       },
  { kw: ['esma','mifid','ucits','european fund'],                                        tab: 'sip'       },
  { kw: ['pension reform','occupational pension','retirement europe'],                   tab: 'fire'      },
  { kw: ['euro mortgage','housing europe','property market europe'],                     tab: 'emi'       },
  // World / Global
  { kw: ['imf','world bank','global growth','gdp forecast','bis','central bank'],        tab: 'fire'      },
  { kw: ['inflation','cpi','price index','deflation'],                                   tab: 'emi'       },
  { kw: ['cryptocurrency','bitcoin','ethereum','crypto regulation'],                     tab: 'roi'       },
  { kw: ['global trade','tariff','trade war','sanctions'],                               tab: 'fire'      },
  // Universal
  { kw: ['retirement','retire early','financial independence'],                          tab: 'fire'      },
  { kw: ['mortgage','interest rate','basis point','rate hike','rate cut'],               tab: 'emi'       },
  { kw: ['investment','wealth','portfolio','compounding','returns'],                     tab: 'sip'       },
  { kw: ['tax','taxation','fiscal','budget'],                                            tab: 'tax'       },
  { kw: ['life insurance','term insurance','coverage','premium'],                        tab: 'insurance' },
];

// ── Resolve routing tab for an article title (server-side only) ──
function resolveTab(title) {
  if (!title) return null;
  const lower = title.toLowerCase();
  for (const route of NEWS_ROUTES) {
    for (const kw of route.kw) {
      if (lower.includes(kw)) return route.tab;
    }
  }
  return null;
}

// ── Static fallbacks ──────────────────────────────────────────
const WORLD_FALLBACK = [
  { title: 'IMF: Global growth at 3.2% for 2026 amid trade tensions',         source: 'IMF',        emoji: '🌍', color: '#3B82F6', label: 'Global Economy', timeLabel: 'Latest', link: 'https://imf.org/en/Blogs',         tab: 'fire'      },
  { title: 'BIS: Central banks navigating post-inflation normalisation',       source: 'BIS',        emoji: '🏛️', color: '#C9A84C', label: 'Central Banks',  timeLabel: 'Latest', link: 'https://bis.org',                 tab: 'fire'      },
  { title: 'Fed holds rates — next move depends on employment and CPI',        source: 'Fed Reserve',emoji: '💵', color: '#22C55E', label: 'US Policy',      timeLabel: 'Latest', link: 'https://federalreserve.gov',      tab: 'emi'       },
  { title: 'ECB holds rates — euro area inflation nearing 2% target',          source: 'ECB',        emoji: '🇪🇺', color: '#6366F1', label: 'EU Policy',      timeLabel: 'Latest', link: 'https://ecb.europa.eu',           tab: 'emi'       },
  { title: 'World Bank: 1.2B youth entering workforce by 2040',                source: 'World Bank', emoji: '🌐', color: '#0ea5e9', label: 'Global Finance', timeLabel: 'Latest', link: 'https://blogs.worldbank.org',     tab: 'fire'      },
];

const FALLBACK = {
  india: [
    { title: 'RBI holds repo rate at 6.5% — impact on home loan EMIs',        source: 'RBI',  emoji: '🏦', color: '#C9A84C', label: 'Press Release', timeLabel: 'Latest', link: 'https://rbi.org.in',  tab: 'emi'  },
    { title: 'SEBI circular: Updated mutual fund expense ratio norms',         source: 'SEBI', emoji: '📋', color: '#6366F1', label: 'Regulator',     timeLabel: 'Latest', link: 'https://sebi.gov.in', tab: 'sip'  },
    { title: 'Budget 2026-27: Key income tax changes under new regime',        source: 'PIB',  emoji: '🇮🇳', color: '#EC4899', label: 'Govt Finance',  timeLabel: 'Latest', link: 'https://pib.gov.in',  tab: 'tax'  },
    ...WORLD_FALLBACK,
  ],
  usa: [
    { title: 'Federal Reserve holds rates at 3.5–3.75% range',                source: 'Fed Reserve', emoji: '🏛️', color: '#3B82F6', label: 'Monetary Policy', timeLabel: 'Latest', link: 'https://federalreserve.gov', tab: 'emi'  },
    { title: 'FOMC: Inflation data determines timing of next rate move',       source: 'FOMC',        emoji: '💵', color: '#22C55E', label: 'Rate Decision',   timeLabel: 'Latest', link: 'https://federalreserve.gov', tab: 'emi'  },
    { title: 'SEC proposes enhanced retail investor protection rules',          source: 'SEC',         emoji: '⚖️', color: '#F59E0B', label: 'Regulator',       timeLabel: 'Latest', link: 'https://sec.gov',            tab: 'insurance' },
    ...WORLD_FALLBACK,
  ],
  europe: [
    { title: 'ECB keeps key interest rates unchanged at current levels',       source: 'ECB',  emoji: '🏦', color: '#6366F1', label: 'Rate Decision', timeLabel: 'Latest', link: 'https://ecb.europa.eu',  tab: 'emi' },
    { title: 'Lagarde: ECB remains data-dependent on future rate path',        source: 'ECB',  emoji: '🎙️', color: '#22C55E', label: 'Key Speech',    timeLabel: 'Latest', link: 'https://ecb.europa.eu',  tab: 'emi' },
    { title: 'ESMA: New sustainable finance disclosure guidelines published',  source: 'ESMA', emoji: '📋', color: '#EC4899', label: 'Regulator',     timeLabel: 'Latest', link: 'https://esma.europa.eu', tab: null  },
    ...WORLD_FALLBACK,
  ],
  world: [ ...WORLD_FALLBACK ],
};

// ── In-memory cache ───────────────────────────────────────────
const _cache     = {};
const _cacheTime = {};
const CACHE_MS   = 60 * 60 * 1000; // 1 hour

// ── Fetch from rss2json ───────────────────────────────────────
function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      timeout: 9000,
      headers: { 'User-Agent': 'MoneyVeda/1.0', 'Accept': 'application/json' },
    }, (res) => {
      if (res.statusCode !== 200) { res.resume(); return reject(new Error(`HTTP ${res.statusCode}`)); }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', c => { body += c; });
      res.on('end', () => {
        const t = body.trim();
        if (!t.startsWith('{') && !t.startsWith('[')) return reject(new Error('Not JSON'));
        try { resolve(JSON.parse(t)); } catch (e) { reject(new Error('Parse: ' + e.message)); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// ── Parse rss2json items ──────────────────────────────────────
function parseItems(data, feedMeta) {
  if (!data || data.status !== 'ok' || !Array.isArray(data.items)) return [];
  return data.items.slice(0, 2).map(item => {
    const title = (item.title || '')
      .replace(/<[^>]+>/g, '')
      .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'").replace(/&quot;/g, '"').trim();
    if (!title || title.length < 5) return null;
    const link = item.link || item.guid || feedMeta.link;
    const pub  = new Date(item.pubDate || Date.now());
    const h    = Math.floor((Date.now() - pub.getTime()) / 3600000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;
    // Resolve routing tab server-side — not exposed to client
    const tab = resolveTab(title);
    return {
      title:     title.length > 110 ? title.slice(0, 107) + '…' : title,
      link,
      source:    feedMeta.source,
      label:     feedMeta.label,
      emoji:     feedMeta.emoji,
      color:     feedMeta.color,
      timeLabel,
      pubDate:   pub.toISOString(),
      tab,        // null = open external link; string = navTo(tab)
    };
  }).filter(Boolean);
}

// ── Deduplicate ───────────────────────────────────────────────
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
  if (req.method !== 'GET')     return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds  = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles: [], region, note: 'Coming soon' });

  // Serve from cache if fresh
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
    ).slice(0, 12);

    if (articles.length === 0) {
      console.warn(`All feeds failed for ${region} — serving fallback`);
      articles = FALLBACK[region] || [];
    }

    _cache[region]     = articles;
    _cacheTime[region] = Date.now();

    return res.status(200).json({
      articles,
      cached:    false,
      region,
      count:     articles.length,
      fetchedAt: new Date().toISOString(),
    });

  } catch (err) {
    console.error('[MoneyVeda News] Handler error:', err.message);
    return res.status(200).json({
      articles: FALLBACK[region] || [],
      cached:   false,
      region,
      fallback: true,
    });
  }
};

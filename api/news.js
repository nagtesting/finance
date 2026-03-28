// ============================================================
// /api/news.js — MoneyVeda  Region-aware Financial News Feed
//
// FIXES vs previous version:
//   FIX-1  Changed from CommonJS (module.exports + require('https'))
//          to ESM (export default) to match market.js and Vercel
//          serverless function convention.
//   FIX-2  Replaced Node require('https') with global fetch() —
//          fetch is available in all Vercel Node 18+ runtimes and
//          is simpler and more reliable than hand-rolling https.get.
//   FIX-3  Added per-feed timeout via AbortSignal.timeout(7000) so
//          a single slow feed never hangs the whole response.
//   FIX-4  Fallback is now ALWAYS returned when live feeds return
//          0 articles — the strip is never left blank or hidden.
//   FIX-5  Added CORS headers + OPTIONS pre-flight handling.
//   FIX-6  Redirect following is handled automatically by fetch().
//   FIX-7  Added server-side 5 min in-memory cache so repeated page
//          loads don't hammer RSS sources.
//
// FEEDS USED:
//   India:  Economic Times, ET Markets, ET Wealth, Business Standard,
//           RBI, SEBI, PIB + world feeds
//   USA:    Fed Reserve, FOMC, MarketWatch, Nasdaq, SEC + world feeds
//   Europe: ECB, ESMA + world feeds
//   World:  Fed, ECB, IMF, BIS, Nasdaq, MarketWatch, Investing.com,
//           World Bank
//
// NOTE: Reuters RSS shut down March 2026.
// ============================================================

// ── Feed registry ─────────────────────────────────────────────
const feed = (rssUrl, source, label, emoji, color, link) =>
  ({ rssUrl, source, label, emoji, color, link });

const FED_URL        = 'https://www.federalreserve.gov/feeds/press_all.xml';
const ECB_URL        = 'https://www.ecb.europa.eu/rss/press.html';
const BIS_URL        = 'https://www.bis.org/doclist/cbspeeches.rss';
const IMF_URL        = 'https://www.imf.org/en/News/rss?category=newsfeed';
const NASDAQ_URL     = 'https://www.nasdaq.com/feed/nasdaq-originals.rss';
const INVESTING_URL  = 'https://in.investing.com/rss/news.rss';
const ET_URL         = 'https://economictimes.indiatimes.com/rssfeedstopstories.cms';
const ET_MARKET_URL  = 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms';
const ET_FINANCE_URL = 'https://economictimes.indiatimes.com/wealth/rssfeeds/837555173.cms';
const BS_URL         = 'https://www.business-standard.com/rss/finance-markets-10201.rss';
const BS_ECON_URL    = 'https://www.business-standard.com/rss/economy-policy-10102.rss';
const MW_URL         = 'https://feeds.content.dowjones.io/public/rss/mw_topstories';
const WORLDBANK_URL  = 'https://blogs.worldbank.org/en/rss.xml';

const WORLD_FEEDS = [
  feed(FED_URL,       'Fed Reserve',   'US Policy',      '💵', '#22C55E', 'https://federalreserve.gov'),
  feed(ECB_URL,       'ECB',           'EU Policy',      '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
  feed(IMF_URL,       'IMF',           'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/News'),
  feed(BIS_URL,       'BIS',           'Central Banks',  '🏛️', '#C9A84C', 'https://bis.org'),
  feed(INVESTING_URL, 'Investing.com', 'Markets',        '📊', '#F59E0B', 'https://in.investing.com'),
];

const FEEDS = {
  india: [
    feed(ET_URL,         'Economic Times', 'Top Stories',     '📰', '#F97316', 'https://economictimes.indiatimes.com'),
    feed(ET_MARKET_URL,  'Economic Times', 'Markets',         '📈', '#C9A84C', 'https://economictimes.indiatimes.com/markets'),
    feed(ET_FINANCE_URL, 'ET Wealth',      'Personal Finance','💰', '#22C55E', 'https://economictimes.indiatimes.com/wealth'),
    feed(BS_URL,         'Business Std',   'Finance',         '📊', '#6366F1', 'https://business-standard.com'),
    feed(BS_ECON_URL,    'Business Std',   'Economy',         '🏛️', '#EC4899', 'https://business-standard.com'),
    feed('https://rbi.org.in/pressreleases_rss.xml',
      'RBI',  'Press Release', '🏦', '#C9A84C', 'https://rbi.org.in'),
    feed('https://www.sebi.gov.in/sebirss.xml',
      'SEBI', 'Regulator',     '📋', '#6366F1', 'https://sebi.gov.in'),
    feed('https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      'PIB',  'Govt Finance',  '🇮🇳', '#EC4899', 'https://pib.gov.in'),
    ...WORLD_FEEDS,
  ],
  usa: [
    feed(FED_URL,
      'Fed Reserve', 'Monetary Policy', '🏛️', '#3B82F6', 'https://federalreserve.gov'),
    feed('https://www.federalreserve.gov/feeds/press_monetary.xml',
      'FOMC', 'Rate Decision', '💵', '#22C55E', 'https://federalreserve.gov'),
    feed(MW_URL,
      'MarketWatch', 'Top Stories', '📈', '#F97316', 'https://marketwatch.com'),
    feed(NASDAQ_URL,
      'Nasdaq', 'Markets', '💹', '#22C55E', 'https://nasdaq.com'),
    feed('https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom',
      'SEC', 'Regulator', '⚖️', '#F59E0B', 'https://sec.gov'),
    ...WORLD_FEEDS,
  ],
  europe: [
    feed(ECB_URL,
      'ECB', 'Rate Decision', '🏦', '#6366F1', 'https://ecb.europa.eu'),
    feed('https://www.ecb.europa.eu/rss/key.html',
      'ECB', 'Key Speech', '🎙️', '#22C55E', 'https://ecb.europa.eu'),
    feed('https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      'ESMA', 'Regulator', '📋', '#EC4899', 'https://esma.europa.eu'),
    ...WORLD_FEEDS,
  ],
  world: [
    feed(FED_URL,       'Fed Reserve',   'US Policy',      '💵', '#22C55E', 'https://federalreserve.gov'),
    feed(ECB_URL,       'ECB',           'EU Policy',      '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
    feed(IMF_URL,       'IMF',           'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/News'),
    feed(BIS_URL,       'BIS',           'Central Banks',  '🏛️', '#C9A84C', 'https://bis.org'),
    feed(NASDAQ_URL,    'Nasdaq',        'Markets',        '💹', '#22C55E', 'https://nasdaq.com'),
    feed(MW_URL,        'MarketWatch',   'Top Stories',    '📈', '#F97316', 'https://marketwatch.com'),
    feed(INVESTING_URL, 'Investing.com', 'Markets',        '📊', '#F59E0B', 'https://in.investing.com'),
    feed(WORLDBANK_URL, 'World Bank',    'Global Finance', '🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
  ],
};

// ── Tab routing keywords ───────────────────────────────────────
const NEWS_ROUTES = [
  { kw: ['nps','national pension','pfrda','pension corpus'],              tab: 'nps'       },
  { kw: ['sip','mutual fund','amfi','elss','equity fund','nav'],          tab: 'sip'       },
  { kw: ['ppf','public provident fund','small savings'],                  tab: 'ppf'       },
  { kw: ['epf','provident fund','pf withdrawal','employees provident'],   tab: 'epf'       },
  { kw: ['home loan','repo rate','emi','housing loan','rbi rate'],        tab: 'emi'       },
  { kw: ['income tax','tax slab','80c','section 80','itr','new regime'],  tab: 'tax'       },
  { kw: ['insurance','term plan','life cover','health insurance'],        tab: 'insurance' },
  { kw: ['sukanya','girl child','samriddhi'],                             tab: 'ssa'       },
  { kw: ['federal reserve','fomc','fed rate','interest rate'],            tab: 'emi'       },
  { kw: ['401k','roth ira','retirement savings'],                         tab: 'fire'      },
  { kw: ['mortgage rate','housing market'],                               tab: 'emi'       },
  { kw: ['s&p 500','nasdaq','stock market','sensex','nifty','bse','nse'], tab: 'sip'       },
  { kw: ['capital gains','income tax','irs','federal tax'],               tab: 'tax'       },
  { kw: ['ecb','european central bank','eurozone'],                       tab: 'emi'       },
  { kw: ['imf','world bank','global growth','gdp'],                       tab: 'fire'      },
  { kw: ['inflation','cpi','price index','repo'],                         tab: 'emi'       },
  { kw: ['retirement','retire early','financial independence','fire'],    tab: 'fire'      },
  { kw: ['mutual fund','sip','investment','portfolio','compounding'],     tab: 'sip'       },
  { kw: ['tax','taxation','fiscal','budget','deduction'],                 tab: 'tax'       },
  { kw: ['life insurance','term insurance','coverage','premium'],         tab: 'insurance' },
  { kw: ['crorepati','crore','millionaire','wealth goal'],                tab: 'crorepati' },
  { kw: ['roi','returns','cagr','compound interest'],                     tab: 'roi'       },
];

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

// ── Fallback articles (shown when ALL live feeds fail) ─────────
// FIX-4: these are always returned rather than leaving the strip blank
const FALLBACK = {
  india: [
    { title: 'RBI Monetary Policy: Latest rate decision and outlook',         source: 'RBI',            emoji: '🏦', color: '#C9A84C', label: 'Press Release',    timeLabel: 'Latest', link: 'https://rbi.org.in',                   tab: 'emi'  },
    { title: 'SEBI: New mutual fund and investment regulation update',        source: 'SEBI',           emoji: '📋', color: '#6366F1', label: 'Regulator',        timeLabel: 'Latest', link: 'https://sebi.gov.in',                  tab: 'sip'  },
    { title: 'Economic Times: India markets and finance top stories',         source: 'Economic Times', emoji: '📰', color: '#F97316', label: 'Top Stories',      timeLabel: 'Latest', link: 'https://economictimes.indiatimes.com', tab: null   },
    { title: 'Budget 2025-26: Income tax slab and deduction announcements',   source: 'PIB',            emoji: '🇮🇳', color: '#EC4899', label: 'Govt Finance',    timeLabel: 'Latest', link: 'https://pib.gov.in',                   tab: 'tax'  },
    { title: 'Nifty 50 and Sensex: Market movement and outlook',              source: 'ET Markets',     emoji: '📈', color: '#C9A84C', label: 'Markets',          timeLabel: 'Latest', link: 'https://economictimes.indiatimes.com/markets', tab: 'sip' },
    { title: 'PPF, NPS, EPF: Latest interest rate and rule changes',         source: 'ET Wealth',      emoji: '💰', color: '#22C55E', label: 'Personal Finance', timeLabel: 'Latest', link: 'https://economictimes.indiatimes.com/wealth', tab: 'ppf' },
    { title: 'Fed Reserve latest monetary policy statement',                  source: 'Fed Reserve',    emoji: '💵', color: '#22C55E', label: 'US Policy',        timeLabel: 'Latest', link: 'https://federalreserve.gov',           tab: 'emi'  },
    { title: 'IMF: Global growth and emerging markets outlook 2026',          source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',   timeLabel: 'Latest', link: 'https://imf.org/en/News',              tab: 'fire' },
  ],
  usa: [
    { title: 'Federal Reserve: Latest monetary policy decision and minutes',  source: 'Fed Reserve',    emoji: '🏛️', color: '#3B82F6', label: 'Monetary Policy', timeLabel: 'Latest', link: 'https://federalreserve.gov',           tab: 'emi'  },
    { title: 'FOMC: Interest rate decision and economic projections',         source: 'FOMC',           emoji: '💵', color: '#22C55E', label: 'Rate Decision',    timeLabel: 'Latest', link: 'https://federalreserve.gov',           tab: 'emi'  },
    { title: 'MarketWatch: S&P 500, Dow and Nasdaq market update',           source: 'MarketWatch',    emoji: '📈', color: '#F97316', label: 'Top Stories',      timeLabel: 'Latest', link: 'https://marketwatch.com',              tab: 'sip'  },
    { title: 'Nasdaq: Technology stocks and market update',                   source: 'Nasdaq',         emoji: '💹', color: '#22C55E', label: 'Markets',          timeLabel: 'Latest', link: 'https://nasdaq.com',                   tab: 'sip'  },
    { title: 'SEC: Latest regulatory filing and investor alert',              source: 'SEC',            emoji: '⚖️', color: '#F59E0B', label: 'Regulator',        timeLabel: 'Latest', link: 'https://sec.gov',                      tab: null   },
    { title: 'IMF: US and global economic outlook 2026',                      source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',   timeLabel: 'Latest', link: 'https://imf.org/en/News',              tab: 'fire' },
    { title: 'BIS: Central bank policy and financial stability report',       source: 'BIS',            emoji: '🏛️', color: '#C9A84C', label: 'Central Banks',   timeLabel: 'Latest', link: 'https://bis.org',                      tab: null   },
  ],
  europe: [
    { title: 'ECB: Interest rate decision and monetary policy statement',     source: 'ECB',            emoji: '🏦', color: '#6366F1', label: 'Rate Decision',    timeLabel: 'Latest', link: 'https://ecb.europa.eu',                tab: 'emi'  },
    { title: 'ECB: Key economic speech and policy outlook',                   source: 'ECB',            emoji: '🎙️', color: '#22C55E', label: 'Key Speech',       timeLabel: 'Latest', link: 'https://ecb.europa.eu',                tab: 'emi'  },
    { title: 'ESMA: Sustainable finance and investment regulation update',    source: 'ESMA',           emoji: '📋', color: '#EC4899', label: 'Regulator',        timeLabel: 'Latest', link: 'https://esma.europa.eu',               tab: null   },
    { title: 'IMF: Euro area economic assessment and growth forecast',        source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',   timeLabel: 'Latest', link: 'https://imf.org/en/News',              tab: 'fire' },
    { title: 'BIS: European banking and financial stability review',          source: 'BIS',            emoji: '🏛️', color: '#C9A84C', label: 'Central Banks',   timeLabel: 'Latest', link: 'https://bis.org',                      tab: null   },
    { title: 'MarketWatch: Euro Stoxx, DAX and FTSE market update',          source: 'MarketWatch',    emoji: '📈', color: '#F97316', label: 'Markets',          timeLabel: 'Latest', link: 'https://marketwatch.com',              tab: 'sip'  },
  ],
  world: [
    { title: 'Fed Reserve: Latest monetary policy statement',                 source: 'Fed Reserve',    emoji: '💵', color: '#22C55E', label: 'US Policy',        timeLabel: 'Latest', link: 'https://federalreserve.gov',           tab: 'emi'  },
    { title: 'ECB: Euro area rate decision and economic outlook',             source: 'ECB',            emoji: '🇪🇺', color: '#6366F1', label: 'EU Policy',        timeLabel: 'Latest', link: 'https://ecb.europa.eu',                tab: 'emi'  },
    { title: 'IMF: Global growth outlook and emerging markets 2026',          source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',   timeLabel: 'Latest', link: 'https://imf.org/en/News',              tab: 'fire' },
    { title: 'BIS: Global central bank policy and financial stability',       source: 'BIS',            emoji: '🏛️', color: '#C9A84C', label: 'Central Banks',   timeLabel: 'Latest', link: 'https://bis.org',                      tab: null   },
    { title: 'Nasdaq: Global technology and equity market update',            source: 'Nasdaq',         emoji: '💹', color: '#22C55E', label: 'Markets',          timeLabel: 'Latest', link: 'https://nasdaq.com',                   tab: 'sip'  },
    { title: 'MarketWatch: Global markets — S&P 500, Nifty, DAX round-up',  source: 'MarketWatch',    emoji: '📈', color: '#F97316', label: 'Top Stories',      timeLabel: 'Latest', link: 'https://marketwatch.com',              tab: 'sip'  },
    { title: 'World Bank: Global finance and development finance update',     source: 'World Bank',     emoji: '🌐', color: '#0ea5e9', label: 'Global Finance',   timeLabel: 'Latest', link: 'https://blogs.worldbank.org',          tab: null   },
    { title: 'Investing.com: Commodities, forex and global markets',         source: 'Investing.com',  emoji: '📊', color: '#F59E0B', label: 'Markets',          timeLabel: 'Latest', link: 'https://in.investing.com',             tab: 'roi'  },
  ],
};

// ── In-memory server cache (5 min) ────────────────────────────
const _cache     = {};
const _cacheTime = {};
const CACHE_MS   = 5 * 60 * 1000;

// ── Fetch RSS/Atom XML via global fetch (FIX-1, FIX-2) ────────
// Uses fetch() with AbortSignal.timeout — simpler and works in all
// Vercel Node 18+ runtimes. Redirect following is automatic.
async function fetchRSS(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 7000); // FIX-3: per-feed timeout
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; MoneyVeda/1.0; +https://moneyveda.org)',
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
        'Cache-Control': 'no-cache',
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(timer);
  }
}

// ── XML helpers ───────────────────────────────────────────────
function extractTag(xml, tag) {
  const cdata = new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>`, 'i');
  const plain = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i');
  const m = xml.match(cdata) || xml.match(plain);
  return m ? m[1].trim() : '';
}

function decodeEntities(str) {
  return str
    .replace(/&amp;/g,  '&')
    .replace(/&lt;/g,   '<')
    .replace(/&gt;/g,   '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g,  "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n))
    .replace(/<[^>]+>/g, '')
    .trim();
}

// ── Parse RSS or Atom XML into article objects ─────────────────
function parseRSS(xml, feedMeta) {
  const articles   = [];
  const itemRegex  = /<(?:item|entry)[\s>]([\s\S]*?)<\/(?:item|entry)>/gi;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const block = match[1];

    let title = decodeEntities(extractTag(block, 'title'));
    if (!title || title.length < 5) continue;
    if (title.length > 110) title = title.slice(0, 107) + '…';

    let link = extractTag(block, 'link');
    if (!link) {
      const hrefM = block.match(/<link[^>]+href="([^"]+)"/i);
      if (hrefM) link = hrefM[1];
    }
    if (!link) link = extractTag(block, 'guid');
    link = (link || feedMeta.link).trim();

    const rawDate =
      extractTag(block, 'pubDate')  ||
      extractTag(block, 'published') ||
      extractTag(block, 'updated')  ||
      extractTag(block, 'dc:date')  || '';

    const pub      = rawDate ? new Date(rawDate) : new Date();
    const valid    = !isNaN(pub.getTime()) ? pub : new Date();
    const h        = Math.floor((Date.now() - valid.getTime()) / 3600000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;

    articles.push({
      title,
      link,
      source:    feedMeta.source,
      label:     feedMeta.label,
      emoji:     feedMeta.emoji,
      color:     feedMeta.color,
      timeLabel,
      pubDate:   valid.toISOString(),
      tab:       resolveTab(title),
    });

    if (articles.length >= 3) break; // max 3 per feed to keep diversity
  }

  return articles;
}

// ── Deduplicate by first 60 chars of title ────────────────────
function dedupe(articles) {
  const seen = new Set();
  return articles.filter(a => {
    const key = a.title.toLowerCase().slice(0, 60);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ── Main handler (ESM export — FIX-1) ─────────────────────────
export default async function handler(req, res) {
  // FIX-5: CORS headers
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'no-store');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET')     return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds  = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles: FALLBACK.india, region, note: 'Unknown region, defaulting to india' });

  // Serve from server-side cache if fresh (FIX-7)
  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  try {
    // Fetch all feeds concurrently; each has its own 7s timeout (FIX-3)
    const results = await Promise.allSettled(
      feeds.map(f =>
        fetchRSS(f.rssUrl)
          .then(xml => parseRSS(xml, f))
          .catch(err => {
            console.warn(`[news/${region}] ${f.source} failed: ${err.message}`);
            return []; // FIX-4: individual feed failure → empty, not crash
          })
      )
    );

    let articles = dedupe(
      results
        .filter(r => r.status === 'fulfilled')
        .flatMap(r => r.value)
        .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    ).slice(0, 12);

    // FIX-4: always fall back to static content — strip is never left blank
    if (articles.length === 0) {
      console.warn(`[news/${region}] All RSS feeds failed — serving static fallback`);
      articles = FALLBACK[region] || FALLBACK.india;
    }

    _cache[region]     = articles;
    _cacheTime[region] = Date.now();

    return res.status(200).json({
      articles,
      cached:    false,
      region,
      count:     articles.length,
      fallback:  articles === (FALLBACK[region] || FALLBACK.india),
      fetchedAt: new Date().toISOString(),
    });

  } catch (err) {
    console.error('[MoneyVeda News] Unexpected error:', err.message);
    // FIX-4: even on hard crash, return fallback so news strip renders
    return res.status(200).json({
      articles:  FALLBACK[region] || FALLBACK.india,
      cached:    false,
      region,
      fallback:  true,
    });
  }
}

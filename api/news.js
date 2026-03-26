// ============================================================
// /api/news.js — MoneyVeda (Direct RSS + Quality Feeds)
//
// Fetches RSS directly — no rss2json middleman.
// rss2json free plan caches for 60min and can't be bypassed.
// This version hits RSS sources directly using Node https.
//
// FEEDS USED:
//   India:  Economic Times, Business Standard, RBI, SEBI, PIB
//   USA:    Fed Reserve, FOMC, MarketWatch, Nasdaq
//   Europe: ECB, ESMA + world feeds
//   World:  Fed, ECB, Investing.com, Nasdaq
//
// NOTE: Reuters RSS shut down March 2026.
// ============================================================

const https = require('https');
const http  = require('http');

const feed = (rssUrl, source, label, emoji, color, link) =>
  ({ rssUrl, source, label, emoji, color, link });

// ── Feed URLs ─────────────────────────────────────────────────
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
  feed(FED_URL,       'Fed Reserve', 'US Policy',      '💵', '#22C55E', 'https://federalreserve.gov'),
  feed(ECB_URL,       'ECB',         'EU Policy',      '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
  feed(IMF_URL,       'IMF',         'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/News'),
  feed(BIS_URL,       'BIS',         'Central Banks',  '🏛️', '#C9A84C', 'https://bis.org'),
  feed(INVESTING_URL, 'Investing.com','Markets',       '📊', '#F59E0B', 'https://in.investing.com'),
];

const FEEDS = {
  india: [
    feed(ET_URL,         'Economic Times', 'Top Stories',  '📰', '#F97316', 'https://economictimes.indiatimes.com'),
    feed(ET_MARKET_URL,  'Economic Times', 'Markets',      '📈', '#C9A84C', 'https://economictimes.indiatimes.com/markets'),
    feed(ET_FINANCE_URL, 'ET Wealth',      'Personal Finance','💰','#22C55E','https://economictimes.indiatimes.com/wealth'),
    feed(BS_URL,         'Business Standard','Finance',    '📊', '#6366F1', 'https://business-standard.com'),
    feed(BS_ECON_URL,    'Business Standard','Economy',    '🏛️', '#EC4899', 'https://business-standard.com'),
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
      'ECB',  'Rate Decision',  '🏦', '#6366F1', 'https://ecb.europa.eu'),
    feed('https://www.ecb.europa.eu/rss/key.html',
      'ECB',  'Key Speech',     '🎙️', '#22C55E', 'https://ecb.europa.eu'),
    feed('https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      'ESMA', 'Regulator',      '📋', '#EC4899', 'https://esma.europa.eu'),
    ...WORLD_FEEDS,
  ],
  world: [
    feed(FED_URL,       'Fed Reserve',    'US Policy',     '💵', '#22C55E', 'https://federalreserve.gov'),
    feed(ECB_URL,       'ECB',            'EU Policy',     '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
    feed(IMF_URL,       'IMF',            'Global Economy','🌍', '#3B82F6', 'https://imf.org/en/News'),
    feed(BIS_URL,       'BIS',            'Central Banks', '🏛️', '#C9A84C', 'https://bis.org'),
    feed(NASDAQ_URL,    'Nasdaq',         'Markets',       '💹', '#22C55E', 'https://nasdaq.com'),
    feed(MW_URL,        'MarketWatch',    'Top Stories',   '📈', '#F97316', 'https://marketwatch.com'),
    feed(INVESTING_URL, 'Investing.com',  'Markets',       '📊', '#F59E0B', 'https://in.investing.com'),
    feed(WORLDBANK_URL, 'World Bank',     'Global Finance','🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
  ],
};

// ── News tab routing ──────────────────────────────────────────
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

// ── Static fallback (only when ALL feeds fail) ────────────────
const FALLBACK = {
  india: [
    { title: 'RBI MPC: Latest monetary policy decision',                 source: 'RBI',            emoji: '🏦', color: '#C9A84C', label: 'Press Release',   timeLabel: 'Latest', link: 'https://rbi.org.in',                        tab: 'emi'  },
    { title: 'SEBI: New mutual fund regulation circular',                source: 'SEBI',           emoji: '📋', color: '#6366F1', label: 'Regulator',       timeLabel: 'Latest', link: 'https://sebi.gov.in',                       tab: 'sip'  },
    { title: 'Economic Times: India markets top stories',                source: 'Economic Times', emoji: '📰', color: '#F97316', label: 'Top Stories',     timeLabel: 'Latest', link: 'https://economictimes.indiatimes.com',       tab: null   },
    { title: 'Budget 2025-26: Income tax key announcements',             source: 'PIB',            emoji: '🇮🇳', color: '#EC4899', label: 'Govt Finance',    timeLabel: 'Latest', link: 'https://pib.gov.in',                        tab: 'tax'  },
    { title: 'Fed: Latest monetary policy statement',                    source: 'Fed Reserve',    emoji: '💵', color: '#22C55E', label: 'US Policy',       timeLabel: 'Latest', link: 'https://federalreserve.gov',                tab: 'emi'  },
    { title: 'IMF: Global growth outlook 2026',                          source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',  timeLabel: 'Latest', link: 'https://imf.org/en/News',                   tab: 'fire' },
  ],
  usa: [
    { title: 'Federal Reserve: Latest monetary policy decision',         source: 'Fed Reserve',    emoji: '🏛️', color: '#3B82F6', label: 'Monetary Policy', timeLabel: 'Latest', link: 'https://federalreserve.gov',                tab: 'emi'  },
    { title: 'MarketWatch: US markets top stories',                      source: 'MarketWatch',    emoji: '📈', color: '#F97316', label: 'Top Stories',     timeLabel: 'Latest', link: 'https://marketwatch.com',                   tab: null   },
    { title: 'Nasdaq: Markets and trading update',                       source: 'Nasdaq',         emoji: '💹', color: '#22C55E', label: 'Markets',         timeLabel: 'Latest', link: 'https://nasdaq.com',                        tab: 'sip'  },
    { title: 'IMF: Global economic outlook',                             source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',  timeLabel: 'Latest', link: 'https://imf.org/en/News',                   tab: 'fire' },
  ],
  europe: [
    { title: 'ECB: Interest rate and monetary policy decision',          source: 'ECB',            emoji: '🏦', color: '#6366F1', label: 'Rate Decision',   timeLabel: 'Latest', link: 'https://ecb.europa.eu',                     tab: 'emi'  },
    { title: 'ESMA: New sustainable finance guidelines',                 source: 'ESMA',           emoji: '📋', color: '#EC4899', label: 'Regulator',       timeLabel: 'Latest', link: 'https://esma.europa.eu',                    tab: null   },
    { title: 'IMF: Euro area economic assessment',                       source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',  timeLabel: 'Latest', link: 'https://imf.org/en/News',                   tab: 'fire' },
  ],
  world: [
    { title: 'Fed: Latest monetary policy statement',                    source: 'Fed Reserve',    emoji: '💵', color: '#22C55E', label: 'US Policy',       timeLabel: 'Latest', link: 'https://federalreserve.gov',                tab: 'emi'  },
    { title: 'ECB: Euro area rate decision',                             source: 'ECB',            emoji: '🇪🇺', color: '#6366F1', label: 'EU Policy',       timeLabel: 'Latest', link: 'https://ecb.europa.eu',                     tab: 'emi'  },
    { title: 'IMF: Global growth outlook 2026',                          source: 'IMF',            emoji: '🌍', color: '#3B82F6', label: 'Global Economy',  timeLabel: 'Latest', link: 'https://imf.org/en/News',                   tab: 'fire' },
    { title: 'Nasdaq: Markets and trading update',                       source: 'Nasdaq',         emoji: '💹', color: '#22C55E', label: 'Markets',         timeLabel: 'Latest', link: 'https://nasdaq.com',                        tab: 'sip'  },
    { title: 'MarketWatch: Global markets top stories',                  source: 'MarketWatch',    emoji: '📈', color: '#F97316', label: 'Top Stories',     timeLabel: 'Latest', link: 'https://marketwatch.com',                   tab: null   },
  ],
};

// ── In-memory cache (5 min) ───────────────────────────────────
const _cache     = {};
const _cacheTime = {};
const CACHE_MS   = 5 * 60 * 1000;

// ── Fetch raw RSS/Atom XML directly ──────────────────────────
function fetchRSS(url, redirectCount) {
  redirectCount = redirectCount || 0;
  if (redirectCount > 3) return Promise.reject(new Error('Too many redirects'));
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, {
      timeout: 8000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; MoneyVeda/1.0; +https://moneyveda.org)',
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
        'Cache-Control': 'no-cache',
      },
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        return fetchRSS(res.headers.location, redirectCount + 1).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// ── Extract XML tag value (handles CDATA) ─────────────────────
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

// ── Parse RSS or Atom XML ─────────────────────────────────────
function parseRSS(xml, feedMeta) {
  const articles = [];
  const itemRegex = /<(?:item|entry)[\s>]([\s\S]*?)<\/(?:item|entry)>/gi;
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
      extractTag(block, 'pubDate') ||
      extractTag(block, 'published') ||
      extractTag(block, 'updated') ||
      extractTag(block, 'dc:date') || '';

    const pub = rawDate ? new Date(rawDate) : new Date();
    const validDate = !isNaN(pub.getTime()) ? pub : new Date();
    const h = Math.floor((Date.now() - validDate.getTime()) / 3600000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;

    articles.push({
      title,
      link,
      source:    feedMeta.source,
      label:     feedMeta.label,
      emoji:     feedMeta.emoji,
      color:     feedMeta.color,
      timeLabel,
      pubDate:   validDate.toISOString(),
      tab:       resolveTab(title),
    });

    if (articles.length >= 3) break;
  }

  return articles;
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
  res.setHeader('Cache-Control', 'no-store'); // no Vercel CDN caching

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET')     return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds  = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles: [], region, note: 'Coming soon' });

  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  try {
    const results = await Promise.allSettled(
      feeds.map(f =>
        fetchRSS(f.rssUrl)
          .then(xml => parseRSS(xml, f))
          .catch(err => {
            console.warn(`[${f.source}] failed: ${err.message}`);
            return [];
          })
      )
    );

    let articles = dedupe(
      results
        .filter(r => r.status === 'fulfilled')
        .flatMap(r => r.value)
        .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    ).slice(0, 12);

    if (articles.length === 0) {
      console.warn(`All RSS feeds failed for ${region} — serving fallback`);
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
    console.error('[MoneyVeda News] Error:', err.message);
    return res.status(200).json({
      articles:  FALLBACK[region] || [],
      cached:    false,
      region,
      fallback:  true,
    });
  }
};

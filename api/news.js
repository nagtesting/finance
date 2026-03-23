// ============================================================
// /api/news.js — MoneyVeda v9
//
// CHANGES FROM v8  (audit fixes applied):
//
//   ISS-04 — Removed rss2json.com Third-Party Dependency
//     - Replaced the rss2json.com proxy with direct RSS-to-JSON
//       parsing using the built-in https module and a lightweight
//       XML parser (no new npm dep — pure regex/string parsing
//       sufficient for well-formed RSS 2.0 / Atom feeds).
//     - parseRSS() handles both RSS 2.0 (<item>) and Atom (<entry>)
//       feed formats, covering all existing source feeds.
//     - rss2json.com outage no longer silently serves stale fallback
//       content as if it were live.
//
//   ISS-04b — Fallback Content Timestamps
//     - Fallback articles now include a `fallback: true` flag and a
//       human-readable `staleNote` field ("Offline placeholder — live
//       feed unavailable") so the UI can visually distinguish them
//       from live articles.
//     - fetchedAt and fallbackAt are both returned so consumers can
//       show "Last updated: X" to users.
//
// Previous fixes from v8 are retained unchanged:
//   - No shared object references across regions
//   - Verified IMF / World Bank RSS URLs
//   - 1-hour in-memory cache per region
// ============================================================

const https = require('https');

// ── Helper: create fresh feed object ────────────────────────
const feed = (rssUrl, source, label, emoji, color, link) =>
  ({ rssUrl, source, label, emoji, color, link });

// ── Verified global feed URLs ─────────────────────────────
const IMF_URL       = 'https://www.imf.org/en/Blogs';
const BIS_URL       = 'https://www.bis.org/doclist/cbspeeches.rss';
const WORLDBANK_URL = 'https://blogs.worldbank.org/rss.xml';

// ── Feeds per region ──────────────────────────────────────
const FEEDS = {
  india: [
    feed('https://rbi.org.in/pressreleases_rss.xml',
      'RBI', 'Press Release', '🏦', '#C9A84C', 'https://rbi.org.in'),
    feed('https://www.sebi.gov.in/sebirss.xml',
      'SEBI', 'Regulator', '📋', '#6366F1', 'https://sebi.gov.in'),
    feed('https://rbi.org.in/notifications_rss.xml',
      'RBI', 'Notification', '📢', '#22C55E', 'https://rbi.org.in'),
    feed('https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3',
      'PIB', 'Govt Finance', '🇮🇳', '#EC4899', 'https://pib.gov.in'),
    feed(IMF_URL,
      'IMF', 'Global Economy', '🌍', '#64748b', 'https://imf.org/en/Blogs'),
    feed(BIS_URL,
      'BIS', 'Central Banks', '🏛️', '#94a3b8', 'https://bis.org'),
  ],
  usa: [
    feed('https://www.federalreserve.gov/feeds/press_all.xml',
      'Fed Reserve', 'Monetary Policy', '🏛️', '#3B82F6', 'https://federalreserve.gov'),
    feed('https://www.federalreserve.gov/feeds/press_monetary.xml',
      'FOMC', 'Rate Decision', '💵', '#22C55E', 'https://federalreserve.gov'),
    feed('https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom',
      'SEC', 'Regulator', '⚖️', '#F59E0B', 'https://sec.gov'),
    feed(IMF_URL,
      'IMF', 'Global Economy', '🌍', '#64748b', 'https://imf.org/en/Blogs'),
    feed(WORLDBANK_URL,
      'World Bank', 'Global Finance', '🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
  ],
  europe: [
    feed('https://www.ecb.europa.eu/rss/press.html',
      'ECB', 'Rate Decision', '🏦', '#6366F1', 'https://ecb.europa.eu'),
    feed('https://www.ecb.europa.eu/rss/key.html',
      'ECB', 'Key Speech', '🎙️', '#22C55E', 'https://ecb.europa.eu'),
    feed('https://www.esma.europa.eu/sites/default/files/library/esma_news.xml',
      'ESMA', 'Regulator', '📋', '#EC4899', 'https://esma.europa.eu'),
    feed(IMF_URL,
      'IMF', 'Global Economy', '🌍', '#64748b', 'https://imf.org/en/Blogs'),
    feed(BIS_URL,
      'BIS', 'Central Banks', '🏛️', '#94a3b8', 'https://bis.org'),
  ],
  world: [
    feed(IMF_URL,
      'IMF', 'Global Economy', '🌍', '#3B82F6', 'https://imf.org/en/Blogs'),
    feed(BIS_URL,
      'BIS', 'Central Banks', '🏛️', '#C9A84C', 'https://bis.org'),
    feed('https://www.federalreserve.gov/feeds/press_all.xml',
      'Fed Reserve', 'US Policy', '💵', '#22C55E', 'https://federalreserve.gov'),
    feed('https://www.ecb.europa.eu/rss/press.html',
      'ECB', 'EU Policy', '🇪🇺', '#6366F1', 'https://ecb.europa.eu'),
    feed(WORLDBANK_URL,
      'World Bank', 'Global Finance', '🌐', '#0ea5e9', 'https://blogs.worldbank.org'),
  ],
};

// ── ISS-04b: Fallback articles with stale indicator ──────
// All fallback articles carry fallback:true and staleNote so
// the UI can render a "Showing cached content" banner.
const FALLBACK_STAMP = {
  fallback:   true,
  staleNote:  'Offline placeholder — live feed unavailable',
  timeLabel:  'Cached',
};

const FALLBACK = {
  india: [
    { ...FALLBACK_STAMP, title:'RBI monetary policy — latest press release', source:'RBI', emoji:'🏦', color:'#C9A84C', label:'Press Release', link:'https://rbi.org.in', pubDate:null },
    { ...FALLBACK_STAMP, title:'SEBI circular — mutual fund and market updates', source:'SEBI', emoji:'📋', color:'#6366F1', label:'Regulator', link:'https://sebi.gov.in', pubDate:null },
    { ...FALLBACK_STAMP, title:'PIB — Government finance and budget updates', source:'PIB', emoji:'🇮🇳', color:'#EC4899', label:'Govt Finance', link:'https://pib.gov.in', pubDate:null },
    { ...FALLBACK_STAMP, title:'IMF — India and Asia Pacific economic outlook', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', link:'https://imf.org/en/Blogs', pubDate:null },
    { ...FALLBACK_STAMP, title:'BIS — Global central bank policy update', source:'BIS', emoji:'🏛️', color:'#94a3b8', label:'Central Banks', link:'https://bis.org', pubDate:null },
  ],
  usa: [
    { ...FALLBACK_STAMP, title:'Federal Reserve — latest monetary policy statement', source:'Fed Reserve', emoji:'🏛️', color:'#3B82F6', label:'Monetary Policy', link:'https://federalreserve.gov', pubDate:null },
    { ...FALLBACK_STAMP, title:'FOMC — interest rate and inflation update', source:'FOMC', emoji:'💵', color:'#22C55E', label:'Rate Decision', link:'https://federalreserve.gov', pubDate:null },
    { ...FALLBACK_STAMP, title:'SEC — latest regulatory and investor protection news', source:'SEC', emoji:'⚖️', color:'#F59E0B', label:'Regulator', link:'https://sec.gov', pubDate:null },
    { ...FALLBACK_STAMP, title:'IMF — United States economic outlook', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', link:'https://imf.org/en/Blogs', pubDate:null },
    { ...FALLBACK_STAMP, title:'World Bank — global economic and trade update', source:'World Bank', emoji:'🌐', color:'#0ea5e9', label:'Global Finance', link:'https://blogs.worldbank.org', pubDate:null },
  ],
  europe: [
    { ...FALLBACK_STAMP, title:'ECB — key interest rate decision', source:'ECB', emoji:'🏦', color:'#6366F1', label:'Rate Decision', link:'https://ecb.europa.eu', pubDate:null },
    { ...FALLBACK_STAMP, title:'ECB — President speech and policy guidance', source:'ECB', emoji:'🎙️', color:'#22C55E', label:'Key Speech', link:'https://ecb.europa.eu', pubDate:null },
    { ...FALLBACK_STAMP, title:'ESMA — European market regulation update', source:'ESMA', emoji:'📋', color:'#EC4899', label:'Regulator', link:'https://esma.europa.eu', pubDate:null },
    { ...FALLBACK_STAMP, title:'IMF — Euro area economic outlook', source:'IMF', emoji:'🌍', color:'#64748b', label:'Global Economy', link:'https://imf.org/en/Blogs', pubDate:null },
    { ...FALLBACK_STAMP, title:'BIS — European banking and rates update', source:'BIS', emoji:'🏛️', color:'#94a3b8', label:'Central Banks', link:'https://bis.org', pubDate:null },
  ],
  world: [
    { ...FALLBACK_STAMP, title:'IMF — Global economic growth and trade outlook', source:'IMF', emoji:'🌍', color:'#3B82F6', label:'Global Economy', link:'https://imf.org/en/Blogs', pubDate:null },
    { ...FALLBACK_STAMP, title:'BIS — Central banks and post-rate-cycle normalisation', source:'BIS', emoji:'🏛️', color:'#C9A84C', label:'Central Banks', link:'https://bis.org', pubDate:null },
    { ...FALLBACK_STAMP, title:'Fed Reserve — US monetary policy latest', source:'Fed Reserve', emoji:'💵', color:'#22C55E', label:'US Policy', link:'https://federalreserve.gov', pubDate:null },
    { ...FALLBACK_STAMP, title:'ECB — Euro area inflation and rate path', source:'ECB', emoji:'🇪🇺', color:'#6366F1', label:'EU Policy', link:'https://ecb.europa.eu', pubDate:null },
    { ...FALLBACK_STAMP, title:'World Bank — global development and finance update', source:'World Bank', emoji:'🌐', color:'#0ea5e9', label:'Global Finance', link:'https://blogs.worldbank.org', pubDate:null },
  ],
};

// ── In-memory cache ───────────────────────────────────────
const _cache     = {};
const _cacheTime = {};
const CACHE_MS   = 60 * 60 * 1000; // 1 hour

// ─────────────────────────────────────────────────────────────────────────────
// ISS-04 FIX — DIRECT RSS FETCHING (no rss2json.com proxy)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetches raw RSS/Atom XML directly from the source URL.
 * Returns the raw string body or throws on network/timeout errors.
 */
function fetchRawXML(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      timeout: 9000,
      headers: {
        'User-Agent': 'MoneyVeda/2.0',
        'Accept':     'application/rss+xml, application/atom+xml, text/xml, */*',
      },
    }, (res) => {
      // Follow a single redirect (NSE, RBI occasionally redirect)
      if (res.statusCode === 301 || res.statusCode === 302) {
        const location = res.headers.location;
        res.resume();
        if (location) return fetchRawXML(location).then(resolve).catch(reject);
        return reject(new Error('Redirect with no Location header'));
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }

      let body = '';
      res.setEncoding('utf8');
      res.on('data', chunk => { body += chunk; });
      res.on('end',  ()    => resolve(body));
    });
    req.on('error',   reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// ── XML entity decoder (minimal, covers common entities in RSS titles) ──
const XML_ENTITIES = {
  '&amp;':  '&',
  '&lt;':   '<',
  '&gt;':   '>',
  '&quot;': '"',
  '&apos;': "'",
  '&#39;':  "'",
  '&#x27;': "'",
};

function decodeXMLEntities(str) {
  // Decode named entities
  let out = str.replace(/&[a-zA-Z]+;|&#x?[0-9a-fA-F]+;/g, match => {
    if (XML_ENTITIES[match]) return XML_ENTITIES[match];
    // Numeric character references
    if (match.startsWith('&#x')) return String.fromCharCode(parseInt(match.slice(3, -1), 16));
    if (match.startsWith('&#'))  return String.fromCharCode(parseInt(match.slice(2, -1), 10));
    return match;
  });
  return out;
}

/**
 * Extracts text content from the first occurrence of an XML tag.
 * Handles both <tag>text</tag> and CDATA <tag><![CDATA[text]]></tag>.
 */
function extractTag(xml, tag) {
  // Try CDATA first
  const cdataRe = new RegExp(`<${tag}[^>]*>\\s*<!\\[CDATA\\[([\\s\\S]*?)\\]\\]>\\s*</${tag}>`, 'i');
  const cdataM  = xml.match(cdataRe);
  if (cdataM) return cdataM[1].trim();

  // Plain text
  const plainRe = new RegExp(`<${tag}[^>]*>([^<]*)</${tag}>`, 'i');
  const plainM  = xml.match(plainRe);
  if (plainM) return decodeXMLEntities(plainM[1]).trim();

  return '';
}

/**
 * ISS-04 FIX: Parses raw RSS 2.0 or Atom XML into a standard item array.
 * Supports:
 *   - RSS 2.0: <item><title>…</title><link>…</link><pubDate>…</pubDate></item>
 *   - Atom:    <entry><title>…</title><link href="…"/><updated>…</updated></entry>
 */
function parseRSS(xmlBody, feedMeta) {
  const items = [];

  // Detect format
  const isAtom = xmlBody.includes('<feed') && xmlBody.includes('<entry');
  const itemTag = isAtom ? 'entry' : 'item';

  // Split into individual item/entry blocks
  const itemRe = new RegExp(`<${itemTag}[^>]*>([\\s\\S]*?)</${itemTag}>`, 'gi');
  let match;

  while ((match = itemRe.exec(xmlBody)) !== null && items.length < 2) {
    const block = match[1];

    // Title
    const rawTitle = extractTag(block, 'title');
    const title    = rawTitle
      .replace(/<[^>]+>/g, '')   // strip any nested HTML
      .replace(/\s+/g, ' ')
      .trim();

    if (!title || title.length < 5) continue;

    // Link — RSS uses <link>, Atom uses <link href="..."/>
    let link = extractTag(block, 'link');
    if (!link) {
      const hrefM = block.match(/<link[^>]+href=["']([^"']+)["']/i);
      if (hrefM) link = hrefM[1];
    }
    link = link || feedMeta.link;

    // Date — RSS uses <pubDate>, Atom uses <updated> or <published>
    const rawDate = extractTag(block, 'pubDate')
                 || extractTag(block, 'updated')
                 || extractTag(block, 'published');
    const pub     = rawDate ? new Date(rawDate) : new Date();
    const validPub = !isNaN(pub.getTime()) ? pub : new Date();

    const h = Math.floor((Date.now() - validPub.getTime()) / 3_600_000);
    const timeLabel = h < 1 ? 'Just now' : h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;

    items.push({
      title:    title.length > 110 ? title.slice(0, 107) + '…' : title,
      link,
      source:    feedMeta.source,
      label:     feedMeta.label,
      emoji:     feedMeta.emoji,
      color:     feedMeta.color,
      timeLabel,
      pubDate:   validPub.toISOString(),
      fallback:  false,
    });
  }

  return items;
}

// ── Main handler ──────────────────────────────────────────
module.exports = async function handler(req, res) {
  res.setHeader('Content-Type',                 'application/json');
  res.setHeader('Access-Control-Allow-Origin',  '*');
  res.setHeader('Cache-Control',                'public, max-age=3600, stale-while-revalidate=7200');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET')     return res.status(405).json({ error: 'Method not allowed' });

  const region = ((req.query && req.query.region) || 'india').toLowerCase();
  const feeds  = FEEDS[region];
  if (!feeds) return res.status(200).json({ articles: [], region, note: 'Coming soon' });

  // Serve from memory cache if fresh
  if (_cache[region] && (Date.now() - (_cacheTime[region] || 0)) < CACHE_MS) {
    return res.status(200).json({ articles: _cache[region], cached: true, region });
  }

  try {
    // ISS-04 FIX: Direct RSS fetch — no rss2json.com proxy
    const results = await Promise.allSettled(
      feeds.map(f =>
        fetchRawXML(f.rssUrl)
          .then(xml  => parseRSS(xml, f))
          .catch(err => {
            console.warn(`[${f.source}] feed fetch failed: ${err.message}`);
            return [];
          })
      )
    );

    let articles = results
      .filter(r  => r.status === 'fulfilled')
      .flatMap(r => r.value)
      .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
      .slice(0, 8);

    // ISS-04b: Fallback with stale indicator
    if (articles.length === 0) {
      console.warn(`All feeds failed for ${region} — serving fallback`);
      const fallbackArticles = (FALLBACK[region] || []).map(a => ({
        ...a,
        pubDate:      new Date().toISOString(), // timestamp of when fallback was served
        fallbackAt:   new Date().toISOString(),
      }));

      return res.status(200).json({
        articles:   fallbackArticles,
        cached:     false,
        region,
        fallback:   true,
        fallbackAt: new Date().toISOString(),
        count:      fallbackArticles.length,
        fetchedAt:  new Date().toISOString(),
      });
    }

    _cache[region]     = articles;
    _cacheTime[region] = Date.now();

    return res.status(200).json({
      articles,
      cached:    false,
      region,
      fallback:  false,
      count:     articles.length,
      fetchedAt: new Date().toISOString(),
    });

  } catch (err) {
    console.error('[MoneyVeda News] Handler error:', err.message);
    const fallbackArticles = (FALLBACK[region] || []).map(a => ({
      ...a,
      pubDate:    new Date().toISOString(),
      fallbackAt: new Date().toISOString(),
    }));
    return res.status(200).json({
      articles:   fallbackArticles,
      cached:     false,
      region,
      fallback:   true,
      fallbackAt: new Date().toISOString(),
    });
  }
};

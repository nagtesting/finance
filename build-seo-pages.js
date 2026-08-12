#!/usr/bin/env node
/* ============================================================
 * build-seo-pages.js — MoneyVeda static page generator
 * ============================================================
 * Reads calculators.html and emits one real HTML file per
 * calculator, each with its own <title>, meta description,
 * self-referencing canonical, Open Graph tags, breadcrumb and
 * FAQ structured data, correct <h1>, and unique body copy.
 *
 * Why this exists
 * ---------------
 * vercel.json currently rewrites 19 slugs to a single
 * calculators.html. Every one of those URLs therefore serves
 * identical HTML with a canonical pointing at /calculators, so
 * Google consolidates them and none of them rank. The meta
 * swapping in updatePageMeta() runs only on a click, which a
 * crawler never performs.
 *
 * Usage
 * -----
 *   node build-seo-pages.js                  # write files to repo root
 *   node build-seo-pages.js --dry            # report only, write nothing
 *   node build-seo-pages.js --out dist       # write elsewhere
 *   node build-seo-pages.js --src path.html  # non-default source
 *
 * After running, update vercel.json: DELETE the per-calculator
 * rewrites. Vercel serves sip-calculator.html at /sip-calculator
 * automatically. A suggested vercel.json is written for you.
 *
 * Wire it into the build with, in package.json:
 *   "scripts": { "build": "node build-seo-pages.js" }
 * and set that as the Vercel build command.
 * ============================================================ */

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// ── CLI ──────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = argv.indexOf('--' + name);
  return i === -1 ? fallback : (argv[i + 1] || fallback);
};
const DRY     = argv.includes('--dry');
const SRC     = path.resolve(flag('src', 'calculators.html'));
const OUT_DIR = path.resolve(flag('out', '.'));
const ORIGIN  = 'https://moneyveda.org';

const content = require(path.resolve(__dirname, 'seo-content.js'));

// Static pages that are not generated from tabs but belong in the sitemap.
const STATIC_URLS = [
  { loc: '/',                    changefreq: 'hourly',  priority: '1.0' },
  { loc: '/calculators',         changefreq: 'weekly',  priority: '0.9' },
  { loc: '/accuracy-dashboard',  changefreq: 'daily',   priority: '0.6' },
];

// Slugs that are utility pages rather than ranking targets.
const NOINDEX_TABS = new Set(['contact']);

const warnings = [];
const warn = (m) => { warnings.push(m); };

// ── helpers ──────────────────────────────────────────────────
const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/"/g, '&quot;')
  .replace(/</g, '&lt;').replace(/>/g, '&gt;');

const stripTags = (s) => String(s).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

const today = () => new Date().toISOString().slice(0, 10);

/**
 * Replace the first match of `re` in `str` with `next`.
 * Records a warning if the pattern was not found, because a silent
 * miss here is exactly the failure mode that caused the original bug.
 */
function sub(str, re, next, label, slug) {
  if (!re.test(str)) {
    warn(`[${slug}] could not find ${label} — pattern did not match. Check the markup.`);
    return str;
  }
  return str.replace(re, () => next);
}

// ── read source ──────────────────────────────────────────────
if (!fs.existsSync(SRC)) {
  console.error(`Source not found: ${SRC}`);
  process.exit(1);
}
const source = fs.readFileSync(SRC, 'utf8');

// ── extract TAB_SEO from the page itself ─────────────────────
// Single source of truth: the object already living in calculators.html.
// Editing it there keeps the runtime SPA and the generated pages in sync.
function extractTabSeo(html) {
  const m = html.match(/const\s+TAB_SEO\s*=\s*(\{[\s\S]*?\n\});/);
  if (!m) {
    console.error('Could not locate `const TAB_SEO = { ... };` in the source file.');
    console.error('If you renamed it, update the regex in extractTabSeo().');
    process.exit(1);
  }
  try {
    return vm.runInNewContext('(' + m[1] + ')', Object.create(null), { timeout: 1000 });
  } catch (e) {
    console.error('TAB_SEO found but failed to parse:', e.message);
    process.exit(1);
  }
}
const TAB_SEO = extractTabSeo(source);

// Tab order, used to keep sitemap output stable.
const TABS = Object.keys(TAB_SEO);

// ── head rewriting ───────────────────────────────────────────
function rewriteHead(head, id, seo, url) {
  const title = seo.title;
  const desc  = seo.desc;

  head = sub(head, /<title>[\s\S]*?<\/title>/i,
    `<title>${esc(title)}</title>`, '<title>', id);

  head = sub(head, /<meta\s+name=["']description["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta name="description" content="${esc(desc)}">`, 'meta description', id);

  head = sub(head, /<link\s+rel=["']canonical["']\s+href=["'][^"']*["']\s*\/?>/i,
    `<link rel="canonical" href="${url}">`, 'canonical', id);

  head = sub(head, /<meta\s+property=["']og:url["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta property="og:url" content="${url}">`, 'og:url', id);

  head = sub(head, /<meta\s+property=["']og:title["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta property="og:title" content="${esc(title)}">`, 'og:title', id);

  head = sub(head, /<meta\s+property=["']og:description["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta property="og:description" content="${esc(desc)}">`, 'og:description', id);

  // Twitter tags are optional in the source; don't warn if absent.
  head = head.replace(/<meta\s+name=["']twitter:title["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta name="twitter:title" content="${esc(title)}">`);
  head = head.replace(/<meta\s+name=["']twitter:description["']\s+content=["'][^"']*["']\s*\/?>/i,
    `<meta name="twitter:description" content="${esc(desc)}">`);

  // Utility pages should not compete for index space.
  if (NOINDEX_TABS.has(id)) {
    head = head.replace(/<meta\s+name=["']robots["']\s+content=["'][^"']*["']\s*\/?>/i,
      '<meta name="robots" content="noindex, follow">');
  }

  // ── breadcrumb JSON-LD: replace the body of the existing block ──
  const crumbName = title.split(' —')[0].split(' |')[0].trim();
  const breadcrumb = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'MoneyVeda', item: ORIGIN + '/' },
      { '@type': 'ListItem', position: 2, name: 'Calculators', item: ORIGIN + '/calculators' },
      { '@type': 'ListItem', position: 3, name: crumbName, item: url },
    ],
  });
  const crumbRe = /(<script[^>]*id=["']ld-breadcrumb["'][^>]*>)[\s\S]*?(<\/script>)/i;
  if (crumbRe.test(head)) {
    head = head.replace(crumbRe, (_m, open, close) => open + breadcrumb + close);
  } else {
    head = head.replace(/<\/head>/i,
      `<script type="application/ld+json" id="ld-breadcrumb">${breadcrumb}</script>\n</head>`);
  }

  // ── FAQPage + WebApplication JSON-LD ──
  const c = content[id];
  const extra = [];

  if (c && Array.isArray(c.faq) && c.faq.length) {
    extra.push(JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: c.faq.map(f => ({
        '@type': 'Question',
        name: stripTags(f.q),
        acceptedAnswer: { '@type': 'Answer', text: stripTags(f.a) },
      })),
    }));
  }

  if (!NOINDEX_TABS.has(id)) {
    extra.push(JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'WebApplication',
      name: crumbName,
      url: url,
      applicationCategory: 'FinanceApplication',
      operatingSystem: 'Any',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'INR' },
      inLanguage: 'en-IN',
    }));
  }

  if (extra.length) {
    const blocks = extra
      .map(j => `<script type="application/ld+json">${j}</script>`)
      .join('\n');
    head = head.replace(/<\/head>/i, blocks + '\n</head>');
  }

  return head;
}

// ── body rewriting ───────────────────────────────────────────
/**
 * calculators.html carries one <h1> per tab (e.g. <h1 id="sip-title">).
 * On a single-page build that means 19 H1s in every document, and the
 * visible one is generic ("Investment Planner") and identical everywhere.
 *
 * Demote all of them to <h2>, keeping every attribute so setEl() and the
 * localisation layer keep working by id. The generator then injects
 * exactly one page-specific <h1>.
 *
 * If your CSS targets `h1.display` rather than `.display`, add the h2
 * selector before running this, or pass --keep-h1 to skip the step.
 */
function demoteH1s(body) {
  return body
    .replace(/<h1(\s[^>]*)?>/gi, (_m, attrs) => `<h2${attrs || ''}>`)
    .replace(/<\/h1>/gi, '</h2>');
}

function rewriteBody(body, id, fallbackH1) {
  if (!argv.includes('--keep-h1')) body = demoteH1s(body);

  // 1. Move the `active` class onto the correct tab so the right
  //    panel is in the served HTML, not applied later by JS.
  let found = false;
  TABS.forEach(t => {
    const re = new RegExp(`(<div\\s+id=["']${t}["']\\s+class=["']tab)( active)?(["'])`, 'i');
    if (!re.test(body)) {
      if (t === id) warn(`[${id}] tab container <div id="${id}" class="tab"> not found in body.`);
      return;
    }
    if (t === id) found = true;
    body = body.replace(re, (_m, a, _b, c) => a + (t === id ? ' active' : '') + c);
  });
  if (!found) return { body, injected: false };

  // 2. Inject unique copy directly after the tab's opening div.
  const c = content[id];
  {
    const parts = [];

    // Every page needs exactly one H1. Pages without written copy fall back
    // to the TAB_SEO title so demoteH1s() never leaves a page headless.
    const heading = (c && c.h1) || fallbackH1;
    parts.push(
      `<h1 class="display" style="font-size:2.1rem;font-weight:900;margin:0 0 10px;">${esc(heading)}</h1>`
    );
    if (c && c.intro) {
      parts.push(
        `<div class="mv-seo-intro" style="color:var(--muted);font-size:14px;line-height:1.75;` +
        `max-width:74ch;margin-bottom:26px;">${c.intro.trim()}</div>`
      );
    }
    if (c && Array.isArray(c.faq) && c.faq.length) {
      const items = c.faq.map(f => `
        <details style="border-bottom:1px solid rgba(201,168,76,.12);padding:13px 0;">
          <summary style="cursor:pointer;font-weight:600;color:var(--gold-light);font-size:14.5px;list-style:none;">${esc(f.q)}</summary>
          <p style="color:var(--muted);font-size:13.5px;line-height:1.7;margin:10px 0 0;max-width:74ch;">${esc(f.a)}</p>
        </details>`).join('');
      // Rendered here in the HTML so crawlers see it near the H1; the boot
      // script moves it to the bottom of the panel for human readers.
      parts.push(
        `<section id="mv-seo-faq" style="margin-top:34px;">
           <div class="section-eyebrow">Frequently Asked Questions</div>
           <h2 style="font-size:1.4rem;font-weight:800;margin:6px 0 14px;">Common questions</h2>
           ${items}
         </section>`
      );
    }

    if (parts.length) {
      const openRe = new RegExp(`(<div\\s+id=["']${id}["']\\s+class=["']tab active["']\\s*>)`, 'i');
      body = body.replace(openRe, (m) => m + '\n' + parts.join('\n') + '\n');
    }
  }

  if (!c && !NOINDEX_TABS.has(id)) {
    warn(`[${id}] no entry in seo-content.js — page is thin. It will rank for little until you add copy.`);
  }

  // 3. Boot script. Sets the active tab without a flash, relocates the
  //    FAQ block, and hands control back to the existing SPA.
  const boot = `
<script>
/* generated by build-seo-pages.js */
window.__MV_TAB__ = ${JSON.stringify(id)};
(function () {
  function boot() {
    var id  = window.__MV_TAB__;
    var tab = document.getElementById(id);
    var faq = document.getElementById('mv-seo-faq');
    if (tab && faq && faq.parentNode === tab) tab.appendChild(faq);
    if (typeof navTo === 'function') { try { navTo(id); } catch (e) {} }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { setTimeout(boot, 0); });
  } else {
    setTimeout(boot, 0);
  }
})();
</script>`;

  if (/<\/body>/i.test(body)) {
    body = body.replace(/<\/body>/i, boot + '\n</body>');
  } else {
    body += boot;
    warn(`[${id}] no </body> found; boot script appended at end of file.`);
  }

  return { body, injected: true };
}

// ── generate one page ────────────────────────────────────────
function buildPage(id) {
  const seo = TAB_SEO[id];
  if (!seo || !seo.slug) { warn(`[${id}] missing slug in TAB_SEO — skipped.`); return null; }

  const url = `${ORIGIN}/${seo.slug}`;
  const headEnd = source.indexOf('</head>');
  if (headEnd === -1) { console.error('No </head> in source.'); process.exit(1); }

  const head = rewriteHead(source.slice(0, headEnd + 7), id, seo, url);
  const crumb = seo.title.split(' —')[0].split(' |')[0].trim();
  const rest = rewriteBody(source.slice(headEnd + 7), id, crumb);

  const banner = `<!-- GENERATED by build-seo-pages.js — do not edit by hand.\n` +
                 `     Source: ${path.basename(SRC)} · Tab: ${id} · ${today()} -->\n`;

  return {
    id,
    slug: seo.slug,
    file: `${seo.slug}.html`,
    html: banner + head + rest.body,
    hasContent: Boolean(content[id]),
  };
}

// ── sitemap ──────────────────────────────────────────────────
function buildSitemap(pages) {
  const urls = STATIC_URLS.map(u => ({ ...u, loc: ORIGIN + u.loc }));
  pages.forEach(p => {
    if (NOINDEX_TABS.has(p.id)) return;
    urls.push({
      loc: `${ORIGIN}/${p.slug}`,
      changefreq: 'weekly',
      priority: p.hasContent ? '0.9' : '0.7',
    });
  });
  const body = urls.map(u => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${today()}</lastmod>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;
}

// ── suggested vercel.json ────────────────────────────────────
function buildVercelConfig() {
  let existing = {};
  const p = path.join(path.dirname(SRC), 'vercel.json');
  if (fs.existsSync(p)) {
    try { existing = JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) {
      warn('vercel.json exists but is not valid JSON; generated a fresh one.');
    }
  }
  const slugs = new Set(Object.values(TAB_SEO).map(s => '/' + s.slug));
  const keep = (existing.rewrites || []).filter(r => !slugs.has(r.source));
  // /calculators keeps its rewrite: it is a real hub page, not a duplicate.
  if (!keep.some(r => r.source === '/calculators')) {
    keep.push({ source: '/calculators', destination: '/calculators.html' });
  }
  return JSON.stringify({
    version: 2,
    redirects: existing.redirects || [],
    rewrites: keep,
    cleanUrls: true,
  }, null, 2) + '\n';
}

// ── run ──────────────────────────────────────────────────────
const pages = TABS.map(buildPage).filter(Boolean);

if (!DRY) fs.mkdirSync(OUT_DIR, { recursive: true });

pages.forEach(p => {
  const dest = path.join(OUT_DIR, p.file);
  if (!DRY) fs.writeFileSync(dest, p.html, 'utf8');
});

if (!DRY) {
  fs.writeFileSync(path.join(OUT_DIR, 'sitemap.xml'), buildSitemap(pages), 'utf8');
  fs.writeFileSync(path.join(OUT_DIR, 'vercel.suggested.json'), buildVercelConfig(), 'utf8');
}

// ── report ───────────────────────────────────────────────────
const withCopy = pages.filter(p => p.hasContent);
const thin     = pages.filter(p => !p.hasContent && !NOINDEX_TABS.has(p.id));

console.log(`\n${DRY ? 'Would generate' : 'Generated'} ${pages.length} pages from ${path.basename(SRC)}\n`);
console.log(`  with unique copy : ${withCopy.length}  (${withCopy.map(p => p.id).join(', ') || 'none'})`);
console.log(`  thin             : ${thin.length}  (${thin.map(p => p.id).join(', ') || 'none'})`);
if (!DRY) {
  console.log(`\n  output           : ${OUT_DIR}`);
  console.log(`  sitemap.xml      : rewritten with ${pages.length - NOINDEX_TABS.size} indexable URLs`);
  console.log(`  vercel.suggested.json written — diff it against vercel.json, then replace.`);
}

if (warnings.length) {
  console.log(`\n${warnings.length} warning(s):`);
  warnings.forEach(w => console.log('  ! ' + w));
}

console.log(`\nNext: remove the per-calculator rewrites from vercel.json, deploy, then`);
console.log(`resubmit the sitemap and run URL Inspection on one slug to confirm`);
console.log(`Google-selected canonical now matches the URL itself.\n`);

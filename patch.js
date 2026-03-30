// ================================================================
// MoneyVeda — patch.js  v3  (final)
// Load as: <script src="patch.js"></script>  — AFTER the two
// main <script> blocks in index.html.
//
// FIXES:
//   FIX-1  Investment Planner cards no longer overlap — grid uses
//          minmax(0,1fr) and big-number scales with clamp().
//          Also applied to EMI, PPF, FIRE, NPS top-stat rows.
//
//   FIX-2  Ticker & sidebar show CORRECT region data for UK /
//          Germany / France / Spain (all map → europe endpoint).
//          setMode is wrapped so every mode-switch retriggers
//          the correct mapped ticker — no MutationObserver race.
//
//   FIX-3  Language toggle translates ALL visible text.
//          Root cause: setMode calls updateStaticLabels() (English)
//          THEN applyLanguage(). applyLanguage never touched the
//          static-label elements, so they stayed English.
//          Fix: replace updateStaticLabels() with a version that
//          reads currentLang and picks translated strings, then
//          call it LAST inside applyLanguage so the final paint
//          is always in the chosen language.
//
//   FIX-A  Habit presets use region-local currency + realistic
//          prices for every market.
//   FIX-B  Habit slider ranges update when the user switches
//          region.
//   FIX-C  Every range slider gets a small editable number input
//          beside it so users can type an exact value.
// ================================================================


// ══════════════════════════════════════════════════════════════
// FIX-1 — Prevent result-card overlap in all stat grids
// ══════════════════════════════════════════════════════════════
(function fixCardLayout() {
  const style = document.createElement('style');
  style.textContent = `
    /* Force grid cells to never overflow their column */
    .grid-3 {
      display: grid !important;
      grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
      min-width: 0;
    }
    .grid-3 > * { min-width: 0; overflow: hidden; }

    /* result-box numbers scale with available width */
    .result-box .big-number {
      font-size: clamp(1.2rem, 3vw, 2.6rem) !important;
      line-height: 1.15 !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }
    /* The secondary big numbers (not .big-number class) */
    .result-box [style*="1.7rem"] {
      font-size: clamp(1rem, 2.4vw, 1.7rem) !important;
      overflow-wrap: break-word !important;
    }
    /* Mobile: stack to 1 col below 500px */
    @media (max-width: 500px) {
      .grid-3 { grid-template-columns: 1fr !important; }
    }
    /* Tablet 501-768px: keep 3 cols, smaller font */
    @media (min-width: 501px) and (max-width: 768px) {
      .result-box .big-number { font-size: 1.25rem !important; }
    }
    /* Ensure main area never overflows into sidebar */
    #main { min-width: 0; overflow: hidden; }
    #main-scroll { min-width: 0; }
    .tab { min-width: 0; overflow-x: hidden; }
  `;
  document.head.appendChild(style);
})();


// ══════════════════════════════════════════════════════════════
// FIX-2 — Ticker / sidebar region mapping
// The /api/market endpoint supports: india | usa | europe | world
// UI modes: india | usa | uk | germany | france | spain
// ══════════════════════════════════════════════════════════════
const TICKER_MODE_MAP = {
  india:   'india',
  usa:     'usa',
  uk:      'europe',
  germany: 'europe',
  france:  'europe',
  spain:   'europe',
  europe:  'europe',
  world:   'world',
};

// Wrap the original loadTickerData so the API gets the right mode
const _origLoadTicker = window.loadTickerData;
window.loadTickerData = async function(mode) {
  const apiMode = TICKER_MODE_MAP[mode] || 'india';
  if (typeof _origLoadTicker === 'function') return _origLoadTicker(apiMode);
};

// Wrap loadSidebarLive to translate mode before fetch
window.loadSidebarLive = async function() {
  const apiMode = TICKER_MODE_MAP[window.currentMode || 'india'] || 'india';
  function safeAbort(ms) {
    try { if (typeof AbortSignal !== 'undefined' && AbortSignal.timeout) return AbortSignal.timeout(ms); } catch(e) {}
    const c = new AbortController(); setTimeout(() => c.abort(), ms); return c.signal;
  }
  try {
    const res = await fetch('/api/market?mode=' + apiMode + '&view=sidebar', { signal: safeAbort(5000) });
    if (!res.ok) throw new Error('non-200');
    const data = await res.json();
    const el = document.getElementById('sidebar-market');
    if (el) el.innerHTML = data.sidebarHtml || '';
    const dot = document.getElementById('sidebar-live-dot');
    if (dot) dot.style.background = data.live ? '#4ade80' : '#9090A8';
    const upd = document.getElementById('sidebar-updated');
    if (upd) upd.textContent = data.updatedTime || '';
  } catch(e) { /* keep last content */ }
};

// Wrap startSidebarRefresh to use the patched loadSidebarLive
window.startSidebarRefresh = function() {
  if (window._sidebarTimer) clearInterval(window._sidebarTimer);
  window.loadSidebarLive();
  window._sidebarTimer = setInterval(window.loadSidebarLive, 30000);
};


// ══════════════════════════════════════════════════════════════
// FIX-3 — Full language translation for ALL static label elements
//
// Strategy:
//   Replace updateStaticLabels() with a language-aware version.
//   Patch applyLanguage() to call it at the very end.
//   Call order in setMode becomes:
//     updateStaticLabels (English)   <- original call
//     applyLanguage                  <- original call
//       └─ [our patch] updateStaticLabels (localized) LAST
//   Net result: every element ends up in the chosen language.
// ══════════════════════════════════════════════════════════════

const STATIC_LABEL_STRINGS = {
  india: {
    hi: {
      sipEyebrow:      'SIP · भारत',
      sipDesc:         'अनुशासित मासिक SIP के माध्यम से चक्रवृद्धि — भारत का सबसे शक्तिशाली धन-सृजन उपकरण।',
      sipPLabel:       'मासिक निवेश',
      sipRateHint:     'निफ्टी 50 ऐतिहासिक औसत ~13%',
      sipTaxLabel:     'कर बचत (80C/ELSS)',
      sipTaxNote:      '₹1.5L/वर्ष तक कटौती',
      sipEdu1:         '₹5,000/माह 25 पर = 60 तक ₹2.76 Cr। 35 पर वही SIP = केवल ₹0.85 Cr। जल्दी शुरू करें।',
      sipEdu3Title:    'रुपया लागत औसत',
      sipEdu3:         'SIP बाज़ार गिरने पर अधिक यूनिट और बढ़ने पर कम यूनिट खरीदती है — स्वचालित रूप से औसत लागत कम होती है।',
      emiEyebrow:      'ऋण · भारत',
      emiDesc:         'गृह ऋण पर मासिक किस्त, कुल ब्याज और धारा 24(b) कर लाभ की गणना करें।',
      emiPLabel:       'ऋण राशि',
      emiRateHint:     'SBI होम लोन ~8.25% (2026)',
      emiTaxLabel:     'कर लाभ धारा 24(b)',
      emiTaxNote:      '₹2L/वर्ष तक कटौती',
      emiDtiLabel:     'EMI सकल आय के 40% से कम',
      emiMonthlyLabel: 'मासिक EMI',
      fireEyebrow:     'FIRE · भारत',
      fireExpLabel:    'मासिक खर्च (₹)',
      roiEyebrow:      'रिटर्न · भारत',
      roiPLabel:       'प्रारंभिक निवेश (₹)',
      roiCompareTitle: 'परिसंपत्ति वर्ग तुलना — 20 वर्ष',
      roiCompareSub:   'ऐतिहासिक औसत · आधार: ₹1 लाख',
      insEyebrow:      'बीमा · भारत',
      insDesc:         'मानव जीवन मूल्य (HLV) पद्धति से अनुशंसित बीमा राशि की गणना करें।',
      insIncLabel:     'वार्षिक आय (₹)',
      insLiabLabel:    'देनदारियां (₹)',
      insLocalTitle:   'लोकप्रिय भारतीय बीमा उत्पाद',
      taxEyebrow:      'कर · भारत',
      taxDesc:         'FY2025-26 के लिए पुरानी बनाम नई कर व्यवस्था की तुलना करें।',
    }
  },
  germany: {
    de: {
      sipEyebrow:      'ETF-Sparplan · Deutschland',
      sipDesc:         'Bauen Sie langfristig Vermögen durch disziplinierte monatliche ETF-Sparpläne auf.',
      sipPLabel:       'Monatliche Investition',
      sipRateHint:     'DAX hist. ~8.0% / MSCI World ~9.5%',
      sipTaxLabel:     'Steuerersparnis (est.)',
      sipTaxNote:      'Sparerpauschbetrag: €1.000/Jahr (Single)',
      sipEdu1:         '€300/Monat mit 25 Jahren = ~€730K bis 60 bei 9.5%. Nutze zuerst deinen Sparerpauschbetrag.',
      sipEdu3Title:    'Cost-Average-Effekt',
      sipEdu3:         'Regelmäßige Investitionen kaufen mehr Anteile wenn Kurse fallen — der Durchschnittskosteneffekt senkt deinen mittleren Einstandskurs.',
      emiEyebrow:      'Immobilienfinanzierung · Deutschland',
      emiDesc:         'Berechne monatliche Raten, Gesamtzinsen und steuerliche Aspekte deiner Immobilienfinanzierung.',
      emiPLabel:       'Darlehensbetrag',
      emiRateHint:     'Durchschn. Sollzins ~3.8% (2026)',
      emiTaxLabel:     'Steuerlicher Vorteil',
      emiTaxNote:      'Schuldzinsen i.d.R. nicht absetzbar (Eigenheim)',
      emiDtiLabel:     'Schuldenquote unter 40% empfohlen',
      emiMonthlyLabel: 'Monatliche Rate',
      fireEyebrow:     'FIRE · Deutschland',
      fireExpLabel:    'Monatliche Ausgaben (€)',
      roiEyebrow:      'Rendite · Deutschland',
      roiPLabel:       'Anfangsinvestition (€)',
      roiCompareTitle: 'Anlageklassen-Vergleich — 20 Jahre',
      roiCompareSub:   'Historische Durchschnitte · Basis: €10.000',
      insEyebrow:      'Versicherung · Deutschland',
      insDesc:         'Empfohlene Lebensversicherungssumme ergänzend zur gesetzlichen Rentenversicherung.',
      insIncLabel:     'Jahreseinkommen (€)',
      insLiabLabel:    'Verbindlichkeiten (€)',
      insLocalTitle:   'Beliebte deutsche Versicherungs- & Altersvorsorgeprodukte',
      taxEyebrow:      'Steuer · Deutschland',
      taxDesc:         'Einkommensteuer 2026 mit progressivem Stufentarif, Solidaritätszuschlag und Kirchensteuer.',
    }
  },
  france: {
    fr: {
      sipEyebrow:      'PEA · France',
      sipDesc:         "Constituez votre patrimoine à long terme via des investissements mensuels réguliers dans le PEA.",
      sipPLabel:       'Investissement mensuel',
      sipRateHint:     'CAC 40 moy. hist. ~7.5% / MSCI World ~9.5%',
      sipTaxLabel:     'Économie fiscale (est.)',
      sipTaxNote:      'Abattement PEA: gains exonérés après 5 ans',
      sipEdu1:         "€300/mois à 25 ans dans un PEA MSCI World = ~€700K à 60 ans à 9.5%. Utilisez d'abord votre plafond PEA.",
      sipEdu3Title:    'Effet de lissage des cours',
      sipEdu3:         "Investir un montant fixe régulièrement achète plus de parts quand les marchés baissent — réduisant votre coût moyen d'achat.",
      emiEyebrow:      'Financement immobilier · France',
      emiDesc:         "Calculez vos mensualités, intérêts totaux et avantages fiscaux de votre crédit immobilier.",
      emiPLabel:       'Montant du prêt',
      emiRateHint:     'Taux moyen immobilier ~3.6% (2026)',
      emiTaxLabel:     'Avantage fiscal',
      emiTaxNote:      'PTZ (Prêt à Taux Zéro) pour primo-accédants',
      emiDtiLabel:     "Taux d'endettement < 35% (règle HCSF)",
      emiMonthlyLabel: 'Mensualité',
      fireEyebrow:     'FIRE · France',
      fireExpLabel:    'Dépenses mensuelles (€)',
      roiEyebrow:      'Rendement · France',
      roiPLabel:       'Investissement initial (€)',
      roiCompareTitle: "Comparaison des classes d'actifs — 20 ans",
      roiCompareSub:   'Moyennes historiques · Base : €10 000',
      insEyebrow:      'Assurance · France',
      insDesc:         "Calculez la couverture vie recommandée en complément des régimes de retraite obligatoires.",
      insIncLabel:     'Revenus annuels (€)',
      insLiabLabel:    'Engagements financiers (€)',
      insLocalTitle:   "Produits d'épargne et d'assurance populaires en France",
      taxEyebrow:      'Fiscalité · France',
      taxDesc:         "Impôt sur le revenu 2026 avec barème progressif (0% à 45%), CSG-CRDS et prélèvements sociaux.",
    }
  },
  spain: {
    es: {
      sipEyebrow:      'Fondos Indexados · España',
      sipDesc:         'Construye tu patrimonio a largo plazo con inversiones mensuales regulares en fondos indexados.',
      sipPLabel:       'Inversión mensual',
      sipRateHint:     'IBEX 35 prom. hist. ~7.0% / MSCI World ~9.5%',
      sipTaxLabel:     'Ahorro fiscal (est.)',
      sipTaxNote:      'Plan de Pensiones: hasta €1.500/año deducible',
      sipEdu1:         '€300/mes a los 25 años en un fondo MSCI World = ~€680K a los 60 al 9.5%.',
      sipEdu3Title:    'Efecto del coste medio',
      sipEdu3:         'Invertir una cantidad fija mensual compra más participaciones cuando los mercados caen — reduciendo tu coste medio.',
      emiEyebrow:      'Financiación inmobiliaria · España',
      emiDesc:         'Calcula tu cuota mensual, intereses totales y ventajas fiscales de tu hipoteca española.',
      emiPLabel:       'Importe del préstamo',
      emiRateHint:     'Euríbor + spread ~3.5% hipoteca variable (2026)',
      emiTaxLabel:     'Beneficio fiscal',
      emiTaxNote:      'Deducción hipoteca pre-2013: hasta 15% sobre €9.040',
      emiDtiLabel:     'Cuota < 35% ingresos netos (criterio Banco de España)',
      emiMonthlyLabel: 'Cuota mensual',
      fireEyebrow:     'FIRE · España',
      fireExpLabel:    'Gastos mensuales (€)',
      roiEyebrow:      'Rentabilidad · España',
      roiPLabel:       'Inversión inicial (€)',
      roiCompareTitle: 'Comparativa de activos — 20 años',
      roiCompareSub:   'Medias históricas · Base: €10.000',
      insEyebrow:      'Seguros · España',
      insDesc:         'Calcula la cobertura de vida recomendada complementando la Seguridad Social.',
      insIncLabel:     'Ingresos anuales (€)',
      insLiabLabel:    'Deudas y compromisos (€)',
      insLocalTitle:   'Productos de ahorro y seguros populares en España',
      taxEyebrow:      'Fiscalidad · España',
      taxDesc:         'IRPF 2026 con escala progresiva (19% a 47%), deducción por rendimientos del trabajo.',
    }
  },
};

// Helper: returns translated string or falls back to English value
function _lstr(key, englishFallback) {
  const mode = window.currentMode || 'india';
  const lang = window.currentLang || 'en';
  if (lang === 'en') return englishFallback;
  const t = ((STATIC_LABEL_STRINGS[mode] || {})[lang]) || {};
  return (t[key] !== undefined) ? t[key] : englishFallback;
}

// Helper: set element text safely
function _setTxt(id, val) {
  if (val === undefined || val === null) return;
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// Replace updateStaticLabels with a language-aware version
window.updateStaticLabels = function() {
  const r = window.R ? window.R() : (window.REGIONS || {})[window.currentMode || 'india'];
  if (!r) return;

  // ── SIP ──────────────────────────────────────────────────
  _setTxt('sip-eyebrow',     _lstr('sipEyebrow',      'Investment · ' + r.name));
  _setTxt('sip-desc',        _lstr('sipDesc',          r.sipDesc));
  _setTxt('sip-p-label',     _lstr('sipPLabel',        r.sipLabel));
  _setTxt('sip-rate-hint',   _lstr('sipRateHint',      r.sipRateHint));
  _setTxt('sip-tax-label',   _lstr('sipTaxLabel',      r.sipTaxLabel));
  _setTxt('sip-tax-note',    _lstr('sipTaxNote',       r.sipTaxNote));
  _setTxt('edu-sip-1',       _lstr('sipEdu1',          r.sipEdu1));
  _setTxt('edu-sip-3-title', _lstr('sipEdu3Title',     r.sipEdu3));
  _setTxt('edu-sip-3',       _lstr('sipEdu3',          r.sipEdu3Desc));

  // ── EMI ──────────────────────────────────────────────────
  _setTxt('emi-eyebrow',       _lstr('emiEyebrow',      'Loan · ' + r.name));
  _setTxt('emi-desc',          _lstr('emiDesc',          r.emiDesc));
  _setTxt('emi-p-label',       _lstr('emiPLabel',        r.emiLabel));
  _setTxt('emi-rate-hint',     _lstr('emiRateHint',      r.emiRateHint));
  _setTxt('emi-tax-label',     _lstr('emiTaxLabel',      r.emiTaxLabel));
  _setTxt('emi-tax-note',      _lstr('emiTaxNote',       r.emiTaxNote));
  _setTxt('emi-dti-label',     _lstr('emiDtiLabel',      r.emiDtiLabel));
  _setTxt('emi-monthly-label', _lstr('emiMonthlyLabel',  r.emiMonthlyLabel));

  // ── FIRE ─────────────────────────────────────────────────
  _setTxt('fire-eyebrow',   _lstr('fireEyebrow',   'FIRE · ' + r.name));
  _setTxt('fire-exp-label', _lstr('fireExpLabel',  'Monthly Expenses (' + r.currency + ')'));

  // ── ROI ──────────────────────────────────────────────────
  _setTxt('roi-eyebrow',       _lstr('roiEyebrow',      'Returns · ' + r.name));
  _setTxt('roi-p-label',       _lstr('roiPLabel',        'Initial Investment (' + r.currency + ')'));
  _setTxt('roi-compare-title', _lstr('roiCompareTitle',  'Asset Class Comparison — 20 Years'));
  _setTxt('roi-compare-sub',   _lstr('roiCompareSub',    r.roiCompareSub));

  // ── Insurance ────────────────────────────────────────────
  _setTxt('ins-eyebrow',     _lstr('insEyebrow',    'Insurance · ' + r.name));
  _setTxt('ins-desc',        _lstr('insDesc',        r.insDesc));
  _setTxt('ins-inc-label',   _lstr('insIncLabel',    'Annual Income (' + r.currency + ')'));
  _setTxt('ins-liab-label',  _lstr('insLiabLabel',   'Liabilities (' + r.currency + ')'));
  _setTxt('ins-local-title', _lstr('insLocalTitle',  r.insLocalTitle));
  // Insurance local items — region data is already localised per country
  const insContent = document.getElementById('ins-local-content');
  if (insContent && r.insLocalItems) {
    insContent.innerHTML = r.insLocalItems.map(item =>
      `<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);">
        <div style="font-size:12px;font-weight:700;color:var(--cream);margin-bottom:4px;">${item.name}</div>
        <div style="font-size:11px;color:var(--muted);line-height:1.7;">${item.detail}</div>
      </div>`
    ).join('');
  }

  // ── Tax ──────────────────────────────────────────────────
  _setTxt('tax-eyebrow', _lstr('taxEyebrow', 'Tax · ' + r.name));
  _setTxt('tax-desc',    _lstr('taxDesc',    r.taxDesc));
};

// Patch applyLanguage: call the new language-aware updateStaticLabels AT THE END
const _origApplyLang = window.applyLanguage;
window.applyLanguage = function(mode, lang) {
  if (typeof _origApplyLang === 'function') _origApplyLang(mode, lang);
  // Run AFTER original so translated strings win over English defaults
  window.updateStaticLabels();
};


// ══════════════════════════════════════════════════════════════
// Wrap setMode — consolidates FIX-2 ticker retrigger + FIX-A/B
// habit reset into one clean wrapper, chaining correctly after
// all existing wrappers (goal-planner wrapper in main HTML).
// ══════════════════════════════════════════════════════════════
const _origSetModePatch = window.setMode;
window.setMode = function(mode) {
  // Run full existing chain (original + goal-planner wrapper)
  if (typeof _origSetModePatch === 'function') _origSetModePatch(mode);

  // FIX-2: force ticker with correctly mapped API mode
  window.loadTickerData(mode);

  // FIX-A/B: rebuild habit pills for new region
  updateHabitPresets(mode);
};


// ══════════════════════════════════════════════════════════════
// FIX-A & FIX-B — Habit presets with realistic regional prices
// ══════════════════════════════════════════════════════════════
const HABIT_PRESETS = {
  india: [
    { key:'coffee',    emoji:'☕', label:'Coffee',       labelFull:'Daily Coffee',      monthly: 3000 },
    { key:'swiggy',    emoji:'🛵', label:'Swiggy',       labelFull:'Food Delivery',     monthly: 4500 },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',    labelFull:'Cigarettes',        monthly: 3000 },
    { key:'ott',       emoji:'📺', label:'OTT',          labelFull:'OTT Subscriptions', monthly: 1200 },
    { key:'custom',    emoji:'✏️', label:'Custom',       labelFull:'This Habit',        monthly: 0    },
  ],
  usa: [
    { key:'coffee',    emoji:'☕', label:'Coffee',       labelFull:'Daily Coffee',      monthly:  130 },
    { key:'doordash',  emoji:'🛵', label:'DoorDash',     labelFull:'Food Delivery',     monthly:  150 },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',    labelFull:'Cigarettes',        monthly:  420 },
    { key:'ott',       emoji:'📺', label:'Streaming',    labelFull:'Streaming Subs',    monthly:   50 },
    { key:'custom',    emoji:'✏️', label:'Custom',       labelFull:'This Habit',        monthly:    0 },
  ],
  uk: [
    { key:'coffee',    emoji:'☕', label:'Coffee',       labelFull:'Daily Coffee',      monthly:  120 },
    { key:'dining',    emoji:'🍻', label:'Pub/Dining',   labelFull:'Pub & Dining Out',  monthly:  450 },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',    labelFull:'Cigarettes',        monthly:  360 },
    { key:'streaming', emoji:'📺', label:'Streaming',    labelFull:'Streaming Subs',    monthly:   30 },
    { key:'custom',    emoji:'✏️', label:'Custom',       labelFull:'This Habit',        monthly:    0 },
  ],
  germany: [
    { key:'coffee',    emoji:'☕', label:'Kaffee',       labelFull:'Täglicher Kaffee',  monthly:   90 },
    { key:'dining',    emoji:'🍺', label:'Ausgehen',     labelFull:'Ausgehen / Gastro', monthly:  450 },
    { key:'cigarette', emoji:'🚬', label:'Zigaretten',   labelFull:'Zigaretten',        monthly:  240 },
    { key:'streaming', emoji:'📺', label:'Streaming',    labelFull:'Streaming-Dienste', monthly:   20 },
    { key:'custom',    emoji:'✏️', label:'Sonstiges',    labelFull:'Diese Gewohnheit',  monthly:    0 },
  ],
  france: [
    { key:'coffee',    emoji:'☕', label:'Café',         labelFull:'Café quotidien',    monthly:   60 },
    { key:'dining',    emoji:'🥐', label:'Restaurant',   labelFull:'Restaurant',        monthly:  450 },
    { key:'cigarette', emoji:'🚬', label:'Cigarettes',   labelFull:'Cigarettes',        monthly:  330 },
    { key:'streaming', emoji:'📺', label:'Streaming',    labelFull:'Streaming',         monthly:   15 },
    { key:'custom',    emoji:'✏️', label:'Personnalisé', labelFull:'Cette habitude',    monthly:    0 },
  ],
  spain: [
    { key:'coffee',    emoji:'☕', label:'Café',         labelFull:'Café diario',       monthly:   45 },
    { key:'dining',    emoji:'🥘', label:'Restaurante',  labelFull:'Restaurante',       monthly:  360 },
    { key:'cigarette', emoji:'🚬', label:'Cigarrillos',  labelFull:'Cigarrillos',       monthly:  150 },
    { key:'streaming', emoji:'📺', label:'Streaming',    labelFull:'Streaming',         monthly:   13 },
    { key:'custom',    emoji:'✏️', label:'Personalizado',labelFull:'Este hábito',       monthly:    0 },
  ],
};

let _currentHabit     = 'coffee';
let _currentHabitName = 'Daily Coffee';

function updateHabitPresets(mode) {
  const m = mode || window.currentMode || 'india';
  const presets = HABIT_PRESETS[m] || HABIT_PRESETS.india;
  const wrap = document.getElementById('habit_pills');
  if (!wrap) return;

  const sym = (window.R && window.R()) ? window.R().currency : '₹';
  const large = (m === 'india');
  const maxH  = large ? 50000 : (['usa','uk'].includes(m) ? 2000 : 1500);
  const step  = large ? 100   : 5;

  wrap.innerHTML = presets.map((p, i) => {
    const css = i === 0
      ? 'background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.4);color:var(--gold-light);'
      : 'background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);';
    const amt = p.monthly > 0
      ? ` ${sym}${p.monthly >= 1000 ? (p.monthly/1000).toFixed(p.monthly%1000===0?0:1)+'K':p.monthly}/mo`
      : '';
    return `<button onclick="setHabit('${p.key}',${p.monthly})" id="hp-${p.key}"
      style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;
             ${css}font-family:'DM Sans',sans-serif;">${p.emoji} ${p.label}${amt}</button>`;
  }).join('');

  const first = presets.find(p => p.key !== 'custom') || presets[0];
  _currentHabit     = first.key;
  _currentHabitName = first.labelFull;

  const hab = document.getElementById('hab_p');
  if (hab) { hab.min=0; hab.max=maxH; hab.step=step; hab.value=first.monthly; }
  const num = document.getElementById('ft_hab_p');
  if (num) { num.min=0; num.max=maxH; num.step=step; num.value=first.monthly; }

  if (typeof window.calcHabit === 'function') window.calcHabit();
}

function setHabit(type, monthly) {
  const presets = HABIT_PRESETS[window.currentMode || 'india'] || HABIT_PRESETS.india;
  const preset  = presets.find(p => p.key === type);
  _currentHabit     = type;
  _currentHabitName = preset ? preset.labelFull : 'This Habit';

  presets.forEach(p => {
    const el = document.getElementById('hp-' + p.key);
    if (!el) return;
    el.style.background = 'transparent';
    el.style.borderColor = 'rgba(255,255,255,.1)';
    el.style.color = 'var(--muted)';
  });
  const act = document.getElementById('hp-' + type);
  if (act) { act.style.background='rgba(201,168,76,.12)'; act.style.borderColor='rgba(201,168,76,.4)'; act.style.color='var(--gold-light)'; }
  if (monthly > 0) {
    const s = document.getElementById('hab_p'); if (s) s.value = monthly;
    const n = document.getElementById('ft_hab_p'); if (n) n.value = monthly;
  }
  if (typeof window.calcHabit === 'function') window.calcHabit();
}

function calcHabit() {
  const p = +document.getElementById('hab_p').value;
  const t = +document.getElementById('hab_t').value;
  const r = +document.getElementById('hab_r').value;
  const name = _currentHabitName || 'This Habit';
  const fmt  = window.fmtSym || (n => String(n));
  document.getElementById('v_hab_p').textContent = fmt(p);
  document.getElementById('v_hab_t').textContent = t;
  document.getElementById('v_hab_r').textContent = r.toFixed(1);
  if (typeof window.apiCalc === 'function') {
    window.apiCalc({ type:'habit', p, t, r }, d => {
      document.getElementById('hab_spent').textContent     = fmt(d.spent);
      document.getElementById('hab_spent_sub').textContent = 'Spent on '+name+' over '+d.years+' years';
      document.getElementById('hab_corpus').textContent    = fmt(d.corpus);
      document.getElementById('hab_corpus_sub').textContent= 'At '+r+'% SIP returns · Gains: '+fmt(d.gains);
      document.getElementById('hab_verdict').innerHTML     =
        'Your '+name+' habit costs '+fmt(d.monthly)+'/month. Over '+d.years+
        ' years you spend '+fmt(d.spent)+' — gone forever. Invest that same '+
        fmt(d.monthly)+'/month at '+r+'% returns and you would have '+
        fmt(d.corpus)+' — a '+d.mult+'x multiplier.';
    });
  }
}

window.updateHabitPresets = updateHabitPresets;
window.setHabit           = setHabit;
window.calcHabit          = calcHabit;


// ══════════════════════════════════════════════════════════════
// FIX-C — Fine-tune number input beside every range slider
// ══════════════════════════════════════════════════════════════
(function addFineTuneInputs() {
  const style = document.createElement('style');
  style.textContent = `
    .ft-num {
      width: 76px; background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.15); border-radius: 6px;
      color: #C9A84C; font-size: 12px;
      font-family: 'DM Mono', 'Courier New', monospace;
      font-weight: 600; padding: 4px 6px; text-align: right;
      margin-left: 8px; flex-shrink: 0; -moz-appearance: textfield;
    }
    .ft-num::-webkit-outer-spin-button,
    .ft-num::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    .ft-num:focus { outline: none; border-color: rgba(201,168,76,.6); }
    .ft-wrap { display: flex !important; align-items: center; }
  `;
  document.head.appendChild(style);

  const MAP = {
    sip_p:'calcSIP',    sip_r:'calcSIP',    sip_t:'calcSIP',
    emi_p:'calcEMI',    emi_r:'calcEMI',    emi_t:'calcEMI',
    fire_age:'calcFIRE',fire_exp:'calcFIRE',fire_saved:'calcFIRE',
    fire_inv:'calcFIRE',fire_ret:'calcFIRE',fire_inf:'calcFIRE',
    roi_p:'calcROI',    roi_r:'calcROI',    roi_t:'calcROI',
    ins_inc:'calcInsurance',ins_age:'calcInsurance',ins_ret:'calcInsurance',
    ins_liab:'calcInsurance',ins_exist:'calcInsurance',
    ppf_y:'calcPPF',    ppf_t:'calcPPF',
    epf_sal:'calcEPF',  epf_age:'calcEPF',  epf_grow:'calcEPF',
    nps_p:'calcNPS',    nps_age:'calcNPS',  nps_eq:'calcNPS',
    ss_p:'calcStepSIP', ss_step:'calcStepSIP',ss_r:'calcStepSIP',ss_t:'calcStepSIP',
    ssa_age:'calcSSA',  ssa_dep:'calcSSA',
    cr_target:'calcCrorepati',cr_t:'calcCrorepati',cr_r:'calcCrorepati',
    hab_p:'calcHabit',  hab_t:'calcHabit',  hab_r:'calcHabit',
    cmp_p:'buildCompare',cmp_r:'buildCompare',cmp_t:'buildCompare',
    tax_inc:'_calcIndiaTax',tax_80c:'_calcIndiaTax',tax_80d:'_calcIndiaTax',
    tax_hl:'_calcIndiaTax', tax_nps:'_calcIndiaTax',
    grat_sal:'calcGratuity',grat_yrs:'calcGratuity',
    hw_income:'calcHomeWizard',hw_price:'calcHomeWizard',hw_tenure:'calcHomeWizard',
  };

  function attach(slider, fnName) {
    if (document.getElementById('ft_' + slider.id)) return;
    const num = document.createElement('input');
    num.type='number'; num.id='ft_'+slider.id; num.className='ft-num';
    num.min=slider.min; num.max=slider.max; num.step=slider.step||1;
    num.value=slider.value; num.title='Type exact value';

    // Insert the number input directly after the slider — never move the slider
    // itself, because re-parenting a visible slider breaks the SIP tab layout.
    slider.insertAdjacentElement('afterend', num);
    // Mark the slider's parent so we don't double-attach
    if (slider.parentNode) slider.parentNode.classList.add('ft-wrap');

    slider.addEventListener('input', () => { num.value = slider.value; });
    num.addEventListener('input', () => {
      let v = parseFloat(num.value);
      if (isNaN(v)) return;
      v = Math.max(parseFloat(slider.min), Math.min(parseFloat(slider.max), v));
      slider.value = v; num.value = v;
      const fn = window[fnName];
      if (typeof fn === 'function') fn();
    });
    num.addEventListener('keydown', e => {
      if (e.key === 'Enter') num.dispatchEvent(new Event('input'));
    });
  }

  function initAll() {
    Object.entries(MAP).forEach(([id, fn]) => {
      const el = document.getElementById(id);
      if (el && el.type === 'range') attach(el, fn);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initAll);
  else initAll();
})();


// ══════════════════════════════════════════════════════════════
// Bootstrap — runs after DOM + main scripts are fully ready
// ══════════════════════════════════════════════════════════════
function _patchBoot() {
  const mode = window.currentMode || 'india';
  const lang = window.currentLang || 'en';

  updateHabitPresets(mode);           // FIX-A/B
  window.updateStaticLabels();        // FIX-3 (language-aware)
  window.loadTickerData(mode);        // FIX-2
  window.startSidebarRefresh();       // FIX-2
}

// Delay so window.onload in main script fires first
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => setTimeout(_patchBoot, 300));
} else {
  setTimeout(_patchBoot, 300);
}

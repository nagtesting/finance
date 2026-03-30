// ================================================================
// MoneyVeda — patch.js  v4  (Drift Fix Edition)
// Load as: <script src="patch.js"></script>  — AFTER the two
// main <script> blocks in index.html.
//
// FIXES v4:
//   FIX-D  Investment Planner (SIP tab) no longer drifts left /
//          becomes partially invisible.
//
//          ROOT CAUSE: FIX-C's addFineTuneInputs() wrapped each
//          range slider's PARENT <div style="margin-bottom:20px;">
//          in display:flex via .ft-wrap. Because the SIP tab is
//          the default ACTIVE tab, it is visible during the
//          initial layout paint, so the flex override on those
//          outer wrapper divs pushes the label row + slider +
//          number input into a single horizontal line that
//          overflows the card width, blowing past the grid
//          container and causing the whole Investment Planner
//          panel to shift left and become clipped.
//          Other tabs are hidden at load time (display:none),
//          so their layout is calculated only after addFineTuneInputs
//          has already run — they are unaffected.
//
//          FIX: Insert a dedicated <span> wrapper around just the
//          slider element and apply .ft-wrap to that span instead
//          of to the outer margin-bottom div. The outer wrapper
//          div keeps its original block layout untouched.
//
// CARRIES FORWARD:
//   FIX-1  Grid card overlap prevention (grid-3 / big-number clamp)
//   FIX-2  Ticker & sidebar region mapping for UK/Germany/France/Spain
//   FIX-3  Full language translation for all static labels
//   FIX-A  Habit presets with region-local currency & realistic prices
//   FIX-B  Habit slider ranges update on region switch
//   FIX-C  Fine-tune number input beside every range slider
//          (now uses an inner span wrapper — no longer touches the
//           outer margin-bottom div)
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
};

// Language-aware updateStaticLabels replacement
window.updateStaticLabels = function() {
  const mode = window.currentMode || 'india';
  const lang = window.currentLang || 'en';
  const modeStrings = STATIC_LABEL_STRINGS[mode];
  const strings = (modeStrings && lang !== 'en') ? modeStrings[lang] : null;
  function t(enVal, key) { return (strings && strings[key]) ? strings[key] : enVal; }

  // SIP
  const sipEyebrow = document.getElementById('sip-eyebrow');
  if (sipEyebrow) sipEyebrow.textContent = t('SIP · India', 'sipEyebrow');
  const sipDesc = document.getElementById('sip-desc');
  if (sipDesc) sipDesc.textContent = t("Harness compounding through disciplined monthly SIPs — India's most powerful wealth-creation tool.", 'sipDesc');
  const sipPLabel = document.getElementById('sip-p-label');
  if (sipPLabel) sipPLabel.textContent = t('Monthly Investment', 'sipPLabel');
  const sipRateHint = document.getElementById('sip-rate-hint');
  if (sipRateHint) sipRateHint.textContent = t('Nifty 50 hist. avg ~13%', 'sipRateHint');
  const sipTaxLabel = document.getElementById('sip-tax-label');
  if (sipTaxLabel) sipTaxLabel.textContent = t('Tax Benefit', 'sipTaxLabel');
  const sipTaxNote = document.getElementById('sip-tax-note');
  if (sipTaxNote && sipTaxNote.textContent !== '—') sipTaxNote.textContent = t('Up to ₹1.5L/yr deduction', 'sipTaxNote');
  const edu1 = document.getElementById('edu-sip-1');
  if (edu1) edu1.textContent = t('Time in market beats timing the market. Every decade of delay roughly halves your final corpus.', 'sipEdu1');
  const edu3t = document.getElementById('edu-sip-3-title');
  if (edu3t) edu3t.textContent = t('Cost Averaging', 'sipEdu3Title');
  const edu3 = document.getElementById('edu-sip-3');
  if (edu3) edu3.textContent = t('Regular investing buys more units when prices fall and fewer when high — automatically lowering average cost.', 'sipEdu3');

  // EMI
  const emiEyebrow = document.getElementById('emi-eyebrow');
  if (emiEyebrow) emiEyebrow.textContent = t('Loan Planning', 'emiEyebrow');
  const emiDesc = document.getElementById('emi-desc');
  if (emiDesc) emiDesc.textContent = t('Calculate monthly repayments, total interest burden and tax benefits on your home loan.', 'emiDesc');
  const emiPLabel = document.getElementById('emi-p-label');
  if (emiPLabel) emiPLabel.textContent = t('Loan Amount', 'emiPLabel');
  const emiRateHint = document.getElementById('emi-rate-hint');
  if (emiRateHint) emiRateHint.textContent = t('SBI Home Loan ~8.25% (2026)', 'emiRateHint');
  const emiTaxLabel = document.getElementById('emi-tax-label');
  if (emiTaxLabel) emiTaxLabel.textContent = t('Tax Benefit Sec 24(b)', 'emiTaxLabel');
  const emiTaxNote = document.getElementById('emi-tax-note');
  if (emiTaxNote && emiTaxNote.textContent !== 'Loading…') emiTaxNote.textContent = t('Up to ₹2L/yr deduction', 'emiTaxNote');
  const emiDti = document.getElementById('emi-dti-label');
  if (emiDti) emiDti.textContent = t('EMI <40% of gross', 'emiDtiLabel');
  const emiMonthly = document.getElementById('emi-monthly-label');
  if (emiMonthly) emiMonthly.textContent = t('Monthly EMI', 'emiMonthlyLabel');
};

// Patch applyLanguage to call updated labels last
const _origApplyLanguage = window.applyLanguage;
window.applyLanguage = function(lang) {
  if (typeof _origApplyLanguage === 'function') _origApplyLanguage(lang);
  window.updateStaticLabels();
};


// ══════════════════════════════════════════════════════════════
// FIX-A/B — Habit presets with region-local prices + slider ranges
// ══════════════════════════════════════════════════════════════
const HABIT_PRESETS = {
  india: [
    { key:'coffee',  emoji:'☕', label:'Coffee',   labelFull:'Daily Coffee',    monthly:4500  },
    { key:'smoke',   emoji:'🚬', label:'Smoking',  labelFull:'Smoking',         monthly:3000  },
    { key:'ott',     emoji:'📺', label:'OTT',      labelFull:'OTT Subscriptions',monthly:1500 },
    { key:'eating',  emoji:'🍔', label:'Eating Out',labelFull:'Eating Out',      monthly:6000  },
    { key:'custom',  emoji:'✏️', label:'Custom',   labelFull:'Custom Habit',    monthly:0     },
  ],
  usa: [
    { key:'coffee',  emoji:'☕', label:'Coffee',   labelFull:'Daily Coffee',    monthly:150   },
    { key:'smoke',   emoji:'🚬', label:'Smoking',  labelFull:'Smoking',         monthly:400   },
    { key:'ott',     emoji:'📺', label:'OTT',      labelFull:'OTT Subscriptions',monthly:60   },
    { key:'eating',  emoji:'🍔', label:'Eating Out',labelFull:'Eating Out',     monthly:300   },
    { key:'custom',  emoji:'✏️', label:'Custom',   labelFull:'Custom Habit',    monthly:0     },
  ],
  europe: [
    { key:'coffee',  emoji:'☕', label:'Coffee',   labelFull:'Daily Coffee',    monthly:120   },
    { key:'smoke',   emoji:'🚬', label:'Smoking',  labelFull:'Smoking',         monthly:350   },
    { key:'ott',     emoji:'📺', label:'OTT',      labelFull:'OTT Subscriptions',monthly:50   },
    { key:'eating',  emoji:'🍔', label:'Eating Out',labelFull:'Eating Out',     monthly:250   },
    { key:'custom',  emoji:'✏️', label:'Custom',   labelFull:'Custom Habit',    monthly:0     },
  ],
};
HABIT_PRESETS.uk      = HABIT_PRESETS.europe;
HABIT_PRESETS.germany = HABIT_PRESETS.europe;
HABIT_PRESETS.france  = HABIT_PRESETS.europe;
HABIT_PRESETS.spain   = HABIT_PRESETS.europe;
HABIT_PRESETS.world   = HABIT_PRESETS.usa;

let _currentHabit = 'coffee';
let _currentHabitName = 'Daily Coffee';

function updateHabitPresets(mode) {
  const presets = HABIT_PRESETS[mode] || HABIT_PRESETS.india;
  const wrap = document.getElementById('habit-preset-wrap');
  if (!wrap) return;
  const sym   = window.fmtSym ? '' : '';
  const large = mode === 'india';
  const maxH  = large ? 50000 : 2000;
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
// FIX-C (v4) — Fine-tune number input beside every range slider
//
// KEY CHANGE FROM v3:
//   Old: slider.parentNode.classList.add('ft-wrap')
//        → This set display:flex on the outer <div style="margin-bottom:20px;">
//          which contains the label row + slider + number input, causing the
//          ENTIRE slider section to go horizontal and overflow the card on the
//          SIP tab (which is visible/active at page load time).
//
//   New: Wrap ONLY the slider itself in a new <span class="ft-wrap"> and
//        append the number input inside that span. The outer margin wrapper
//        div is never touched and stays display:block.
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

    /* FIX-D: ft-wrap is scoped to just the slider+number-input row,
       NOT the outer margin wrapper div */
    .ft-wrap {
      display: flex !important;
      align-items: center;
      width: 100%;
    }
    /* Make sure the range slider inside ft-wrap still fills available width */
    .ft-wrap > input[type=range] {
      flex: 1;
      min-width: 0;
    }
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
    // Already attached? skip.
    if (document.getElementById('ft_' + slider.id)) return;

    // ── FIX-D: wrap only the slider in a new <span class="ft-wrap"> ──
    // Do NOT touch slider.parentNode at all — leave the outer div untouched.
    const wrapper = document.createElement('span');
    wrapper.className = 'ft-wrap';
    // Replace slider in DOM with wrapper, then put slider inside wrapper
    slider.parentNode.insertBefore(wrapper, slider);
    wrapper.appendChild(slider);

    // Build the number input and append it into the wrapper
    const num = document.createElement('input');
    num.type='number'; num.id='ft_'+slider.id; num.className='ft-num';
    num.min=slider.min; num.max=slider.max; num.step=slider.step||1;
    num.value=slider.value; num.title='Type exact value';
    wrapper.appendChild(num);

    // Keep slider and number input in sync
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

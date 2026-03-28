// ================================================================
// MoneyVeda — Patch File  (drop this <script> block just before
// the closing </script> of index.html's main script block, or
// load it as a separate <script src="patch.js"> after the main
// script.  It monkey-patches / replaces the three functions and
// adds the fine-tune number inputs via a one-time DOM pass.)
//
// FIXES APPLIED:
//   FIX-A  Habit presets use region-local currency and realistic
//          prices for every market.
//   FIX-B  Habit slider ranges update when the user switches
//          region, so the slider never shows ₹ values in a $/ €
//          context.
//   FIX-C  Every range slider gains a small editable number box
//          (type="number") next to it, letting the user type an
//          exact value instead of trying to drag to it precisely.
//          The box and slider stay in sync both ways.
// ================================================================


// ── FIX-A & FIX-B: Per-region habit presets ───────────────────
//
// Prices are realistic monthly costs per market (2025-26):
//
// INDIA:
//   Coffee:    ₹150/day × 30 = ₹4,500/mo   (Café-style, city)
//              Revised → ₹100/day × 30 = ₹3,000/mo  (realistic for
//              a Starbucks-/CCD-level single coffee in tier-1 city;
//              many people spend ~₹80-120/day)
//   Swiggy:    ₹400/day is too high; average order ₹300 × 15
//              orders/mo = ₹4,500/mo (realistic urban ordering)
//   Cigarette: ₹200/day is too high; 1 pack/day ~₹300-400/wk
//              → ₹20 × 20 cigarettes × 30 / typical = 1 pack
//              10-sticks pack ₹120 × 2/day = ₹240/day overstated.
//              Realistic: ₹150/day → ₹4,500/mo (1 pack/day Gold Flake)
//              But for "social smoker" archetype: ₹50/day → ₹1,500/mo
//              We use ₹3,000/mo as middle ground (half pack/day city)
//   OTT:       ₹2,000/mo is slightly high (Netflix Max ₹649, Hotstar
//              ₹299/mo, etc.); ₹1,200/mo is realistic for 2-3 subs
//
// USA:
//   Coffee:    $6/day Starbucks × 22 workdays = ~$130/mo
//   DoorDash:  $150/mo (3 orders/wk × $50 avg)
//   Cigarette: $14/pack × 30 = $420/mo (1 pack/day)
//   OTT:       $50/mo (Netflix+Hulu+Disney+)
//
// EUROPE:
//   Coffee:    €3.5/day × 22 = ~€80/mo
//   Delivery:  €80/mo (Deliveroo/UberEats, 4 orders/mo × €20)
//   Cigarette: €8/pack × 30 = €240/mo (1 pack/day)
//   OTT:       €30/mo (Netflix+Prime)
//
// WORLD ($):
//   Coffee:    $5/day × 22 = ~$110/mo
//   Delivery:  $100/mo
//   Cigarette: $10/pack × 30 = $300/mo
//   OTT:       $40/mo

const HABIT_PRESETS = {
  india: [
    { key:'coffee',    emoji:'☕', label:'Coffee',     labelFull:'Daily Coffee',     monthly:3000,  desc:'₹100/day (1 café coffee)' },
    { key:'swiggy',    emoji:'🛵', label:'Swiggy',     labelFull:'Food Delivery',    monthly:4500,  desc:'₹150/day avg order' },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',  labelFull:'Cigarettes',       monthly:3000,  desc:'Half pack/day (Gold Flake)' },
    { key:'ott',       emoji:'📺', label:'OTT',        labelFull:'OTT Subscriptions',monthly:1200,  desc:'Netflix + Hotstar + Prime' },
    { key:'custom',    emoji:'✏️', label:'Custom',     labelFull:'This Habit',       monthly:0,     desc:'' },
  ],
  usa: [
    { key:'coffee',    emoji:'☕', label:'Coffee',     labelFull:'Daily Coffee',     monthly:130,   desc:'$6/day (Starbucks latte)' },
    { key:'doordash',  emoji:'🛵', label:'DoorDash',   labelFull:'Food Delivery',    monthly:150,   desc:'~3 orders/week avg $50' },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',  labelFull:'Cigarettes',       monthly:420,   desc:'1 pack/day ~$14/pack' },
    { key:'ott',       emoji:'📺', label:'OTT',        labelFull:'OTT Subscriptions',monthly:50,    desc:'Netflix + Hulu + Disney+' },
    { key:'custom',    emoji:'✏️', label:'Custom',     labelFull:'This Habit',       monthly:0,     desc:'' },
  ],
  europe: [
    { key:'coffee',    emoji:'☕', label:'Coffee',     labelFull:'Daily Coffee',     monthly:80,    desc:'€3.5/day (espresso/flat white)' },
    { key:'delivery',  emoji:'🛵', label:'Delivery',   labelFull:'Food Delivery',    monthly:80,    desc:'4 Deliveroo orders/month' },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',  labelFull:'Cigarettes',       monthly:240,   desc:'1 pack/day ~€8/pack' },
    { key:'ott',       emoji:'📺', label:'OTT',        labelFull:'OTT Subscriptions',monthly:30,    desc:'Netflix + Prime' },
    { key:'custom',    emoji:'✏️', label:'Custom',     labelFull:'This Habit',       monthly:0,     desc:'' },
  ],
  world: [
    { key:'coffee',    emoji:'☕', label:'Coffee',     labelFull:'Daily Coffee',     monthly:110,   desc:'$5/day worldwide avg' },
    { key:'delivery',  emoji:'🛵', label:'Delivery',   labelFull:'Food Delivery',    monthly:100,   desc:'~$25/order × 4/month' },
    { key:'cigarette', emoji:'🚬', label:'Cigarette',  labelFull:'Cigarettes',       monthly:300,   desc:'1 pack/day ~$10/pack' },
    { key:'ott',       emoji:'📺', label:'OTT',        labelFull:'OTT Subscriptions',monthly:40,    desc:'Major streaming services' },
    { key:'custom',    emoji:'✏️', label:'Custom',     labelFull:'This Habit',       monthly:0,     desc:'' },
  ],
};

// Track active habit key globally (replaces the old _currentHabit)
var _currentHabit = 'coffee';
var _currentHabitName = 'Daily Coffee';

// Rebuild the pill buttons when region changes
function updateHabitPresets() {
  const presets = HABIT_PRESETS[currentMode] || HABIT_PRESETS.india;
  const wrap = document.getElementById('habit_pills');
  if (!wrap) return;

  // Rebuild pill HTML
  wrap.innerHTML = presets.map(p => {
    const isActive = (p.key === 'coffee' || (p.key !== 'custom' && presets[0].key === p.key));
    const activeStyle = isActive
      ? 'background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.4);color:var(--gold-light);'
      : 'background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);';
    const titleAttr = p.desc ? ` title="${p.desc}"` : '';
    const sym = (currentMode === 'india') ? '₹'
              : (currentMode === 'europe') ? '€' : '$';
    const amtLabel = p.monthly > 0
      ? ` ${sym}${p.monthly >= 1000 ? (p.monthly/1000).toFixed(p.monthly%1000===0?0:1)+'K' : p.monthly}/mo`
      : '';
    return `<button onclick="setHabit('${p.key}',${p.monthly})" id="hp-${p.key}"${titleAttr} `
      + `style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;${activeStyle}font-family:'DM Sans',sans-serif;">`
      + `${p.emoji} ${p.label}${amtLabel}</button>`;
  }).join('');

  // Reset to first non-custom preset
  const first = presets.find(p => p.key !== 'custom') || presets[0];
  _currentHabit = first.key;
  _currentHabitName = first.labelFull;

  // Update slider range for habit cost (so it's sensible for the currency)
  const r = REGIONS[currentMode] || REGIONS.india;
  const maxHabit = currentMode === 'india' ? 50000
                 : currentMode === 'usa'    ? 2000
                 : currentMode === 'europe' ? 1500
                 : 2000;
  const stepHabit = currentMode === 'india' ? 100
                  : currentMode === 'usa'    ? 5
                  : currentMode === 'europe' ? 5
                  : 5;
  setSlider('hab_p', 0, maxHabit, stepHabit, first.monthly);
  // Sync the fine-tune number input if it exists
  const numEl = document.getElementById('ft_hab_p');
  if (numEl) { numEl.min=0; numEl.max=maxHabit; numEl.step=stepHabit; numEl.value=first.monthly; }
  calcHabit();
}

// Patched setHabit — uses HABIT_PRESETS instead of hardcoded values
function setHabit(type, monthly) {
  const presets = HABIT_PRESETS[currentMode] || HABIT_PRESETS.india;
  const preset = presets.find(p => p.key === type);
  _currentHabit = type;
  _currentHabitName = preset ? preset.labelFull : 'This Habit';

  // Style all pills
  presets.forEach(p => {
    const el = document.getElementById('hp-' + p.key);
    if (!el) return;
    el.style.background = 'transparent';
    el.style.borderColor = 'rgba(255,255,255,.1)';
    el.style.color = 'var(--muted)';
  });
  const active = document.getElementById('hp-' + type);
  if (active) {
    active.style.background = 'rgba(201,168,76,.12)';
    active.style.borderColor = 'rgba(201,168,76,.4)';
    active.style.color = 'var(--gold-light)';
  }

  if (monthly > 0) {
    const el = document.getElementById('hab_p');
    if (el) el.value = monthly;
    const numEl = document.getElementById('ft_hab_p');
    if (numEl) numEl.value = monthly;
  }
  calcHabit();
}

// Patched calcHabit — uses _currentHabitName from presets
function calcHabit() {
  const p = +document.getElementById('hab_p').value;
  const t = +document.getElementById('hab_t').value;
  const r = +document.getElementById('hab_r').value;
  const name = _currentHabitName || 'This Habit';
  document.getElementById('v_hab_p').textContent = fmtSym(p);
  document.getElementById('v_hab_t').textContent = t;
  document.getElementById('v_hab_r').textContent = r.toFixed(1);
  apiCalc({ type: 'habit', p, t, r }, d => {
    document.getElementById('hab_spent').textContent = fmtSym(d.spent);
    document.getElementById('hab_spent_sub').textContent = 'Spent on ' + name + ' over ' + d.years + ' years';
    document.getElementById('hab_corpus').textContent = fmtSym(d.corpus);
    document.getElementById('hab_corpus_sub').textContent = 'At ' + r + '% SIP returns · Gains: ' + fmtSym(d.gains);
    document.getElementById('hab_verdict').innerHTML =
      'Your ' + name + ' habit costs ' + fmtSym(d.monthly) + '/month. Over ' + d.years +
      ' years you spend ' + fmtSym(d.spent) + ' — gone forever. Invest that same ' +
      fmtSym(d.monthly) + '/month at ' + r + '% returns and you would have ' +
      fmtSym(d.corpus) + ' — a ' + d.mult + 'x multiplier.';
  });
}

// Hook into setMode: after it runs, call updateHabitPresets
const _origSetMode = setMode;
function setMode(mode) {
  _origSetMode(mode);
  updateHabitPresets();
}


// ── FIX-C: Fine-tune number inputs next to every slider ────────
//
// Strategy: after DOM is ready, find every <input type="range">
// that has an id matching our pattern and inject a small
// <input type="number"> immediately after it. The two inputs stay
// in sync: dragging the range updates the number, typing in the
// number updates the range and fires the calc.
//
// We also inject a tiny CSS block so the number inputs look right
// in the dark theme without touching the main stylesheet.

(function addFineTuneInputs() {
  // Inject style for the fine-tune boxes
  const style = document.createElement('style');
  style.textContent = `
    .ft-num {
      width: 72px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.15);
      border-radius: 6px;
      color: #C9A84C;
      font-size: 12px;
      font-family: 'DM Mono', 'Courier New', monospace;
      font-weight: 600;
      padding: 4px 6px;
      text-align: right;
      margin-left: 8px;
      flex-shrink: 0;
      -moz-appearance: textfield;
    }
    .ft-num::-webkit-outer-spin-button,
    .ft-num::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    .ft-num:focus { outline: none; border-color: rgba(201,168,76,.6); }
    .ft-wrap { display: flex; align-items: center; }
  `;
  document.head.appendChild(style);

  // Map of slider id → { calcFn, isPercent }
  // calcFn is the string name of the function to call after sync
  const SLIDER_MAP = {
    // SIP
    sip_p:    { calc: 'calcSIP',        isPercent: false },
    sip_r:    { calc: 'calcSIP',        isPercent: true  },
    sip_t:    { calc: 'calcSIP',        isPercent: false },
    // EMI
    emi_p:    { calc: 'calcEMI',        isPercent: false },
    emi_r:    { calc: 'calcEMI',        isPercent: true  },
    emi_t:    { calc: 'calcEMI',        isPercent: false },
    // FIRE
    fire_age: { calc: 'calcFIRE',       isPercent: false },
    fire_exp: { calc: 'calcFIRE',       isPercent: false },
    fire_saved:{ calc: 'calcFIRE',      isPercent: false },
    fire_inv: { calc: 'calcFIRE',       isPercent: false },
    fire_ret: { calc: 'calcFIRE',       isPercent: true  },
    fire_inf: { calc: 'calcFIRE',       isPercent: true  },
    // ROI
    roi_p:    { calc: 'calcROI',        isPercent: false },
    roi_r:    { calc: 'calcROI',        isPercent: true  },
    roi_t:    { calc: 'calcROI',        isPercent: false },
    // Insurance
    ins_inc:  { calc: 'calcInsurance',  isPercent: false },
    ins_age:  { calc: 'calcInsurance',  isPercent: false },
    ins_ret:  { calc: 'calcInsurance',  isPercent: false },
    ins_liab: { calc: 'calcInsurance',  isPercent: false },
    ins_exist:{ calc: 'calcInsurance',  isPercent: false },
    // PPF
    ppf_y:    { calc: 'calcPPF',        isPercent: false },
    ppf_t:    { calc: 'calcPPF',        isPercent: false },
    // EPF
    epf_sal:  { calc: 'calcEPF',        isPercent: false },
    epf_age:  { calc: 'calcEPF',        isPercent: false },
    epf_grow: { calc: 'calcEPF',        isPercent: true  },
    // NPS
    nps_p:    { calc: 'calcNPS',        isPercent: false },
    nps_age:  { calc: 'calcNPS',        isPercent: false },
    nps_eq:   { calc: 'calcNPS',        isPercent: true  },
    // Step SIP
    ss_p:     { calc: 'calcStepSIP',    isPercent: false },
    ss_step:  { calc: 'calcStepSIP',    isPercent: true  },
    ss_r:     { calc: 'calcStepSIP',    isPercent: true  },
    ss_t:     { calc: 'calcStepSIP',    isPercent: false },
    // SSA
    ssa_age:  { calc: 'calcSSA',        isPercent: false },
    ssa_dep:  { calc: 'calcSSA',        isPercent: false },
    // Crorepati
    cr_target:{ calc: 'calcCrorepati',  isPercent: false },
    cr_t:     { calc: 'calcCrorepati',  isPercent: false },
    cr_r:     { calc: 'calcCrorepati',  isPercent: true  },
    // Habit
    hab_p:    { calc: 'calcHabit',      isPercent: false },
    hab_t:    { calc: 'calcHabit',      isPercent: false },
    hab_r:    { calc: 'calcHabit',      isPercent: true  },
    // Compare
    cmp_p:    { calc: 'buildCompare',   isPercent: false },
    cmp_r:    { calc: 'buildCompare',   isPercent: true  },
    cmp_t:    { calc: 'buildCompare',   isPercent: false },
    // Tax
    tax_inc:  { calc: '_calcIndiaTax',        isPercent: false },
    tax_80c:  { calc: '_calcIndiaTax',        isPercent: false },
    tax_80d:  { calc: '_calcIndiaTax',        isPercent: false },
    tax_hl:   { calc: '_calcIndiaTax',        isPercent: false },
    tax_nps:  { calc: '_calcIndiaTax',        isPercent: false },
  };

  function attachFineTune(slider, cfg) {
    // Don't double-attach
    if (document.getElementById('ft_' + slider.id)) return;

    const num = document.createElement('input');
    num.type = 'number';
    num.id = 'ft_' + slider.id;
    num.className = 'ft-num';
    num.min = slider.min;
    num.max = slider.max;
    num.step = slider.step || 1;
    num.value = slider.value;
    num.title = 'Type an exact value';

    // Wrap slider + number input together if not already wrapped
    const parent = slider.parentNode;
    if (parent && !parent.classList.contains('ft-wrap')) {
      const wrapper = document.createElement('div');
      wrapper.className = 'ft-wrap';
      parent.insertBefore(wrapper, slider);
      wrapper.appendChild(slider);
      wrapper.appendChild(num);
    } else {
      slider.insertAdjacentElement('afterend', num);
    }

    // Range → Number sync
    slider.addEventListener('input', () => {
      num.value = slider.value;
    });

    // Number → Range sync + recalc
    num.addEventListener('input', () => {
      let v = parseFloat(num.value);
      if (isNaN(v)) return;
      const mn = parseFloat(slider.min), mx = parseFloat(slider.max);
      v = Math.max(mn, Math.min(mx, v));
      slider.value = v;
      num.value = v;
      // Fire the associated calc function
      const fn = window[cfg.calc];
      if (typeof fn === 'function') fn();
    });

    // Also handle Enter key in number box
    num.addEventListener('keydown', e => {
      if (e.key === 'Enter') num.dispatchEvent(new Event('input'));
    });
  }

  function initFineTuneAll() {
    Object.entries(SLIDER_MAP).forEach(([id, cfg]) => {
      const el = document.getElementById(id);
      if (el && el.type === 'range') attachFineTune(el, cfg);
    });
  }

  // Run on DOM ready (the script is at end of body so DOM is ready)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFineTuneAll);
  } else {
    initFineTuneAll();
  }
})();


// ── Bootstrap ─────────────────────────────────────────────────
// Rebuild habit presets for the initial india mode on load
document.addEventListener('DOMContentLoaded', () => {
  updateHabitPresets();
});
// If DOMContentLoaded already fired (script placed after main script):
if (document.readyState !== 'loading') {
  updateHabitPresets();
}

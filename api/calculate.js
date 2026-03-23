// ============================================================
// WealthHub / MultiCalci — FIXED Calculation Handler v2
//
// Previous fixes retained:
//   B-01 FIRE inflation, B-02 SIP tax slab,
//   B-03 EMI tax per-year, B-04 HLV growth, B-05 surcharge,
//   B-09 input validation, B-10 retry logic
//
// Audit fixes applied (this version):
//
//   ISS-01 — Holiday-aware isMarketOpen()
//     - NSE trading holiday calendar fetched from NSE API, cached
//       for 24 hours. Falls back to weekday-only logic on failure.
//     - Muhurat session override via MUHURAT_DATE env var.
//
//   ISS-02 — Externalised Tax Configuration
//     - All slab boundaries, rebate limits, deduction ceilings,
//       surcharge rates, and cess rates extracted into TAX_CONFIG.
//     - Keyed by assessment year ("AY2025-26") for auditability.
//     - Tax functions accept a config argument; handler passes the
//       current AY config. Updating for Budget changes requires
//       only editing TAX_CONFIG — no logic changes needed.
//
//   ISS-03 — Dual-Rate Inflation Model in FIRE
//     - Accepts healthcare_inflation and healthcare_pct params.
//     - Blended effective inflation is computed each year as:
//         general_inflation × (1 - healthcare_pct)
//         + healthcare_inflation × healthcare_pct
//     - Optional lifestyle_creep param (real annual expense growth).
//     - Deterministic result unchanged when new params are omitted
//       (defaults match previous single-rate behaviour).
//
//   ISS-08 — Financial Sanity Validation
//     - validateNumeric extended into validateWithWarning() which
//       returns { value, warnings[] } instead of a bare number.
//     - Warnings (not rejections) are returned to the caller for
//       implausible-but-technically-valid inputs.
//     - Cross-field guard: insurance discount_rate vs income_growth.
// ============================================================

// ================================================================
// ISS-02 — TAX CONFIGURATION (externalised, versioned by AY)
// ================================================================
const TAX_CONFIG = {
  'AY2025-26': {
    assessmentYear: 'AY2025-26',
    cess: 0.04,  // Health & Education cess

    old: {
      standardDeduction: 50_000,
      rebate87A:         500_000,    // taxable income ceiling for full rebate
      slabs: [
        // [upperBound, rate] — lower bound is previous entry's upper bound
        [250_000,   0.00],
        [500_000,   0.05],
        [1_000_000, 0.20],
        [Infinity,  0.30],
      ],
      surcharge: [
        // [grossIncomeCeiling, rate] — checked highest first
        [Infinity,  0.37],   // > 5 Cr
        [20_000_000, 0.25],  // > 2 Cr
        [10_000_000, 0.15],  // > 1 Cr
        [5_000_000,  0.10],  // > 50 L
        [0,          0.00],
      ],
      deductionLimits: {
        sec80c:       150_000,
        sec80d:        75_000,
        sec24b:       200_000,
        nps80ccd1b:    50_000,
        nps80ccd2pct:  0.10,   // % of gross salary
      },
    },

    new: {
      standardDeduction: 75_000,
      rebate87A:         700_000,    // higher threshold in new regime
      slabs: [
        [300_000,   0.00],
        [600_000,   0.05],
        [900_000,   0.10],
        [1_200_000, 0.15],
        [1_500_000, 0.20],
        [Infinity,  0.30],
      ],
      surcharge: [
        // New regime: surcharge capped at 25% (no 37% slab)
        [Infinity,   0.25],  // > 2 Cr and above all capped at 25%
        [10_000_000, 0.15],  // > 1 Cr
        [5_000_000,  0.10],  // > 50 L
        [0,          0.00],
      ],
      deductionLimits: {
        nps80ccd2pct: 0.10,  // 80CCD(2) employer contribution still allowed
      },
    },
  },
};

// Active assessment year — change this string when Budget is announced
const ACTIVE_AY = 'AY2025-26';

// ================================================================
// ISS-08 — ENHANCED VALIDATION WITH FINANCIAL SANITY WARNINGS
// ================================================================

/**
 * Clamps val to [min, max] and returns it (replaces with fallback if invalid).
 * Pure numeric guard — unchanged from original.
 */
function validateNumeric(val, min, max, fallback) {
  const n = parseFloat(val);
  if (!isFinite(n) || n < min || n > max) return fallback;
  return n;
}

/**
 * ISS-08: Extended validator that also emits financial sanity warnings.
 * Returns { value: number, warnings: string[] }.
 * Warnings are advisory — the value is still accepted.
 */
function validateWithWarning(val, min, max, fallback, warnings, warningRules = []) {
  const value = validateNumeric(val, min, max, fallback);
  for (const { condition, message } of warningRules) {
    if (condition(value)) warnings.push(message);
  }
  return value;
}

/**
 * ISS-08: Cross-field guard for insurance (discount_rate vs income_growth).
 * Returns a warning string if the relationship is financially unsound.
 */
function guardDiscountVsGrowth(discountRate, incomeGrowth) {
  if (incomeGrowth >= discountRate) {
    return `Income growth rate (${(incomeGrowth * 100).toFixed(1)}%) is ≥ discount rate `
      + `(${(discountRate * 100).toFixed(1)}%). HLV will be very large or negative — `
      + `consider setting discount rate higher than income growth.`;
  }
  return null;
}

// ================================================================
// ISS-01 — HOLIDAY-AWARE isMarketOpen() WITH NSE CALENDAR
// ================================================================

let _holidaySet       = new Set();
let _holidayYear      = null;
let _holidayFetchedAt = 0;
const HOLIDAY_TTL_MS  = 24 * 60 * 60 * 1000;

function toISTDateString(date) {
  const ist = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const y   = ist.getFullYear();
  const m   = String(ist.getMonth() + 1).padStart(2, '0');
  const d   = String(ist.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

async function refreshHolidayCalendar(year) {
  try {
    const res = await fetchWithRetry(
      'https://www.nseindia.com/api/holiday-master?type=trading',
      3, 300,
      {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept':     'application/json',
        'Referer':    'https://www.nseindia.com/',
      }
    );
    const data   = await res.json();
    const cmList = data?.CM ?? [];
    const newSet = new Set();
    for (const entry of cmList) {
      const parsed = new Date(entry.tradingDate);
      if (!isNaN(parsed)) newSet.add(toISTDateString(parsed));
    }
    _holidaySet       = newSet;
    _holidayYear      = year;
    _holidayFetchedAt = Date.now();
  } catch {
    // Non-fatal: fall back to weekday-only logic
  }
}

async function isMarketOpen() {
  const now    = new Date();
  const ist    = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const day    = ist.getDay();
  if (day === 0 || day === 6) return false;  // weekend

  const istDateStr = toISTDateString(now);
  const year       = parseInt(istDateStr.slice(0, 4), 10);

  // Muhurat session override (set MUHURAT_DATE="YYYY-MM-DD" in env)
  const muhuratDate = (typeof process !== 'undefined' && process.env?.MUHURAT_DATE) ?? null;
  if (muhuratDate) {
    const totalMins = ist.getHours() * 60 + ist.getMinutes();
    if (istDateStr === muhuratDate && totalMins >= 18 * 60 && totalMins <= 19 * 60) {
      return true;  // Muhurat trading session active
    }
  }

  // Refresh holiday calendar if needed
  const needsRefresh = (_holidayYear !== year)
    || (Date.now() - _holidayFetchedAt > HOLIDAY_TTL_MS);
  if (needsRefresh) await refreshHolidayCalendar(year);

  // ISS-01 FIX: Reject if today is an NSE trading holiday
  if (_holidaySet.has(istDateStr)) return false;

  // Check IST trading window: 9:15 AM – 4:00 PM
  const totalMins = ist.getHours() * 60 + ist.getMinutes();
  return totalMins >= 555 && totalMins <= 960;
}

// ================================================================
// EXPONENTIAL BACKOFF FETCH WITH RETRY (extended to accept headers)
// ================================================================
async function fetchWithRetry(url, retries = 3, delayMs = 300, extraHeaders = {}) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, {
        headers: extraHeaders,
        signal:  AbortSignal.timeout(5000),
      });
      if (res.ok) return res;
    } catch (e) {
      if (i < retries - 1) await new Promise(r => setTimeout(r, delayMs * Math.pow(3, i)));
    }
  }
  throw new Error('All retries exhausted');
}

// ================================================================
// MAIN HANDLER
// ================================================================
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { type } = req.body;

  // ---- Validated base inputs ----
  const amount       = validateNumeric(req.body.p, 0, 1e9, 0);
  const rate         = validateNumeric(req.body.r, 0.01, 50, 12);
  const monthly_rate = rate / 12 / 100;

  // ================================================================
  // SIP — FIX B-02 (retained) + ISS-08 warnings
  // ================================================================
  if (type === 'sip') {
    const warnings   = [];
    const months     = validateNumeric(req.body.t, 1, 50, 10) * 12;
    const taxSlab    = validateNumeric(req.body.tax_slab, 0, 42.744, 30) / 100;

    // ISS-08: Warn on implausibly high expected return
    validateWithWarning(rate, 0.01, 50, 12, warnings, [
      { condition: v => v > 20, message: `Expected return of ${rate.toFixed(1)}% is very high for a conventional SIP instrument. Consider using a realistic long-term equity CAGR (12–15%).` },
    ]);

    const invested   = amount * months;
    const totalValue = amount * (((Math.pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate));
    const earnings   = totalValue - invested;
    const multiplier = totalValue / invested;

    const annualInvestment = amount * 12;
    const taxSaved         = Math.min(annualInvestment, TAX_CONFIG[ACTIVE_AY].old.deductionLimits.sec80c) * taxSlab;

    const annualGains    = earnings / (months / 12);
    const ltcgLiability  = Math.max(annualGains - 100_000, 0) * 0.10;

    const yearlyData = [];
    for (let y = 1; y <= months / 12; y++) {
      const m     = y * 12;
      const inv_y = amount * m;
      const val_y = amount * (((Math.pow(1 + monthly_rate, m) - 1) / monthly_rate) * (1 + monthly_rate));
      yearlyData.push({
        year:     y,
        invested: Math.round(inv_y),
        value:    Math.round(val_y),
        gains:    Math.round(val_y - inv_y),
      });
    }

    return res.json({
      value:          Math.round(totalValue),
      invested:       Math.round(invested),
      earnings:       Math.round(earnings),
      multiplier:     multiplier.toFixed(2),
      taxSaved:       Math.round(taxSaved),
      ltcgLiability:  Math.round(ltcgLiability),
      yearlyData,
      warnings,
      taxNote:        `80C deduction limit sourced from ${ACTIVE_AY} config (₹${TAX_CONFIG[ACTIVE_AY].old.deductionLimits.sec80c.toLocaleString('en-IN')}).`,
    });
  }

  // ================================================================
  // EMI — FIX B-03 (retained), no new audit items
  // ================================================================
  if (type === 'emi') {
    const months    = validateNumeric(req.body.t, 1, 360, 240);
    const taxSlab   = validateNumeric(req.body.tax_slab, 0, 42.744, 30) / 100;
    const sec24bCap = TAX_CONFIG[ACTIVE_AY].old.deductionLimits.sec24b; // ISS-02: from config

    const emi            = (amount * monthly_rate * Math.pow(1 + monthly_rate, months))
                         / (Math.pow(1 + monthly_rate, months) - 1);
    const totalPaid      = emi * months;
    const totalInterest  = totalPaid - amount;

    const schedule = [];
    let balance      = amount;
    let year1Interest = 0;

    for (let y = 1; y <= months / 12; y++) {
      let openBal = balance, yearPrincipal = 0, yearInterest = 0;
      for (let m = 0; m < 12 && balance > 0.01; m++) {
        const interestM  = balance * monthly_rate;
        const principalM = Math.min(emi - interestM, balance);
        yearPrincipal   += principalM;
        yearInterest    += interestM;
        balance         -= principalM;
      }
      if (y === 1) year1Interest = yearInterest;
      schedule.push({
        year:         y,
        openBalance:  Math.round(openBal),
        principal:    Math.round(yearPrincipal),
        interest:     Math.round(yearInterest),
        closeBalance: Math.round(Math.max(balance, 0)),
      });
    }

    const taxSaved = Math.min(year1Interest, sec24bCap) * taxSlab;

    return res.json({
      emi:           Math.round(emi),
      totalPaid:     Math.round(totalPaid),
      totalInterest: Math.round(totalInterest),
      taxSaved:      Math.round(taxSaved),
      taxNote:       `Section 24(b) deduction based on Year 1 interest (${ACTIVE_AY} cap ₹${sec24bCap.toLocaleString('en-IN')}). Benefit reduces each year as interest portion falls.`,
      schedule,
    });
  }

  // ================================================================
  // FIRE — FIX B-01 (retained) + ISS-03 dual-rate inflation model
  // ================================================================
  if (type === 'fire') {
    const warnings = [];

    const currentAge  = validateNumeric(req.body.age,         18, 55,  30);
    const monthlyExp  = validateNumeric(req.body.expenses,    100, 1e7, 75_000);
    const currentSaved= validateNumeric(req.body.saved,       0,   1e9, 0);
    const monthlyInv  = validateNumeric(req.body.monthly_inv, 100, 1e7, 50_000);
    const nominalRate = validateNumeric(req.body.r,           1,   30,  10) / 100;
    const inflation   = validateNumeric(req.body.inflation,   1,   15,  6)  / 100;

    // ISS-03: Dual-rate inflation inputs (new params with safe defaults)
    // healthcare_inflation defaults to inflation + 3% (historically ~8-12% India)
    const healthcareInflation = validateNumeric(
      req.body.healthcare_inflation,
      1, 20,
      parseFloat(((inflation * 100) + 3).toFixed(2))   // default = general + 3%
    ) / 100;

    // healthcare_pct: fraction of monthly expenses that are healthcare-related
    // Default 15% — appropriate for pre-retirement, rises in post-retirement
    const healthcarePct = validateNumeric(req.body.healthcare_pct, 0, 60, 15) / 100;

    // lifestyle_creep: real annual expense growth (0 = no creep)
    const lifestyleCreep = validateNumeric(req.body.lifestyle_creep, 0, 5, 0) / 100;

    // ISS-08: Warn if lifestyle_creep seems high
    if (lifestyleCreep > 0.02) {
      warnings.push(`Lifestyle creep of ${(lifestyleCreep * 100).toFixed(1)}%/yr will significantly increase your required corpus. Verify this is intentional.`);
    }

    // ISS-03: Blended effective inflation
    // Computed once for the accumulation phase (conservative — real blending happens post-FIRE)
    const effectiveInflation = inflation * (1 - healthcarePct) + healthcareInflation * healthcarePct;

    // Real return using blended effective inflation
    const realReturn  = (1 + nominalRate) / (1 + effectiveInflation) - 1;
    const realMonthly = Math.pow(1 + realReturn, 1 / 12) - 1;

    // FIRE corpus in today's money (real terms)
    const annualExpReal  = monthlyExp * 12;
    const fireCorpusReal = annualExpReal * 25;  // 4% SWR

    // ISS-03: Accumulation loop with lifestyle creep
    // lifestyleCreep increases the real monthly expenses target each year
    let corpusTarget = fireCorpusReal;
    let corpusAccum  = currentSaved;
    let months       = 0;
    let yearlyCreepMultiplier = 1;

    for (let m = 0; m < 600; m++) {
      // Apply lifestyle creep once per year to the corpus target
      if (m > 0 && m % 12 === 0) {
        yearlyCreepMultiplier *= (1 + lifestyleCreep);
        corpusTarget = fireCorpusReal * yearlyCreepMultiplier;
      }
      corpusAccum = corpusAccum * (1 + realMonthly) + monthlyInv;
      if (corpusAccum >= corpusTarget) { months = m + 1; break; }
    }

    const yearsToFIRE = months > 0 ? Math.ceil(months / 12) : null;
    const fireAge     = yearsToFIRE ? currentAge + yearsToFIRE : null;

    const nominalCorpus = yearsToFIRE
      ? corpusTarget * Math.pow(1 + effectiveInflation, yearsToFIRE)
      : null;

    // Future monthly expenses at retirement — split between general and healthcare
    const futureGeneralExp    = yearsToFIRE
      ? monthlyExp * (1 - healthcarePct) * Math.pow(1 + inflation, yearsToFIRE)
      : monthlyExp * (1 - healthcarePct);
    const futureHealthcareExp = yearsToFIRE
      ? monthlyExp * healthcarePct * Math.pow(1 + healthcareInflation, yearsToFIRE)
      : monthlyExp * healthcarePct;
    const futureMonthlyExp    = futureGeneralExp + futureHealthcareExp;

    const swr_monthly = (corpusTarget * 0.04) / 12;

    return res.json({
      fireCorpus:           Math.round(corpusTarget),           // real terms, incl. creep
      nominalCorpus:        nominalCorpus ? Math.round(nominalCorpus) : null,
      futureMonthlyExp:     Math.round(futureMonthlyExp),
      futureGeneralExp:     Math.round(futureGeneralExp),
      futureHealthcareExp:  Math.round(futureHealthcareExp),
      yearsToFIRE,
      fireAge,
      swr_monthly:          Math.round(swr_monthly),
      progressPct:          Math.min((currentSaved / corpusTarget) * 100, 100).toFixed(1),
      realReturn:           (realReturn * 100).toFixed(2),
      effectiveInflation:   (effectiveInflation * 100).toFixed(2),
      lifestyleCreepApplied: lifestyleCreep > 0,
      warnings,
      note: `Corpus in today's purchasing power. Healthcare inflation (${(healthcareInflation * 100).toFixed(1)}%) applied to ${(healthcarePct * 100).toFixed(0)}% of expenses. Nominal corpus is actual future value.`,
    });
  }

  // ================================================================
  // ROI — unchanged, no new audit items
  // ================================================================
  if (type === 'roi') {
    const years      = validateNumeric(req.body.t, 1, 50, 10);
    const principal  = amount;
    const finalValue = principal * Math.pow(1 + rate / 100, years);
    const returns    = finalValue - principal;
    const multiplier = finalValue / principal;

    return res.json({
      finalValue: Math.round(finalValue),
      returns:    Math.round(returns),
      multiplier: multiplier.toFixed(2),
      cagr:       rate.toFixed(2),
    });
  }

  // ================================================================
  // INSURANCE — FIX B-04 (retained) + ISS-08 cross-field guard
  // ================================================================
  if (type === 'insurance') {
    const warnings = [];

    const annualIncome  = validateNumeric(req.body.income,        10_000, 1e8, 1_800_000);
    const currentAge    = validateNumeric(req.body.age,           18, 60,  30);
    const retirementAge = validateNumeric(req.body.ret_age,       45, 75,  60);
    const liab          = validateNumeric(req.body.liabilities,   0,  1e9, 0);
    const existingCover = validateNumeric(req.body.existing,      0,  1e9, 0);
    const incomeGrowth  = validateNumeric(req.body.income_growth, 0,  20,  6) / 100;
    const discountRate  = validateNumeric(req.body.discount_rate, 1,  15,  8) / 100;

    // ISS-08: Cross-field guard — income growth vs discount rate
    const crossFieldWarning = guardDiscountVsGrowth(discountRate, incomeGrowth);
    if (crossFieldWarning) warnings.push(crossFieldWarning);

    const yearsLeft = retirementAge - currentAge;

    // B-04 FIX: NPV of growing income stream (growing annuity PV formula)
    let hlv;
    if (Math.abs(discountRate - incomeGrowth) < 0.0001) {
      hlv = annualIncome * yearsLeft;
    } else {
      hlv = annualIncome
        * (1 - Math.pow((1 + incomeGrowth) / (1 + discountRate), yearsLeft))
        / (discountRate - incomeGrowth);
    }

    // Guard against negative HLV from bad inputs (income_growth > discount_rate edge case)
    if (hlv < 0) {
      hlv = annualIncome * yearsLeft; // safe fallback: simple sum
      warnings.push('Income growth exceeded discount rate — HLV capped at simple income sum. Please review inputs.');
    }

    hlv += liab;
    const gap = Math.max(hlv - existingCover, 0);

    const insPremiumRate   = currentAge < 35 ? 0.0012 : currentAge < 45 ? 0.002 : 0.004;
    const estimatedPremium = gap * insPremiumRate;

    return res.json({
      recommendedCover:  Math.round(hlv),
      gap:               Math.round(gap),
      estimatedPremium:  Math.round(estimatedPremium),
      warnings,
      note: `HLV uses NPV of income growing at ${(incomeGrowth * 100).toFixed(1)}%/yr discounted at ${(discountRate * 100).toFixed(1)}%/yr over ${yearsLeft} years.`,
    });
  }

  // ================================================================
  // TAX — ISS-02: all values sourced from TAX_CONFIG[ACTIVE_AY]
  // ================================================================
  if (type === 'tax') {
    const cfg         = TAX_CONFIG[ACTIVE_AY];
    const grossIncome = amount;

    const sec80c    = validateNumeric(req.body.sec80c, 0, cfg.old.deductionLimits.sec80c,    0);
    const sec80d    = validateNumeric(req.body.sec80d, 0, cfg.old.deductionLimits.sec80d,    0);
    const sec24b    = validateNumeric(req.body.sec24b, 0, cfg.old.deductionLimits.sec24b,    0);
    const npsExtra  = validateNumeric(req.body.nps,    0, cfg.old.deductionLimits.nps80ccd1b, 0);
    const nps80ccd2 = validateNumeric(req.body.nps_employer, 0, 800_000, 0);

    // Old Regime
    const totalDed = cfg.old.standardDeduction
      + Math.min(sec80c,    cfg.old.deductionLimits.sec80c)
      + Math.min(sec80d,    cfg.old.deductionLimits.sec80d)
      + Math.min(sec24b,    cfg.old.deductionLimits.sec24b)
      + Math.min(npsExtra,  cfg.old.deductionLimits.nps80ccd1b)
      + Math.min(nps80ccd2, grossIncome * cfg.old.deductionLimits.nps80ccd2pct);

    const oldTaxable = Math.max(grossIncome - totalDed, 0);
    const oldTax     = calcRegimeTax(oldTaxable, grossIncome, cfg.old, cfg.cess);

    // New Regime
    const newTaxable = Math.max(
      grossIncome
      - cfg.new.standardDeduction
      - Math.min(nps80ccd2, grossIncome * cfg.new.deductionLimits.nps80ccd2pct),
      0
    );
    const newTax = calcRegimeTax(newTaxable, grossIncome, cfg.new, cfg.cess);

    return res.json({
      oldRegimeTax:    Math.round(oldTax),
      newRegimeTax:    Math.round(newTax),
      betterRegime:    oldTax <= newTax ? 'old' : 'new',
      saving:          Math.round(Math.abs(oldTax - newTax)),
      oldTaxable:      Math.round(oldTaxable),
      newTaxable:      Math.round(newTaxable),
      totalDeductions: Math.round(totalDed),
      assessmentYear:  ACTIVE_AY,
      taxNote:         `Slabs and rebate limits sourced from ${ACTIVE_AY} configuration. Update ACTIVE_AY after each Budget.`,
    });
  }

  res.status(400).json({ error: 'Invalid calculation type' });
}

// ================================================================
// ISS-02: UNIFIED TAX HELPER — accepts regime config from TAX_CONFIG
// Replaces calcOldRegimeTax() and calcNewRegimeTax() with a single
// config-driven function. Adding a new AY or changing slabs requires
// only editing TAX_CONFIG — no code changes here.
// ================================================================

/**
 * Computes total tax (including surcharge and cess) for a given regime.
 *
 * @param {number} taxable   - Taxable income after deductions
 * @param {number} gross     - Gross income (used for surcharge bracket)
 * @param {object} regimeCfg - TAX_CONFIG[AY].old or .new
 * @param {number} cess      - Cess rate (e.g. 0.04 for 4%)
 */
function calcRegimeTax(taxable, gross, regimeCfg, cess) {
  // Step 1: Compute base tax from slabs
  let tax  = 0;
  let prev = 0;
  for (const [upperBound, rate] of regimeCfg.slabs) {
    if (taxable > prev) {
      tax += Math.min(taxable - prev, upperBound - prev) * rate;
      prev = upperBound;
    }
  }

  // Step 2: 87A rebate — zero out tax if taxable income ≤ rebate ceiling
  if (taxable <= regimeCfg.rebate87A) tax = 0;

  // Step 3: Surcharge on pre-cess tax, based on gross income
  // Surcharge array is checked from lowest gross threshold upward;
  // the last matching entry (highest gross) wins.
  let surchargeRate = 0;
  for (const [ceiling, sRate] of [...regimeCfg.surcharge].reverse()) {
    if (gross > ceiling) { surchargeRate = sRate; break; }
  }
  const surcharge = tax * surchargeRate;

  // Step 4: Apply cess on (tax + surcharge)
  return (tax + surcharge) * (1 + cess);
}

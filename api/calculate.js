// ============================================================
// WealthHub / MultiCalci — FIXED Calculation Handler
// Fixed bugs: B-01 FIRE inflation, B-02 SIP tax slab,
// B-03 EMI tax per-year, B-04 HLV growth, B-05 surcharge,
// B-09 input validation, B-10 retry logic
// ============================================================

// ---- Input validation helper ----
function validateNumeric(val, min, max, fallback) {
  const n = parseFloat(val);
  if (!isFinite(n) || n < min || n > max) return fallback;
  return n;
}

// ---- Exponential backoff fetch with retry ----
async function fetchWithRetry(url, retries = 3, delayMs = 300) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
      if (res.ok) return res;
    } catch (e) {
      if (i < retries - 1) await new Promise(r => setTimeout(r, delayMs * Math.pow(3, i)));
    }
  }
  throw new Error('All retries exhausted');
}

// ---- Market hours check (IST) ----
function isMarketOpen() {
  const now = new Date();
  const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const day = ist.getDay(); // 0=Sun, 6=Sat
  if (day === 0 || day === 6) return false;
  const h = ist.getHours(), m = ist.getMinutes();
  const mins = h * 60 + m;
  return mins >= 555 && mins <= 960; // 9:15 AM – 4:00 PM IST
}

export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { type } = req.body;

  // ---- Validated inputs ----
  const amount  = validateNumeric(req.body.p,  0,      1e9,  0);
  const rate    = validateNumeric(req.body.r,  0.01,   50,   12);
  const monthly_rate = rate / 12 / 100;

  // ================================================================
  // SIP — FIX B-02: accept tax_slab param; default 30% only if not supplied
  // ================================================================
  if (type === 'sip') {
    const months = validateNumeric(req.body.t, 1, 50, 10) * 12;
    const taxSlab = validateNumeric(req.body.tax_slab, 0, 42.744, 30) / 100; // max incl cess

    const invested   = amount * months;
    const totalValue = amount * (((Math.pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate));
    const earnings   = totalValue - invested;
    const multiplier = totalValue / invested;

    // B-02 FIX: use caller-supplied slab
    const annualInvestment = amount * 12;
    const taxSaved = Math.min(annualInvestment, 150000) * taxSlab;

    // LTCG note — gains above ₹1L/yr attract 10% LTCG
    const annualGains = earnings / (months / 12);
    const ltcgLiability = Math.max(annualGains - 100000, 0) * 0.10;

    const yearlyData = [];
    for (let y = 1; y <= months / 12; y++) {
      const m = y * 12;
      const inv_y = amount * m;
      const val_y = amount * (((Math.pow(1 + monthly_rate, m) - 1) / monthly_rate) * (1 + monthly_rate));
      yearlyData.push({
        year: y,
        invested: Math.round(inv_y),
        value:    Math.round(val_y),
        gains:    Math.round(val_y - inv_y)
      });
    }

    return res.json({
      value:          Math.round(totalValue),
      invested:       Math.round(invested),
      earnings:       Math.round(earnings),
      multiplier:     multiplier.toFixed(2),
      taxSaved:       Math.round(taxSaved),
      ltcgLiability:  Math.round(ltcgLiability),
      yearlyData
    });
  }

  // ================================================================
  // EMI — FIX B-03: use year-1 actual interest for Section 24(b)
  // ================================================================
  if (type === 'emi') {
    const months = validateNumeric(req.body.t, 1, 360, 240);
    const taxSlab = validateNumeric(req.body.tax_slab, 0, 42.744, 30) / 100;

    const emi = (amount * monthly_rate * Math.pow(1 + monthly_rate, months))
              / (Math.pow(1 + monthly_rate, months) - 1);
    const totalPaid    = emi * months;
    const totalInterest = totalPaid - amount;

    // B-03 FIX: build amortization first, then use year-1 actual interest
    const schedule = [];
    let balance = amount;
    let year1Interest = 0;

    for (let y = 1; y <= months / 12; y++) {
      let openBal = balance, yearPrincipal = 0, yearInterest = 0;
      for (let m = 0; m < 12 && balance > 0.01; m++) {
        const interestM  = balance * monthly_rate;
        const principalM = Math.min(emi - interestM, balance);
        yearPrincipal += principalM;
        yearInterest  += interestM;
        balance       -= principalM;
      }
      if (y === 1) year1Interest = yearInterest;
      schedule.push({
        year:        y,
        openBalance: Math.round(openBal),
        principal:   Math.round(yearPrincipal),
        interest:    Math.round(yearInterest),
        closeBalance: Math.round(Math.max(balance, 0))
      });
    }

    // B-03 FIX: Section 24(b) uses current year's actual interest (year 1 shown as example)
    const taxSaved = Math.min(year1Interest, 200000) * taxSlab;

    return res.json({
      emi:           Math.round(emi),
      totalPaid:     Math.round(totalPaid),
      totalInterest: Math.round(totalInterest),
      taxSaved:      Math.round(taxSaved),        // year-1 deduction
      taxNote:       'Section 24(b) deduction based on Year 1 interest. Benefit reduces each year as interest portion falls.',
      schedule
    });
  }

  // ================================================================
  // FIRE — FIX B-01: inflation-adjusted expenses AND real return
  // ================================================================
  if (type === 'fire') {
    const currentAge  = validateNumeric(req.body.age,         18, 55,  30);
    const monthlyExp  = validateNumeric(req.body.expenses,    100, 1e7, 75000);
    const currentSaved= validateNumeric(req.body.saved,       0,  1e9, 0);
    const monthlyInv  = validateNumeric(req.body.monthly_inv, 100, 1e7, 50000);
    const nominalRate = validateNumeric(req.body.r,           1,  30,  10) / 100;
    const inflation   = validateNumeric(req.body.inflation,   1,  15,  6)  / 100;

    // B-01 FIX — Step 1: project expenses to retirement using inflation
    // We first find years to FIRE in the loop, then project expenses to that point.
    // Use REAL return in the accumulation loop so corpus & expenses are in today's money.
    const realReturn  = (1 + nominalRate) / (1 + inflation) - 1; // real return p.a.
    const realMonthly = Math.pow(1 + realReturn, 1/12) - 1;

    // FIRE corpus in today's money (real terms)
    const annualExpReal  = monthlyExp * 12;
    const fireCorpusReal = annualExpReal * 25; // 4% SWR on real expenses

    // Find years to reach real corpus in real terms
    let corpusAccum = currentSaved;
    let months = 0;
    for (let m = 0; m < 600; m++) {
      corpusAccum = corpusAccum * (1 + realMonthly) + monthlyInv;
      if (corpusAccum >= fireCorpusReal) { months = m + 1; break; }
    }

    const yearsToFIRE = months > 0 ? Math.ceil(months / 12) : null;
    const fireAge     = yearsToFIRE ? currentAge + yearsToFIRE : null;

    // Nominal corpus at retirement (what the number will look like in future rupees)
    const nominalCorpus = yearsToFIRE
      ? fireCorpusReal * Math.pow(1 + inflation, yearsToFIRE)
      : null;

    // Future monthly expenses at retirement date (for context)
    const futureMonthlyExp = yearsToFIRE
      ? monthlyExp * Math.pow(1 + inflation, yearsToFIRE)
      : monthlyExp;

    const swr_monthly = (fireCorpusReal * 0.04) / 12;

    return res.json({
      fireCorpus:       Math.round(fireCorpusReal),   // in today's money
      nominalCorpus:    nominalCorpus ? Math.round(nominalCorpus) : null, // future ₹
      futureMonthlyExp: Math.round(futureMonthlyExp), // expenses at retirement date
      yearsToFIRE:      yearsToFIRE,
      fireAge:          fireAge,
      swr_monthly:      Math.round(swr_monthly),
      progressPct:      Math.min((currentSaved / fireCorpusReal) * 100, 100).toFixed(1),
      realReturn:       (realReturn * 100).toFixed(2),
      note:             'FIRE corpus shown in today\'s purchasing power (real terms). Nominal corpus is the actual future value.'
    });
  }

  // ================================================================
  // ROI — unchanged but validated
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
      cagr:       rate.toFixed(2)  // CAGR = input rate for lump sum fixed return
    });
  }

  // ================================================================
  // INSURANCE — FIX B-04: income growth and NPV-based HLV
  // ================================================================
  if (type === 'insurance') {
    const annualIncome   = validateNumeric(req.body.income,      10000, 1e8, 1800000);
    const currentAge     = validateNumeric(req.body.age,         18, 60,   30);
    const retirementAge  = validateNumeric(req.body.ret_age,     45, 75,   60);
    const liab           = validateNumeric(req.body.liabilities, 0,  1e9,  0);
    const existingCover  = validateNumeric(req.body.existing,    0,  1e9,  0);
    const incomeGrowth   = validateNumeric(req.body.income_growth, 0, 20,  6) / 100;
    const discountRate   = validateNumeric(req.body.discount_rate, 1, 15,  8) / 100;

    const yearsLeft = retirementAge - currentAge;

    // B-04 FIX: NPV of growing income stream (Income Replacement method)
    // PV of growing annuity = income × (1 - ((1+g)/(1+d))^n) / (d - g)
    let hlv;
    if (Math.abs(discountRate - incomeGrowth) < 0.0001) {
      hlv = annualIncome * yearsLeft; // edge case: g ≈ d
    } else {
      hlv = annualIncome * (1 - Math.pow((1 + incomeGrowth) / (1 + discountRate), yearsLeft))
            / (discountRate - incomeGrowth);
    }
    hlv += liab;

    const gap = Math.max(hlv - existingCover, 0);

    const insPremiumRate = currentAge < 35 ? 0.0012 : currentAge < 45 ? 0.002 : 0.004;
    const estimatedPremium = gap * insPremiumRate;

    return res.json({
      recommendedCover:  Math.round(hlv),
      gap:               Math.round(gap),
      estimatedPremium:  Math.round(estimatedPremium),
      note:              `HLV uses NPV of income growing at ${(incomeGrowth*100).toFixed(1)}%/yr discounted at ${(discountRate*100).toFixed(1)}%/yr over ${yearsLeft} years.`
    });
  }

  // ================================================================
  // TAX — FIX B-05: add surcharge + accept slab for consistency
  // ================================================================
  if (type === 'tax') {
    const grossIncome = amount;
    const sec80c      = validateNumeric(req.body.sec80c, 0, 150000, 0);
    const sec80d      = validateNumeric(req.body.sec80d, 0, 75000,  0);
    const sec24b      = validateNumeric(req.body.sec24b, 0, 200000, 0);
    const npsExtra    = validateNumeric(req.body.nps,    0, 50000,  0);
    const nps80ccd2   = validateNumeric(req.body.nps_employer, 0, 800000, 0); // 80CCD(2)

    // Old Regime
    const stdDeduction = 50000;
    const totalDed = stdDeduction
      + Math.min(sec80c, 150000)
      + Math.min(sec80d, 75000)
      + Math.min(sec24b, 200000)
      + Math.min(npsExtra, 50000)
      + Math.min(nps80ccd2, grossIncome * 0.10); // 80CCD(2) — up to 10% of basic
    const oldTaxable = Math.max(grossIncome - totalDed, 0);
    const oldTax = calcOldRegimeTax(oldTaxable, grossIncome); // pass gross for surcharge

    // New Regime FY2025-26
    const newStdDed  = 75000;
    const newTaxable = Math.max(grossIncome - newStdDed - Math.min(nps80ccd2, grossIncome * 0.10), 0);
    const newTax     = calcNewRegimeTax(newTaxable, grossIncome);

    return res.json({
      oldRegimeTax:     Math.round(oldTax),
      newRegimeTax:     Math.round(newTax),
      betterRegime:     oldTax <= newTax ? 'old' : 'new',
      saving:           Math.round(Math.abs(oldTax - newTax)),
      oldTaxable:       Math.round(oldTaxable),
      newTaxable:       Math.round(newTaxable),
      totalDeductions:  Math.round(totalDed)
    });
  }

  res.status(400).json({ error: 'Invalid calculation type' });
}

// ================================================================
// TAX HELPERS — FIX B-05: full surcharge brackets added
// ================================================================
function calcOldRegimeTax(taxable, gross) {
  let tax = 0;
  if (taxable <= 250000)      tax = 0;
  else if (taxable <= 500000) tax = (taxable - 250000) * 0.05;
  else if (taxable <= 1000000) tax = 12500 + (taxable - 500000) * 0.20;
  else                         tax = 112500 + (taxable - 1000000) * 0.30;

  if (taxable <= 500000) tax = 0; // 87A rebate old regime

  // B-05 FIX: Surcharge on gross income (not taxable)
  let surcharge = 0;
  if (gross > 50000000)       surcharge = tax * 0.37;  // >5 Cr
  else if (gross > 20000000)  surcharge = tax * 0.25;  // >2 Cr
  else if (gross > 10000000)  surcharge = tax * 0.15;  // >1 Cr
  else if (gross > 5000000)   surcharge = tax * 0.10;  // >50 L

  return (tax + surcharge) * 1.04; // 4% cess
}

function calcNewRegimeTax(taxable, gross) {
  let tax = 0;
  const slabs = [
    [300000,  0],
    [600000,  0.05],
    [900000,  0.10],
    [1200000, 0.15],
    [1500000, 0.20],
    [Infinity, 0.30]
  ];
  let prev = 0;
  for (const [limit, rate] of slabs) {
    if (taxable > prev) {
      tax += Math.min(taxable - prev, limit - prev) * rate;
      prev = limit;
    }
  }
  if (taxable <= 700000) tax = 0; // 87A rebate new regime

  // B-05 FIX: New regime surcharge (capped at 25% for new regime — no 37% slab)
  let surcharge = 0;
  if (gross > 50000000)       surcharge = tax * 0.25;  // capped at 25% in new regime
  else if (gross > 20000000)  surcharge = tax * 0.25;
  else if (gross > 10000000)  surcharge = tax * 0.15;
  else if (gross > 5000000)   surcharge = tax * 0.10;

  return (tax + surcharge) * 1.04; // 4% cess
}

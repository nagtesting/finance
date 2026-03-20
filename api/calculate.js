export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { type, p, r, t, n, age, expenses, saved, monthly_inv, inflation, income, ret_age, liabilities, existing } = req.body;
  const amount = parseFloat(p);
  const rate = parseFloat(r);
  const monthly_rate = rate / 12 / 100;

  if (type === 'sip') {
    const months = parseFloat(t) * 12;
    const invested = amount * months;
    const totalValue = amount * (((Math.pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate));
    const earnings = totalValue - invested;
    const multiplier = totalValue / invested;

    // Tax: Section 80C — ELSS SIPs capped at ₹1.5L/year at 30% slab
    const annualInvestment = amount * 12;
    const taxSaved = Math.min(annualInvestment, 150000) * 0.30;

    // Year-by-year data
    const yearlyData = [];
    for (let y = 1; y <= parseFloat(t); y++) {
      const m = y * 12;
      const inv_y = amount * m;
      const val_y = amount * (((Math.pow(1 + monthly_rate, m) - 1) / monthly_rate) * (1 + monthly_rate));
      yearlyData.push({ year: y, invested: Math.round(inv_y), value: Math.round(val_y), gains: Math.round(val_y - inv_y) });
    }

    return res.json({
      value: Math.round(totalValue),
      invested: Math.round(invested),
      earnings: Math.round(earnings),
      multiplier: multiplier.toFixed(2),
      taxSaved: Math.round(taxSaved),
      yearlyData
    });
  }

  if (type === 'emi') {
    const months = parseFloat(t); // t = months for EMI
    const emi = (amount * monthly_rate * Math.pow(1 + monthly_rate, months)) / (Math.pow(1 + monthly_rate, months) - 1);
    const totalPaid = emi * months;
    const totalInterest = totalPaid - amount;

    // Section 24(b) — Home Loan interest deduction up to ₹2L at 30%
    const annualInterest = totalInterest / (months / 12);
    const taxSaved = Math.min(annualInterest, 200000) * 0.30;

    // Amortization schedule (yearly)
    const schedule = [];
    let balance = amount;
    for (let y = 1; y <= months / 12; y++) {
      let openBal = balance, yearPrincipal = 0, yearInterest = 0;
      for (let m = 0; m < 12; m++) {
        const interestM = balance * monthly_rate;
        const principalM = emi - interestM;
        yearPrincipal += principalM;
        yearInterest += interestM;
        balance -= principalM;
      }
      schedule.push({
        year: y,
        openBalance: Math.round(openBal),
        principal: Math.round(yearPrincipal),
        interest: Math.round(yearInterest),
        closeBalance: Math.round(Math.max(balance, 0))
      });
    }

    return res.json({
      emi: Math.round(emi),
      totalPaid: Math.round(totalPaid),
      totalInterest: Math.round(totalInterest),
      taxSaved: Math.round(taxSaved),
      schedule
    });
  }

  if (type === 'fire') {
    const currentAge = parseFloat(age || 30);
    const monthlyExp = parseFloat(expenses || 75000);
    const currentSaved = parseFloat(saved || 0);
    const monthlyInv = parseFloat(monthly_inv || 50000);
    const retRate = parseFloat(r || 10) / 100;
    const inf = parseFloat(inflation || 6) / 100;

    const annualExp = monthlyExp * 12;
    const fireCorpus = annualExp * 25; // 4% SWR rule
    const swr_monthly = (fireCorpus * 0.04) / 12;

    // Find years to reach FIRE corpus
    const mr = retRate / 12;
    let corpus = currentSaved;
    let months = 0;
    for (let m = 0; m < 600; m++) {
      corpus = corpus * (1 + mr) + monthlyInv;
      if (corpus >= fireCorpus) { months = m + 1; break; }
    }

    const yearsToFIRE = Math.ceil(months / 12);
    const fireAge = currentAge + yearsToFIRE;

    return res.json({
      fireCorpus: Math.round(fireCorpus),
      yearsToFIRE,
      fireAge,
      swr_monthly: Math.round(swr_monthly),
      progressPct: Math.min((currentSaved / fireCorpus) * 100, 100).toFixed(1)
    });
  }

  if (type === 'roi') {
    const principal = amount;
    const years = parseFloat(t);
    const finalValue = principal * Math.pow(1 + rate / 100, years);
    const returns = finalValue - principal;
    const multiplier = finalValue / principal;
    const cagr = rate;

    return res.json({
      finalValue: Math.round(finalValue),
      returns: Math.round(returns),
      multiplier: multiplier.toFixed(2),
      cagr: cagr.toFixed(2)
    });
  }

  if (type === 'insurance') {
    const annualIncome = parseFloat(income || amount);
    const currentAge = parseFloat(age || 30);
    const retirementAge = parseFloat(ret_age || 60);
    const liab = parseFloat(liabilities || 0);
    const existingCover = parseFloat(existing || 0);

    const yearsLeft = retirementAge - currentAge;
    const hlv = (annualIncome * yearsLeft) + liab;
    const gap = Math.max(hlv - existingCover, 0);

    // Premium estimation based on age
    const premiumRate = currentAge < 35 ? 0.0012 : currentAge < 45 ? 0.002 : 0.004;
    const estimatedPremium = gap * premiumRate;

    return res.json({
      recommendedCover: Math.round(hlv),
      gap: Math.round(gap),
      estimatedPremium: Math.round(estimatedPremium)
    });
  }

  if (type === 'tax') {
    const grossIncome = amount;
    const sec80c = parseFloat(req.body.sec80c || 0);
    const sec80d = parseFloat(req.body.sec80d || 0);
    const sec24b = parseFloat(req.body.sec24b || 0);
    const npsExtra = parseFloat(req.body.nps || 0);

    // Old Regime
    const stdDeduction = 50000;
    const totalDed = stdDeduction + Math.min(sec80c, 150000) + Math.min(sec80d, 75000) + Math.min(sec24b, 200000) + Math.min(npsExtra, 50000);
    const oldTaxable = Math.max(grossIncome - totalDed, 0);
    const oldTax = calcOldRegimeTax(oldTaxable);

    // New Regime FY2025-26
    const newStdDed = 75000;
    const newTaxable = Math.max(grossIncome - newStdDed, 0);
    const newTax = calcNewRegimeTax(newTaxable);

    return res.json({
      oldRegimeTax: Math.round(oldTax),
      newRegimeTax: Math.round(newTax),
      betterRegime: oldTax <= newTax ? 'old' : 'new',
      saving: Math.round(Math.abs(oldTax - newTax)),
      oldTaxable: Math.round(oldTaxable),
      newTaxable: Math.round(newTaxable),
      totalDeductions: Math.round(totalDed)
    });
  }

  res.status(400).json({ error: 'Invalid calculation type' });
}

function calcOldRegimeTax(income) {
  let tax = 0;
  if (income <= 250000) tax = 0;
  else if (income <= 500000) tax = (income - 250000) * 0.05;
  else if (income <= 1000000) tax = 12500 + (income - 500000) * 0.20;
  else tax = 112500 + (income - 1000000) * 0.30;
  if (income <= 500000) tax = 0; // 87A rebate
  return tax * 1.04; // 4% cess
}

function calcNewRegimeTax(income) {
  let tax = 0;
  const slabs = [
    [300000, 0],
    [600000, 0.05],
    [900000, 0.10],
    [1200000, 0.15],
    [1500000, 0.20],
    [Infinity, 0.30]
  ];
  let prev = 0;
  for (const [limit, rate] of slabs) {
    if (income > prev) {
      tax += Math.min(income - prev, limit - prev) * rate;
      prev = limit;
    }
  }
  if (income <= 700000) tax = 0; // 87A rebate new regime
  return tax * 1.04; // 4% cess
}

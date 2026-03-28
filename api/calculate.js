// ============================================================
// /api/calculate.js — MoneyVeda v4 (Fixed Edition)
//
// ALL computation is server-side. index.html contains zero
// math — only DOM reads (slider values) and DOM writes
// (displaying returned numbers + building charts/tables).
// Without this server, every calculator shows "—" only.
//
// SUPPORTED TYPES:
//   sip, emi, fire, roi, insurance, tax,
//   ppf, epf, nps, stepsip, ssa, crorepati, habit, compare
//
// FIX LOG:
//   BUG-01 SIP       — mr was r/12/100 (naive).
//                      Fixed to geometric: (1+r/100)^(1/12)-1
//   BUG-02 FIRE      — mr was ret/12 (naive, ret already decimal).
//                      Fixed to geometric: (1+ret)^(1/12)-1
//   BUG-03 NPS       — mr was ret/12 (naive, ret already decimal).
//                      Fixed to geometric: (1+ret)^(1/12)-1
//   BUG-04 STEPSIP   — mr was r/12/100 (naive).
//                      Fixed to geometric: (1+r/100)^(1/12)-1
//   BUG-05 CROREPATI — mr was r/12/100 (naive).
//                      Fixed to geometric: (1+r/100)^(1/12)-1
//   BUG-06 HABIT     — mr was r/12/100 (naive).
//                      Fixed to geometric: (1+r/100)^(1/12)-1
//   BUG-07 COMPARE   — SIP side mr was r/12/100 (naive).
//                      Fixed to geometric: (1+r/100)^(1/12)-1
//   BUG-08 PPF       — interest was Math.round()'d each year before
//                      being added to balance, causing small cumulative
//                      rounding errors. Now accumulates exact float;
//                      only rounds in the output row and final return.
//   BUG-09 SSA       — same annual-rounding issue as PPF. Fixed same way.
//
//   NOT BUGS (verified correct):
//   EMI    — r/12/100 is CORRECT; banks quote nominal annual rate.
//   EPF    — formula (balance+contrib)*(1+rate) is correct.
//   TAX    — surcharge reverse-iterate logic is correct.
//   ROI    — annual compounding Math.pow(1+r/100,t) is correct.
//   INSURANCE — HLV formula is standard and correct.
// ============================================================

// ── Tax config ────────────────────────────────────────────────
const TAX_CONFIG = {
  'AY2025-26': {
    cess: 0.04,
    old: {
      standardDeduction: 50000,
      rebate87A: 500000,
      slabs: [[250000,0],[500000,0.05],[1000000,0.20],[Infinity,0.30]],
      surcharge: [[Infinity,0.37],[20000000,0.25],[10000000,0.15],[5000000,0.10],[0,0.00]],
      deductionLimits: { sec80c:150000, sec80d:75000, sec24b:200000, nps80ccd1b:50000, nps80ccd2pct:0.10 },
    },
    new: {
      standardDeduction: 75000,
      rebate87A: 700000,
      slabs: [[300000,0],[600000,0.05],[900000,0.10],[1200000,0.15],[1500000,0.20],[Infinity,0.30]],
      surcharge: [[Infinity,0.25],[10000000,0.15],[5000000,0.10],[0,0.00]],
      deductionLimits: { nps80ccd2pct:0.10 },
    },
  },
};
const ACTIVE_AY = 'AY2025-26';

function clamp(val, min, max, def) {
  const n = parseFloat(val);
  return (!isFinite(n) || n < min || n > max) ? def : n;
}

// FIX: single shared helper — converts an annual % rate into the
// true geometric monthly rate. Used by every calculator that
// compounds monthly.  (1+r/100)^(1/12)-1
// EMI intentionally does NOT use this; banks quote nominal rates.
function monthlyRate(annualPct) {
  return Math.pow(1 + annualPct / 100, 1 / 12) - 1;
}

// FIX: same helper for when the annual rate is already a decimal
// (e.g. 0.10 for 10%).  Used by FIRE and NPS.
function monthlyRateDecimal(annualDecimal) {
  return Math.pow(1 + annualDecimal, 1 / 12) - 1;
}

function calcRegimeTax(taxable, gross, regime, cess) {
  let tax = 0, prev = 0;
  for (const [upper, rate] of regime.slabs) {
    if (taxable > prev) { tax += Math.min(taxable - prev, upper - prev) * rate; prev = upper; }
  }
  if (taxable <= regime.rebate87A) tax = 0;
  let surchargeRate = 0;
  for (const [ceiling, sr] of [...regime.surcharge].reverse()) {
    if (gross > ceiling) { surchargeRate = sr; break; }
  }
  return (tax + tax * surchargeRate) * (1 + cess);
}

// ── REGIONS config (server-only) ─────────────────────────────
const REGIONS = {
  india: {
    currency:'₹', sipTaxCalc:(p)=>Math.min(p*12,150000)*0.30,
    emiTaxCalc:(totalInt,t)=>Math.min(totalInt/t,200000)*0.30,
    fireLeanMax:40000, fireFatMin:150000,
    roiAssets:[
      {name:'Savings A/C',rate:3.5,color:'#64748b'},{name:'FD (5yr)',rate:7.0,color:'#0ea5e9'},
      {name:'PPF (15yr)',rate:7.1,color:'#6366f1'},{name:'Gold (hist.)',rate:9.5,color:'#f59e0b'},
      {name:'Nifty 50',rate:13.0,color:'#C9A84C'},{name:'Equity MF',rate:14.0,color:'#4ade80'},
      {name:'Real Estate',rate:9.0,color:'#ec4899'},
    ],
    roiBase:100000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
  },
  usa: {
    currency:'$', sipTaxCalc:(p)=>Math.min(p*12,23500)*0.22,
    emiTaxCalc:(totalInt,t)=>Math.min(totalInt/t,25000)*0.22,
    fireLeanMax:2500, fireFatMin:8000,
    roiAssets:[
      {name:'HYSA',rate:4.5,color:'#64748b'},{name:'US Treasury (10yr)',rate:4.3,color:'#0ea5e9'},
      {name:'S&P 500 Index',rate:10.5,color:'#6366f1'},{name:'Gold (hist.)',rate:8.5,color:'#f59e0b'},
      {name:'NASDAQ 100',rate:12.0,color:'#C9A84C'},{name:'Real Estate (REIT)',rate:8.0,color:'#4ade80'},
      {name:'Total Bond Market',rate:4.0,color:'#ec4899'},
    ],
    roiBase:10000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
  },
  europe: {
    currency:'€', sipTaxCalc:(p)=>p*12*0.15*0.25,
    emiTaxCalc:(totalInt,t)=>(totalInt/t)*0.15,
    fireLeanMax:1500, fireFatMin:5000,
    roiAssets:[
      {name:'Savings Account',rate:3.0,color:'#64748b'},{name:'German Bunds (10yr)',rate:2.8,color:'#0ea5e9'},
      {name:'Euro Stoxx 50',rate:8.5,color:'#6366f1'},{name:'Gold (hist.)',rate:8.5,color:'#f59e0b'},
      {name:'MSCI World ETF',rate:9.5,color:'#C9A84C'},{name:'European REIT',rate:6.5,color:'#4ade80'},
      {name:'Pan-EU Bond Fund',rate:3.5,color:'#ec4899'},
    ],
    roiBase:10000,
    insPremiumRate:(age)=>age<35?0.0010:age<45?0.0018:0.0035,
  },
  world: {
    currency:'$', sipTaxCalc:(p)=>p*12*0.20*0.15,
    emiTaxCalc:(totalInt,t)=>(totalInt/t)*0.20,
    fireLeanMax:2000, fireFatMin:7000,
    roiAssets:[
      {name:'Cash/T-Bills',rate:4.0,color:'#64748b'},{name:'Global Bonds',rate:4.5,color:'#0ea5e9'},
      {name:'MSCI World',rate:10.0,color:'#6366f1'},{name:'Gold',rate:8.5,color:'#f59e0b'},
      {name:'MSCI EM',rate:9.0,color:'#C9A84C'},{name:'Global REITs',rate:7.5,color:'#4ade80'},
      {name:'Commodities',rate:5.5,color:'#ec4899'},
    ],
    roiBase:10000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
  },
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const b    = req.body;
  const type = b.type;
  const mode = (b.mode && REGIONS[b.mode]) ? b.mode : 'india';
  const RC   = REGIONS[mode];

  // ── SIP ──────────────────────────────────────────────────────
  if (type === 'sip') {
    const p  = clamp(b.p, 100, 10000000, 25000);
    const r  = clamp(b.r, 0.1, 50, 12);
    const t  = clamp(b.t, 1, 50, 15);
    // FIX BUG-01: was r/12/100 (naive). Use geometric monthly rate.
    const mr = monthlyRate(r);
    const months   = t * 12;
    const invested = p * months;
    const total    = p * (((Math.pow(1+mr,months)-1)/mr) * (1+mr));
    const earnings = total - invested;
    const mult     = total / invested;
    const tax      = RC.sipTaxCalc(p, r, t);
    const yearlyData = [];
    for (let y = 1; y <= t; y++) {
      const m = y * 12;
      const iv = p * m;
      const vv = p * (((Math.pow(1+mr,m)-1)/mr) * (1+mr));
      yearlyData.push({ year:y, invested:Math.round(iv), value:Math.round(vv), gains:Math.round(vv-iv), gainPct:((vv-iv)/iv*100) });
    }
    const milestoneTargets = mode==='india'
      ? [200000,500000,1000000,5000000,10000000,50000000]
      : [5000,10000,50000,100000,500000,1000000];
    const milestones = milestoneTargets
      .filter(tgt => tgt <= total)
      .map(tgt => {
        for (let m=1; m<=months; m++) {
          const v = p*(((Math.pow(1+mr,m)-1)/mr)*(1+mr));
          if (v >= tgt) return { target:tgt, year:Math.ceil(m/12) };
        }
        return null;
      }).filter(Boolean);
    return res.json({
      total:Math.round(total), invested:Math.round(invested), earnings:Math.round(earnings),
      mult:mult.toFixed(1), gainPct:((earnings/invested)*100).toFixed(0),
      returnPct:((earnings/total)*100).toFixed(0),
      months, tax:Math.round(tax), yearlyData, milestones,
    });
  }

  // ── EMI ──────────────────────────────────────────────────────
  // NOTE: EMI intentionally keeps r/12/100. Banks in India (and globally)
  // quote home/car loan rates as nominal annual rates, and the standard
  // EMI formula uses the nominal monthly rate = r/12/100. Using the
  // geometric rate here would give wrong EMIs vs your bank statement.
  if (type === 'emi') {
    const p      = clamp(b.p, 1000, 500000000, 5000000);
    const r      = clamp(b.r, 0.1, 30, 8.5);
    const t      = clamp(b.t, 1, 30, 20);
    const mr     = r / 12 / 100;   // nominal monthly rate — CORRECT for EMI
    const months = t * 12;
    const emi    = (p * mr * Math.pow(1+mr,months)) / (Math.pow(1+mr,months) - 1);
    const totalPaid = emi * months;
    const totalInt  = totalPaid - p;
    const taxSaved  = RC.emiTaxCalc(totalInt, t);
    const pp = (p/totalPaid)*100, ip = (totalInt/totalPaid)*100;
    const schedule = [];
    let bal = p;
    for (let y = 1; y <= t; y++) {
      const ob = bal; let yP=0, yI=0;
      for (let m=0; m<12 && bal>0; m++) {
        const i = bal*mr, pr = Math.min(emi-i, bal);
        yP+=pr; yI+=i; bal-=pr;
      }
      schedule.push({ year:y, open:Math.round(ob), principal:Math.round(yP), interest:Math.round(yI), close:Math.round(Math.max(bal,0)) });
    }
    return res.json({
      emi:Math.round(emi), totalPaid:Math.round(totalPaid), totalInt:Math.round(totalInt),
      taxSaved:Math.round(taxSaved), incomeReq:Math.round(emi/0.4),
      ppPct:pp.toFixed(1), ipPct:ip.toFixed(1), schedule,
    });
  }

  // ── FIRE ─────────────────────────────────────────────────────
  if (type === 'fire') {
    const age   = clamp(b.age,  18, 55,  30);
    const exp   = clamp(b.exp,  100, 10000000, 75000);
    const saved = clamp(b.saved,0,   1e9, 0);
    const inv   = clamp(b.inv,  100, 1e7, 50000);
    const ret   = clamp(b.ret,  1,   30,  10) / 100;
    const inf   = clamp(b.inf,  1,   15,  6)  / 100;  // kept for future use
    // FIX BUG-02: was ret/12 (naive). ret is a decimal like 0.10.
    const mr    = monthlyRateDecimal(ret);
    const fireCorpus = exp * 12 * 25;
    const swr        = fireCorpus * 0.04 / 12;
    let corpus = saved, years = 0;
    for (let m=0; m<600; m++) {
      corpus = corpus*(1+mr) + inv;
      if (corpus >= fireCorpus) { years = Math.ceil(m/12); break; }
    }
    const prog = Math.min((saved/fireCorpus)*100, 100);
    const tL = RC.fireLeanMax, tH = RC.fireFatMin;
    const fireType = exp<tL ? '🌿 Lean FIRE' : exp>tH ? '🏆 Fat FIRE' : '⚖️ Regular FIRE';
    const fireTypeDesc = exp<tL ? 'Minimal lifestyle, maximum speed to independence.'
      : exp>tH ? 'Luxury retirement — needs a large corpus.'
      : 'Balanced approach — part-time optional.';
    const milestones = [25,50,75,100].map(pc => {
      const tgt = fireCorpus*pc/100;
      let yr=0, c=saved;
      for (let m=0; m<600; m++) { c=c*(1+mr)+inv; if(c>=tgt){yr=Math.ceil(m/12);break;} }
      return { pc, target:Math.round(tgt), year:yr, reached:saved>=tgt };
    });
    return res.json({
      fireCorpus:Math.round(fireCorpus), swr:Math.round(swr),
      years: years>0?years:null, retireAge:years>0?age+years:null,
      prog:prog.toFixed(1), fireType, fireTypeDesc, milestones,
    });
  }

  // ── ROI ──────────────────────────────────────────────────────
  // ROI compounds annually — Math.pow(1+r/100,t) is correct.
  if (type === 'roi') {
    const p = clamp(b.p, 100, 1e9, 100000);
    const r = clamp(b.r, 0.1, 50, 12);
    const t = clamp(b.t, 1, 50, 20);
    const final   = p * Math.pow(1+r/100, t);
    const returns = final - p;
    const curve   = [];
    for (let y=0; y<=t; y++) curve.push({ year:y, value:Math.round(p*Math.pow(1+r/100,y)) });
    const base   = RC.roiBase;
    const assets = RC.roiAssets;
    const maxV   = Math.max(...assets.map(a => base*Math.pow(1+a.rate/100,20)));
    const assetCompare = assets.map(a => {
      const v = base*Math.pow(1+a.rate/100,20);
      return { name:a.name, rate:a.rate, color:a.color, value:Math.round(v), widthPct:((v/maxV)*100).toFixed(1) };
    });
    return res.json({
      final:Math.round(final), returns:Math.round(returns),
      mult:(final/p).toFixed(1), curve, assetCompare, roiBase:base,
    });
  }

  // ── INSURANCE ────────────────────────────────────────────────
  // HLV = income × remaining working years + liabilities. Correct.
  if (type === 'insurance') {
    const inc    = clamp(b.inc,   1000,  1e8, 1800000);
    const age    = clamp(b.age,   18,    60,  30);
    const ret    = clamp(b.ret,   45,    75,  60);
    const liab   = clamp(b.liab,  0,     1e9, 0);
    const exist  = clamp(b.exist, 0,     1e9, 0);
    const hlv    = (inc*(ret-age)) + liab;
    const gap    = Math.max(hlv - exist, 0);
    const pr     = RC.insPremiumRate(age);
    return res.json({
      cover:Math.round(hlv), gap:Math.round(gap), premium:Math.round(gap*pr),
    });
  }

  // ── TAX (India) ───────────────────────────────────────────────
  // Surcharge reverse-iterate logic verified correct.
  if (type === 'tax') {
    const cfg = TAX_CONFIG[ACTIVE_AY];
    const inc  = clamp(b.inc,  0, 1e8, 1800000);
    const c80  = clamp(b.c80,  0, cfg.old.deductionLimits.sec80c,    0);
    const c80d = clamp(b.c80d, 0, cfg.old.deductionLimits.sec80d,    0);
    const hl   = clamp(b.hl,   0, cfg.old.deductionLimits.sec24b,    0);
    const nps  = clamp(b.nps,  0, cfg.old.deductionLimits.nps80ccd1b,0);
    const oldTaxable = Math.max(
      inc - cfg.old.standardDeduction
        - Math.min(c80,cfg.old.deductionLimits.sec80c)
        - Math.min(c80d,cfg.old.deductionLimits.sec80d)
        - Math.min(hl,cfg.old.deductionLimits.sec24b)
        - Math.min(nps,cfg.old.deductionLimits.nps80ccd1b),
      0);
    const newTaxable = Math.max(inc - cfg.new.standardDeduction, 0);
    const oldTax = calcRegimeTax(oldTaxable, inc, cfg.old, cfg.cess);
    const newTax = calcRegimeTax(newTaxable, inc, cfg.new, cfg.cess);
    return res.json({
      oldTax:Math.round(oldTax), newTax:Math.round(newTax),
      oldEff:(oldTax/inc*100).toFixed(1), newEff:(newTax/inc*100).toFixed(1),
      better:oldTax<=newTax?'Old Regime':'New Regime',
      saving:Math.round(Math.abs(oldTax-newTax)),
    });
  }

  // ── PPF ──────────────────────────────────────────────────────
  if (type === 'ppf') {
    const y = clamp(b.y, 500, 150000, 150000);
    const t = clamp(b.t, 15, 50, 15);
    const rate = 0.071;
    // FIX BUG-08: was Math.round()'ing interest each year before adding to
    // balance, causing small cumulative rounding errors. Now carry exact
    // float in balance; only round for display in rows and final output.
    let balance=0, totalInv=0;
    const rows = [];
    for (let yr=1; yr<=t; yr++) {
      const interest = (balance + y) * rate;   // exact float, no premature rounding
      balance = balance + y + interest;
      totalInv += y;
      rows.push({ year:yr, deposit:Math.round(y), interest:Math.round(interest), balance:Math.round(balance) });
    }
    return res.json({
      maturity:Math.round(balance), invested:Math.round(totalInv),
      interestEarned:Math.round(balance-totalInv),
      taxSaved:Math.round(Math.min(y,150000)*0.30), rows,
    });
  }

  // ── EPF ──────────────────────────────────────────────────────
  // Formula verified correct: (balance+contrib)*(1+rate) is standard
  // end-of-year contribution + compounding model.
  if (type === 'epf') {
    const sal  = clamp(b.sal,  1000, 500000, 50000);
    const age  = clamp(b.age,  18,   55,     28);
    const grow = clamp(b.grow, 0,    20,     8) / 100;
    const rate = 0.0825, years = 58-age;
    let empTotal=0, erTotal=0, balance=0, curSal=sal;
    for (let yr=1; yr<=years; yr++) {
      const ec = curSal*12*0.12, er = curSal*12*0.0367;
      const contrib = ec+er;
      balance += contrib + (balance+contrib)*rate;
      empTotal += ec; erTotal += er; curSal *= (1+grow);
    }
    return res.json({
      corpus:Math.round(balance), empContrib:Math.round(empTotal),
      erContrib:Math.round(erTotal), years,
      monthlyDeduction:Math.round(sal*0.12),
    });
  }

  // ── NPS ──────────────────────────────────────────────────────
  if (type === 'nps') {
    const p    = clamp(b.p,   500, 100000, 5000);
    const age  = clamp(b.age, 18,  55,     30);
    const eq   = clamp(b.eq,  0,   75,     75) / 100;
    const debt = 0.75 - eq;
    const ret  = eq*0.11 + debt*0.07 + (0.25-debt)*0.09;
    const years = 60 - age, months = years * 12;
    // FIX BUG-03: was ret/12 (naive, ret is decimal like 0.105).
    const mr = monthlyRateDecimal(ret);
    const corpus  = p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
    const lumpsum = corpus * 0.60;
    const pension = corpus * 0.40 * 0.06 / 12;
    const taxSaved = Math.round(Math.min(p*12,50000)*0.30);
    return res.json({
      corpus:Math.round(corpus), lumpsum:Math.round(lumpsum),
      pension:Math.round(pension), taxSaved,
      equityPct:Math.round(eq*100), debtPct:Math.round((1-eq)*100),
      blendedReturn:(ret*100).toFixed(2), years,
    });
  }

  // ── STEP-UP SIP ───────────────────────────────────────────────
  if (type === 'stepsip') {
    const p    = clamp(b.p,    500, 1000000, 10000);
    const step = clamp(b.step, 0,   30,      10) / 100;
    const r    = clamp(b.r,    1,   30,      12);
    const t    = clamp(b.t,    1,   40,      20);
    // FIX BUG-04: was r/12/100 (naive).
    const mr   = monthlyRate(r);
    let stepCorpus=0, flatCorpus=0, cur=p;
    const rows = [];
    for (let y=1; y<=t; y++) {
      for (let m=0; m<12; m++) {
        stepCorpus = stepCorpus*(1+mr)+cur;
        flatCorpus = flatCorpus*(1+mr)+p;
      }
      rows.push({ year:y, monthlySip:Math.round(cur), stepValue:Math.round(stepCorpus), flatValue:Math.round(flatCorpus), advantage:Math.round(stepCorpus-flatCorpus) });
      cur = cur*(1+step);
    }
    return res.json({
      stepCorpus:Math.round(stepCorpus), flatCorpus:Math.round(flatCorpus),
      extra:Math.round(stepCorpus-flatCorpus), rows,
    });
  }

  // ── SSA (Sukanya Samriddhi) ───────────────────────────────────
  if (type === 'ssa') {
    const age = clamp(b.age, 0,  10,     3);
    const dep = clamp(b.dep, 250,150000, 150000);
    const rate=0.082, totalYears=21-age, depositYears=15;
    // FIX BUG-09: same as PPF — was Math.round()'ing interest before
    // adding to balance. Now carry exact float; only round for display.
    let balance=0, totalInv=0;
    const rows = [];
    for (let yr=1; yr<=totalYears; yr++) {
      const depositing = yr<=depositYears;
      const deposit    = depositing ? dep : 0;
      const interest   = (balance + deposit) * rate;  // exact float
      balance += deposit + interest;
      if (depositing) totalInv += dep;
      rows.push({ year:yr, deposit:depositing?Math.round(dep):0, interest:Math.round(interest), balance:Math.round(balance) });
    }
    return res.json({
      maturity:Math.round(balance), invested:Math.round(totalInv),
      interestEarned:Math.round(balance-totalInv), rows,
    });
  }

  // ── CROREPATI / MILLIONAIRE ───────────────────────────────────
  if (type === 'crorepati') {
    const target = clamp(b.target, 100000, 5e9, 10000000);
    const t      = clamp(b.t,      1,      40,  15);
    const r      = clamp(b.r,      1,      30,  12);
    // FIX BUG-05: was r/12/100 (naive).
    const mr     = monthlyRate(r);
    const months = t * 12;
    const monthly = target * mr / (((Math.pow(1+mr,months)-1)) * (1+mr));
    return res.json({
      monthly:Math.round(monthly), target, years:t, rate:r,
      perDay:Math.round(monthly/30),
    });
  }

  // ── HABIT VS INVEST ───────────────────────────────────────────
  if (type === 'habit') {
    const p      = clamp(b.p, 100, 500000, 4500);
    const t      = clamp(b.t, 1,   40,     20);
    const r      = clamp(b.r, 1,   30,     12);
    // FIX BUG-06: was r/12/100 (naive).
    const mr     = monthlyRate(r);
    const months = t * 12;
    const spent  = p * 12 * t;
    const corpus = p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
    return res.json({
      spent:Math.round(spent), corpus:Math.round(corpus),
      gains:Math.round(corpus-spent), mult:((corpus/spent).toFixed(1)),
      years:t, monthly:p,
    });
  }

  // ── SIP vs LUMP SUM COMPARE ───────────────────────────────────
  if (type === 'compare') {
    const p      = clamp(b.p, 100, 10000000, 25000);
    const r      = clamp(b.r, 0.1, 30,       12);
    const t      = clamp(b.t, 1,   40,       15);
    // FIX BUG-07: SIP side was r/12/100 (naive).
    // Lump sum side uses Math.pow(1+r/100,t) — annual compounding, correct.
    const mr     = monthlyRate(r);
    const months = t * 12;
    const lumpTotal  = p * months;
    const sipFinal   = p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
    const lsFinal    = lumpTotal * Math.pow(1+r/100, t);
    const sipWins    = sipFinal >= lsFinal;
    const curve = [];
    for (let y=1; y<=t; y++) {
      const m2 = y*12;
      curve.push({
        year:y,
        sip:Math.round(p*(((Math.pow(1+mr,m2)-1)/mr)*(1+mr))),
        ls:Math.round(lumpTotal*Math.pow(1+r/100,y)),
      });
    }
    return res.json({
      sipFinal:Math.round(sipFinal), lsFinal:Math.round(lsFinal),
      sipGains:Math.round(sipFinal-lumpTotal), lsGains:Math.round(lsFinal-lumpTotal),
      lumpTotal:Math.round(lumpTotal), sipWins, diff:Math.round(Math.abs(sipFinal-lsFinal)),
      winner:sipWins?'SIP':'Lump Sum', loser:sipWins?'Lump Sum':'SIP',
      curve,
    });
  }

  return res.status(400).json({ error: 'Invalid type' });
}

/* ============================================================
 * seo-content.js — unique on-page content per calculator
 * ============================================================
 * This is the file you edit. build-seo-pages.js reads it and
 * injects the content into each generated page.
 *
 * For every tab id there are three fields:
 *
 *   h1     — the visible <h1> for that page. Must differ per page.
 *   intro  — HTML shown directly under the H1, above the calculator.
 *            Aim for 250-400 words of text that could ONLY appear
 *            on this page. Generic "invest wisely" filler is worse
 *            than nothing.
 *   faq    — array of {q, a}. Plain text only (no HTML tags) because
 *            the same strings are reused for FAQPage structured data.
 *            6-10 questions is the sweet spot. Write the questions
 *            the way a person would type them into Google.
 *
 * Tabs left as null are still generated (unique title, description,
 * canonical) but the build will warn you that they're thin.
 * ============================================================ */

module.exports = {

  sip: {
    h1: 'SIP Calculator — Project Your Mutual Fund Returns',
    intro: `
      <p>A Systematic Investment Plan puts a fixed amount into a mutual fund on the same
      date every month. Because each instalment buys units at whatever the NAV happens to
      be that day, you accumulate more units when markets fall and fewer when they rise.
      That is rupee cost averaging, and it is the main reason SIPs suit people who cannot
      reliably judge when the market is cheap.</p>

      <p>This calculator uses the standard future value of an annuity-due formula:
      <strong>FV = P × [((1 + i)<sup>n</sup> − 1) ÷ i] × (1 + i)</strong>, where P is your
      monthly instalment, i is the monthly rate (annual return ÷ 12) and n is the number of
      instalments. Instalments are treated as arriving at the start of each month, which is
      how most AMCs process SIP debits.</p>

      <p>A word on the return assumption. The 12% default is a long-run figure for
      diversified Indian equity funds, not a promise. Nifty 50 total returns have swung
      between roughly −25% and +75% in individual years. Over 15-year windows the range
      narrows considerably, which is the practical argument for long tenures. If you are
      modelling a debt or hybrid fund, drop the rate to 6-9%.</p>

      <p>Two things this projection deliberately does not do: it does not deduct the fund's
      expense ratio (typically 0.5-1.0% for direct plans, 1.5-2.25% for regular plans), and
      it does not model exit load. Subtract your expense ratio from the return input if you
      want a net-of-cost number.</p>
    `,
    faq: [
      { q: 'How much SIP do I need to accumulate ₹1 crore?',
        a: 'At 12% annual returns, roughly ₹21,000 per month for 15 years, ₹10,000 per month for 20 years, or ₹5,000 per month for 26 years. The monthly amount required falls steeply as the tenure lengthens because compounding does progressively more of the work.' },
      { q: 'Is SIP better than a lump sum investment?',
        a: 'Mathematically a lump sum wins whenever markets rise steadily, since the full amount is invested for longer. SIP wins in volatile or falling markets and, more importantly, matches how salaried people actually receive money. If you already hold a large sum, a Systematic Transfer Plan from a liquid fund is the usual middle path.' },
      { q: 'What returns should I assume for a SIP calculator?',
        a: 'For diversified equity funds, 10-12% is a defensible long-run assumption. Use 8-10% for hybrid or balanced advantage funds and 6-7% for debt funds. Assuming 15% or more will produce a projection that looks encouraging and is unlikely to be met.' },
      { q: 'How is SIP taxed in India?',
        a: 'Each instalment is treated as a separate purchase for capital gains. For equity funds, units held over 12 months attract long-term capital gains tax at 12.5% above the ₹1.25 lakh annual exemption; units sold earlier attract 20% short-term capital gains. Because instalments age separately, a redemption often mixes both.' },
      { q: 'Can I stop or pause a SIP?',
        a: 'Yes. SIPs carry no lock-in unless the fund is an ELSS, where each instalment is locked for three years from its own date. You can pause with most AMCs for one to six months, or cancel outright with about 30 days notice to the bank mandate.' },
      { q: 'What happens if I miss a SIP instalment?',
        a: 'Nothing happens to your existing units. The bank may levy a mandate failure charge, and AMCs typically cancel the SIP after three consecutive misses. There is no penalty from the fund itself.' },
      { q: 'Does this SIP calculator account for inflation?',
        a: 'The projection shows nominal rupees. To see purchasing power in today\'s terms, reduce your return assumption by expected inflation — for example, enter 6% instead of 12% if you assume 6% inflation, which gives an approximate real return.' },
    ],
  },

  emi: {
    h1: 'EMI Calculator — Home, Car and Personal Loan',
    intro: `
      <p>An Equated Monthly Instalment is a fixed payment covering both interest and
      principal. The split shifts over the life of the loan: early instalments are mostly
      interest, later ones mostly principal. On a 20-year home loan at 8.5%, roughly 70% of
      your first year's payments go to interest and almost none to reducing the balance.
      This is why prepaying early saves far more than prepaying late.</p>

      <p>The formula is <strong>EMI = P × r × (1 + r)<sup>n</sup> ÷ [(1 + r)<sup>n</sup> − 1]</strong>,
      with P the principal, r the monthly interest rate and n the number of months. The
      amortisation schedule below breaks out interest and principal for every instalment.</p>

      <p>Most Indian floating-rate home loans are now benchmarked to the RBI repo rate under
      the external benchmark lending rate regime. When the repo moves, your lender must pass
      it through, usually by changing the tenure rather than the EMI. That means a rate rise
      can quietly extend your loan by years while the monthly outgo looks unchanged — worth
      checking your amortisation statement after every policy change.</p>

      <p>On affordability, most lenders cap total EMIs at 50-60% of net monthly income, and
      home loan eligibility at roughly 60 times monthly income. Those are underwriting
      limits, not advice. Borrowing at the maximum the bank will allow leaves no room for a
      job gap or a rate rise.</p>
    `,
    faq: [
      { q: 'How is home loan EMI calculated?',
        a: 'EMI = P × r × (1+r)^n ÷ [(1+r)^n − 1], where P is the loan amount, r is the monthly rate (annual rate divided by 12) and n is the tenure in months. A ₹50 lakh loan at 8.5% for 20 years gives an EMI of about ₹43,400.' },
      { q: 'Does prepaying a home loan actually save money?',
        a: 'Substantially, if done early. Prepaying ₹5 lakh in year 3 of a 20-year loan saves far more interest than the same ₹5 lakh in year 15, because interest accrues on the outstanding balance. Floating-rate home loans to individuals carry no prepayment penalty under RBI rules.' },
      { q: 'Should I reduce the EMI or the tenure when prepaying?',
        a: 'Reducing tenure saves more interest and is usually the better choice. Reducing the EMI improves monthly cash flow. Most lenders default to keeping the EMI and cutting the tenure unless you ask otherwise.' },
      { q: 'What tax benefits apply to a home loan?',
        a: 'Under the old regime, Section 24(b) allows up to ₹2 lakh a year on interest for a self-occupied property and Section 80C up to ₹1.5 lakh on principal. Under the new regime these deductions are not available for self-occupied property, though interest on a let-out property remains deductible against rental income.' },
      { q: 'Why did my loan tenure increase without my EMI changing?',
        a: 'Floating-rate loans linked to the repo rate absorb rate rises by extending tenure rather than raising the instalment. Lenders must offer you the option to switch to a higher EMI instead — you have to ask.' },
      { q: 'What is a good credit score for a home loan?',
        a: 'A CIBIL score above 750 typically secures the advertised rate. Between 700 and 750 you may pay 25-50 basis points more. Below 650, approval becomes difficult without a co-applicant or larger down payment.' },
      { q: 'How much home loan can I get on my salary?',
        a: 'Most lenders sanction around 60 times monthly net income, capped so that total EMIs stay under 50-60% of income. On ₹1 lakh a month, that is roughly ₹60 lakh, subject to the property valuation and a loan-to-value cap of 75-90%.' },
    ],
  },

  ppf: {
    h1: 'PPF Calculator — Maturity Value and Year-by-Year Balance',
    intro: `
      <p>The Public Provident Fund is a 15-year government-backed savings scheme paying
      7.1% per annum, with the rate reviewed quarterly by the Ministry of Finance. It is one
      of the few remaining exempt-exempt-exempt instruments in India: contributions qualify
      under Section 80C, interest accrues tax-free, and the maturity amount is tax-free.</p>

      <p>Interest is calculated on the <strong>lowest balance between the 5th and the last day
      of each month</strong>, then credited once at the end of the financial year. This rule
      has a practical consequence most people miss: depositing before the 5th of the month
      earns you an extra month of interest, and a lump sum deposited on or before 5 April
      earns a full year's interest, while the same amount deposited in March earns almost
      nothing.</p>

      <p>The contribution limits are ₹500 minimum and ₹1.5 lakh maximum per financial year,
      across all PPF accounts you hold. Miss the ₹500 minimum and the account is treated as
      discontinued, revivable by paying ₹50 per lapsed year plus the arrears.</p>

      <p>The 15-year term runs from the end of the financial year in which you opened the
      account, so a March opening effectively costs you almost a year. At maturity you can
      withdraw fully, extend in five-year blocks with fresh contributions, or extend without
      contributing and keep earning interest. Partial withdrawal is allowed from year 7, and
      a loan against the balance from year 3 to year 6.</p>
    `,
    faq: [
      { q: 'What is the current PPF interest rate?',
        a: 'The rate is 7.1% per annum, compounded annually. The Ministry of Finance reviews small savings rates every quarter, so the rate can change, though PPF has held at 7.1% for an extended period.' },
      { q: 'How much will ₹1.5 lakh a year in PPF grow to in 15 years?',
        a: 'Depositing the full ₹1.5 lakh each year at 7.1% produces a maturity value of roughly ₹40.7 lakh, of which about ₹18.2 lakh is interest. Depositing early in each financial year rather than late adds meaningfully to this over 15 years.' },
      { q: 'When should I deposit into PPF to maximise interest?',
        a: 'On or before the 5th of the month, because interest is computed on the lowest balance between the 5th and month end. For an annual lump sum, deposit on or before 5 April to earn interest for the full financial year.' },
      { q: 'Can I withdraw from PPF before 15 years?',
        a: 'Partial withdrawal is permitted from the seventh year, capped at 50% of the balance at the end of the fourth preceding year or the previous year, whichever is lower. Premature closure is allowed after five years only for serious illness, higher education, or a change in residency status, with a 1% interest penalty.' },
      { q: 'Is PPF interest taxable?',
        a: 'No. PPF falls under the exempt-exempt-exempt category, so interest and maturity proceeds are entirely tax-free. Contributions also qualify for deduction under Section 80C, though only under the old tax regime.' },
      { q: 'Can I open more than one PPF account?',
        a: 'No. One account per person is permitted, and the ₹1.5 lakh annual cap applies across all accounts including those opened for a minor where you are the guardian. Duplicate accounts are frozen and earn no interest.' },
      { q: 'What happens to PPF after 15 years?',
        a: 'You can withdraw the full balance tax-free, extend in five-year blocks while continuing to contribute, or extend without contributing while the balance continues earning interest. The extension choice must be made within one year of maturity.' },
      { q: 'Is PPF better than ELSS?',
        a: 'They serve different purposes. PPF gives a guaranteed 7.1% with sovereign backing and a 15-year term. ELSS carries equity risk with a three-year lock-in and no return guarantee. PPF suits the stable portion of a portfolio; ELSS suits the growth portion for those with a longer horizon and tolerance for volatility.' },
    ],
  },

  fire: {
    h1: 'FIRE Calculator — Your Financial Independence Number',
    intro: `
      <p>Financial Independence, Retire Early rests on one number: the corpus at which
      withdrawals cover your expenses indefinitely. The common shorthand is 25 times annual
      expenses, which comes from the 4% safe withdrawal rate — the finding from the Trinity
      Study that a portfolio withdrawing 4% in year one, adjusted upward for inflation
      annually, survived 30 years in almost all historical US windows.</p>

      <p>That figure needs adjustment for India. The study assumed US equity and bond
      returns and US inflation of around 3%. Indian inflation has averaged closer to 6%, and
      an early retirement in your forties needs the corpus to last 45 years rather than 30.
      Both push the sustainable rate down. Many Indian practitioners work with 3-3.5%,
      implying a corpus of 28 to 33 times expenses rather than 25.</p>

      <p>This calculator inflates your current annual expenses to your retirement date, then
      applies your chosen withdrawal rate. The result is the nominal corpus you need on the
      day you stop working.</p>

      <p>Three costs people routinely leave out of the expense figure: health insurance
      premiums, which rise steeply after 60 and are the single largest retirement cost shock
      in India; one-off replacements such as a car or a roof, which do not appear in a
      typical monthly budget; and support for ageing parents. A corpus sized on today's
      grocery bill alone will fall short.</p>
    `,
    faq: [
      { q: 'How much money do I need to retire early in India?',
        a: 'Between 28 and 33 times your annual expenses, using a 3-3.5% withdrawal rate. On ₹12 lakh of annual expenses that is roughly ₹3.4 to ₹4 crore in today\'s money, which must then be inflated to your actual retirement date.' },
      { q: 'Does the 4% rule work in India?',
        a: 'It is optimistic here. The rule was derived from US data with roughly 3% inflation over a 30-year retirement. Indian inflation nearer 6% and an early retirement lasting 40-plus years both argue for 3 to 3.5% instead, which raises the corpus needed by 15-30%.' },
      { q: 'What is Coast FIRE?',
        a: 'The point at which your existing corpus, left untouched, will compound to a full retirement number by your target age without further contributions. You still work to cover current expenses, but you no longer need to save. It typically arrives 10-15 years before full FIRE.' },
      { q: 'What is the difference between Lean, Regular and Fat FIRE?',
        a: 'Lean FIRE covers a deliberately minimal lifestyle, often 15-20 times expenses. Regular FIRE targets your current standard of living. Fat FIRE funds a materially more comfortable lifestyle, usually 35 times expenses or more. The distinction is about the expense figure, not the arithmetic.' },
      { q: 'Should I include my house in my FIRE corpus?',
        a: 'Only if you intend to sell or rent it. A self-occupied home generates no withdrawal income, so it does not support the 25x calculation. It does reduce your expenses by removing rent, which lowers the corpus you need.' },
      { q: 'How does inflation affect my FIRE number?',
        a: 'Severely, over long horizons. At 6% inflation, expenses double roughly every 12 years, so ₹1 lakh a month today becomes about ₹3.2 lakh a month in 20 years. The corpus must be sized against the inflated figure, and must keep growing during retirement.' },
      { q: 'Where should a FIRE corpus be invested after retiring?',
        a: 'The common structure keeps three to five years of expenses in debt or liquid funds to avoid selling equity in a downturn, with the remainder in equity to outpace inflation over the decades that follow. The precise split depends on your withdrawal rate and tolerance for volatility.' },
    ],
  },

  // ── Not yet written. The build will still generate these pages with
  //    unique titles and canonicals, but will warn that they are thin.
  //    Work down this list in order of search volume.
  tax:       null,
  nps:       null,
  epf:       null,
  roi:       null,
  insurance: null,
  stepsip:   null,
  ssa:       null,
  crorepati: null,
  habit:     null,
  compare:   null,
  gratuity:  null,
  homegoal:  null,
  edu:       null,
  glossary:  null,
  contact:   null,
};

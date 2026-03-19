export default function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { type, p, r, t, n } = req.body;
    const amount = parseFloat(p);
    const rate = parseFloat(r) / 12 / 100;

    if (type === 'sip') {
        const months = parseFloat(t) * 12;
        const invested = amount * months;
        const totalValue = amount * (((Math.pow(1 + rate, months) - 1) / rate) * (1 + rate));
        
        // Tax logic: 80C applies to ELSS SIPs (capped at 1.5L/year)
        const annualInvestment = amount * 12;
        const taxSaved = Math.min(annualInvestment, 150000) * 0.30; // 30% slab

        return res.json({
            value: totalValue.toFixed(0),
            invested: invested.toFixed(0),
            earnings: (totalValue - invested).toFixed(0),
            taxSaved: taxSaved
        });
    }

    if (type === 'emi') {
        const months = parseFloat(t); // assuming t is months for EMI
        const emi = (amount * rate * Math.pow(1 + rate, months)) / (Math.pow(1 + rate, months) - 1);
        return res.json({ value: emi.toFixed(0) });
    }

    res.status(400).json({ error: 'Invalid calculation type' });
}

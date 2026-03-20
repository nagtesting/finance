// Financial rounding helper for 2-decimal accuracy [cite: 6]
const round = (num) => Math.round((num + Number.EPSILON) * 100) / 100;

export default function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    try {
        const { type, p, r, t, taxSlab = 30, inflation = 6 } = req.body;

        // 1. Input Validation: amount > 0, rate >= 0, tenure > 0 [cite: 3, 4]
        const P = parseFloat(p);
        const annualRate = parseFloat(r);
        const T = parseFloat(t);

        if (isNaN(P) || P <= 0 || isNaN(annualRate) || annualRate < 0 || isNaN(T) || T <= 0) {
            return res.status(400).json({ error: "Invalid inputs. Ensure values are positive numbers." });
        }

        const monthlyRate = annualRate / 12 / 100;

        // 2. SIP Logic with Zero-Rate Handling [cite: 1]
        if (type === 'sip') {
            const months = T * 12;
            let totalValue;
            
            if (monthlyRate === 0) {
                totalValue = P * months;
            } else {
                totalValue = P * (((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) * (1 + monthlyRate));
            }

            const invested = P * months;
            const taxSaved = Math.min(invested / T, 150000) * (taxSlab / 100); // Dynamic Tax Slab [cite: 5]
            const realValue = totalValue / Math.pow(1 + (inflation / 100), T); // Inflation Adjustment [cite: 12]

            return res.json({
                value: round(totalValue),
                invested: round(invested),
                earnings: round(totalValue - invested),
                taxSaved: round(taxSaved),
                inflationAdjustedValue: round(realValue)
            });
        }

        // 3. EMI Logic with Zero-Rate Handling [cite: 2]
        if (type === 'emi') {
            let emi;
            if (monthlyRate === 0) {
                emi = P / T;
            } else {
                emi = (P * monthlyRate * Math.pow(1 + monthlyRate, T)) / (Math.pow(1 + monthlyRate, T) - 1);
            }

            const totalPayable = emi * T;
            return res.json({
                value: round(emi),
                totalInterest: round(totalPayable - P),
                totalPayable: round(totalPayable)
            });
        }

        return res.status(400).json({ error: "Unsupported calculator type" });

    } catch (error) {
        return res.status(500).json({ error: "Internal Server Error" }); // Server-side error handling 
    }
}

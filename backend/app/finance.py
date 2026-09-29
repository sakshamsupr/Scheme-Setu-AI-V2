import re

def parse_rate(rate: str, default: float = 8.0) -> float:
    text = str(rate or "").replace(",", "")
    vals = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not vals:
        return default
    return sum(vals)/len(vals)

def calculate(loan_amount: float, subsidy_percentage: float, interest_rate: str, tenure_years: int, moratorium_months: int = 0) -> dict:
    principal = max(0.0, float(loan_amount) * (1 - float(subsidy_percentage)/100.0))
    annual = parse_rate(interest_rate)
    months = max(1, int(tenure_years)*12)
    monthly_rate = annual / 100 / 12
    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = principal * monthly_rate * (1+monthly_rate)**months / ((1+monthly_rate)**months - 1)
    total = emi * months
    return {
        "requested_loan": round(float(loan_amount),2),
        "subsidy_percentage": float(subsidy_percentage),
        "estimated_principal_after_subsidy": round(principal,2),
        "estimated_annual_interest_rate": round(annual,2),
        "tenure_years": int(tenure_years),
        "moratorium_months": int(moratorium_months),
        "monthly_emi": round(emi,2),
        "total_repayment": round(total,2),
        "total_interest": round(max(0,total-principal),2),
        "disclaimer": "Indicative calculation. Actual terms depend on the lender and sanctioned facility."
    }

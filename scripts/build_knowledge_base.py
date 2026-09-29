from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'data'/'seed'/'schemes_seed.csv'
out=ROOT/'data'/'knowledge_base'
out.mkdir(parents=True,exist_ok=True)
with source.open(encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))
for r in rows:
    path=out/f"{r['scheme_id']}.md"
    path.write_text(f"# {r['scheme_name']}\n\n{r['description']}\n\n## Eligibility\n- Gender: {r['gender']}\n- Category: {r['category']}\n- Age: {r['min_age']}–{r['max_age']}\n- Business: {r['business_type']}\n- State: {r['state']}\n\n## Finance\n- Loan: ₹{r['min_loan_inr']}–₹{r['max_loan_inr']}\n- Subsidy: {r['max_subsidy_pct']}%\n- Interest: {r['interest_rate']}\n- Tenure: {r['tenure_years']} years\n\n## Documents\n{r['documents']}\n\n## Source\n{r['apply_link']}\n", encoding='utf-8')
print(f'Generated {len(rows)} knowledge-base documents in {out}')

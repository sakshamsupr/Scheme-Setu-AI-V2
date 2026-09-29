"""Compare current seed scheme data with a saved snapshot and publish notification items for material changes."""
from __future__ import annotations
import csv, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
current=ROOT/'data/seed/schemes_seed.csv'
snap=ROOT/'data/runtime/schemes_snapshot.csv'
updates=ROOT/'data/runtime/updates.json'
keys=['scheme_name','max_loan_inr','min_loan_inr','max_subsidy_pct','interest_rate','tenure_years','documents','description','apply_link']

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return {r['scheme_id']:r for r in csv.DictReader(f)}
now=read(current)
old=read(snap) if snap.exists() else {}
items=json.loads(updates.read_text(encoding='utf-8')) if updates.exists() else []
for sid,row in now.items():
    prev=old.get(sid)
    if not prev: continue
    changed=[k for k in keys if str(prev.get(k,''))!=str(row.get(k,''))]
    if changed:
        items.insert(0,{'id':f"change-{sid}-{int(time.time())}",'type':'scheme','title':f"Scheme updated: {row['scheme_name']}",'message':f"Updated fields: {', '.join(changed)}. Re-check the official source before applying.",'source':row.get('apply_link') or '','createdAt':time.strftime('%Y-%m-%d')})
updates.write_text(json.dumps(items[:100],ensure_ascii=False,indent=2),encoding='utf-8')
# Save new snapshot.
with snap.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(next(iter(now.values())).keys())); writer.writeheader(); writer.writerows(now.values())
print(f'Compared {len(now)} schemes; notification feed updated when material changes were detected.')

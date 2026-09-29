import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'data/runtime/updates.json'
items=json.loads(F.read_text(encoding='utf-8')) if F.exists() else []
if len(sys.argv)<5:
    raise SystemExit('Usage: python scripts/add_update.py TYPE TITLE MESSAGE TARGET_OR_SOURCE')
type_,title,msg,target=sys.argv[1:5]
row={'id':f'u-{int(time.time())}','type':type_,'title':title,'message':msg,'createdAt':time.strftime('%Y-%m-%d')}
if target.startswith('http'): row['source']=target
else: row['target']=target
items.insert(0,row)
F.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(row)

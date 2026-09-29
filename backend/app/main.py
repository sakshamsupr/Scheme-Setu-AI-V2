from __future__ import annotations
from typing import Any
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import CORS_ORIGINS
from .data_store import scheme_records, normalize_scheme, get_scheme, match_schemes, nearby_partners
from .finance import calculate
from .rag import retrieve
from .ai import chat

app=FastAPI(title="Scheme Setu AI V2 API", version="2.0.0", description="AI-powered government scheme navigation, financial intelligence and partner discovery.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT = 60
RATE_WINDOW = 60


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    bucket = _rate_buckets[client_ip]

    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again shortly."},
            headers={"Retry-After": str(RATE_WINDOW)},
        )

    bucket.append(now)

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=(self)"

    return response

class Profile(BaseModel):
    name: str = ""
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str = ""
    category: str = ""
    state: str = ""
    district: str = ""
    business_type: str = ""
    loan_amount: float = Field(default=0, ge=0)
    income: float = Field(default=0, ge=0)
    education_status: str = ""

class MatchRequest(BaseModel):
    profile: Profile
    limit: int = Field(default=15, ge=1, le=50)

class CalcRequest(BaseModel):
    loan_amount: float = Field(gt=0)
    subsidy_percentage: float = Field(default=0, ge=0, le=100)
    interest_rate: str = "8"
    tenure_years: int = Field(default=5, ge=1, le=30)
    moratorium_months: int = Field(default=0, ge=0, le=60)

class PartnerRequest(BaseModel):
    latitude: float
    longitude: float
    scheme_name: str = ""
    max_distance_km: float = Field(default=300, gt=0, le=500)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    profile: dict[str,Any] = {}
    history: list[dict[str,Any]] = []
    language: str = "auto"

@app.get("/")
def root(): return {"name":"Scheme Setu AI","version":"2.0.0","status":"ready"}
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/stats")
def stats():
    schemes=scheme_records()
    from .data_store import partner_records
    partners=partner_records()
    return {"schemes":len(schemes),"partners":len(partners),"knowledge_documents":len(schemes),"api":"local-fallback-ready"}

@app.get("/schemes")
def schemes(q: str = Query(""), category: str = "", state: str = "", limit: int = 50):
    rows=[normalize_scheme(x) for x in scheme_records()]
    ql=q.lower().strip(); cl=category.lower().strip(); sl=state.lower().strip()
    out=[]
    for r in rows:
        hay=" ".join(str(r.get(k,"")) for k in ["scheme_name","description","business_type","category","documents"]).lower()
        if ql and ql not in hay: continue
        if cl and cl not in str(r.get("category","")).lower(): continue
        if sl and sl not in str(r.get("state","")).lower() and "all-india" not in str(r.get("state"," ")).lower(): continue
        out.append(r)
    return {"items":out[:max(1,min(limit,100))],"total":len(out)}

@app.get("/schemes/{scheme_id}")
def scheme_detail(scheme_id: str):
    row=get_scheme(scheme_id)
    if not row: raise HTTPException(404,"Scheme not found")
    return row

@app.post("/match-schemes")
def match(req: MatchRequest):
    if not req.profile.age: raise HTTPException(400,"Age is required for personalized matching")
    results=match_schemes(req.profile.model_dump(), req.limit)
    return {"profile":req.profile.model_dump(),"total":len(results),"items":results}

@app.post("/calculate-loan")
def calc(req: CalcRequest): return calculate(**req.model_dump())

@app.post("/nearby-partners")
def partners(req: PartnerRequest):
    items=nearby_partners(req.latitude, req.longitude, req.scheme_name, req.max_distance_km)
    return {"items":items,"total":len(items)}

@app.get("/search")
def search(q: str, top_k: int = 5): return {"items":retrieve(q, top_k)}

@app.post("/eligibility-gap")
def eligibility_gap(req: MatchRequest):
    if not req.profile.age:
        raise HTTPException(400, "Age is required for gap detection")
    results=match_schemes(req.profile.model_dump(), 50)
    return {"items":[{"scheme_id":r["scheme_id"],"scheme_name":r["scheme_name"],"eligible":r["eligible"],"gaps":r.get("gaps",[]),"match_reasons":r.get("match_reasons",[]),"score":r.get("score",0)} for r in results]}

@app.get("/notifications")
def notifications():
    import json
    from pathlib import Path
    runtime = Path(__file__).resolve().parents[2] / "data" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    feed_file = runtime / "updates.json"
    reminders_file = runtime / "reminders.json"
    items=[]
    if feed_file.exists():
        try: items.extend(json.loads(feed_file.read_text(encoding="utf-8")))
        except Exception: pass
    if not items:
        items=[
            {"id":"n1","type":"scheme","title":"NSSH evidence update","message":"Official MSME annual-report evidence is linked in this alert.","source":"https://www.msme.gov.in/sites/default/files/FINALMSMEANNUALREPORT2023-24ENGLISH.pdf","createdAt":"2026-09-20"},
            {"id":"n2","type":"application","title":"Application roadmap ready","message":"Continue your selected scheme step-by-step from Application Roadmap.","target":"/roadmap","createdAt":"2026-09-20"},
            {"id":"n3","type":"deadline","title":"Verify the latest deadline","message":"Application windows can change; verify the current official source before submitting.","target":"/schemes","createdAt":"2026-09-20"}
        ]
    if reminders_file.exists():
        try: items.extend(json.loads(reminders_file.read_text(encoding="utf-8")))
        except Exception: pass
    return {"items": items}

@app.post("/notifications/reminders")
def add_reminder(payload: dict[str,Any]):
    import json, time
    from pathlib import Path
    runtime = Path(__file__).resolve().parents[2] / "data" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    file = runtime / "reminders.json"
    try: existing=json.loads(file.read_text(encoding="utf-8")) if file.exists() else []
    except Exception: existing=[]
    reminder={"id":f"r-{int(time.time()*1000)}","type":"reminder","read":False,**payload}
    existing.insert(0, reminder)
    file.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding="utf-8")
    return reminder

@app.post("/copilot")
def copilot(req: ChatRequest): return chat(req.message, req.profile, req.history, req.language)

@app.post("/profile/normalize")
def normalize_profile(profile: Profile): return profile.model_dump()

@app.get("/roadmap/{scheme_id}")
def roadmap(scheme_id: str):
    s=get_scheme(scheme_id)
    if not s: raise HTTPException(404,"Scheme not found")
    docs=s.get("documents","")
    return {"scheme":s["scheme_name"],"steps":[
        {"step":1,"title":"Check eligibility","detail":"Review category, age, geography, business type and loan range against the scheme."},
        {"step":2,"title":"Prepare documents","detail":docs or "Check the official source for the latest document checklist."},
        {"step":3,"title":"Prepare project details","detail":"Keep project cost, business plan and repayment requirement ready where applicable."},
        {"step":4,"title":"Approach the authorized channel","detail":"Use Scheme Setu partner locator to identify a relevant nearby partner."},
        {"step":5,"title":"Verify and apply","detail":"Confirm the current terms and submit through the official channel."},
    ]}

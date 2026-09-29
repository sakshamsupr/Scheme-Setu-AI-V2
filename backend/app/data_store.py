from __future__ import annotations
import math
import re
from pathlib import Path
from typing import Any
import pandas as pd
from .config import SCHEMES_FILE, PARTNERS_FILE

_REQUIRED_SCHEME_COLUMNS = [
    "scheme_id","scheme_name","gender","category","min_age","max_age","max_loan_inr","min_loan_inr",
    "max_subsidy_pct","business_type","state","interest_rate","tenure_years","scheme_type","documents","description","apply_link"
]
_REQUIRED_PARTNER_COLUMNS = [
    "partner_id","partner_name","partner_type","state","district","city","pincode","latitude","longitude",
    "schemes_supported","active","application_status","capacity_status","fund_utilization_pct","npa_status","overdue_status","priority_score","contact_phone","official_website"
]

def _clean(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()

def tokens(v: Any) -> list[str]:
    text = _clean(v).lower().replace("/", ";").replace(",", ";").replace("|", ";")
    return [x.strip() for x in text.split(";") if x.strip()]

def load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path.name}: {missing}")
    return df.fillna("")

def scheme_records() -> list[dict[str, Any]]:
    df = load_csv(SCHEMES_FILE, _REQUIRED_SCHEME_COLUMNS)
    return df.to_dict(orient="records")

def partner_records() -> list[dict[str, Any]]:
    df = load_csv(PARTNERS_FILE, _REQUIRED_PARTNER_COLUMNS)
    return df.to_dict(orient="records")

def get_scheme(scheme_id: str) -> dict[str, Any] | None:
    for row in scheme_records():
        if _clean(row["scheme_id"]).lower() == scheme_id.lower():
            return normalize_scheme(row)
    return None

def normalize_scheme(row: dict[str, Any]) -> dict[str, Any]:
    def num(name, default=0):
        try: return float(_clean(row.get(name, "")))
        except Exception: return default
    return {
        **row,
        "min_age": int(num("min_age")),
        "max_age": int(num("max_age")),
        "max_loan_inr": num("max_loan_inr"),
        "min_loan_inr": num("min_loan_inr"),
        "max_subsidy_pct": num("max_subsidy_pct"),
        "tenure_years": int(num("tenure_years")),
        "gender_values": tokens(row.get("gender")),
        "category_values": tokens(row.get("category")),
        "business_values": tokens(row.get("business_type")),
        "state_values": tokens(row.get("state")),
        "documents_list": tokens(row.get("documents")),
    }

def profile_matches_scheme(profile: dict[str, Any], scheme: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    gender = _clean(profile.get("gender")).lower()
    category = _clean(profile.get("category")).lower()
    business = _clean(profile.get("business_type")).lower()
    state = _clean(profile.get("state")).lower()
    age = int(profile.get("age") or 0)
    loan = float(profile.get("loan_amount") or 0)
    reasons: list[str] = []
    gaps: list[str] = []
    gv = scheme["gender_values"] or ["all"]
    cv = scheme["category_values"] or ["all"]
    bv = scheme["business_values"] or ["all"]
    sv = scheme["state_values"] or ["all-india"]

    if "all" in gv or gender in gv or ("women" in cv and gender == "female"):
        reasons.append("Gender requirement matched")
    else:
        gaps.append("Gender requirement does not match")
    if "all" in cv or category in cv or (category == "general" and "general" in cv):
        reasons.append("Social category matched")
    else:
        gaps.append("Social category does not match")
    if scheme["min_age"] <= age <= scheme["max_age"]:
        reasons.append(f"Age {age} falls within {scheme['min_age']}–{scheme['max_age']}")
    else:
        gaps.append(f"Age must be between {scheme['min_age']} and {scheme['max_age']}")
    if "all" in bv or "all-india" in bv or business in bv:
        reasons.append("Business type matched")
    else:
        gaps.append("Business type is not listed")
    if any(x in {state, "all", "all-india", "all india"} for x in sv) or "all-india" in sv:
        reasons.append("Geography matched")
    else:
        gaps.append("State availability does not match")
    if scheme["min_loan_inr"] <= loan <= scheme["max_loan_inr"]:
        reasons.append("Requested loan amount is within the stated loan range")
    else:
        gaps.append("Requested loan amount is outside the stated loan range")
    hard = [x for x in gaps if "loan amount" not in x]
    return len(hard) == 0, reasons, gaps

def match_schemes(profile: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    results = []
    for raw in scheme_records():
        s = normalize_scheme(raw)
        eligible, reasons, gaps = profile_matches_scheme(profile, s)
        score = 0
        score += 25 if "Social category matched" in reasons else 0
        score += 20 if "Gender requirement matched" in reasons else 0
        score += 20 if any(r.startswith("Age ") for r in reasons) else 0
        score += 15 if "Business type matched" in reasons else 0
        score += 10 if "Geography matched" in reasons else 0
        score += 10 if "Requested loan amount is within the stated loan range" in reasons else 0
        if eligible:
            score += 15
        results.append({**s, "eligible": eligible, "score": min(score, 100), "match_reasons": reasons, "gaps": gaps})
    results.sort(key=lambda r: (r["eligible"], r["score"], r["max_subsidy_pct"]), reverse=True)
    return results[:limit]

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def nearby_partners(latitude: float, longitude: float, scheme_name: str = "", max_distance_km: float = 300, limit: int = 15) -> list[dict[str, Any]]:
    results=[]
    query = scheme_name.lower().strip()
    for raw in partner_records():
        try:
            plat=float(raw["latitude"]); plon=float(raw["longitude"])
        except Exception:
            continue
        distance = haversine_km(latitude, longitude, plat, plon)
        supported = tokens(raw.get("schemes_supported"))
        scheme_match = (not query) or any(query in s.lower() or s.lower() in query for s in supported)
        if distance <= max_distance_km and (scheme_match or not query):
            operational = _clean(raw.get("active")).lower() in {"true","1","yes"} and _clean(raw.get("application_status")).lower() != "closed"
            health = 0
            if _clean(raw.get("capacity_status")).lower() in {"available","open"}: health += 25
            if _clean(raw.get("npa_status")).lower() in {"healthy","good"}: health += 25
            if _clean(raw.get("overdue_status")).lower() in {"low","none"}: health += 25
            try: priority=float(raw.get("priority_score") or 0)
            except: priority=0
            rank = (100 if scheme_match else 0) + (30 if operational else 0) + health + priority - distance
            results.append({**raw, "distance_km": round(distance,2), "scheme_match": scheme_match, "operational": operational, "route_url": f"https://www.google.com/maps/dir/?api=1&destination={plat},{plon}", "rank": round(rank,2)})
    results.sort(key=lambda x: x["rank"], reverse=True)
    return results[:limit]

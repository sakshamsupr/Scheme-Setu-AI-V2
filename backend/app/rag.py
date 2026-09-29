from __future__ import annotations
from functools import lru_cache
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .data_store import scheme_records, normalize_scheme

@lru_cache(maxsize=1)
def _index():
    rows=[]
    texts=[]
    for raw in scheme_records():
        s=normalize_scheme(raw)
        text=" ".join([
            str(s.get("scheme_name","")), str(s.get("description","")), str(s.get("category","")),
            str(s.get("business_type","")), str(s.get("state","")), str(s.get("documents","")),
            str(s.get("scheme_type","")), str(s.get("interest_rate",""))
        ])
        rows.append(s); texts.append(text)
    vectorizer=TfidfVectorizer(ngram_range=(1,2), stop_words="english")
    matrix=vectorizer.fit_transform(texts)
    return vectorizer,matrix,rows

def retrieve(query: str, top_k: int = 5):
    vectorizer,matrix,rows=_index()
    q=vectorizer.transform([query])
    scores=cosine_similarity(q,matrix).ravel()
    order=scores.argsort()[::-1][:top_k]
    results=[]
    for i in order:
        if scores[i] <= 0: continue
        r=dict(rows[i]); r["retrieval_score"]=round(float(scores[i]),4); results.append(r)
    return results

def build_context(results):
    blocks=[]
    for r in results:
        blocks.append(
            f"SCHEME: {r['scheme_name']}\n"
            f"DESCRIPTION: {r.get('description','')}\n"
            f"ELIGIBILITY: category={r.get('category','')}; gender={r.get('gender','')}; age={r.get('min_age','')}-{r.get('max_age','')}; business={r.get('business_type','')}; state={r.get('state','')}\n"
            f"FINANCE: loan={r.get('min_loan_inr','')}-{r.get('max_loan_inr','')}; subsidy={r.get('max_subsidy_pct','')}%; interest={r.get('interest_rate','')}; tenure={r.get('tenure_years','')} years\n"
            f"DOCUMENTS: {r.get('documents','')}\n"
            f"SOURCE: {r.get('apply_link','')}"
        )
    return "\n\n---\n\n".join(blocks)

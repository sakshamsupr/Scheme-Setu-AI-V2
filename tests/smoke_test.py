import sys
sys.path.insert(0,'.')
from backend.app.main import app
from backend.app.data_store import scheme_records, partner_records, match_schemes

def main():
    assert len(scheme_records()) >= 1
    assert len(partner_records()) >= 1
    profile={"age":25,"gender":"Female","category":"SC","state":"Uttar Pradesh","district":"Ghaziabad","business_type":"Manufacturing","loan_amount":500000}
    results=match_schemes(profile,20)
    assert results
    print(f"smoke ok: {len(scheme_records())} schemes, {len(partner_records())} partners, {len(results)} matches")

if __name__ == '__main__': main()

import sys
sys.path.insert(0, '.')
from backend.app.ai import chat, detect_intent, extract_profile_patch

def assert_case():
    assert detect_intent('hi') == 'greeting'
    assert 'retrieved' in chat('hi', {}, [], 'en-IN')

    msg = 'Meri age 25 hai, main female hu, SC category se hu aur UP me manufacturing business start karna chahti hu'
    patch = extract_profile_patch(msg)
    assert patch == {
        'age': 25,
        'gender': 'Female',
        'category': 'SC',
        'state': 'Uttar Pradesh',
        'business_type': 'Manufacturing',
    }
    result = chat(msg, {}, [], 'hi-IN')
    assert result['intent'] == 'update_profile'
    assert result['profile_patch']['age'] == 25

    result = chat('mere liye schemes batao', {
        'age': 25, 'gender': 'Female', 'category': 'SC', 'state': 'Uttar Pradesh',
        'business_type': 'Manufacturing', 'loan_amount': 500000,
    }, [], 'hi-IN')
    assert result['intent'] == 'find_schemes'
    assert result['actions'] and result['actions'][0]['target'] == '/schemes'

    result = chat('500000 ka EMI batao', {'loan_amount': 500000}, [], 'en-IN')
    assert result['intent'] == 'calculate_loan'
    assert 'EMI' in result['answer']

    assert detect_intent('eligibility gap batao') == 'eligibility_gap'
    assert detect_intent('application roadmap dikhao') == 'roadmap'
    assert detect_intent('compare these schemes') == 'compare_schemes'

if __name__ == '__main__':
    assert_case()
    print('Copilot tests passed.')

def assert_multiturn_request_history():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client=TestClient(app)
    profile={'age':25,'gender':'Female','category':'SC','state':'Uttar Pradesh','business_type':'Manufacturing','loan_amount':500000}
    first=client.post('/copilot',json={'message':'I want to check my schemes','profile':profile,'history':[],'language':'en-IN'})
    assert first.status_code==200
    payload=first.json()
    rich={'role':'assistant','content':payload['answer'],'actions':payload.get('actions',[]),'retrieved':payload.get('retrieved',[])}
    second=client.post('/copilot',json={'message':'h','profile':profile,'history':[rich],'language':'en-IN'})
    assert second.status_code==200
    p300=client.post('/nearby-partners',json={'latitude':28.67,'longitude':77.45,'scheme_name':'','max_distance_km':300})
    assert p300.status_code==200

if __name__ == '__main__':
    assert_multiturn_request_history()

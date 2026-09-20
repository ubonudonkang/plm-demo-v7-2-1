import json
import os
import urllib.request

base=os.getenv('PLM_BASE_URL','http://127.0.0.1:8000')
def call(path, method='GET', data=None):
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(base+path, data=body, method=method, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

health=call('/api/health')
modules=call('/api/modules/bootstrap')
products=call('/api/v2/products')
templates=call('/api/v2/templates')
requests=call('/api/v2/requests')
users=call('/api/v2/users')
assert health['status']=='ok'
assert len(modules['modules'])>=10
assert isinstance(products['items'], list)
assert isinstance(templates['items'], list)
assert isinstance(requests['items'], list)
assert isinstance(users['items'], list)
print('PASS', {
    'modules':len(modules['modules']),
    'products':len(products['items']),
    'templates':len(templates['items']),
    'requests':len(requests['items']),
    'users':len(users['items'])
})

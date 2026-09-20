import json
import sys
import urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

def get(path):
    with urllib.request.urlopen(base + path) as r:
        return json.load(r)

health = get('/api/health')
assert health['status'] == 'ok'
products = get('/api/products')
requests = get('/api/requests')
users = get('/api/users')
assert products, 'No products returned'
assert requests, 'No requests returned'
assert users, 'No users returned'
print(f"PASS health={health['database']} products={len(products)} requests={len(requests)} users={len(users)}")

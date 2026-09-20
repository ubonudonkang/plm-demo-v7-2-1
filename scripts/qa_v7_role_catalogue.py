from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import TEST_ROLE_BLUEPRINTS, TEST_ROLE_MODULES

ALIASES={
    'Finance':'Finance / Tax','Finance/Tax':'Finance / Tax','Technology':'Technology Approver',
    'Regulatory':'Regulatory / Legal','Legal / Regulatory':'Regulatory / Legal','CAB':'CAB / Change Manager',
    'Records / Governance':'Records Manager','Compliance':'Compliance Officer','Release / Test Analyst':'Test Analyst',
    'Approver':'Business Assurance'
}
def norm(v:str)->str:return ALIASES.get(str(v or '').strip(),str(v or '').strip())

expected=[x['name'] for x in TEST_ROLE_BLUEPRINTS]
assert len(expected)==21 and len(set(expected))==21, expected
assert set(expected)==set(TEST_ROLE_MODULES), (set(expected)-set(TEST_ROLE_MODULES),set(TEST_ROLE_MODULES)-set(expected))

con=sqlite3.connect(ROOT/'data'/'plm_demo.db')
admin=json.loads(con.execute("select data_json from module_state where module_name='administration'").fetchone()[0])
requests=json.loads(con.execute("select data_json from module_state where module_name='requests'").fetchone()[0])
con.close()
cfg=admin['adminConfigV31']
roles=cfg.get('roles',[])
role_names=[r['name'] for r in roles]
assert set(role_names)==set(expected), (set(expected)-set(role_names),set(role_names)-set(expected))
assert cfg.get('testModeRoleModelVersion')=='7.0'
assert cfg.get('roleScopeVersion')=='7.0'
for role in roles:
    assert role.get('modules')==TEST_ROLE_MODULES[role['name']], (role['name'],role.get('modules'),TEST_ROLE_MODULES[role['name']])

users=admin.get('users',[])
mut=next(u for u in users if u.get('name')=='Mutolib Ottan')
chi=next(u for u in users if u.get('name')=='Chiamaka Eleodi')
assert set(mut.get('roles',[]))==set(expected) and len(mut.get('roles',[]))==21
assert chi.get('roles')==['Product Manager'] and chi.get('role')=='Product Manager'

route_refs=[]
for r in cfg.get('approvalRoutes',[]):
    route_refs.extend(r.get('business',[])); route_refs.extend(r.get('production',[])); route_refs.append(r.get('uat'))
unresolved_routes=sorted({x for x in route_refs if x and norm(x) not in expected})
assert not unresolved_routes, unresolved_routes

approval_refs=[a.get('role') for r in requests.get('requests',[]) for a in r.get('approvals',[]) if a.get('role')]
unresolved_approvals=sorted({x for x in approval_refs if norm(x) not in expected})
assert not unresolved_approvals, unresolved_approvals

print(json.dumps({
    'PASS':True,'roles':len(expected),'mutolib_roles':len(mut['roles']),
    'chiamaka':'Product Manager','approval_route_refs':len(route_refs),
    'request_approval_role_names':sorted(set(approval_refs)),
    'legacy_aliases_resolved':sorted({x for x in approval_refs if x!=norm(x)})
},indent=2))

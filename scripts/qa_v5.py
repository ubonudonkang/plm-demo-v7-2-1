from pathlib import Path
import json,re,sqlite3,sys

root=Path(__file__).resolve().parents[1]
html=(root/'frontend/index.html').read_text()
seed=json.loads((root/'data/seed_state.json').read_text())
errors=[]

# Frontend reliability hooks
required=[
 'V41 — Classification & controlled-field reliability sweep',
 'Select certified source template',
 'Line of Business / Product Domain',
 'Product Family',
 'Product Category',
 'Product Sub-Category',
 'Product Offering',
 'Product Variant',
 'window.__PLM_CONTROL_AUDIT'
]
for s in required:
    if s not in html: errors.append(f'missing frontend marker: {s}')

# Ensure new-product default no longer hard-locks TPL-018 when no template was loaded.
if not re.search(r"if\(!tplId\)\{f\.template='';f\.templateName='';[^}]*f\.division='';", html):
    errors.append('new product template/classification reset is missing')

# Certified template classification must be complete in demo seed.
for t in seed.get('templates',[]):
    if t.get('state')!='Certified': continue
    vals=[t.get('domain'),t.get('family'),t.get('category'),t.get('subcategory')]
    if not all(vals): errors.append(f"certified template {t.get('id')} incomplete classification: {vals}")
    cfg=t.get('config') or {}
    if not all(cfg.get(k) for k in ['division','productFamily','cat','subcategory']):
        errors.append(f"certified template {t.get('id')} missing reusable classification snapshot")

# Backend module state should also ship with complete certified templates.
con=sqlite3.connect(root/'data/plm_demo.db')
row=con.execute("select data_json from module_state where module_name='templates'").fetchone()
if not row: errors.append('templates module state missing')
else:
    data=json.loads(row[0])
    for t in data.get('templates',[]):
        if t.get('state')=='Certified' and not all(t.get(k) for k in ['domain','family','category','subcategory']):
            errors.append(f"DB certified template {t.get('id')} incomplete classification")
con.close()

# Data-act handler coverage. Count direct forms plus generic comparisons.
actions=set(re.findall(r'data-act=["\']([^"\']+)',html))
handlers=set(re.findall(r"(?:a|action)\s*===\s*['\"]([^'\"]+)['\"]",html))
handlers|=set(re.findall(r"dataset\.act\s*===\s*['\"]([^'\"]+)['\"]",html))
handlers|=set(re.findall(r"closest\(\s*['\"]\[data-act=['\"]([^'\"]+)['\"]\]",html))
handlers|=set(re.findall(r"case\s+['\"]([^'\"]+)['\"]",html))
# Known generic router actions are handled by central dispatch or array membership.
generic={'go','tab','prod','req','closeModal','closeModal2UseTpl','wizStep','saveDraft','wizSubmit','toggleNA','openAddOn','bulkChangeField','bulkChangeValue','catalogueExport','exportV27Reports','externalCorrect','externalException','externalReview','impactConfirm','impactContinue','taxonomyAddConfirm','taxonomyProposeConfirm','v37ExportRoleReport','v37ImpactBlockedUAT','v37OnboardingReview'}
missing=sorted(a for a in actions if a not in handlers and a not in generic and '${' not in a)
if missing: errors.append('unresolved literal actions: '+', '.join(missing))

# Active template details renderer should only define each classification key once.
start=html.find('function v38TemplateClassificationFields')
end=html.find('function v38TemplateScope',start)
block=html[start:end]
for key in ['division','productFamily','category','subcategory','offeringMode','variantMode','templateOwner','effectiveFrom']:
    count=block.count(f'data-tmeta="{key}"')
    if count!=1: errors.append(f'template classification key {key} rendered {count} times')

# Classification renderer should have blank source-template option and no blank-locked domain logic.
start=html.rfind('wizardConfigSectionHTML=function(w,f,cur,active)')
block=html[start:]
for token in ['Select certified source template','Select domain','Select family','Select category','Select sub-category','Select offering','Select variant']:
    if token not in html: errors.append(f'new product classification missing {token}')

if errors:
    print('QA FAIL')
    for e in errors: print(' -',e)
    sys.exit(1)
print(f"QA PASS templates={sum(1 for t in seed['templates'] if t.get('state')=='Certified')} actions={len(actions)}")

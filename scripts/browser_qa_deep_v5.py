import asyncio,pathlib,json,re
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')

async def audit(page,label):
    bad=await page.evaluate('''() => [...document.querySelectorAll('select:not([disabled])')].map(e=>({name:e.dataset.f||e.dataset.tmeta||e.id||e.name||'select', value:e.value, opts:[...e.options].filter(o=>!o.disabled && String(o.value||'').trim()).map(o=>o.value)})).filter(x=>x.opts.length===0)''')
    if bad: raise AssertionError(f'{label}: empty enabled selects {bad}')
    for attr in ['data-f','data-tmeta']:
      dup=await page.evaluate('''(attr)=>{const m={};document.querySelectorAll(`[${attr}]`).forEach(e=>{if(e.offsetParent===null)return;const k=e.getAttribute(attr);if(!k)return;m[k]=(m[k]||0)+1});return Object.entries(m).filter(x=>x[1]>1)}''',attr)
      if dup: raise AssertionError(f'{label}: duplicate {attr}: {dup}')

async def auth(page,idx,role):
    await page.evaluate('''([idx,role])=>{AUTH.account=ACCOUNTS[idx];AUTH.stage='authed';state.role=role;renderAuth();}''',[idx,role]); await page.wait_for_timeout(20)

async def close_modal(page):
    if await page.locator('#modalOverlay:not(.hidden), .modal-overlay:not(.hidden)').count():
      try: await page.evaluate('closeModal()')
      except: pass
      await page.wait_for_timeout(10)
    else:
      try: await page.evaluate('closeModal()')
      except: pass

async def click_action(page,action,label):
    loc=page.locator(f'[data-act="{action}"]:visible').first
    if await loc.count()==0: return False
    await loc.click(); await page.wait_for_timeout(30); await audit(page,label); await close_modal(page); return True

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1500,'height':1050}); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
  await page.set_content(HTML,wait_until='domcontentloaded'); await page.wait_for_timeout(100)

  # Product owner
  await auth(page,0,'po')
  tids=await page.evaluate("DATA.templates.filter(t=>t.state==='Certified').map(t=>t.id)")
  for tid in tids:
    await page.evaluate("go('requests');startWizard('create')"); await page.wait_for_timeout(20)
    await page.select_option('[data-f="template"]',tid); await page.dispatch_event('[data-f="template"]','change'); await page.wait_for_timeout(40)
    # choose offering/variant if available
    off=page.locator('[data-f="offering"]')
    if await off.count() and not await off.is_disabled():
      vals=await off.locator('option').evaluate_all("els=>els.map(o=>o.value).filter(Boolean)")
      if vals:
        await off.select_option(vals[0]); await off.dispatch_event('change'); await page.wait_for_timeout(20)
    var=page.locator('[data-f="variant"]')
    if await var.count() and not await var.is_disabled():
      vals=await var.locator('option').evaluate_all("els=>els.map(o=>o.value).filter(Boolean)")
      if vals: await var.select_option(vals[0]); await var.dispatch_event('change'); await page.wait_for_timeout(20)
    sections=await page.evaluate("requestConfigSections(state.wizard).map(x=>x[0])")
    for sec in sections:
      await page.evaluate('(s)=>{state.wizard.section=s;render()}',sec); await page.wait_for_timeout(20); await audit(page,f'{tid} section {sec}')
  print('wizard sections pass')

  # Template creation representative configurations and all tabs
  reps=[
    ('Marketing','Voice','Tariff Plans','Prepaid',None,None),
    ('Marketing','Data','Data Bundles','Commercial Plans','dataProductType','Standard Data Bundle'),
    ('Enterprise Business','Enterprise Mobile','Tariff Plans','Enterprise Plans','enterprisePlanType','CUG Standard'),
    ('Enterprise Business','Data & IoT','Data Bundles','Business Plans','dataProductType','IoT Per-SIM Bundle'),
    ('Marketing','Loans','Loan Services','Loan Products',None,None),
  ]
  for dom,fam,cat,sub,typekey,typeval in reps:
    await page.evaluate("state.templateDraft=null;ensureTemplateDraft();go('templates','create')"); await page.wait_for_timeout(20)
    for key,val in [('division',dom),('productFamily',fam),('category',cat),('subcategory',sub)]:
      loc=page.locator(f'[data-tmeta="{key}"]')
      if not await loc.count(): raise AssertionError(f'template missing {key} for {dom}/{fam}')
      await loc.select_option(val); await loc.dispatch_event('change'); await page.wait_for_timeout(30)
    if typekey:
      await page.evaluate('([k,v])=>{state.templateDraft.fields[k]=v;render()}',[typekey,typeval]); await page.wait_for_timeout(30)
    tabs=await page.locator('[data-act="templateSection"]:visible').evaluate_all("els=>els.map(e=>e.dataset.section)")
    for sec in tabs:
      await page.evaluate('(s)=>{state.templateDraft.section=s;render()}',sec); await page.wait_for_timeout(20); await audit(page,f'template {dom}/{fam}/{sec}')
  print('template sections pass')

  # Add-on modal types
  await page.evaluate("go('requests');startWizard('create')"); await page.wait_for_timeout(20)
  await page.select_option('[data-f="template"]','TPL-022'); await page.dispatch_event('[data-f="template"]','change'); await page.wait_for_timeout(30)
  await page.evaluate("openAddOnModal('wizard',-1)"); await page.wait_for_timeout(30); await audit(page,'addon initial')
  types=await page.locator('#ao-type option').evaluate_all("els=>els.map(o=>o.value||o.textContent).filter(Boolean)")
  for typ in types:
    await page.select_option('#ao-type',typ); await page.dispatch_event('#ao-type','change'); await page.wait_for_timeout(20); await audit(page,f'addon {typ}')
  await close_modal(page); print('addon pass',types)

  # Admin pages and modals
  await auth(page,4,'admin')
  admin_actions={
    'taxonomy':['v37TaxAdd','v37TaxEdit'],
    'rules':['v37RiskEdit','v39RuleAdd','v39RuleEdit'],
    'access':['v37AccessCampaignAdd','adm33DelegationAdd','v37RoleAdd','v37UserAdd','adm33UserView','v37UserEdit','v37EmergencyAccess','v37RoleEdit'],
    'lifecycle':['v37TransitionAdd','v37TransitionEdit','v37ApprovalStageEdit'],
    'systems':['v37SystemAdd','v37SystemEdit'],
    'notifications':['v37NotifGovAdd','v37NotifGovEdit'],
  }
  for tab,acts in admin_actions.items():
    await page.evaluate('(t)=>go("admin",null,t)',tab); await page.wait_for_timeout(20); await audit(page,f'admin {tab}')
    for act in acts:
      await page.evaluate('(t)=>go("admin",null,t)',tab); await page.wait_for_timeout(15)
      ok=await click_action(page,act,f'admin {tab} modal {act}')
      if not ok: print('skip action',tab,act)
  print('admin modals pass')

  # Testing queue and release workspaces under Test Analyst
  await auth(page,3,'test'); await page.evaluate("go('testing')"); await page.wait_for_timeout(20); await audit(page,'testing queue')
  reqs=await page.evaluate("Object.keys(DATA.releasePipeline||{})")
  for rid in reqs[:4]:
    await page.evaluate('(r)=>go("testing",r)',rid); await page.wait_for_timeout(20); await audit(page,f'testing {rid}')
  print('testing pass')

  # Product owner other main modules and detail screens
  await auth(page,0,'po')
  for route in ['catalogue','requests','retirement','recon','exceptions','audit','reports','templates']:
    await page.evaluate('(r)=>go(r)',route); await page.wait_for_timeout(20); await audit(page,route)
  pids=await page.evaluate("DATA.products.slice(0,5).map(p=>p.id)")
  for pid in pids:
    await page.evaluate('(id)=>go("catalogue",id)',pid); await page.wait_for_timeout(20); await audit(page,f'product {pid}')
  # request detail all requests duplicate critical headings
  rids=await page.evaluate("DATA.requests.map(r=>r.id)")
  for rid in rids:
    await page.evaluate('(id)=>go("requests",id)',rid); await page.wait_for_timeout(15); await audit(page,f'request {rid}')
    hs=[x.strip() for x in await page.locator('h3:visible').all_text_contents() if x.strip()]
    critical={'Impact Analysis','Impact Assessment Reviews','Request Control','Summary','Approval route','Control gates'}
    d=[x for x in set(hs) if x in critical and hs.count(x)>1]
    if d: raise AssertionError(f'{rid}: duplicate critical headings {d}')
  print('module/details pass')

  # classification control audit should have no enabled-empty controls on current page and taxonomy integrity no dup/malformed
  tax=await page.evaluate('''() => {v41RepairClassificationModel();const a=adm31Cfg().taxonomy||[],seen=new Set();let bad=0,dups=0;for(const n of a){if(typeof n.name!=='string'||!n.name.trim())bad++;const k=[n.level,n.parentId||'',n.name].join('::');if(seen.has(k))dups++;seen.add(k);}return {bad,dups,count:a.length}}''')
  if tax['bad'] or tax['dups']: raise AssertionError(f'tax integrity {tax}')
  if errors: raise AssertionError('page errors '+repr(errors))
  print(json.dumps({'PASS':True,'templates':len(tids),'releasePipelines':len(reqs),'requests':len(rids),'products_tested':len(pids),'taxonomy':tax},indent=2))
  await browser.close()
asyncio.run(main())

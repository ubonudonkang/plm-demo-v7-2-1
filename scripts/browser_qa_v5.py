import asyncio, pathlib, json, sys
from collections import Counter
from playwright.async_api import async_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')

async def audit_enabled_selects(page,label):
    bad=await page.evaluate('''() => [...document.querySelectorAll('select:not([disabled])')].map(e=>({name:e.dataset.f||e.dataset.tmeta||e.id||e.name||e.getAttribute('aria-label')||'select', opts:[...e.options].filter(o=>!o.disabled && String(o.value||o.textContent||'').trim()).map(o=>String(o.value||o.textContent||'').trim()), value:e.value})).filter(x=>x.opts.length===0)''')
    if bad:
        raise AssertionError(f'{label}: enabled selects with no usable options: {bad}')

async def assert_no_duplicate_bindings(page,label,attr):
    dup=await page.evaluate('''(attr) => {const m={};document.querySelectorAll(`[${attr}]`).forEach(e=>{if(e.offsetParent===null)return;const k=e.getAttribute(attr);m[k]=(m[k]||0)+1});return Object.entries(m).filter(([k,n])=>k&&n>1)}''',attr)
    if dup:
        raise AssertionError(f'{label}: duplicate visible {attr} controls: {dup}')

async def auth(page,idx,role):
    await page.evaluate('''([idx,role])=>{AUTH.account=ACCOUNTS[idx];AUTH.stage='authed';state.role=role;renderAuth();}''',[idx,role])
    await page.wait_for_timeout(30)

async def main():
  async with async_playwright() as p:
    browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=await browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    await page.set_content(HTML,wait_until='domcontentloaded',timeout=30000)
    await page.wait_for_timeout(100)

    # PRODUCT OWNER: New Product classification cascade
    await auth(page,0,'po')
    await page.evaluate("go('requests');startWizard('create');")
    await page.wait_for_timeout(40)
    initial=await page.evaluate('''() => {const e=document.querySelector('[data-f="template"]');return {template:e&&{value:e.value,disabled:e.disabled,opts:[...e.options].filter(o=>o.value).length},classification:[...document.querySelectorAll('[data-f="division"],[data-f="productFamily"],[data-f="cat"],[data-f="subcategory"],[data-f="offering"],[data-f="variant"]')].length}}''')
    assert initial['template']['value']=='' and not initial['template']['disabled'] and initial['template']['opts']>0
    assert initial['classification']==0, f'classification fields should not render before source-template selection: {initial}'
    await audit_enabled_selects(page,'new product initial')

    # Every certified template must load complete classification and a usable offering/variant cascade.
    tids=await page.evaluate("DATA.templates.filter(t=>t.state==='Certified').map(t=>t.id)")
    for tid in tids:
        await page.evaluate("startWizard('create')")
        await page.wait_for_timeout(20)
        await page.select_option('[data-f="template"]',tid)
        await page.dispatch_event('[data-f="template"]','change')
        await page.wait_for_timeout(50)
        vals=await page.evaluate('''() => Object.fromEntries(['division','productFamily','cat','subcategory'].map(k=>{const e=document.querySelector(`[data-f="${k}"]`);return [k,e&&{v:e.value,d:e.disabled}]}))''')
        for k,x in vals.items():
            assert x and x['v'], f'{tid}: {k} not populated'
            assert x['d'], f'{tid}: inherited {k} should be locked'
        offers=await page.locator('[data-f="offering"] option').evaluate_all("els=>els.map(x=>x.value).filter(Boolean)")
        assert offers, f'{tid}: no offering choices'
        await page.select_option('[data-f="offering"]',offers[0])
        await page.dispatch_event('[data-f="offering"]','change')
        await page.wait_for_timeout(30)
        variants=await page.locator('[data-f="variant"] option').evaluate_all("els=>els.map(x=>x.value).filter(Boolean)")
        assert variants, f'{tid}: no variant choices after offering selection'
        await audit_enabled_selects(page,f'new product {tid}')
        await assert_no_duplicate_bindings(page,f'new product {tid}','data-f')

    # Canonical hierarchy must not leak Enterprise sub-categories into Consumer classification or vice versa.
    hierarchy=await page.evaluate('''() => {v41RepairClassificationModel();const rows=adm31Cfg().taxonomy;const find=(lvl,name,parent='')=>rows.find(n=>n.level===lvl&&n.name===name&&(parent===''||n.parentId===parent));const dM=find('Domain','Marketing'),fV=find('Family','Voice',dM&&dM.id),cT=find('Category','Tariff Plans',fV&&fV.id);const dE=find('Domain','Enterprise Business'),fEM=find('Family','Enterprise Mobile',dE&&dE.id),cET=find('Category','Tariff Plans',fEM&&fEM.id);return {marketing:(rows.filter(n=>n.level==='Sub-Category'&&n.parentId===(cT&&cT.id)).map(n=>n.name)),enterprise:(rows.filter(n=>n.level==='Sub-Category'&&n.parentId===(cET&&cET.id)).map(n=>n.name))};}''')
    assert 'Enterprise Plans' not in hierarchy['marketing'], hierarchy
    assert 'Prepaid' not in hierarchy['enterprise'] and 'Postpaid' not in hierarchy['enterprise'], hierarchy

    # TEMPLATE CREATION: deliberately blank cascade; then full cascade.
    await page.evaluate("state.templateDraft=null;ensureTemplateDraft();go('templates','create');")
    await page.wait_for_timeout(50)
    tinit=await page.evaluate('''() => Object.fromEntries(['division','productFamily','category','subcategory','offeringMode','variantMode'].map(k=>{const e=document.querySelector(`[data-tmeta="${k}"]`);return [k,e&&{v:e.value,d:e.disabled,opts:[...e.options].filter(o=>o.value).length}]}))''')
    assert tinit['division']['v']=='' and not tinit['division']['d']
    for k in ('productFamily','category','subcategory','offeringMode','variantMode'):
        assert tinit[k]['d'], f'template {k} should wait for parent: {tinit[k]}'
    await assert_no_duplicate_bindings(page,'template creation initial','data-tmeta')
    for k,v in [('division','Marketing'),('productFamily','Data'),('category','Data Bundles'),('subcategory','Commercial Plans')]:
        await page.select_option(f'[data-tmeta="{k}"]',v)
        await page.dispatch_event(f'[data-tmeta="{k}"]','change')
        await page.wait_for_timeout(40)
    om=page.locator('[data-tmeta="offeringMode"]')
    assert not await om.is_disabled(), 'Offering applicability must enable after sub-category'
    await audit_enabled_selects(page,'template creation classified')
    await assert_no_duplicate_bindings(page,'template creation classified','data-tmeta')

    # Request detail should not contain duplicate section headings/cards.
    rid=await page.evaluate("DATA.requests[0].id")
    await page.evaluate('(rid)=>go("requests",rid)',rid)
    await page.wait_for_timeout(30)
    hs=[x.strip() for x in await page.locator('h3').all_text_contents() if x.strip()]
    dup=[(k,n) for k,n in Counter(hs).items() if n>1 and k in {'Impact Analysis','Impact Assessment Reviews','Request Control','Summary','Approval route','Control gates'}]
    assert not dup, f'request details duplicate sections: {dup}'

    # Modify/Clone render without broken controlled fields.
    pid=await page.evaluate("DATA.products.find(p=>p.current)?.id || DATA.products[0].id")
    for typ in ('modify','clone'):
        await page.evaluate('([typ,pid])=>{go("requests");startWizard(typ,pid)}',[typ,pid])
        await page.wait_for_timeout(30)
        await audit_enabled_selects(page,f'{typ} wizard')

    # ADMIN: every major configuration tab must render without empty enabled selects.
    await auth(page,4,'admin')
    for tab in ('taxonomy','rules','access','lifecycle','systems','notifications','governance'):
        await page.evaluate('(tab)=>go("admin",null,tab)',tab)
        await page.wait_for_timeout(30)
        await audit_enabled_selects(page,f'admin {tab}')

    # TEST ANALYST: Testing & Release queue/workspace and test controls.
    await auth(page,3,'test')
    await page.evaluate("go('testing')")
    await page.wait_for_timeout(30)
    await audit_enabled_selects(page,'testing queue')
    req=await page.evaluate("Object.keys(DATA.releasePipeline||{})[0]||''")
    if req:
        await page.evaluate('(req)=>go("testing",req)',req)
        await page.wait_for_timeout(30)
        await audit_enabled_selects(page,'testing workspace')

    # PRODUCT OWNER: Retirement and catalogue.
    await auth(page,0,'po')
    for route in ('catalogue','retirement','recon','exceptions','audit','reports'):
        await page.evaluate('(r)=>go(r)',route)
        await page.wait_for_timeout(30)
        await audit_enabled_selects(page,route)

    # Core taxonomy should be clean after repeated renders.
    tax=await page.evaluate('''() => {const a=adm31Cfg().taxonomy||[],seen=new Set();let bad=0,dups=0;for(const n of a){if(typeof n.name!=='string'||!n.name.trim())bad++;const k=[n.level,n.parentId||'',n.name].join('::');if(seen.has(k))dups++;seen.add(k);}return {bad,dups,count:a.length}}''')
    assert tax['bad']==0 and tax['dups']==0, f'taxonomy integrity: {tax}'

    if errors:
        raise AssertionError('Browser page errors: '+repr(errors))
    print(json.dumps({'status':'PASS','certified_templates':len(tids),'taxonomy_nodes':tax['count'],'request_id':rid,'product_id':pid,'page_errors':0},indent=2))
    await browser.close()

if __name__=='__main__':
    asyncio.run(main())

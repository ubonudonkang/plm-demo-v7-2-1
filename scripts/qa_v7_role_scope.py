import asyncio, json, pathlib
from playwright.async_api import async_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
EXPECTED={
  'Product Manager':['dashboard','catalogue','templates','requests','workflow','testing','recon','exceptions','retirement','reports','audit'],
  'Product Owner':['dashboard','catalogue','templates','requests','workflow','testing','recon','exceptions','retirement','reports','audit'],
  'Pricing / MKT BI':['dashboard','catalogue','requests','workflow','reports','audit'],
  'Finance / Tax':['dashboard','catalogue','requests','workflow','reports','audit'],
  'Business Assurance':['dashboard','catalogue','requests','workflow','testing','recon','exceptions','retirement','reports','audit'],
  'Customer Experience':['dashboard','catalogue','requests','workflow','reports','audit'],
  'Technology Approver':['dashboard','catalogue','requests','workflow','testing','recon','reports','audit'],
  'Technical Owner':['dashboard','catalogue','requests','workflow','testing','recon','exceptions','retirement','reports','audit'],
  'Regulatory / Legal':['dashboard','catalogue','requests','workflow','exceptions','retirement','reports','audit'],
  'Executive Sponsor':['dashboard','requests','workflow','reports','audit'],
  'CAB / Change Manager':['dashboard','requests','workflow','testing','reports','audit'],
  'Test Analyst':['dashboard','catalogue','requests','testing','reports','audit'],
  'Release Manager':['dashboard','catalogue','requests','workflow','testing','recon','exceptions','reports','audit'],
  'Reconciliation & Monitoring Analyst':['dashboard','catalogue','requests','testing','recon','exceptions','reports','audit'],
  'Exception & Rollback Manager':['dashboard','catalogue','requests','testing','recon','exceptions','reports','audit'],
  'Product Governance':['dashboard','catalogue','requests','workflow','exceptions','retirement','reports','audit'],
  'Records Manager':['dashboard','catalogue','retirement','reports','audit'],
  'Compliance Officer':['dashboard','catalogue','requests','workflow','exceptions','retirement','reports','audit'],
  'Audit & Compliance Reviewer':['dashboard','catalogue','requests','workflow','testing','recon','exceptions','retirement','reports','audit'],
  'Product Classification Administrator':['dashboard','catalogue','reports','audit','admin'],
  'Platform Administrator':['dashboard','catalogue','templates','requests','workflow','testing','recon','exceptions','retirement','reports','audit','admin'],
}

async def sign_in(page,name='Mutolib Ottan'):
    await page.evaluate('''(name)=>{ensureUserDirectoryV33();const u=DATA.users.find(x=>x.name===name);AUTH.account={dynamic:true,userId:u.id,name:u.name,email:u.email,title:u.title,initials:v33Initials(u.name)};AUTH.stage='authed';renderAuth();const role=v33SetRoleSelector(u);state.role=v33RoleCode(role.name);go('dashboard');}''',name)
    await page.wait_for_timeout(30)

async def choose_role(page,role):
    await page.select_option('#roleSel',label=role)
    await page.wait_for_timeout(25)

async def main():
  async with async_playwright() as p:
    browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=await browser.new_page(viewport={'width':1500,'height':1050})
    errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
    await page.set_content(HTML,wait_until='domcontentloaded'); await page.wait_for_timeout(120)
    await sign_in(page)

    # Every canonical role must expose exactly its v7 module scope without changing account.
    account=await page.evaluate('AUTH.account.name')
    for role,expected in EXPECTED.items():
      await choose_role(page,role)
      now=await page.evaluate('''()=>({account:AUTH.account.name,active:v7ActiveRoleName(),routes:[...document.querySelectorAll('#nav [data-route]')].map(x=>x.dataset.route),cfg:(v7RoleConfig()||{}).modules||[]})''')
      assert now['account']==account, (role,now)
      assert now['active']==role, (role,now)
      assert set(now['routes'])==set(expected), (role,now['routes'],expected)
      assert now['cfg']==expected, (role,now['cfg'],expected)

    # Direct navigation is protected as well as hidden navigation.
    await choose_role(page,'Test Analyst')
    await page.evaluate("go('admin')"); await page.wait_for_timeout(20)
    assert await page.evaluate('state.route')=='dashboard'

    # Active role survives user-directory refresh/edit of the current account.
    await choose_role(page,'Release Manager')
    before=await page.locator('#roleSel').input_value()
    await page.evaluate('''()=>{const u=v33CurrentUser();v33SetRoleSelector(u);}''')
    after=await page.locator('#roleSel').input_value()
    active=await page.evaluate('v7ActiveRoleName()')
    assert before==after and active=='Release Manager',(before,after,active)

    # Classification admin only sees taxonomy in Administration; Platform Admin sees the full admin set.
    await choose_role(page,'Product Classification Administrator')
    await page.evaluate("go('admin',null,'rules')"); await page.wait_for_timeout(30)
    assert await page.evaluate('state.route')=='admin' and await page.evaluate('state.tab')=='taxonomy'
    visible_tabs=await page.locator('.tabs [data-act="tab"]:visible').evaluate_all('els=>els.map(e=>e.dataset.tab)')
    assert visible_tabs==['taxonomy'],visible_tabs
    await choose_role(page,'Platform Administrator'); await page.evaluate("go('admin',null,'access')"); await page.wait_for_timeout(25)
    visible_tabs=await page.locator('.tabs [data-act="tab"]:visible').evaluate_all('els=>els.map(e=>e.dataset.tab)')
    assert set(visible_tabs)=={'governance','taxonomy','rules','access','lifecycle','systems','notifications'},visible_tabs

    # Create Template is Product role scoped, not merely any signed-in account.
    await choose_role(page,'Product Owner'); await page.evaluate("go('templates')"); await page.wait_for_timeout(25)
    assert await page.locator('[data-act="proposeTemplate"]:visible').count()==1
    await choose_role(page,'Pricing / MKT BI'); await page.evaluate("go('catalogue')"); await page.wait_for_timeout(15)
    assert 'templates' not in await page.locator('#nav [data-route]').evaluate_all('els=>els.map(e=>e.dataset.route)')

    # Request approval maps to the selected named role, not legacy BA/first-pending behavior.
    await choose_role(page,'Business Assurance')
    rid=await page.evaluate("DATA.requests.find(r=>r.status==='Pending Approval'&&(r.approvals||[]).some(a=>a.role==='Business Assurance'&&a.state==='Pending'))?.id")
    assert rid
    await page.evaluate('(rid)=>go("requests",rid)',rid); await page.wait_for_timeout(25)
    assert await page.locator('[data-act="approve"]:visible').count()==1
    await page.locator('[data-act="approve"]:visible').click(); await page.fill('#ap-comment','v7 role-correct approval test'); await page.locator('[data-act="doApprove"]:visible').click(); await page.wait_for_timeout(30)
    rows=await page.evaluate('''(rid)=>DATA.requests.find(r=>r.id===rid).approvals.map(a=>({role:a.role,state:a.state,decidedBy:a.decidedBy||null,decidedRole:a.decidedRole||null}))''',rid)
    ba=next(x for x in rows if x['role']=='Business Assurance'); cx=next(x for x in rows if x['role']=='Customer Experience')
    assert ba['state']=='Approved' and ba['decidedBy']=='Mutolib Ottan' and ba['decidedRole']=='Business Assurance',rows
    assert cx['state']=='Pending',rows

    # Customer Experience can now act on its own pending row on the same request.
    await choose_role(page,'Customer Experience'); await page.evaluate('(rid)=>go("requests",rid)',rid); await page.wait_for_timeout(25)
    assert await page.locator('[data-act="approve"]:visible').count()==1

    # Test controls are role-scoped; Release Manager must not inherit Test Analyst actions through a legacy code.
    pipeline=await page.evaluate("Object.keys(DATA.releasePipeline||{})[0]")
    await choose_role(page,'Test Analyst'); await page.evaluate('(r)=>{state.releaseRequest=r;go("testing","release","cases")}',pipeline); await page.wait_for_timeout(25)
    assert await page.locator('[data-act="addTestCase"]:visible').count()>=1
    await choose_role(page,'Release Manager'); await page.evaluate('(r)=>{state.releaseRequest=r;go("testing","release","cases")}',pipeline); await page.wait_for_timeout(25)
    assert await page.locator('[data-act="addTestCase"]:visible').count()==0

    # Reports must follow the selected named role, not the union of an all-role account.
    await choose_role(page,'Test Analyst'); await page.evaluate("go('reports')"); await page.wait_for_timeout(25)
    report_text=await page.locator('#main-content').inner_text()
    assert 'Test Analyst Dashboard' in report_text,report_text[:500]
    await choose_role(page,'Release Manager'); await page.evaluate("go('reports')"); await page.wait_for_timeout(25)
    report_text=await page.locator('#main-content').inner_text()
    assert 'Release Manager Dashboard' in report_text and 'Test Analyst Dashboard' not in report_text,report_text[:500]

    # New named operational roles must map to compatible legacy handlers without inheriting unrelated actions.
    await choose_role(page,'Exception & Rollback Manager')
    compat=await page.evaluate("()=>({code:state.role,rollback:v7ActionAllowed('confirmRollback'),release:v7ActionAllowed('v37DeployProduction'),admin:v7ActionAllowed('adm31RuleAdd')})")
    assert compat=={'code':'rel','rollback':True,'release':False,'admin':False},compat
    await choose_role(page,'Product Manager')
    compat=await page.evaluate("()=>({code:state.role,dependency:v7ActionAllowed('v37DependencySave'),launch:v7ActionAllowed('v37ScheduleLaunchSave'),admin:v7ActionAllowed('adm31RuleAdd')})")
    assert compat=={'code':'po','dependency':True,'launch':False,'admin':False},compat
    await choose_role(page,'Platform Administrator')
    compat=await page.evaluate("()=>({code:state.role,admin:v7ActionAllowed('adm31RuleAdd'),launch:v7ActionAllowed('v37ScheduleLaunchSave')})")
    assert compat=={'code':'admin','admin':True,'launch':False},compat

    # Chiamaka remains a Product Manager persona and can create templates.
    await sign_in(page,'Chiamaka Eleodi'); await page.evaluate("go('templates')"); await page.wait_for_timeout(25)
    assert await page.evaluate('v7ActiveRoleName()')=='Product Manager'
    assert await page.locator('[data-act="proposeTemplate"]:visible').count()==1

    if errors: raise AssertionError('page errors '+repr(errors))
    print(json.dumps({'PASS':True,'roles_scoped':len(EXPECTED),'route_guard':'PASS','active_role_preserved':'PASS','approval_role_binding':'PASS','template_scope':'PASS','test_release_separation':'PASS','reports_selected_role':'PASS','legacy_role_compatibility':'PASS','chiamaka':'PASS','page_errors':0},indent=2))
    await browser.close()

if __name__=='__main__': asyncio.run(main())

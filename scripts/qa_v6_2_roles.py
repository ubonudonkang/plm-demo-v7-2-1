import asyncio
import json
import pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
EXPECTED_ROLES = [
    'Product Manager','Product Owner','Pricing / MKT BI','Finance / Tax','Business Assurance',
    'Customer Experience','Technology Approver','Technical Owner','Regulatory / Legal','Executive Sponsor',
    'CAB / Change Manager','Test Analyst','Release Manager','Reconciliation & Monitoring Analyst',
    'Exception & Rollback Manager','Product Governance','Records Manager','Compliance Officer',
    'Audit & Compliance Reviewer','Product Classification Administrator','Platform Administrator'
]

async def sign_in_dynamic(page, name):
    await page.evaluate('''(name)=>{
      ensureUserDirectoryV33();
      const u=DATA.users.find(x=>x.name===name);if(!u)throw new Error('Missing user '+name);
      AUTH.account={dynamic:true,userId:u.id,name:u.name,email:u.email,title:u.title,initials:v33Initials(u.name)};
      AUTH.stage='authed';renderAuth();const role=v33SetRoleSelector(u);state.role=v33RoleCode(role.name);go('dashboard');
    }''', name)
    await page.wait_for_timeout(30)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        page = await browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.set_content(HTML, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(100)

        # Canonical role catalogue + Chiamaka persona.
        model = await page.evaluate('''() => ({
          roles: adm31Cfg().roles.filter(r=>r.status==='Active').map(r=>r.name),
          chiamaka: DATA.users.find(u=>u.name==='Chiamaka Eleodi'),
          sod: v33SodConflicts(['Product Owner','Test Analyst','Platform Administrator'])
        })''')
        missing=[r for r in EXPECTED_ROLES if r not in model['roles']]
        assert not missing, f'missing canonical roles: {missing}'
        assert model['chiamaka'] and model['chiamaka']['roles']==['Product Manager'], model['chiamaka']
        assert model['chiamaka']['accessStatus']=='Active'
        assert model['sod']==[], f'access assignment SoD still enforced: {model["sod"]}'
        refs=await page.evaluate('''()=>({routes:adm31Cfg().approvalRoutes,transitions:adm31Cfg().transitions,roleNames:adm31Cfg().roles.map(r=>r.name)})''')
        names=set(refs['roleNames'])
        for route in refs['routes']:
            for role in (route.get('business') or [])+(route.get('production') or [])+[route.get('uat')]:
                assert role in names, f'approval workflow references missing role: {role}'
        for transition in refs['transitions']:
            assert transition.get('role') in names, f'lifecycle transition references missing role: {transition}'

        # Product Owner Create Template must be an actual responsive click path.
        await sign_in_dynamic(page,'Uche Chiemejonam')
        await page.evaluate("go('templates')")
        await page.wait_for_timeout(30)
        btn=page.locator('[data-act="proposeTemplate"]')
        assert await btn.count()==1 and await btn.is_visible(), 'Create Template button missing for Product Owner'
        await btn.click()
        await page.wait_for_timeout(40)
        created=await page.evaluate('''()=>({route:state.route,sub:state.sub,draft:!!state.templateDraft,title:document.querySelector('#main-content h2')?.textContent||''})''')
        assert created['route']=='templates' and created['sub']=='create' and created['draft'], created
        assert 'Create' in created['title'] and 'Template' in created['title'], created

        # Multi-role role switching must keep the same authenticated account.
        await sign_in_dynamic(page,'Mutolib Ottan')
        opts=await page.locator('#roleSel option').all_text_contents()
        for r in EXPECTED_ROLES:
            assert r in opts, f'Mutolib test account missing role {r}'
        account_before=await page.evaluate('AUTH.account.name')
        for label,code in [('Test Analyst','test'),('Product Manager','po'),('Release Manager','rel'),('Platform Administrator','admin')]:
            await page.select_option('#roleSel',label=label)
            await page.wait_for_timeout(25)
            now=await page.evaluate('''()=>({account:AUTH.account.name,code:state.role,selected:roleSel.selectedOptions[0].text,stage:AUTH.stage,route:state.route})''')
            assert now['account']==account_before and now['stage']=='authed', now
            assert now['code']==code and now['selected']==label, now

        # Administration access changes are direct in test mode and support multiple roles.
        await page.select_option('#roleSel',label='Platform Administrator')
        await page.wait_for_timeout(25)
        await page.evaluate("go('admin',null,'access')")
        await page.wait_for_timeout(40)
        ch=await page.evaluate("DATA.users.find(u=>u.name==='Chiamaka Eleodi').id")
        await page.locator(f'[data-act="v37UserEdit"][data-id="{ch}"]').click()
        await page.wait_for_timeout(25)
        assert await page.locator('#modalRoot [data-act="adm33UserSave"]').count()==1, 'Access edit is still maker-checker gated'
        assert await page.locator('#modalRoot [data-act="v37UserSubmit"]').count()==0
        for role in ['Test Analyst','Platform Administrator']:
            cb=page.locator(f'input[name="adm33-user-role"][value="{role}"]')
            if not await cb.is_checked(): await cb.check()
        await page.locator('#modalRoot [data-act="adm33UserSave"]').click()
        await page.wait_for_timeout(40)
        assigned=await page.evaluate("DATA.users.find(u=>u.name==='Chiamaka Eleodi').roles")
        assert set(['Product Manager','Test Analyst','Platform Administrator']).issubset(assigned), assigned

        # Role configuration itself is direct in test mode too.
        await page.locator('[data-act="v37RoleEdit"]').first.click()
        await page.wait_for_timeout(25)
        assert await page.locator('#modalRoot [data-act="adm31RoleSave"]').count()==1
        assert await page.locator('#modalRoot [data-act="v37RoleSubmit"]').count()==0

        if errors:
            raise AssertionError('Browser page errors: '+repr(errors))
        print(json.dumps({'status':'PASS','canonical_roles':len(EXPECTED_ROLES),'role_switches':4,'create_template':'PASS','multi_role_assignment':'PASS','chiamaka':'PASS','page_errors':0},indent=2))
        await browser.close()

if __name__=='__main__':
    asyncio.run(main())

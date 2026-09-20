import asyncio, json, pathlib, sqlite3
from playwright.async_api import async_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
DB=ROOT/'data'/'plm_demo.db'

def persisted_admin():
    con=sqlite3.connect(DB)
    try:
        row=con.execute("select data_json from module_state where module_name='administration'").fetchone()
        return json.loads(row[0]) if row else {}
    finally:
        con.close()

async def main():
    admin=persisted_admin()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1500,'height':1050})
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        await page.set_content(HTML,wait_until='domcontentloaded'); await page.wait_for_timeout(120)

        # Use persisted Administration state, including approved price bands.
        await page.evaluate("""(admin)=>{Object.entries(admin).forEach(([k,v])=>DATA[k]=JSON.parse(JSON.stringify(v)));if(window.v42RepairApprovedPriceBands)v42RepairApprovedPriceBands();}""",admin)

        # A data request with Data price populated must not fail the legacy generic-price requirement.
        result=await page.evaluate("""()=>{
          const f=newWizardFields('TPL-022');
          Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',template:'TPL-022',templateMode:'existing',name:'QA 10 GB Bundle',serviceClass:'DATA_QA',eff:'2026-10-01',dataProductType:'Standard Data Bundle',dataPlanClass:'Monthly',dataVolume:'10 GB',dataPrice:'9000',dataValidity:'30 Days',channels:['USSD'],price:''});
          const v=validateWizard(f);
          const band=priceBandForProduct(f);
          return {errs:v.errs,warns:v.warns,band,priceAfter:f.price};
        }""")
        assert not any('Price is mandatory' in e for e in result['errs']), result
        assert result['band'] and result['band']['min'] <= 9000 <= result['band']['max'], result
        assert result['priceAfter']=='', result  # compatibility shim must not overwrite persisted request schema

        # Out-of-range Data price is checked against the approved band, proving dataPrice reaches the band validator.
        outside=await page.evaluate("""()=>{
          const f=newWizardFields('TPL-022');
          Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',template:'TPL-022',templateMode:'existing',name:'QA Expensive Bundle',serviceClass:'DATA_QA2',eff:'2026-10-01',dataProductType:'Standard Data Bundle',dataPlanClass:'Monthly',dataVolume:'10 GB',dataPrice:'30000',dataValidity:'30 Days',channels:['USSD'],price:''});
          return validateWizard(f).errs;
        }""")
        assert any('outside the approved range' in e for e in outside), outside

        # Render the Product Owner data-core form and verify clearer controls/labels.
        await page.evaluate("""()=>{
          AUTH.account={dynamic:true,name:'Uche Chiemejonam',email:'uche@mtn.com'};AUTH.stage='authed';state.role='po';
          const f=newWizardFields('TPL-022');Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',dataProductType:'Standard Data Bundle',template:'TPL-022',templateMode:'existing'});
          state.wizard={type:'create',step:2,target:null,fields:f,currentFields:null,section:'dataCore',errors:null};state.route='requests';state.sub=null;renderAuth();render();
        }""")
        await page.wait_for_timeout(60)
        main=page.locator('#main-content')
        txt=await main.inner_text()
        for label in ['Included voice minutes','YouTube night data allowance','Other bundled benefits','Data transfer / gifting']:
            assert label in txt, label
        qty_sel='[data-v45-qty="dataVolume"]' if await page.locator('[data-v45-qty="dataVolume"]').count() else '[data-v44-qty="dataVolume"]'
        unit_sel='[data-v45-unit="dataVolume"]' if await page.locator('[data-v45-unit="dataVolume"]').count() else '[data-v44-unit="dataVolume"]'
        assert await page.locator(qty_sel).count()==1
        unit=page.locator(unit_sel)
        assert await unit.evaluate("el=>[...el.options].map(o=>o.value)")==['MB','GB','TB']

        # Quantity + unit must persist as a single backward-compatible value.
        await page.locator(qty_sel).fill('25')
        await unit.select_option('GB')
        stored=await page.evaluate("state.wizard.fields.dataVolume")
        assert stored=='25 GB', stored

        # Transferability becomes structured instead of vague free text.
        await page.select_option('[data-f="dataTransferability"]','Conditional')
        await page.wait_for_timeout(30)
        assert await page.locator('[data-f="dataAdditionalInfo"]').count()==1

        if errors: raise AssertionError(errors)
        print(json.dumps({'PASS':True,'data_price_uses_approved_band':'PASS','out_of_band_rejected':'PASS','data_volume_unit_selector':['MB','GB','TB'],'clarified_fields':'PASS','transferability_structured':'PASS','page_errors':0},indent=2))
        await browser.close()

if __name__=='__main__': asyncio.run(main())

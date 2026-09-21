import asyncio, json, os, pathlib, sqlite3
from playwright.async_api import async_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
DB=ROOT/'data'/'plm_demo.db'

def persisted_admin():
    con=sqlite3.connect(DB)
    try:
        row=con.execute("select data_json,revision from module_state where module_name='administration'").fetchone()
        return (json.loads(row[0]), row[1]) if row else ({},0)
    finally:
        con.close()

async def main():
    admin,revision=persisted_admin()
    async with async_playwright() as p:
        launch={'headless':True,'channel':'msedge'} if os.name=='nt' else {'headless':True,'executable_path':'/usr/bin/chromium','args':['--no-sandbox','--disable-dev-shm-usage']}
        browser=await p.chromium.launch(**launch)
        page=await browser.new_page(viewport={'width':1500,'height':1100})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.set_content(HTML,wait_until='domcontentloaded')
        await page.wait_for_timeout(120)
        await page.evaluate("""(admin)=>{Object.entries(admin).forEach(([k,v])=>DATA[k]=JSON.parse(JSON.stringify(v)));if(window.v42RepairApprovedPriceBands)v42RepairApprovedPriceBands();}""",admin)

        # Approved Data Bundles band is consumed directly by dataPrice, not the legacy f.price alias.
        in_band=await page.evaluate("""()=>{
          const f=newWizardFields('TPL-022');
          Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',template:'TPL-022',templateMode:'existing',name:'QA 10 GB Bundle',serviceClass:'DATA_QA',eff:'2026-10-01',dataProductType:'Standard Data Bundle',dataPlanClass:'Monthly',dataVolume:'10 GB',dataPrice:'4000',dataValidity:'30',channels:['USSD'],price:''});
          const v=validateWizard(f), band=priceBandForProduct(f);
          return {errs:v.errs,warns:v.warns,band,priceAfter:f.price};
        }""")
        assert not any('Price is mandatory' in e for e in in_band['errs']), in_band
        assert not any('outside the approved range' in e for e in in_band['errs']), in_band
        assert in_band['band'] and in_band['band']['min'] <= 4000 <= in_band['band']['max'], in_band
        assert in_band['priceAfter']=='', in_band

        out_band=await page.evaluate("""()=>{
          const f=newWizardFields('TPL-022');
          Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',template:'TPL-022',templateMode:'existing',name:'QA Expensive Bundle',serviceClass:'DATA_QA2',eff:'2026-10-01',dataProductType:'Standard Data Bundle',dataPlanClass:'Monthly',dataVolume:'10 GB',dataPrice:'30000',dataValidity:'30',channels:['USSD'],price:''});
          return validateWizard(f).errs;
        }""")
        assert any('outside the approved range' in e for e in out_band), out_band

        # Product rule registry itself is authoritative after approval, even if baseline is stale/missing.
        registry=await page.evaluate("""()=>{
          const oldBase=JSON.parse(JSON.stringify(DATA.baseline||[]));
          const cfg=adm31Cfg(), oldRules=JSON.parse(JSON.stringify(cfg.productRules||[]));
          DATA.baseline=(DATA.baseline||[]).filter(x=>x.id!=='QA-APPROVED-BAND');
          cfg.productRules=(cfg.productRules||[]).filter(x=>x.id!=='QA-APPROVED-BAND');
          cfg.productRules.push({id:'QA-APPROVED-BAND',group:'Product validation',name:'QA approved commercial data band',value:'₦3,000 to ₦4,500',applies:'Data Bundles',ruleType:'Price band',kind:'priceBand',min:3000,max:4500,unit:'NGN',status:'Active'});
          const f=newWizardFields('TPL-022');Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',template:'TPL-022',templateMode:'existing',name:'QA Rule Registry Bundle',serviceClass:'DATA_QA3',eff:'2026-10-01',dataProductType:'Standard Data Bundle',dataPlanClass:'Monthly',dataVolume:'10 GB',dataPrice:'4000',dataValidity:'30',channels:['USSD'],price:''});
          const band=priceBandForProduct(f),errs=validateWizard(f).errs;
          DATA.baseline=oldBase;cfg.productRules=oldRules;
          return {band,errs};
        }""")
        assert registry['band']['id']=='QA-APPROVED-BAND', registry
        assert not any('Price is mandatory' in e or 'No active approved price band' in e or 'outside the approved range' in e for e in registry['errs']), registry

        # Render Data Core and verify semantic controls.
        await page.evaluate("""()=>{
          AUTH.account=ACCOUNTS[0];AUTH.stage='authed';state.role='po';
          const f=newWizardFields('TPL-022');const t=DATA.templates.find(x=>x.id==='TPL-022');applyTemplateConfig(f,t);
          Object.assign(f,{division:'Marketing',productFamily:'Data',cat:'Data Bundles',subcategory:'Commercial Plans',offering:'Commercial Data',variant:'Standard',dataProductType:'Standard Data Bundle',template:'TPL-022',templateMode:'existing'});
          state.wizard={type:'create',step:2,target:null,fields:f,currentFields:null,section:'dataCore',errors:null};state.route='requests';state.sub=null;renderAuth();render();
        }""")
        await page.wait_for_timeout(80)
        volume=page.locator('[data-v45-qty="dataVolume"]')
        assert await volume.count()==1 and await volume.get_attribute('type')=='number'
        vol_unit=page.locator('[data-v45-unit="dataVolume"]')
        assert await vol_unit.evaluate("el=>[...el.options].map(o=>o.value)")==['MB','GB','TB']
        await volume.fill('25');await vol_unit.select_option('GB');await vol_unit.dispatch_event('change')
        assert await page.evaluate('state.wizard.fields.dataVolume')=='25 GB'

        validity=page.locator('[data-f="dataValidity"]')
        assert await validity.get_attribute('type')=='number'
        await validity.fill('45')
        assert await page.evaluate('state.wizard.fields.dataValidity')=='45'

        voice=page.locator('[data-f="dataVoiceMinutes"]')
        assert await voice.get_attribute('type')=='number' and await voice.input_value()==''
        assert await page.locator('[data-v45-qty="youtubeNight"]').input_value()==''
        assert await page.locator('[data-v45-qty="youtubeDay"]').input_value()==''
        assert await page.locator('[data-f="dataOtherAddons"]').evaluate("el=>el.tagName")=='TEXTAREA'
        assert await page.locator('[data-f="dataTransferability"]').count()==0

        # Purchase & Sharing is a product-level section for every product family.
        await page.evaluate("state.wizard.section='purchaseSharing';render()")
        assert await page.locator('[data-f="sharingAllowed"]').evaluate("el=>[...el.options].map(o=>o.value)")==['No','Yes']
        assert await page.locator('[data-f="buyForOthersAllowed"]').evaluate("el=>[...el.options].map(o=>o.value)")==['No','Yes']
        await page.select_option('[data-f="sharingAllowed"]','Yes')
        await page.wait_for_timeout(30)
        assert await page.locator('[data-f="shareablePercentage"]').get_attribute('max')=='100'
        await page.evaluate("state.wizard.section='dataCore';render()")

        # Required markers in the core data form.
        labels=await page.locator('.config-main label').all_text_contents()
        for label in ['Plan class / duration*','Data volume*','Price (₦)*','Validity*']:
            assert label in [x.strip() for x in labels], (label,labels)

        # Service Class communicates its existing mandatory validator rule.
        await page.evaluate("state.wizard.section='classification';render()")
        await page.wait_for_timeout(40)
        service_labels=[x.strip() for x in await page.locator('.config-main label').all_text_contents() if 'Service Class' in x]
        assert service_labels and service_labels[0].endswith('*'), service_labels

        # Platform form audit: no editable literal N/A values in visible wizard fields.
        audit=await page.evaluate('window.v45AuditVisibleForm()')
        assert audit==[], audit

        # Review every certified template/section for editable N/A defaults.
        dirty=[]
        tids=await page.evaluate("DATA.templates.filter(t=>t.state==='Certified').map(t=>t.id)")
        for tid in tids:
            await page.evaluate("""(tid)=>{const f=newWizardFields(tid);const t=DATA.templates.find(x=>x.id===tid);if(t)applyTemplateConfig(f,t);state.wizard={type:'create',step:2,target:null,fields:f,currentFields:null,section:'classification',errors:null};state.route='requests';render();}""",tid)
            sections=await page.evaluate("requestConfigSections(state.wizard).map(x=>x[0])")
            for sec in sections:
                await page.evaluate("(sec)=>{state.wizard.section=sec;render()}",sec);await page.wait_for_timeout(8)
                bad=await page.evaluate("""()=>[...document.querySelectorAll('.config-main input:not([readonly]):not([disabled]):not([type=checkbox]),.config-main textarea:not([readonly]):not([disabled])')].filter(x=>String(x.value||'').trim().toUpperCase()==='N/A').map(x=>x.dataset.f||x.id||'field')""")
                if bad: dirty.append({'template':tid,'section':sec,'fields':bad})
        assert not dirty, dirty

        # Every currently visible field that the validator considers mandatory must show the red required marker.
        required_marker_gaps=[]
        for tid in tids:
            await page.evaluate("""(tid)=>{const f=newWizardFields(tid);const t=DATA.templates.find(x=>x.id===tid);if(t)applyTemplateConfig(f,t);state.wizard={type:'create',step:2,target:null,fields:f,currentFields:null,section:'classification',errors:null};state.route='requests';render();}""",tid)
            sections=await page.evaluate("requestConfigSections(state.wizard).map(x=>x[0])")
            for sec in sections:
                await page.evaluate("(sec)=>{state.wizard.section=sec;render()}",sec);await page.wait_for_timeout(10)
                gaps=await page.evaluate("""()=>{
                  const req=new Set(window.v45RequiredWizardKeys(state.wizard.fields));
                  return [...document.querySelectorAll('.config-main .field')].map(field=>{
                    const c=field.querySelector('[data-f],[data-v45-qty]'); if(!c)return null;
                    const key=c.dataset.f||c.dataset.v45Qty; if(!req.has(key))return null;
                    const label=field.querySelector(':scope > label')||field.querySelector('label');
                    return (!label||!label.querySelector('.req'))?key:null;
                  }).filter(Boolean);
                }""")
                if gaps: required_marker_gaps.append({'template':tid,'section':sec,'fields':gaps})
        assert not required_marker_gaps, required_marker_gaps

        if errors: raise AssertionError(errors)
        print(json.dumps({'PASS':True,'approved_data_price':'PASS','out_of_band_rejected':'PASS','approved_rule_registry_fallback':'PASS','data_volume':'number + MB/GB/TB','validity':'number of days','voice_minutes':'numeric optional blank','required_markers':'PASS across certified request forms','editable_NA_audit':'PASS','admin_revision':revision,'page_errors':0},indent=2))
        await browser.close()

if __name__=='__main__': asyncio.run(main())

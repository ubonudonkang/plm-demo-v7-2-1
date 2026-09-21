import asyncio
import json
import os
import pathlib

from playwright.async_api import async_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        launch = (
            {"headless": True, "channel": "msedge"}
            if os.name == "nt"
            else {
                "headless": True,
                "executable_path": "/usr/bin/chromium",
                "args": ["--no-sandbox", "--disable-dev-shm-usage"],
            }
        )
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page(viewport={"width": 1500, "height": 1050})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.set_content(HTML, wait_until="domcontentloaded")
        await page.wait_for_timeout(150)

        result = await page.evaluate(
            """()=>{
              const legacy={
                division:'EB',cat:'Data Bundles',subcategory:'Business Plans',
                dataProductType:'IoT Per-SIM',iotSimBand:'1–10,000 SIMs',
                apnRequired:true,serviceScopeType:'Selected services/apps',
                serviceApps:['WhatsApp','Teams'],channels:['MyMTN','Eshop'],dataPrice:'$25'
              };
              v47NormalizeConfig(legacy);

              const current=Object.assign(newWizardFields(),{
                division:'Marketing',cat:'Data Bundles',subcategory:'Commercial Plans',
                dataProductType:'Standard Data Bundle',name:'Existing',price:'1000',
                dataPrice:'1000',sharingAllowed:'No',buyForOthersAllowed:'No'
              });
              const proposed=JSON.parse(JSON.stringify(current));
              proposed.dataPrice='1500';proposed.sharingAllowed='Yes';
              proposed.shareablePercentage='25';
              const diffs=buildRequestDiffs({type:'modify',currentFields:current,fields:proposed});

              const transfer=Object.assign(newWizardFields(),{
                division:'Marketing',cat:'Data Bundles',subcategory:'Commercial Plans',
                dataProductType:'Data Transfer Service',name:'Transfer QA',eff:'2026-10-01',
                dataPlanClass:'Monthly',dataVolume:'10GB',dataPrice:'1000',
                dataValidity:'30 Days',transferBand:'1GB–10GB',transferRules:'Once daily',
                channels:['USSD'],eligibility:'Prepaid',sharingAllowed:'No'
              });

              const product=DATA.products.find(x=>x.id==='PRD-2255');
              const detail=productConfigSnapshot(product);
              const eb=Object.assign(newWizardFields(),{
                division:'EB',cat:'Data Bundles',subcategory:'Business Plans',
                dataProductType:'Postpaid Data Bundle',channels:['Enterprise Portal']
              });
              const ebChannels=wizardConfigSectionHTML({type:'create'},eb,{},'channels');
              const money=templateFieldInput('Data price',{dataPrice:'$100',currency:'USD'},{'Data price':'Editable'});
              const holder=document.createElement('div');holder.innerHTML=money;
              const currency=holder.querySelector('[data-v39-currency]')?.value;
              const allBusinessSequential=(DATA.approvalWorkflowV37||[]).every(w=>(w.stages||[]).filter(s=>/Business/i.test(s.name)).every(s=>s.mode==='Sequential'));
              return {
                legacy,diffs,
                transferErrors:validateWizard(transfer).errs,
                detail,ebChannels,currency,allBusinessSequential,
                requestSections:requestConfigSections({type:'create',fields:current}).map(x=>x[0])
              };
            }"""
        )

        legacy = result["legacy"]
        assert legacy["dataProductType"] == "IoT Per-SIM Bundle", result
        assert legacy["simPopulationBand"] == "1–10,000 SIMs", result
        assert legacy["apnRequired"] == "Yes", result
        assert legacy["dataServiceDetails"] == "WhatsApp, Teams", result
        assert legacy["channels"] == ["MyMTN App", "eShop"], result
        assert legacy["currency"] == "USD", result

        diff_keys = {item.get("key") for item in result["diffs"]}
        assert {"dataPrice", "sharingAllowed", "shareablePercentage"}.issubset(diff_keys), result
        assert any("requires Shareable to be Yes" in error for error in result["transferErrors"]), result
        assert "Commercial, Tax &amp; Regulatory" in result["detail"], result
        assert "Sharing policy" in result["detail"], result
        assert "Buy for Others" in result["detail"], result
        assert "Selected apps / services" in result["detail"], result
        assert "WhatsApp, TikTok" in result["detail"], result
        assert "Enterprise Portal" in result["ebChannels"], result
        assert "Enterprise notification" in result["ebChannels"], result
        assert result["currency"] == "USD", result
        assert result["allBusinessSequential"], result
        assert "commercialPolicy" in result["requestSections"], result
        assert "entitlementPolicy" in result["requestSections"], result
        assert not errors, errors

        print(
            json.dumps(
                {
                    "PASS": True,
                    "legacy_field_migration": "PASS",
                    "request_change_diffs": "PASS",
                    "transfer_sharing_invariant": "PASS",
                    "live_catalogue_policy_visibility": "PASS",
                    "enterprise_channel_scope": "PASS",
                    "currency_consistency": "PASS",
                    "sequential_business_approvals": "PASS",
                    "page_errors": 0,
                },
                indent=2,
            )
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import os
import pathlib

from playwright.async_api import async_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")


async def main():
    async with async_playwright() as p:
        launch = {"headless": True, "channel": "msedge"} if os.name == "nt" else {"headless": True, "executable_path": "/usr/bin/chromium", "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page(viewport={"width": 1500, "height": 1050})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.set_content(HTML, wait_until="domcontentloaded")
        await page.wait_for_timeout(150)

        model = await page.evaluate(
            """()=>{
              const fresh=newWizardFields();
              const legacy={dataTransferability:'Conditional',dataAdditionalInfo:'Up to 20% once per day',buyForOther:'Yes'};
              const holder={products:[{current:legacy}],templates:[],requests:[]};
              const original=DATA.products;DATA.products=holder.products;
              v46EnsurePurchaseSharingModel();DATA.products=original;
              return {
                defaults:{shareable:fresh.sharingAllowed,percentage:fresh.shareablePercentage,buyForOthers:fresh.buyForOthersAllowed},
                migrated:legacy,
                baseSections:CONFIG_SECTIONS.map(x=>x[0]),
                templateLabels:TEMPLATE_GROUPS.purchaseSharing,
                oldTemplateBuy:(TEMPLATE_GROUPS.enterpriseAllowances||[]).includes('Buy For Other'),
                oldTemplateTransfer:(TEMPLATE_GROUPS.dataCore||[]).includes('Transferability / additional info')
              };
            }"""
        )
        assert model["defaults"] == {"shareable": "No", "percentage": "", "buyForOthers": "No"}, model
        assert model["migrated"]["sharingAllowed"] == "Yes", model
        assert model["migrated"]["shareablePercentage"] == "20", model
        assert model["migrated"]["buyForOthersAllowed"] == "Yes", model
        assert "purchaseSharing" in model["baseSections"], model
        assert model["templateLabels"] == ["Shareable", "Maximum shareable percentage", "Buy for Others", "Sharing conditions"], model
        assert not model["oldTemplateBuy"] and not model["oldTemplateTransfer"], model

        await page.evaluate(
            """()=>{
              AUTH.account={dynamic:true,name:'Uche Chiemejonam',email:'uche@mtn.com'};AUTH.stage='authed';state.role='po';
              const f=newWizardFields('TPL-018');
              Object.assign(f,{division:'Marketing',productFamily:'Consumer',cat:'Tariff Plans',subcategory:'Prepaid Plans',templateMode:'existing',template:'TPL-018',name:'QA Sharing Product',serviceClass:'QA_SHARE',eff:'2026-10-01',price:'1000',channels:['USSD'],offering:'Prepaid',variant:'Standard'});
              state.wizard={type:'create',step:2,target:null,fields:f,currentFields:null,section:'purchaseSharing',errors:null};
              state.route='requests';state.sub=null;renderAuth();render();
            }"""
        )
        main = page.locator("#main-content")
        text = await main.inner_text()
        assert "Purchase & Sharing" in text, text
        assert "Maximum shareable percentage" not in text, text
        assert await page.locator('[data-f="sharingAllowed"]').count() == 1
        assert await page.locator('[data-f="buyForOthersAllowed"]').count() == 1
        assert await page.locator('[data-f="dataTransferability"]').count() == 0
        assert await page.locator('[data-f="buyForOther"]').count() == 0

        await page.select_option('[data-f="sharingAllowed"]', "Yes")
        await page.wait_for_timeout(50)
        assert await page.locator('[data-f="shareablePercentage"]').count() == 1
        await page.fill('[data-f="shareablePercentage"]', "25")
        await page.select_option('[data-f="buyForOthersAllowed"]', "Yes")
        valid = await page.evaluate("()=>validateWizard(state.wizard.fields).errs.filter(x=>/share|Buy for Others/i.test(x))")
        assert not valid, valid

        await page.fill('[data-f="shareablePercentage"]', "101")
        invalid = await page.evaluate("()=>validateWizard(state.wizard.fields).errs")
        assert any("whole number from 1 to 100" in error for error in invalid), invalid

        risk = await page.evaluate("()=>riskAssessment(state.wizard.fields).find(x=>x.component==='Sharing & recipient purchase')")
        assert risk and risk["score"] == 2, risk

        governed_outputs = await page.evaluate(
            """()=>{
              const product=DATA.products[0];
              const tabs=productDetailTabs('sharing',product),detail=renderProductDetailTab(product,'sharing');
              const req={id:'REQ-QA-9999',type:'Create',typeKey:'create',target:'QA Sharing Product',title:'QA sharing controls',owner:'Uche Chiemejonam',status:'Testing',tier:3,ver:'v1.0',submitted:'2026-09-21 12:00',diffs:[],approvals:[],gates:[],requestData:{sharingAllowed:'Yes',shareablePercentage:'25',sharingConditions:'One transfer per day',buyForOthersAllowed:'Yes'}};
              DATA.requests.push(req);ensureReleasePipelineForRequest(req);state.role='test';
              generateRiskBasedTestPack(req.id);
              const scenarios=DATA.releasePipeline[req.id].tests.map(t=>t.scenario||t.scen);
              delete DATA.releasePipeline[req.id];DATA.requests=DATA.requests.filter(x=>x.id!==req.id);
              return {tabs,detail,scenarios};
            }"""
        )
        assert 'data-tab="sharing"' in governed_outputs["tabs"], governed_outputs
        assert "Buy for Others" in governed_outputs["detail"], governed_outputs
        for scenario in ["Share at configured percentage ceiling", "Reject share above configured ceiling", "Buy for an eligible recipient"]:
            assert scenario in governed_outputs["scenarios"], governed_outputs

        assert not errors, errors
        print(json.dumps({
            "PASS": True,
            "defaults": model["defaults"],
            "legacy_migration": {"shareable": "Yes", "percentage": "20", "buy_for_others": "Yes"},
            "conditional_percentage_control": "PASS",
            "percentage_boundary_validation": "PASS",
            "legacy_controls_removed": "PASS",
            "template_configuration": "PASS",
            "product_detail": "PASS",
            "generated_uat_coverage": "PASS",
            "page_errors": 0,
        }, indent=2))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

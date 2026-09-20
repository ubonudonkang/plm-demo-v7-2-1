import asyncio
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
DB = ROOT / "data" / "plm_demo.db"


def backend_recovery_check():
    with tempfile.TemporaryDirectory() as td:
        temp_db = pathlib.Path(td) / "plm_demo.db"
        shutil.copy2(DB, temp_db)
        code = r'''
import json
from backend.app import _recover_price_bands_from_app_state, normalize_price_band_state

app = {
    "adminConfigV31": {
        "governanceChanges": [{
            "id": "GOV-0099",
            "area": "Product Rule",
            "state": "Approved",
            "approvedAt": "2026-09-18 12:59",
            "payload": {
                "id": "bg-price-tariff",
                "data": {
                    "group": "Product validation",
                    "name": "Approved price band, tariff plans",
                    "value": "₦100 to ₦5,000",
                    "applies": "Tariff Plans",
                    "ruleType": "Price band",
                    "min": 100,
                    "max": 5000,
                    "unit": "NGN",
                    "status": "Active"
                }
            }
        }]
    },
    "baseline": []
}
admin = {
    "adminConfigV31": {
        "productRules": [{
            "id": "bg-price-tariff",
            "group": "Product validation",
            "name": "Approved price band, tariff plans",
            "value": "Not configured",
            "applies": "Tariff Plans",
            "ruleType": "Price band",
            "min": None,
            "max": None,
            "unit": "NGN",
            "status": "Active"
        }]
    },
    "baseline": [{
        "id": "bg-price-tariff",
        "kind": "priceBand",
        "applies": "Tariff Plans",
        "min": None,
        "max": None,
        "value": "Not configured"
    }]
}
changed = _recover_price_bands_from_app_state(app, admin)
normalize_price_band_state(admin)
rule = next(x for x in admin["adminConfigV31"]["productRules"] if x["id"] == "bg-price-tariff")
band = next(x for x in admin["baseline"] if x["id"] == "bg-price-tariff")
assert changed
assert rule["min"] == 100 and rule["max"] == 5000 and rule["kind"] == "priceBand"
assert band["min"] == 100 and band["max"] == 5000 and band["kind"] == "priceBand"
print(json.dumps({"recovered": True, "rule": rule, "band": band}))
'''
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{temp_db.as_posix()}"
        out = subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)
        return json.loads(out.strip().splitlines()[-1])


def persisted_admin():
    con = sqlite3.connect(DB)
    try:
        row = con.execute(
            "select data_json from module_state where module_name='administration'"
        ).fetchone()
        return json.loads(row[0])
    finally:
        con.close()


async def browser_check():
    admin = persisted_admin()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.set_content(HTML, wait_until="domcontentloaded")
        await page.wait_for_timeout(50)

        persisted = await page.evaluate(
            """(admin)=>{
                Object.entries(admin).forEach(([k,v])=>DATA[k]=v);
                v42RepairApprovedPriceBands();
                const f={division:'Marketing',productFamily:'Voice',cat:'Tariff Plans',subcategory:'Prepaid',price:'500'};
                const errs=[],warns=[];
                enforcePriceBaseline(f,errs,warns);
                return {
                  scopeLevel:v32InferScopeLevel('Tariff Plans'),
                  band:priceBandForProduct(f),
                  errs,warns
                };
            }""",
            admin,
        )
        assert persisted["scopeLevel"] == "Category"
        assert persisted["band"] and persisted["band"]["kind"] == "priceBand"
        assert not persisted["errs"]

        precedence = await page.evaluate(
            """()=>{
              DATA.baseline=[
                {id:'global',kind:'priceBand',applies:'All products',min:100,max:5000,status:'Active'},
                {id:'specific',kind:'priceBand',applies:'Marketing / Voice / Tariff Plans',min:200,max:4000,status:'Active'}
              ];
              const f={division:'Marketing',productFamily:'Voice',cat:'Tariff Plans',subcategory:'Prepaid',price:'500'};
              return priceBandForProduct(f).id;
            }"""
        )
        assert precedence == "specific"

        # Restore the persisted Administration state before maker-checker validation.
        await page.evaluate(
            """(admin)=>{Object.entries(admin).forEach(([k,v])=>DATA[k]=JSON.parse(JSON.stringify(v)));v42RepairApprovedPriceBands();}""",
            admin,
        )

        await page.evaluate(
            """()=>{
              AUTH.account={dynamic:true,name:'Mutolib Ottan',email:'mutolib.ottan@mtn.com'};
              AUTH.stage='authed';state.role='admin';renderAuth();
            }"""
        )
        change_id = await page.evaluate(
            """()=>{
              const p={id:'bg-price-tariff',data:{
                group:'Product validation',name:'Approved price band, tariff plans',
                value:'₦120 to ₦4,800',applies:'Tariff Plans',ruleType:'Price band',
                min:120,max:4800,unit:'NGN',status:'Active',source:'baseline'
              }};
              return v37SubmitGovChange('Product Rule',p.data.name,p);
            }"""
        )
        await page.evaluate(
            "(id)=>v37GovReviewModal(adm31Cfg().governanceChanges.find(x=>x.id===id))",
            change_id,
        )
        await page.locator(
            f'[data-act="v37GovDecision"][data-id="{change_id}"][data-decision="Approve"]'
        ).click()
        maker_state = await page.evaluate(
            "(id)=>adm31Cfg().governanceChanges.find(x=>x.id===id).state", change_id
        )
        assert maker_state == "Pending Approval"

        await page.evaluate(
            """()=>{
              AUTH.account={dynamic:true,name:'Tosin Adebayo',email:'tosin.adebayo@mtn.com'};
              AUTH.stage='authed';state.role='admin';renderAuth();
            }"""
        )
        await page.evaluate(
            "(id)=>v37GovReviewModal(adm31Cfg().governanceChanges.find(x=>x.id===id))",
            change_id,
        )
        await page.locator(
            f'[data-act="v37GovDecision"][data-id="{change_id}"][data-decision="Approve"]'
        ).click()
        await page.wait_for_timeout(50)
        checker = await page.evaluate(
            """(id)=>{
              const c=adm31Cfg().governanceChanges.find(x=>x.id===id);
              const band=DATA.baseline.find(x=>x.id==='bg-price-tariff');
              const errs=[],warns=[];
              enforcePriceBaseline(
                {division:'Marketing',productFamily:'Voice',cat:'Tariff Plans',subcategory:'Prepaid',price:'500'},
                errs,warns
              );
              return {state:c.state,approvedBy:c.approvedBy,band,errs,warns};
            }""",
            change_id,
        )
        assert checker["state"] == "Approved"
        assert checker["approvedBy"] == "Tosin Adebayo"
        assert checker["band"]["kind"] == "priceBand"
        assert not checker["errs"]
        assert not errors, errors

        await browser.close()
        return {
            "persisted_validation": persisted,
            "specificity": precedence,
            "maker_state": maker_state,
            "checker": checker,
            "page_errors": errors,
        }


async def main():
    backend = backend_recovery_check()
    browser = await browser_check()
    print(json.dumps({"PASS": True, "backend": backend, "browser": browser}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

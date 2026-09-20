# PLM Demo v7.2 Regression

Status: **PASS**

## v7.2 targeted form and price-band tests

- Data Bundle `dataPrice` consumed as commercial price: PASS
- In-band Data price accepted against persisted approved band: PASS
- Out-of-band Data price rejected with approved-range message: PASS
- Approved Administration product-rule registry works when baseline is stale/missing: PASS
- Data volume is numeric-only: PASS
- Data volume units MB / GB / TB: PASS
- Validity is numeric days: PASS
- Included voice minutes is numeric and optional: PASS
- YouTube night/day allowances are structured quantity/unit controls: PASS
- Other bundled benefits is optional multiline text: PASS
- Transferability/gifting is structured enum: PASS
- Conditional gifting conditions required only for `Conditional`: PASS
- Required red markers aligned across certified Product Request forms: PASS
- Editable literal `N/A` audit across certified request forms: PASS
- Browser page errors: 0

## Existing functional regression

- `qa_v5.py`: PASS — 5 certified templates / 289 actions
- `qa_v6_price_band.py`: PASS — approved recovery, canonical `priceBand`, independent maker-checker
- `qa_v6_2_roles.py`: PASS — 21 roles, role switching, Create Template, multi-role users, Chiamaka persona
- `qa_v7_role_catalogue.py`: PASS — 21 canonical roles
- `qa_v7_role_scope.py`: PASS — route scope, role-correct approvals, Test/Release separation, Reports role context
- `qa_v7_1_data_form.py`: PASS
- `qa_v7_2_form_controls.py`: PASS

## Browser regression

- `browser_qa_v5.py`: PASS
  - certified templates: 5
  - taxonomy nodes: 106
  - page errors: 0
- `browser_qa_deep_v5.py`: PASS
  - request wizard sections: PASS
  - template sections: PASS
  - all add-on types: PASS
  - Administration modals: PASS
  - Testing & Release: PASS
  - module/detail screens: PASS
  - taxonomy errors: 0
  - taxonomy duplicates: 0

## Live backend regression

- `/api/health`: PASS — SQLite healthy
- `/api/meta`: PASS — version 7.2.0
- `smoke_test_v3.py`: PASS — 12 modules, 21 products, 7 templates, 13 requests, 10 users
- `smoke_test.py`: PASS
- Backend restart persistence: PASS — Administration revision 19 remained 19
- CSV test-case import: PASS
- XLSX existing-estate import: PASS
- QA import batches removed after validation; delivered database has no import-test residue.

## Governance controls preserved

- Maker cannot approve their own governed Administration change: PASS
- Independent checker approval remains active: PASS
- Approved price-band rule normalisation/recovery remains active: PASS
- v7 21-role test model remains intact: PASS

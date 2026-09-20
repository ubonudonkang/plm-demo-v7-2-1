# PLM Demo v7 — Regression Record

Date: 20 September 2026

## Result

**PASS** for the v7 hardening scope.

## Static/browser regression

- `scripts/qa_v5.py` — PASS; literal action-handler coverage retained.
- `scripts/qa_v6_price_band.py` — PASS; v5 recovery, canonical `priceBand`, Tariff Plans validation and maker-checker retained.
- `scripts/qa_v6_2_roles.py` — PASS; Create Template, multi-role assignment/switching and Chiamaka persona retained.
- `scripts/qa_v7_role_catalogue.py` — PASS; 21 canonical roles, configured module scopes and workflow aliases resolve.
- `scripts/qa_v7_role_scope.py` — PASS; all 21 selected-role navigation scopes, direct-route guard, selected-role approvals, Product Manager template access, Test/Release separation, role-aware Reports, compatibility role mappings and Chiamaka persona.
- `scripts/browser_qa_v5.py` — PASS; 0 page errors.
- `scripts/browser_qa_deep_v5.py` — PASS; wizard sections, templates, add-ons, Administration modals, Testing & Release and module/detail coverage.

## Live backend regression

- `GET /api/health` — PASS (`sqlite`).
- `scripts/smoke_test.py` — PASS: 21 products, 13 requests, 10 users.
- `scripts/smoke_test_v3.py` — PASS: 12 modules, 21 products, 7 templates, 13 requests, 10 users.
- Administration role model — PASS: 21 roles, every role has a module scope.
- Mutolib Ottan — PASS: all 21 test roles.
- Chiamaka Eleodi — PASS: Product Manager only.
- Administration startup idempotence — PASS: revision remained 19 after full backend restart.
- Approved Tariff Plans band — PASS: ₦100–₦5,000 remains persisted; canonical `priceBand` is present in active rule/baseline state.
- CSV test-case import — PASS: 1/1 valid, 0 errors.
- XLSX estate import — PASS: 1/1 valid, 0 errors/warnings.
- QA import batches were removed after validation so the delivered demo database remains clean.

## Browser/backend execution note

The execution environment blocks Chromium navigation to `127.0.0.1` with `ERR_BLOCKED_BY_ADMINISTRATOR`. Therefore browser regression was executed against the exact packaged frontend via Playwright `set_content`, while backend/API/persistence regression was executed against the live Uvicorn service. This is the same split-validation approach used for the prior stable build; both sides passed independently.

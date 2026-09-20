# PLM Demo v6.1 — Regression Record

## Defect reproduced

The persisted Administration database contained an approved `bg-price-tariff` rule with numeric range ₦100–₦5,000 and scope `All products`. Before the v6.1 scope fix, browser validation returned:

`No active approved price band is configured for Tariff Plans.`

The failure was reproduced directly in Chromium before the patch.

## Corrected behavior

- `All products` price bands apply to Tariff Plans.
- Governed taxonomy paths such as `Marketing / Voice / Tariff Plans` match the corresponding product classification.
- A specific numeric band takes precedence over a global numeric band.
- Numeric bands take precedence over legacy unconfigured placeholders.
- The approved rule carries canonical machine kind `priceBand`.
- Existing approved governance history can reconstruct a reset active rule/baseline.
- Persisted Administration remains authoritative over seed data.

## Regression results

| Area | Result |
|---|---|
| Python backend compile | PASS |
| Existing `scripts/qa_v5.py` | PASS |
| Existing `scripts/browser_qa_v5.py` | PASS — 0 page errors |
| Existing `scripts/browser_qa_deep_v5.py` | PASS |
| Backend health/products/requests/users smoke | PASS |
| v3 module/resource API smoke | PASS |
| Administration restart idempotency | PASS |
| Approved v5 governance-history recovery | PASS |
| Persisted Tariff Plans browser validation | PASS |
| Maker self-approval block | PASS |
| Independent Platform Administrator approval | PASS |
| CSV test-case import | PASS |
| XLSX existing-estate import | PASS |

## Persisted database state after migration

`bg-price-tariff` remains approved with value ₦100–₦5,000. The active baseline and rule both expose canonical machine kind `priceBand`. Repeated backend startup does not increment the Administration revision or restore `Not configured`.

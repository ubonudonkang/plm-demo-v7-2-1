# PLM Demo v5 — Comprehensive Classification & Form Reliability Fix

## Primary issue fixed

New Product could open with inherited Product Classification fields locked while blank (for example a grey `Select domain`, an empty Product Family dropdown, and an unusable Sub-Category). The root cause was that a source-template ID could exist without the certified template classification being applied before the inherited fields were locked.

## New Product behaviour

- New Product is now **template-first**.
- Before a certified source template is selected, only Source Template is shown for classification.
- Selecting a certified template loads and locks its approved:
  - Product Domain / Line of Business
  - Product Family
  - Product Category
  - Product Sub-Category
- Product Offering and Product Variant remain selectable when the certified template has a broad scope.
- Changing Product Classification no longer silently chooses a template.
- A template with incomplete classification cannot be used.

Verified certified templates:

- TPL-018 — Marketing → Voice → Tariff Plans → Prepaid
- TPL-022 — Marketing → Data → Data Bundles → Commercial Plans
- TPL-024 — Enterprise Business → Enterprise Mobile → Tariff Plans → Enterprise Plans
- TPL-025 — Enterprise Business → Data & IoT → Data Bundles → Business Plans
- TPL-027 — Marketing → Loans → Loan Services → Loan Products

## Product Classification repair

- Removed the old global Sub-Category leakage caused by reusing `CATEGORY_TREE` across unrelated Product Domains/Families.
- Consumer Tariff Plans no longer expose Enterprise Plans.
- Enterprise Tariff Plans no longer expose Prepaid/Postpaid.
- Marketing Data no longer exposes Business Plans.
- Enterprise Data & IoT no longer exposes Commercial Plans.
- Legacy `EB` references normalize to `Enterprise Business`.
- Legacy `Commercial` / `Business` values normalize to `Commercial Plans` / `Business Plans` where applicable.
- Product Classification records are deduplicated during the runtime repair pass.

## Template Creation

Template Creation was regression-tested as a true cascade:

`Domain → Family → Category → Sub-Category → Offering applicability → Variant applicability`

- It starts deliberately blank.
- Dependent controls remain disabled until the parent is selected.
- Disabled controls use explicit prompts such as `Select domain first` rather than empty dropdowns.
- Product Classification is captured once and is not duplicated in configuration tabs.
- Every representative Consumer, Enterprise, Data & IoT and Loan template section was checked for duplicate bindings and empty enabled dropdowns.

## Other form fixes discovered during the sweep

- Benefit Unit is now disabled until Benefit Type is selected; it no longer appears as an enabled dropdown with no options.
- Legacy `EB` in the old Division list is normalized to `Enterprise Business` for older filters still using that array.
- Request Details receives a final render-level deduplication pass so duplicate Impact Analysis / Request Control / Summary / Approval Route / Control Gates / Evidence cards cannot accumulate from legacy stacked renderers.
- The existing Product Request duplicate-card fix is therefore enforced at the final screen output, not only inside one intermediate renderer.

## Backend compatibility

Startup includes an idempotent certified-template classification repair for databases copied from earlier demo versions.

A v4 database was copied into a clean v5 project and started against the v5 backend. All certified templates were verified to contain complete Domain, Family, Category and Sub-Category metadata after startup.

No manual database schema migration is required for v5.

## QA completed

### Static / JavaScript

- Combined JavaScript syntax: PASS
- Literal `data-act` handler audit: PASS
- Certified-template metadata audit: PASS
- Template classification-key uniqueness: PASS

### Browser-level regression

- All 5 certified source templates: PASS
- Product Classification inheritance: PASS
- Offering → Variant cascades: PASS
- Every visible New Product configuration section: PASS
- Representative template configurations across Consumer/Enterprise/Data/IoT/Loans: PASS
- All visible Template Creation sections: PASS
- All 8 Add-On benefit types: PASS
- Administration main tabs: PASS
- Administration configuration modals: PASS
- Testing & Release queue/workspaces: PASS
- Product Catalogue and selected Product Details: PASS
- Every Product Request detail: PASS
- Retirement: PASS
- Reconciliation: PASS
- Exceptions: PASS
- Audit: PASS
- Reports: PASS
- Browser JavaScript page errors: 0
- Product Classification malformed nodes: 0
- Product Classification duplicate nodes: 0

### Backend

- Health API: PASS
- Products API: PASS
- Requests API: PASS
- Users API: PASS
- Module bootstrap/API: PASS
- Older v4 database startup repair: PASS


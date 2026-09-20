# PLM Requirements Validation Demo — v7.2

This project migrates the latest PLM HTML prototype to a persistent demo backend without throwing away the detailed UI built during requirements elicitation.

## Architecture

```text
Browser (existing PLM prototype)
        |
        | /api/state + resource APIs
        v
FastAPI demo backend
        |
        +-- SQLite (default, zero setup)
        +-- PostgreSQL-compatible target schema
        +-- File uploads
        +-- CSV/XLSX parsing
        +-- Mock authoritative-system adapters
```

### Why SQLite locally?

The local demo defaults to SQLite so it can run immediately on a laptop with no database installation. The data model is PostgreSQL-compatible and `db/postgres_schema.sql` is included. Set `DATABASE_URL` and install the PostgreSQL driver when moving the demo to Supabase/Neon/PostgreSQL.

## What is persisted

The frontend now persists by **module** instead of saving the entire prototype as one state document. Each module has an independent revision so concurrent demo sessions can detect conflicting edits. The legacy whole-state endpoints remain only for bootstrap/backward compatibility.

Modules persisted independently include:

- Product Catalogue & Dependencies
- Templates
- Product Requests & Impact Reviews
- Workflow & Approvals
- Testing & Release
- Reconciliation / Drift / External Changes
- Exceptions & Rollback
- Retirement
- Administration / Users / Roles / Integrations / Rules
- Audit
- Notifications
- Existing-estate onboarding

The backend also mirrors core records into queryable relational records for:

- Products
- Templates
- Product Requests
- Users
- Exceptions
- Release packages
- Dependencies
- Systems/Integrations
- Retirement requests
- Audit events

This is an incremental migration strategy: it makes the current prototype persistent immediately, while allowing each module to be migrated from state-sync to dedicated REST endpoints progressively.

## Included API capabilities

- `GET /api/health`
- `GET /api/modules`
- `GET /api/modules/bootstrap`
- `GET /api/modules/{module}`
- `PUT /api/modules/{module}` — revision-aware module persistence
- `GET/POST/PUT/DELETE /api/v2/{resource}` — transactional resource APIs
- `POST /api/v2/requests/{id}/approval-decisions`
- `POST /api/v2/releases/{request_id}/tests/{test_id}/execute`
- `GET /api/state` / `POST /api/state/bootstrap` / `PUT /api/state` — compatibility only
- `POST /api/demo/reset`
- `GET /api/products`
- `GET /api/templates`
- `GET /api/requests`
- `GET /api/users`
- `GET /api/exceptions`
- `GET /api/releases`
- `GET /api/audit`
- `POST /api/auth/login`
- `POST /api/import/test-cases` — CSV/XLSX
- `POST /api/import/estate` — CSV/XLSX
- `POST /api/mock/{system}/deploy`
- Attachment upload/download APIs

## Run locally

### Windows PowerShell

```powershell
cd plm_demo_v7
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### macOS/Linux

```bash
cd plm_demo_v7
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Open:

`http://localhost:8000`

The first browser session enriches the backend's baseline seed with all derived prototype data. After that, the frontend loads and saves **module branches independently**. Refreshes therefore load from the database without replacing unrelated modules.

## Demo reset

Use:

```bash
curl -X POST http://localhost:8000/api/demo/reset
```

Then refresh the browser. This restores the prepared demo seed.

## PostgreSQL / Supabase migration

1. Create a PostgreSQL database.
2. Use `db/postgres_schema.sql` as the target logical schema reference.
3. Set:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE'
```

4. Start the backend normally. SQLAlchemy creates the demo persistence tables automatically.

For Supabase, use its PostgreSQL connection string. Storage and Auth can then replace the local file-store and prototype login in the next migration step.

## Important demo note

The downstream DCM/CIS/MSAP/Charging/CRM integrations are intentionally mocked for requirements validation. The goal is to validate lifecycle controls before connecting to live MTN systems.


## Latest UX / governance fixes

This package includes a regression pass for the requirements-validation demo:

- Template Creation uses typed/compound controls for volumes, prices, durations, counts and time windows.
- Product Request detail removes duplicate Impact Analysis cards caused by legacy renderer stacking.
- Administration product-rule changes (including tariff price bands) now require maker-checker approval.
- To approve a proposed price band, open **Administration → Pending Changes**, select the change, then Approve & Activate using a different Platform Administrator account.

If you previously changed a price band in an older build where it updated immediately, create a new proposal in **Administration → Rules & Risk → Propose change** so it enters the governed approval queue.


## Backend migration v3 notes

### Concurrency

Each module has a revision number. The browser sends `expected_revision` on save. If another browser changes the same module first, the API returns HTTP 409 instead of silently overwriting the newer data.

### API documentation

While the server is running, open:

`http://localhost:8000/docs`

FastAPI exposes interactive Swagger documentation for the migrated APIs.

### Transactional resources

The following resources can already be managed without whole-state writes:

`products`, `dependencies`, `templates`, `requests`, `impact-reviews`, `overrides`, `users`, `delegations`, `admin-changes`, `integrations`, `notification-rules`, `notifications`, `exceptions`, `retirement-plans`, `onboarding-batches`, and `test-data-sets`.

Workflow approval decisions and test executions also have dedicated action endpoints. More frontend actions can now be moved to these endpoints progressively without another database redesign.

## v4 maker-checker / multi-user governance fix

When one Platform Administrator proposes a governed Administration change (for example a Tariff Plan price-band update), the proposal is stored under the Administration module and persisted immediately.

The **Administration > Pending Changes** governance queue now:
- automatically polls the backend every 2.5 seconds while the queue is open;
- refreshes when a newer Administration module revision exists;
- includes a manual **Refresh queue** action;
- does not overwrite unsaved local Administration edits;
- persists approval/rejection decisions immediately;
- correctly counts `Pending Approval` governance changes on the admin dashboard.

This fixes the demo case where Mutolib submits a price-band change but another Platform Administrator who already had the application open could not see the proposal without reloading.

### Preserve an existing local demo database
If upgrading from v3/v2 and you want to keep your current demo data, stop the server and copy your existing `data/plm_demo.db` into the new project folder before starting v4. The schema did not change for this fix.


## v5 classification and form reliability fixes

This build includes a comprehensive controlled-field regression pass.

- **New Product is template-first.** Before a certified source template is selected, the form does not render blank inherited Domain/Family/Category/Sub-Category controls. After selection, the certified classification loads and inherited levels are locked with populated values.
- Certified templates are repaired on backend startup when an older v3/v4 database is copied into this build.
- Product Classification now uses a domain/family-aware hierarchy, preventing Enterprise sub-categories from leaking into Consumer Tariff/Data classifications and vice versa.
- Offering and Variant cascades are populated from the governed Product Classification records.
- Template Creation starts deliberately blank and cascades **Domain → Family → Category → Sub-Category → Offering applicability → Variant applicability**.
- Empty dependent dropdowns remain disabled with explicit prompts until their parent selection exists.
- Benefit Unit remains disabled until a Benefit Type is selected instead of presenting an enabled empty dropdown.
- Request Detail has a final rendering invariant that removes duplicate Impact Analysis / control cards introduced by legacy renderer stacking.
- Existing v4 maker-checker, governance polling, backend persistence, and multi-user revision controls are retained.

### QA included in this package

The build was checked with:

```powershell
python scripts/qa_v5.py
python scripts/browser_qa_v5.py
python scripts/browser_qa_deep_v5.py
```

The browser QA covers all certified source templates, every product-configuration section, representative Consumer/Enterprise/Data template configurations, all Add-On benefit types, Administration pages and configuration modals, Testing & Release, Product Catalogue, Product Requests, Retirement, Reconciliation, Exceptions, Audit and Reports.

Backend smoke tests are also included:

```powershell
# Run the server first
python scripts/smoke_test.py http://127.0.0.1:8000
python scripts/smoke_test_v3.py
```

### Upgrading from v4 without losing demo data

1. Stop the old server.
2. Copy `plm_demo_v4\data\plm_demo.db` to `plm_demo_v5\data\plm_demo.db`.
3. Start v5 normally.

Startup automatically repairs legacy certified-template classification metadata. No manual database migration is required for this release.

## v6 price-band persistence fix

PLM Demo v6 fixes the Tariff Plans price-band maker-checker path and startup persistence. Approved price bands are normalized into the active catalogue baseline, request validation prefers the active numeric band, and existing module state is no longer overwritten by seed data on server restart.

If you are upgrading from v5, copy `data\plm_demo.db` into the v6 `data` folder before starting the server. The startup migration will recover an already-approved Tariff Plans price band from the existing database where possible.

See `FIX_SUMMARY_V6.md` for details.


## v6.1 scope matching and recovery hardening

v6.1 closes one additional defect found while validating the persisted v5/v6 database.

An approved price-band rule can legitimately be scoped as `All products` or stored as a governed taxonomy path such as `Marketing / Voice / Tariff Plans`. Earlier Product Request validation only matched a comma-separated scope that literally contained `Tariff Plans`, so a valid approved global/path-scoped band could still be reported as missing.

v6.1 now:

- matches price bands against `All products`, `All categories`, legacy short category names, and governed taxonomy paths;
- prefers the most specific numeric active price band over a global band or legacy placeholder;
- preserves legacy short rule scopes when an administrator reopens a governed rule;
- infers legacy `Tariff Plans` as a Category scope rather than incorrectly treating it as a Domain;
- stores the canonical machine kind `priceBand` while retaining the human-readable rule type used by the Administration UI;
- can rebuild an approved numeric price band from approved/implemented governance history when older state contains only the approval record;
- keeps a valid persisted Administration rule ahead of seed/AppState recovery data;
- remains idempotent across repeated backend restarts.

### v6.1 regression

Verified on the packaged database:

- Existing approved Tariff Plans band (`₦100`–`₦5,000`): recognized by Product Request validation.
- Maker self-approval: blocked.
- Independent Platform Administrator approval: passes and writes canonical `priceBand`.
- Persisted Administration module after restart: unchanged; seed does not overwrite it.
- Static QA: PASS.
- Browser QA: PASS with 0 page errors.
- Deep browser QA: PASS.
- Backend smoke/API QA: PASS.
- CSV test-case import: PASS.
- XLSX existing-estate import: PASS.


## v6.2 multi-role test mode and template fix

v6.2 fixes the Product Owner **Create Template** action and converts Administration access into a deliberately permissive multi-role test model. Users can hold overlapping roles and switch their active assigned role from the header without signing out. Access-assignment role-combination SoD is disabled for this test build; governed maker-checker decisions such as price-band configuration still require a different user.

The canonical role catalogue contains 21 active roles: Product Manager, Product Owner, Pricing / MKT BI, Finance / Tax, Business Assurance, Customer Experience, Technology Approver, Technical Owner, Regulatory / Legal, Executive Sponsor, CAB / Change Manager, Test Analyst, Release Manager, Reconciliation & Monitoring Analyst, Exception & Rollback Manager, Product Governance, Records Manager, Compliance Officer, Audit & Compliance Reviewer, Product Classification Administrator, and Platform Administrator.

Chiamaka Eleodi is seeded as an active Product Manager. Mutolib Ottan is the all-role test persona and receives the complete canonical role catalogue so every role can be exercised from one authenticated session.

Legacy workflow labels are normalized to real configured roles, including `Regulatory` → `Regulatory / Legal`, `CAB` → `CAB / Change Manager`, `Records / Governance` → `Records Manager`, `Release / Test Analyst` → `Test Analyst`, and generic lifecycle `Approver` → `Business Assurance`.

### v6.2 regression

Run the dedicated role regression with:

```powershell
python scripts/qa_v6_2_roles.py
```

The release was also rerun through `qa_v5.py`, `qa_v6_price_band.py`, `browser_qa_v5.py`, `browser_qa_deep_v5.py`, `smoke_test.py`, and `smoke_test_v3.py`. CSV and XLSX import paths were revalidated. See `REGRESSION_V6_2.md` for the recorded results.



## v7.2 request-form and price-band hardening

v7.2 streamlines the Product Request forms and removes a remaining multi-user price-band validation race. Data volume now uses a numeric value plus MB/GB/TB selector, validity is stored as a numeric number of days, ambiguous editable `N/A` defaults were removed from optional Data Bundle fields, and visible mandatory controls are synchronised with the validator's red required markers.

Before Product Request validation/submission, the browser refreshes the persisted Administration module so a price band approved by another Super Admin becomes effective in an already-open Product Owner session. Data Bundle validation consumes `dataPrice` directly and the approved Administration product-rule registry is an authoritative fallback if the older baseline representation is stale.

Targeted QA:

```bash
python scripts/qa_v7_2_form_controls.py
```

See `FIX_SUMMARY_V7_2.md` and `REGRESSION_V7_2.md` for the detailed change and regression record.

## v7 scoped role and lifecycle hardening

v7 keeps the deliberately permissive **multi-role test assignment** introduced in v6.2, but makes the role currently selected in the header meaningful across navigation, actions, approvals, reports and audit evidence.

Key changes:

- every one of the 21 canonical roles now has an explicit module scope;
- users can continue to hold overlapping roles and switch role without logging out;
- direct navigation to a module outside the selected role scope is blocked, not merely hidden in the navigation;
- Product Request approvals are matched to the **selected named role** instead of the older broad `ba` compatibility code or first pending approval row;
- legacy workflow labels such as `Finance`, `Technology` and `Legal / Regulatory` resolve to their canonical v7 roles;
- Test Analyst and Release Manager actions no longer leak into each other through compatibility role codes;
- Exception & Rollback Manager now maps correctly into the legacy rollback execution path;
- Product Classification Administrator has Administration access limited to Product Classification, while Platform Administrator retains the full Administration surface;
- Product Manager / Product Owner template, draft and request actions are explicitly scoped;
- lifecycle controls such as launch scheduling, bulk deployment, suspension, dependencies, rollback, retirement, reconciliation and archive are tied to the appropriate selected role;
- Reports render a dashboard for the **currently selected role**, even when the authenticated test user holds all roles;
- audit entries for hardened lifecycle actions record the actual signed-in user and selected role instead of older hard-coded prototype identities;
- backend Administration stores `testModeRoleModelVersion=7.0` and `roleScopeVersion=7.0` idempotently.

Role-combination segregation of duties remains disabled for access assignment in this demo. Governed maker-checker controls that were already part of the PLM requirement, including price-band configuration approval, still require a different user.

### v7 QA

```powershell
python scripts/qa_v5.py
python scripts/qa_v6_price_band.py
python scripts/qa_v6_2_roles.py
python scripts/qa_v7_role_catalogue.py
python scripts/qa_v7_role_scope.py
python scripts/browser_qa_v5.py
python scripts/browser_qa_deep_v5.py

# with the server running
python scripts/smoke_test.py http://127.0.0.1:8000
python scripts/smoke_test_v3.py
```

See `ROLE_CATALOGUE_V7.md`, `FIX_SUMMARY_V7.md`, and `REGRESSION_V7.md` for the role matrix, changes and recorded regression results.

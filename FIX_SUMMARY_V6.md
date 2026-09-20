# PLM Demo v6 — Tariff Price-Band Activation Fix

## Root causes fixed

1. Maker-checker approval wrote approved product-rule type as `Price band`, while request validation only recognized the older internal value `priceBand`.
2. When a legacy unconfigured Tariff Plans placeholder and a newly approved configured rule coexisted, validation could select the placeholder first.
3. v5 startup initialization re-synchronized seed module data over persisted module state, which could restore the Tariff Plans baseline to `Not configured` after restart.
4. Existing v5 databases could therefore retain the approved value in AppState while the Administration module had already been reset to seed.

## v6 behavior

- Validation recognizes both legacy and canonical price-band type values.
- A configured numeric active band is preferred over legacy placeholder rows.
- Approval writes the canonical `priceBand` baseline representation.
- Startup no longer overwrites existing module state with seed data.
- Startup migration recovers already-approved numeric price bands from existing v5 AppState when the Administration module was reset.
- Existing correctly persisted module changes take precedence over stale AppState values.
- The stale message telling users to “publish the catalogue baseline” was replaced with the current maker-checker terminology: “approve and activate”.

## Verification

- Static QA: PASS
- Browser regression: PASS, 0 page errors
- Maker-checker price-band flow: PASS
- Legacy `Price band` compatibility: PASS
- Placeholder + active band precedence: PASS
- v5-style AppState recovery into Administration module: PASS
- Persisted Administration module survives restart: PASS
- Python backend compile: PASS
- Backend smoke test: PASS


## v6.1 follow-up discovered during persisted-database verification

The copied v5 database contained an approved Tariff Plans price band with:

- `kind: "Price band"` in the legacy baseline before migration;
- numeric minimum/maximum values present;
- governance state `Approved`;
- scope `All products`.

That exposed an additional validation defect: `priceBandForCategory()` only accepted scopes whose comma-separated value literally contained the current category. Therefore `All products` and taxonomy-path scopes could still be treated as "no approved price band".

v6.1 fixes this by using classification-aware scope matching and specificity precedence. It also recovers numeric price bands directly from approved governance history if both the active rule and baseline were reset in an older build.

The packaged database has been migrated idempotently to canonical `kind: "priceBand"` while retaining the approved value and maker-checker evidence.

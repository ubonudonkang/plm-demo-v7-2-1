# PLM Demo v7 — Fix Summary

## Why v7 was needed

v6.2 enabled multiple roles and role switching, but much of the older prototype still reduced 21 named roles to five compatibility codes (`po`, `ba`, `test`, `rel`, `admin`). This created several risks in an all-role test persona: a selected role could inherit another role's actions, approval could fall through to the wrong pending approval row, Reports could reflect the union of assigned roles instead of the selected role, and some lifecycle audit entries could record hard-coded prototype identities.

## Changes

### 1. Explicit role scope for all 21 roles

Backend and frontend now carry an explicit module scope for every canonical role. The selected role controls navigation and direct-route access. Product Classification Administrator is restricted to the Taxonomy Administration tab; Platform Administrator retains the full Administration surface.

### 2. Selected-role approvals

Product Request approval/reject/return operations now identify the pending approval row that matches the selected named role. Legacy approval names are normalized to canonical roles. Decisions record the signed-in user and the selected role.

### 3. Compatibility-code hardening

New operational roles now map safely into older handlers where required. In particular, Exception & Rollback Manager and Reconciliation & Monitoring Analyst map to the release/recovery compatibility path without inheriting Release Manager controls because named-role action gates are applied first.

### 4. Action hardening

Sensitive actions were scoped to named roles, including template/request authoring, testing, release, reconciliation, rollback, retirement, legal holds, archive, dependencies, launch scheduling, bulk execution and Administration configuration. Legacy Administration mutation controls were also brought under the Platform Administrator/Product Classification Administrator scopes.

### 5. Role-aware Reports

Reports now render from the selected role. Switching from Test Analyst to Release Manager, for example, changes the dashboard and actions without changing the authenticated account.

### 6. Audit identity corrections

Hardened lifecycle operations now write the actual authenticated actor and selected role instead of older hard-coded Product Owner/Release Manager prototype identities where applicable.

### 7. Backend persistence markers

Administration now persists both:

- `testModeRoleModelVersion = 7.0`
- `roleScopeVersion = 7.0`

The startup migration is idempotent. Persisted Administration remains authoritative over seed data.

### 8. Existing fixes preserved

The v6/v6.1 Tariff Plans price-band recovery and scope matching remain intact. The approved Tariff Plans band in the delivered database is ₦100–₦5,000 and canonical machine type `priceBand`.

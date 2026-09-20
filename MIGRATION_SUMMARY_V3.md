# PLM Demo — Migration v3 Summary

## What changed

The demo has moved beyond the original whole-state persistence bridge.

### 1. Module-level persistence
The backend now stores 12 independently revisioned modules:

- catalogue
- templates
- requests
- workflow
- testing_release
- reconciliation
- exceptions
- retirement
- administration
- audit
- notifications
- onboarding

A change in Testing & Release no longer requires rewriting Product Catalogue, Administration, Templates, etc.

### 2. Optimistic concurrency
Every module has a revision. If two browser sessions edit the same module, stale saves receive HTTP 409 instead of overwriting newer data.

### 3. Transactional REST resources
Dedicated CRUD APIs are available for the major collections, including products, templates, requests, users, integrations, exceptions, retirement plans and onboarding batches.

### 4. Workflow action APIs
Dedicated actions are available for approval decisions and test execution records. They update only the owning module and write audit events.

### 5. Compatibility retained
The legacy `/api/state` endpoints remain for first-run bootstrap and older frontend code, but normal browser persistence now uses `/api/modules/*`.

### 6. Existing demo capabilities retained
- CSV/XLSX test case import
- CSV/XLSX estate import
- attachment uploads
- mock authoritative-system deployments
- demo reset
- SQLite zero-setup mode
- PostgreSQL-compatible deployment

## Recommended next engineering step

For a production-style pilot, move the highest-risk UI mutations to their dedicated action APIs first:

1. Product Request submit/withdraw
2. Approval decisions
3. Test case create/execute/retest
4. UAT and Production deployment actions
5. Reconciliation decisions
6. Retirement stage completion
7. Administration maker-checker approvals

The database/API foundation in v3 is ready for that progression.

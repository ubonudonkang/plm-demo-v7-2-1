# Migration Summary

## What changed

The PLM prototype is no longer limited to browser-memory state. The latest UI now boots against a FastAPI backend and persists the complete application state in a database. Core business records are also mirrored into queryable relational records so the migration can continue module by module without discarding the existing detailed screens.

## Migrated capabilities

- Persistent PLM state across refreshes and browser sessions
- Products API
- Templates API
- Product Requests API
- Users API
- Exceptions API
- Release pipeline API
- Audit API
- Prototype authentication lookup
- CSV/XLSX test-case import
- CSV/XLSX existing-estate import endpoint
- Attachment storage
- Mock authoritative-system deployment adapters
- Demo reset
- SQLite local database for immediate use
- PostgreSQL/Supabase-ready connection model and schema reference
- Docker Compose option with PostgreSQL

## Migration approach

This is an incremental migration. The 1.2 MB prototype has a large amount of validated UI and conditional product configuration logic. Rewriting it all at once would introduce unnecessary regression risk. The backend bridge therefore persists the current application state while exposing normalized APIs. Individual modules can now be moved from whole-state persistence to dedicated API transactions progressively.

## Recommended next backend migrations

1. Product Classification and Templates
2. Product Requests and Impact/Risk
3. Workflow decisions
4. Test Plans/Test Cases/Defects
5. Production release and synchronization
6. Reconciliation/Discrepancies
7. Retirement
8. Administration and access governance

At each stage, remove the corresponding in-memory mutation and replace it with an API call plus server-side validation/authorization.

## V2 UX/Governance regression fixes

- Streamlined Template Creation controls for data volume, allowances, money, duration, counts, time windows, and service/app scope.
- Added compound value/unit controls and consistent N/A treatment for typed template fields.
- Added final request-detail deduplication for repeated Impact Analysis / Impact Assessment / Request Control cards caused by legacy stacked renderers.
- Product Rule / Price Band edits now create governed maker-checker proposals instead of modifying the active rule immediately.
- Administration now makes Pending Changes the first-class approval queue, with visible pending counts and a Review Pending Changes CTA.
- Governance review now shows Current vs Proposed values and the full proposed configuration payload.
- Extended governance approval application to Product Rules, Roles & Permissions, User Access, Lifecycle Transitions, Integration Contracts, Environment Policy, and Notification Rules.

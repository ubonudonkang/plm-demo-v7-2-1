# PLM Demo v7 — Role Catalogue

This test build permits one user to hold multiple overlapping roles. The role selected in the header determines the active module/action scope. Mutolib Ottan holds all 21 roles for testing; Chiamaka Eleodi is seeded as Product Manager.

| Role | Primary purpose | Module scope |
|---|---|---|
| Product Manager | Own product lifecycle and commercial product changes | Dashboard, Catalogue, Templates, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit |
| Product Owner | Create/manage product configuration and lifecycle requests | Dashboard, Catalogue, Templates, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit |
| Pricing / MKT BI | Review pricing/commercial impacts | Dashboard, Catalogue, Requests, Workflow, Reports, Audit |
| Finance / Tax | Review finance and taxation impacts | Dashboard, Catalogue, Requests, Workflow, Reports, Audit |
| Business Assurance | Independent business approval and UAT evidence acceptance | Dashboard, Catalogue, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit |
| Customer Experience | Review customer impact | Dashboard, Catalogue, Requests, Workflow, Reports, Audit |
| Technology Approver | Review technology impacts and required approvals | Dashboard, Catalogue, Requests, Workflow, Testing, Reconciliation, Reports, Audit |
| Technical Owner | Own technical dependencies and implementation context | Dashboard, Catalogue, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit |
| Regulatory / Legal | Regulatory/legal review and controlled holds | Dashboard, Catalogue, Requests, Workflow, Exceptions, Retirement, Reports, Audit |
| Executive Sponsor | Executive approval for high-risk changes | Dashboard, Requests, Workflow, Reports, Audit |
| CAB / Change Manager | Change/release governance for high-risk changes | Dashboard, Requests, Workflow, Testing, Reports, Audit |
| Test Analyst | Define and execute UAT cases/evidence | Dashboard, Catalogue, Requests, Testing, Reports, Audit |
| Release Manager | UAT/Production deployment and release scheduling | Dashboard, Catalogue, Requests, Workflow, Testing, Reconciliation, Exceptions, Reports, Audit |
| Reconciliation & Monitoring Analyst | Post-deployment reconciliation, drift and monitoring | Dashboard, Catalogue, Requests, Testing, Reconciliation, Exceptions, Reports, Audit |
| Exception & Rollback Manager | Exception resolution and rollback execution | Dashboard, Catalogue, Requests, Testing, Reconciliation, Exceptions, Reports, Audit |
| Product Governance | Retirement/governance controls and lifecycle oversight | Dashboard, Catalogue, Requests, Workflow, Exceptions, Retirement, Reports, Audit |
| Records Manager | Retention and archive of retired product records | Dashboard, Catalogue, Retirement, Reports, Audit |
| Compliance Officer | Legal holds, regulatory controls and control overrides | Dashboard, Catalogue, Requests, Workflow, Exceptions, Retirement, Reports, Audit |
| Audit & Compliance Reviewer | Evidence review, audit and reporting | Dashboard, Catalogue, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit |
| Product Classification Administrator | Maintain governed product taxonomy/classification | Dashboard, Catalogue, Reports, Audit, Administration (Taxonomy only) |
| Platform Administrator | Full platform/configuration administration | Dashboard, Catalogue, Templates, Requests, Workflow, Testing, Reconciliation, Exceptions, Retirement, Reports, Audit, Administration |

## Legacy workflow aliases

Existing demo data is retained. The following older labels resolve to the canonical role at runtime:

- `Finance` → `Finance / Tax`
- `Technology` → `Technology Approver`
- `Regulatory` / `Legal / Regulatory` → `Regulatory / Legal`
- `CAB` → `CAB / Change Manager`
- `Records / Governance` → `Records Manager`
- `Compliance` → `Compliance Officer`
- `Release / Test Analyst` → `Test Analyst`
- generic `Approver` → `Business Assurance`

## Test-mode control position

Role-combination SoD is disabled for access assignment so a test user can hold Product Owner, Test Analyst, Release Manager, Platform Administrator and other roles simultaneously. The selected role still controls what the UI exposes and what role is written to approval/audit evidence. Existing transaction-level maker-checker controls for governed Administration changes remain active.

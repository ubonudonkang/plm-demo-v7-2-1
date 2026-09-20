# PLM Demo v6.2 Regression Record

Date: 18 September 2026

## Scope

This regression validates the v6.2 multi-role test-mode changes while preserving the v6/v6.1 Tariff Plans price-band repair and the broader PLM v5 feature set.

## Requested fixes

| Area | Result | Evidence |
|---|---|---|
| Product Owner Create Template | PASS | Uche Chiemejonam can click Create Template; route opens the template creation screen and initializes a draft. |
| Role switching without logout | PASS | Mutolib Ottan switches assigned roles from the header while the authenticated account and `authed` session remain unchanged. |
| Multiple roles per user | PASS | Administration saves overlapping roles directly in test mode; role-combination SoD returns no conflicts. |
| Full role catalogue | PASS | 21 canonical active roles are present. Workflow aliases resolve to configured roles. |
| Chiamaka Eleodi | PASS | Active user seeded with Product Manager role. |
| All-role test persona | PASS | Mutolib Ottan has all 21 canonical roles. |
| Access assignment maker-checker | RELAXED AS REQUESTED | User/role assignment changes are direct in test mode. |
| Governed configuration maker-checker | PASS / RETAINED | Price-band maker cannot approve own proposal; a different Platform Administrator can approve. |

## Canonical roles

1. Product Manager
2. Product Owner
3. Pricing / MKT BI
4. Finance / Tax
5. Business Assurance
6. Customer Experience
7. Technology Approver
8. Technical Owner
9. Regulatory / Legal
10. Executive Sponsor
11. CAB / Change Manager
12. Test Analyst
13. Release Manager
14. Reconciliation & Monitoring Analyst
15. Exception & Rollback Manager
16. Product Governance
17. Records Manager
18. Compliance Officer
19. Audit & Compliance Reviewer
20. Product Classification Administrator
21. Platform Administrator

## Regression results

| Check | Result |
|---|---|
| `scripts/qa_v6_2_roles.py` | PASS — 21 roles, Create Template PASS, multi-role assignment PASS, role switching PASS, Chiamaka PASS, 0 page errors |
| `scripts/qa_v5.py` | PASS — templates=5, actions=289 |
| `scripts/qa_v6_price_band.py` | PASS — recovery, scope matching, maker-checker, canonical `priceBand`, 0 page errors |
| `scripts/browser_qa_v5.py` | PASS — 5 certified templates, 106 taxonomy nodes, 0 page errors |
| `scripts/browser_qa_deep_v5.py` | PASS — wizard, templates, add-ons, Administration, Testing & Release, module/details |
| `scripts/smoke_test.py` | PASS — SQLite health, products=21, requests=13, users=10 |
| `scripts/smoke_test_v3.py` | PASS — modules=12, products=21, templates=7, requests=13, users=10 |
| CSV test-case import | PASS — valid row accepted; QA batch removed afterward |
| XLSX existing-estate import | PASS — valid row accepted; QA batch removed afterward |
| Administration restart idempotence | PASS — revision remained 18 after restart |
| Tariff Plans approved band | PASS — persisted `priceBand`, ₦100–₦5,000, active, All products scope |

## Additional fixes found during audit

- Removed stale access-request wording that said role combinations were blocked.
- Updated the header role selector label/title to describe active-role switching rather than the old prototype behavior.
- Added Technical Owner, Records Manager and Compliance Officer because the workflows already referenced those functions but Administration did not contain corresponding roles.
- Normalized legacy workflow role labels so approval routes and lifecycle transitions reference actual configured roles.
- Kept the existing v6.1 startup/persistence behavior so seed state does not overwrite persisted Administration state.

## Environment note

The execution environment blocks headless Chromium from navigating directly to `127.0.0.1` (`ERR_BLOCKED_BY_ADMINISTRATOR`). Browser regression therefore loads the packaged frontend directly, while live FastAPI/SQLite regression runs against the local server. Both sides passed independently; the packaged application uses the same frontend/backend files tested here.

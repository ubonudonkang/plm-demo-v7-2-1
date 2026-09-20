# PLM Demo v6.2 Fix Summary

PLM Demo v6.2 adds a permissive multi-role test mode and fixes Product Owner template creation while preserving governed price-band maker-checker behavior.

## Main changes

- Product Owner/Product Manager **Create Template** click path is explicitly handled and regression-tested.
- A user can hold multiple roles simultaneously.
- The active role can be switched from the header without logout or changing the authenticated user.
- Access-assignment role-combination segregation is disabled for this test build.
- User and role access configuration is applied directly in test mode rather than waiting for a separate access approver.
- Governed Administration changes such as price-band approval retain separate-user maker-checker control.
- 21 canonical roles are created and maintained automatically.
- Chiamaka Eleodi is added as an active Product Manager.
- Mutolib Ottan is maintained as the all-role test persona.
- Legacy approval/lifecycle role labels are normalized to the canonical role catalogue.
- Existing v6.1 Tariff Plans price-band recovery, rule normalization, seed/persistence precedence, request validation, CSV/XLSX imports and backend persistence are retained.

See `REGRESSION_V6_2.md` for detailed test results.

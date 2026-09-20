# PLM Demo v4 — Governance Queue Fix

## Root cause
Governed Administration changes are stored in `adminConfigV31.governanceChanges` inside the Administration module. Module persistence was working, but an already-open second browser/account did not reload the Administration module after another user saved a change. The admin dashboard also used a stale status predicate (`Pending Review`) instead of the actual governance state (`Pending Approval`).

## Fixes
- Force immediate module persistence when a governed change is submitted.
- Force immediate persistence after approval/rejection.
- Poll the Administration module every 2.5 seconds while the Pending Changes queue is open.
- Refresh only when the backend revision is newer and the local module has no unsaved edits.
- Add a manual **Refresh queue** button.
- Correct the admin dashboard pending-change count to use `state === 'Pending Approval'`.
- Keep maker-checker segregation: requester still cannot approve their own change.

## Result
A price-band proposal created by Mutolib is visible to the other Platform Administrator without restarting the demo. The other administrator can review Current vs Proposed values and approve/reject it.

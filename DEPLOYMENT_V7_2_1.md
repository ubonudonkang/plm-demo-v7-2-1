# PLM Demo v7.2.1 — fresh GitHub / Railway deployment

This build fixes a packaging issue in v7.2 where `data/*.db` was ignored by Git, so a fresh GitHub repository could omit the exact SQLite database used in regression.

## Fresh deployment

1. Create a new GitHub repository and commit this folder from its root (the folder containing `Dockerfile`).
2. Confirm `data/plm_demo.db` appears in GitHub.
3. Deploy that repository to Railway.
4. Before adding a volume, verify `/api/meta` reports `7.2.1` and the login screen shows `PLM Demo v7.2.1`.

## Persistent Railway volume

Mount a Railway volume at `/data` and set:

```text
PLM_DB_PATH=/data/plm_demo.db
```

On first start the app copies the prepared baseline database into the volume. On later starts it uses the existing persisted database and never overwrites it.

`DATABASE_URL` still takes precedence if explicitly configured.

## Verification

- `/api/health` includes version `7.2.1`.
- `/api/meta` reports version `7.2.1`.
- Data Volume is numeric with MB/GB/TB selector.
- Validity is numeric days.
- Approved data price bands are present in the prepared database.

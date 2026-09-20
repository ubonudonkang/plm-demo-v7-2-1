# PLM Demo v7.1 — Data Request Form & Price Validation Fix

## Fixes

- Fixed Data Bundle request validation so `dataPrice` is treated as the request's commercial/headline price for approved price-band validation. A populated Data Price no longer incorrectly triggers `Price is mandatory and must sit within the approved price band.`
- Preserved the generic `price` field for Tariff Plans and other non-data products.
- Data Volume now uses a numeric value plus an integrated MB / GB / TB unit selector.
- Renamed and clarified ambiguous Data Bundle fields:
  - `Voice minutes add-on` → `Included voice minutes (optional)` with guidance.
  - `YouTube Night allowance` → `YouTube night data allowance (optional)` using a structured quantity/unit control.
  - `YouTube Day allowance` → `YouTube daytime data allowance (optional)` using a structured quantity/unit control.
  - `Other bundled add-ons` → `Other bundled benefits (optional)` with a multiline description field.
  - `Transferability / additional info` → structured `Data transfer / gifting` selection: Not allowed / Allowed / Conditional, with a separate conditions field when applicable.
- Backward compatibility is retained: quantity controls persist values such as `25 GB`, and existing seeded values such as `4GB` / `N/A` still render correctly.
- Existing approved price-band recovery, rule normalization, maker-checker and v7 role controls remain unchanged.

## Root cause of the price error

Data Bundle forms write the commercial charge to `dataPrice`. The legacy validation function checked only the generic Tariff Plan field `price` before calling approved-band validation. Therefore a request with a valid Data Price could be rejected as if no price had been entered. v7.1 temporarily presents `dataPrice` to the shared validator as the effective request price without mutating the stored request schema.

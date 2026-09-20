# PLM Demo v7.2 — Request Form Quality & Price-Band Synchronisation

## Summary

v7.2 hardens the Product Request experience after a wider form audit. The release focuses on semantic input controls, consistent mandatory-field communication, removal of ambiguous editable `N/A` defaults, and deterministic consumption of newly approved Administration price bands across concurrent demo users.

## Data Bundle form improvements

- **Data volume** now accepts a number only and uses an integrated right-side unit selector: **MB / GB / TB**.
- **Validity** now accepts a positive whole number only; the UI supplies the fixed **days** unit.
- **Price (₦)** is a numeric control and is validated against the latest approved commercial price band.
- **Included voice minutes** is an optional numeric field with a `minutes` suffix. Blank means no voice benefit is included.
- **YouTube night data allowance** and **YouTube daytime data allowance** use numeric value + MB/GB/TB controls. Blank means no dedicated allowance.
- **Other bundled benefits** is an optional free-text description rather than an ambiguous `N/A` input.
- **Data transfer / gifting** is an explicit enum: `Not allowed`, `Allowed`, or `Conditional`. Conditional rules are captured only when `Conditional` is selected.
- Legacy request values containing editable `N/A` are normalised to blank optional fields when the section renders.

## Mandatory-field consistency

- Service Class shows the red required marker whenever the existing validation rules make it mandatory.
- Data Product Type, Plan class / duration, Data volume, Price, Validity, and other conditional mandatory fields are aligned with their validators.
- A DOM-level required-marker synchroniser now applies the red `*` to every visible field that the current Product Request validator considers mandatory. This prevents later template/render overrides from silently dropping required markers.

## Price-band defect — additional root cause and fix

Two independent issues could make an approved price band appear ineffective:

1. Data Bundle commercial price is stored in `dataPrice`, while the legacy shared validator expects `price`.
2. In a multi-user maker-checker flow, a Product Owner browser could retain an older Administration snapshot after another user approved and activated a price-band rule.

v7.2 fixes both paths:

- `dataPrice` is treated as the effective headline price for Data Bundle baseline validation without changing the persisted request schema.
- The approved Administration product-rule registry is an authoritative source for active numeric price bands.
- Immediately before **Validate** and **Submit**, the browser reloads the persisted Administration module from the backend and repairs/normalises approved price-band rows.
- While a request wizard is open, Administration is refreshed periodically so a newly approved rule becomes visible without logging out or reloading the page.
- Missing price and out-of-band price now have different messages. A Data Bundle with no price reports `Data price is required.`; a populated price outside the approved range reports the approved range.

## Wider request-form audit

- Obvious monetary/quantity fields in other request sections were converted from generic text inputs to numeric controls where their semantics are unambiguous.
- Certified Product Request templates were scanned for editable fields that default to the literal text `N/A`; none remain in the rendered request forms.
- Explicit `N/A` remains only where the workflow presents it as a controlled option/toggle rather than ambiguous free text.

## API/build metadata

- FastAPI build metadata updated to **7.2.0**.

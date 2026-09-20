# PLM Demo v7.1 Regression

Status: PASS

## v7.1 targeted tests

- Data Bundle `dataPrice` is accepted as the commercial price: PASS
- In-band Data Price validates against approved price band: PASS
- Out-of-band Data Price is rejected with the approved-range error: PASS
- Data Volume numeric control: PASS
- Data Volume unit options MB / GB / TB: PASS
- Quantity/unit persistence (`25 GB`): PASS
- Clarified voice, YouTube and bundled-benefit labels: PASS
- Structured transfer/gifting control: PASS
- Browser page errors: 0

## Existing regression

- `qa_v5.py`: PASS
- `qa_v6_price_band.py`: PASS
- `qa_v6_2_roles.py`: PASS
- `qa_v7_role_catalogue.py`: PASS
- `qa_v7_role_scope.py`: PASS
- `browser_qa_v5.py`: PASS, 0 page errors
- `browser_qa_deep_v5.py`: PASS
- Price-band maker-checker and approved-state activation: PASS
- 21-role scope model: PASS
- Chiamaka Eleodi Product Manager persona: PASS
- Product Owner Create Template: PASS

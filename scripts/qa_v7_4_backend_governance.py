import importlib
import json
import os
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix="plm-v74-") as temp_dir:
        os.environ["PLM_DB_PATH"] = str(pathlib.Path(temp_dir) / "qa.db")
        app = importlib.import_module("backend.app")

        approval_request = {
            "id": "REQ-QA-SEQUENCE",
            "status": "Pending Approval",
            "typeKey": "modify",
            "sla": "Within SLA",
            "approvals": [
                {"role": "Product Owner", "state": "Pending"},
                {"role": "Pricing / MKT BI", "state": "Not started"},
                {"role": "Business Assurance", "state": "Not started"},
            ],
            "gates": [["G4", "Complete approval", "active", "0 of 3 complete"]],
        }
        withdrawal_request = {
            "id": "REQ-QA-WITHDRAW",
            "status": "Pending Approval",
            "approvals": [
                {"role": "Product Owner", "state": "Approved"},
                {"role": "Business Assurance", "state": "Pending"},
            ],
        }
        with app.Session(app.engine) as session:
            row = session.get(app.ModuleState, "requests")
            if row is None:
                row = app.ModuleState(module_name="requests", revision=1, updated_by="qa", data_json="{}")
                session.add(row)
            row.data_json = json.dumps({"requests": [approval_request, withdrawal_request]})
            session.commit()

        try:
            app.protect_controlled_request_updates(
                {"requests": [approval_request]},
                {"requests": [{**approval_request, "status": "Approved"}]},
            )
            raise AssertionError("generic approval-state mutation was accepted")
        except app.HTTPException as exc:
            assert exc.status_code == 409

        first = app.record_approval_decision(
            approval_request["id"],
            app.ApprovalDecisionPayload(
                role="Product Owner", actor="Uche Chiemejonam", decision="Approved", note="Owner approved"
            ),
        )["request"]
        assert [x["state"] for x in first["approvals"]] == ["Approved", "Pending", "Not started"]
        assert first["status"] == "Pending Approval"

        try:
            app.record_approval_decision(
                approval_request["id"],
                app.ApprovalDecisionPayload(
                    role="Business Assurance", actor="Mercy Andrew", decision="Approved", note="Out of turn"
                ),
            )
            raise AssertionError("later approver was able to act out of turn")
        except app.HTTPException as exc:
            assert exc.status_code == 409

        second = app.record_approval_decision(
            approval_request["id"],
            app.ApprovalDecisionPayload(
                role="Pricing / MKT BI", actor="Lucky Christopher", decision="Approved", note="Pricing approved"
            ),
        )["request"]
        assert [x["state"] for x in second["approvals"]] == ["Approved", "Approved", "Pending"]

        final = app.record_approval_decision(
            approval_request["id"],
            app.ApprovalDecisionPayload(
                role="Business Assurance", actor="Mercy Andrew", decision="Approved", note="BA approved"
            ),
        )["request"]
        assert final["status"] == "Approved"
        assert final["gates"][0][2:] == ["pass", "3 of 3 complete"]

        withdrawn = app.withdraw_request(
            withdrawal_request["id"],
            app.RequestWithdrawalPayload(actor="Uche Chiemejonam", reason="No longer required"),
        )["request"]
        assert withdrawn["status"] == "Cancelled"
        assert withdrawn["approvals"][1]["state"] == "Withdrawn"

        with app.Session(app.engine) as session:
            api_keys = set(session.scalars(app.select(app.AuditEvent.event_key)).all())
            assert api_keys
            app.normalize_state({"requests": [], "audit": []}, session)
            session.commit()
        with app.Session(app.engine) as session:
            after_keys = set(session.scalars(app.select(app.AuditEvent.event_key)).all())
            assert api_keys.issubset(after_keys)

        app.engine.dispose()
        print(
            json.dumps(
                {
                    "PASS": True,
                    "generic_approval_mutation_guard": "PASS",
                    "strict_sequential_route": "PASS",
                    "out_of_turn_rejection": "PASS",
                    "approved_terminal_state": "PASS",
                    "governed_withdrawal": "PASS",
                    "append_only_audit": "PASS",
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

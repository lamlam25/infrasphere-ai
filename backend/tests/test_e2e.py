"""
End-to-End Flagship Workflow Acceptance Test.
Tests the complete multi-agent lifecycle on the Sunamganj flood incident INC-0041:
SecureAI -> Triage -> Knowledge Grid -> Risk -> WorkforceOS -> Response -> Human Approval -> Audit Chain.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_full_incident_investigation_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login as manager
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "manager@infrasphere.bd", "password": "Demo1234!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get incident INC-0041
        inc_res = await ac.get("/api/v1/incidents/INC-0041", headers=headers)
        assert inc_res.status_code == 200
        incident = inc_res.json()
        assert incident["id"] == "INC-0041"
        assert incident["district"] == "Sunamganj"

        # 3. Trigger multi-agent analysis
        analyze_res = await ac.post("/api/v1/incidents/INC-0041/analyze", headers=headers)
        assert analyze_res.status_code == 200
        workflow_data = analyze_res.json()

        assert "workflow_id" in workflow_data
        assert workflow_data["status"] == "waiting_approval"
        assert "triage" in workflow_data["agent_results"]
        assert "risk" in workflow_data["agent_results"]
        assert "knowledge" in workflow_data["agent_results"]
        assert "workforce" in workflow_data["agent_results"]
        assert "response" in workflow_data["agent_results"]

        # 4. Inspect risk score
        risk_data = workflow_data["agent_results"]["risk"]
        assert risk_data["risk_score"] > 0
        assert "limitations" in risk_data

        # 5. Inspect approval request created by Response Agent
        approval_id = workflow_data["approval_id"]
        assert approval_id is not None

        appr_res = await ac.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert appr_res.status_code == 200
        appr_data = appr_res.json()
        assert appr_data["status"] == "pending"

        # 6. Human Manager approves the recommendation
        dec_res = await ac.post(
            f"/api/v1/approvals/{approval_id}/decision",
            headers=headers,
            json={"decision": "approved", "comment": "Ground inspection prioritized as per FFWC telemetry."},
        )
        assert dec_res.status_code == 200
        dec_data = dec_res.json()
        assert dec_data["success"] is True
        assert dec_data["data"]["status"] == "approved"

        # 7. Verify tamper-evident audit trail integrity
        audit_verify_res = await ac.get("/api/v1/audit/verify", headers=headers)
        assert audit_verify_res.status_code == 200
        verify_data = audit_verify_res.json()
        print("\n\n=== VERIFY DATA ===", verify_data, "\n\n")
        assert verify_data["verified"] is True
        assert verify_data["events_checked"] > 0


from typing import Any


class SAPService:
    """SAP integration boundary.

    This is a production-style adapter boundary. In the demo it returns a
    deterministic payload; later it can call SAP PM/QM/SuccessFactors APIs.
    """

    def build_notification_payload(
        self,
        report_number: str,
        collected_data: dict[str, Any],
        report_ai: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        report_ai = report_ai or {}
        return {
            "external_id": report_number,
            "notification_type": "HSE_ANOMALY",
            "short_text": report_ai.get("title") or f"Signalement HSE {report_number}",
            "priority": report_ai.get("urgency", "MEDIUM"),
            "location": collected_data.get("location"),
            "description": collected_data.get("description"),
            "recommended_action": report_ai.get("recommended_action") or collected_data.get("immediate_action"),
            "declarant": collected_data.get("declarant"),
            "status": "READY_TO_SEND" if report_ai.get("sap_ready") else "DRAFT",
        }

    def send_notification(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "sent": False,
            "mode": "mock",
            "message": "SAP non configure. Payload prepare pour integration future.",
            "payload": payload,
        }


sap_service = SAPService()

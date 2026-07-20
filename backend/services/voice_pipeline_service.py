from typing import Any

from sqlalchemy.orm import Session

from agents.emergency_agent import emergency_agent
from agents.intent_agent import intent_agent
from agents.report_agent import report_agent
from sap.sap_service import sap_service
from services.conversation_service import conversation_service
from services.report_service import ReportService
from speech.speech_to_text import speech_to_text_adapter
from speech.text_to_speech import text_to_speech_adapter


class VoicePipelineService:
    """Agentic voice pipeline: STT -> agents/RAG -> dialog -> form -> storage/TTS."""

    def process_voice_message(
        self,
        session_id: str,
        transcript: str,
        db: Session,
        source: str = "browser_speech_recognition",
    ) -> dict[str, Any]:
        normalized_transcript = speech_to_text_adapter.accept_transcript(transcript)

        pipeline = [
            {
                "name": "speech_to_text",
                "status": "done",
                "detail": f"Transcript normalized from {source}.",
            }
        ]

        intent_result = intent_agent._fallback(normalized_transcript)
        pipeline.append(
            {
                "name": "intent_agent",
                "status": "quick",
                "detail": f"intent={intent_result.get('intent')} language={intent_result.get('language')}",
            }
        )

        emergency_result = emergency_agent._fallback(normalized_transcript, [])
        pipeline.append(
            {
                "name": "emergency_agent_rag",
                "status": "quick",
                "detail": (
                    f"urgency={emergency_result.get('urgency')} "
                    f"immediate_danger={emergency_result.get('immediate_danger')}"
                ),
            }
        )

        agent_result = conversation_service.process_message(
            session_id=session_id,
            message=normalized_transcript,
            db=db,
        )

        report_ai = {"sap_ready": False, "urgency": None, "missing_fields": []}
        step_value = str(agent_result["step"].value if hasattr(agent_result["step"], "value") else agent_result["step"])
        should_enrich_report = agent_result["completed"] or step_value in {"summary", "confirmation", "completed"}
        if should_enrich_report:
            try:
                report_ai = report_agent.quick_enrich(
                    collected_data=agent_result["data"],
                    latest_message=normalized_transcript,
                )
                report_status = "done"
            except Exception as exc:
                report_ai = {"sap_ready": False, "urgency": None, "missing_fields": [], "error": str(exc)}
                report_status = "error"
        else:
            report_status = "skipped"

        pipeline.append(
            {
                "name": "report_agent_rag",
                "status": report_status,
                "detail": f"sap_ready={report_ai.get('sap_ready')} urgency={report_ai.get('urgency')}",
            }
        )

        agent_result["response"] = text_to_speech_adapter.prepare_speech_text(
            agent_result["response"]
        )
        pipeline.append(
            {
                "name": "text_to_speech",
                "status": "ready",
                "detail": "Assistant response prepared for browser voice synthesis.",
            }
        )

        sap_payload = None
        if agent_result["completed"]:
            sap_payload = sap_service.build_notification_payload(
                report_number=agent_result["data"].get("report_number", "DRAFT"),
                collected_data=agent_result["data"],
                report_ai=report_ai,
            )
            ReportService.update_ai_context(
                db=db,
                report_id=agent_result["data"].get("report_id"),
                report_ai=report_ai,
                agent_trace={
                    "intent": intent_result,
                    "emergency": emergency_result,
                    "report": report_ai,
                },
                sap_payload=sap_payload,
                source=source,
            )
            pipeline.append(
                {
                    "name": "storage_sap_boundary",
                    "status": "done",
                    "detail": "Report persisted in PostgreSQL and SAP payload prepared.",
                }
            )
        else:
            pipeline.append(
                {
                    "name": "storage_sap_boundary",
                    "status": "pending",
                    "detail": "Storage waits for final user confirmation.",
                }
            )

        return {
            **agent_result,
            "pipeline": pipeline,
            "agent_trace": {
                "intent": intent_result,
                "emergency": emergency_result,
                "report": report_ai,
                "sap_payload": sap_payload,
            },
        }


voice_pipeline_service = VoicePipelineService()


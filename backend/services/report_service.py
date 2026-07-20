from datetime import datetime
import unicodedata
import re
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from core.database import engine
from models.report import Report
from schemas.report import ReportCreate
from speech.speech_to_text import speech_to_text_adapter
from agents.report_agent import report_agent



def normalize_classification(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    normalized = normalized.replace("?", "").replace("’", "'")
    normalized = " ".join(normalized.split())

    unsafe_act_markers = {
        "acte dangereux",
        "act dangereux",
        "unsafe act",
        "comportement dangereux",
        "action dangereuse",
    }
    unsafe_condition_markers = {
        "situation dangereuse",
        "condition dangereuse",
        "unsafe condition",
        "dangerous situation",
        "situation danger",
    }

    if any(marker in normalized for marker in unsafe_act_markers):
        return "Acte dangereux"
    if any(marker in normalized for marker in unsafe_condition_markers):
        return "Situation dangereuse"
    return "Situation dangereuse" if not normalized else value.strip().rstrip(" ?")


def normalize_urgency(value: str | None) -> str | None:
    raw_value = (value or "").strip()
    if not raw_value:
        return None

    normalized = unicodedata.normalize("NFKD", raw_value.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())

    if normalized in {"critical", "critique", "tres elevee", "tres eleve", "extreme", "urgent critique"}:
        return "CRITICAL"
    if normalized in {"high", "haute", "elevee", "eleve", "forte", "urgent", "urgente"}:
        return "HIGH"
    if normalized in {"medium", "moyenne", "moderee", "modere"}:
        return "MEDIUM"
    if normalized in {"low", "faible", "basse"}:
        return "LOW"

    upper_value = raw_value.upper()
    return upper_value if upper_value in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else raw_value



def normalize_status(value: str | None) -> str:
    raw_value = (value or "nouveau").strip()
    if not raw_value:
        return "Nouveau"

    normalized = unicodedata.normalize("NFKD", raw_value.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.replace("?", "e")
    normalized = " ".join(normalized.split())

    if normalized in {"nouveau", "new", "open", "ouvert"}:
        return "Nouveau"
    if normalized in {"en cours", "traitement", "a traiter", "suivi", "pending"}:
        return "En cours"
    if normalized in {"termine", "traite", "closed", "cloture", "cloturee", "done"}:
        return "Traité"
    if normalized in {"annule", "annulee", "cancelled"}:
        return "Annulé"
    return raw_value[:1].upper() + raw_value[1:]


def display_urgency(value: str | None) -> str:
    return normalize_urgency(value) or "Non évaluée"


def urgency_rank(value: str | None) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(normalize_urgency(value) or "", 0)


def normalize_sap_ready(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("status") in {"READY_TO_SEND", "SENT", "PREPARED"}

EXTRA_REPORT_COLUMNS = {
    "reclamant_name": "VARCHAR(150)",
    "session_id": "VARCHAR(120)",
    "language": "VARCHAR(30)",
    "source": "VARCHAR(80)",
    "ai_title": "VARCHAR(255)",
    "urgency": "VARCHAR(50)",
    "danger_type": "VARCHAR(120)",
    "recommended_action": "TEXT",
    "raw_collected_data": "JSON",
    "transcript_history": "JSON",
    "rag_sources": "JSON",
    "agent_trace": "JSON",
    "sap_payload": "JSON",
}


def ensure_report_schema() -> None:
    """Add demo-era report columns when the DB table already exists."""
    inspector = inspect(engine)
    if not inspector.has_table("reports"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("reports")}
    missing_columns = [
        (name, ddl_type)
        for name, ddl_type in EXTRA_REPORT_COLUMNS.items()
        if name not in existing_columns
    ]
    if not missing_columns:
        return

    dialect = engine.dialect.name
    with engine.begin() as connection:
        for name, ddl_type in missing_columns:
            column_type = "JSONB" if dialect == "postgresql" and ddl_type == "JSON" else ddl_type
            connection.execute(text(f"ALTER TABLE reports ADD COLUMN {name} {column_type}"))


class ReportService:
    @staticmethod
    def generate_report_number(
        db: Session,
    ) -> str:
        year = datetime.now().year

        last_report = (
            db.query(Report)
            .order_by(Report.id.desc())
            .first()
        )

        next_number = 1

        if last_report is not None:
            next_number = last_report.id + 1

        return f"SON-HSE-{year}-{next_number:05d}"

    @staticmethod
    def create(
        db: Session,
        report_data: ReportCreate,
    ) -> Report:
        data = report_data.model_dump()
        creation_text_fields = [
            "description",
            "event_datetime",
            "location",
            "observed_person",
            "declarant",
            "reclamant_name",
            "immediate_action",
            "risk_analysis",
        ]
        for field_name in creation_text_fields:
            value = data.get(field_name)
            if isinstance(value, str) and value.strip():
                data[field_name] = speech_to_text_adapter.fix_domain_terms(value)

        data["classification"] = normalize_classification(data.get("classification"))
        if not data.get("reclamant_name"):
            data["reclamant_name"] = data.get("declarant")

        if not data.get("recommended_action") or not data.get("urgency") or not data.get("danger_type"):
            try:
                report_ai = report_agent.quick_enrich(data, str(data.get("description") or ""))
                data["ai_title"] = data.get("ai_title") or report_ai.get("title")
                data["urgency"] = normalize_urgency(data.get("urgency") or report_ai.get("urgency"))
                data["danger_type"] = data.get("danger_type") or report_ai.get("danger_type")
                data["recommended_action"] = data.get("recommended_action") or report_ai.get("recommended_action")
                data["rag_sources"] = data.get("rag_sources") or report_ai.get("rag_sources")
                data["agent_trace"] = data.get("agent_trace") or {"mode": "auto_report_agent", "report": report_ai}
            except Exception as exc:
                data["agent_trace"] = data.get("agent_trace") or {"mode": "auto_report_agent_error", "error": str(exc)}

        report = Report(**data)

        db.add(report)
        db.commit()
        db.refresh(report)

        return report

    @staticmethod
    def update_ai_context(
        db: Session,
        report_id: int,
        report_ai: dict[str, Any] | None = None,
        agent_trace: dict[str, Any] | None = None,
        sap_payload: dict[str, Any] | None = None,
        source: str | None = None,
    ) -> Report | None:
        report = db.get(Report, report_id)
        if report is None:
            return None

        report_ai = report_ai or {}
        report.ai_title = report_ai.get("title")
        report.urgency = normalize_urgency(report_ai.get("urgency"))
        report.danger_type = report_ai.get("danger_type")
        report.recommended_action = report_ai.get("recommended_action")
        report.rag_sources = report_ai.get("rag_sources")
        report.agent_trace = agent_trace
        report.sap_payload = sap_payload
        if source:
            report.source = source

        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def normalize_existing_reports(db: Session) -> int:
        updated = 0
        reports = db.query(Report).all()
        text_fields = [
            "classification",
            "description",
            "event_datetime",
            "location",
            "observed_person",
            "declarant",
            "reclamant_name",
            "immediate_action",
            "risk_analysis",
            "recommended_action",
        ]

        for report in reports:
            if not report.reclamant_name and report.declarant:
                report.reclamant_name = report.declarant
                updated += 1

            normalized_classification = normalize_classification(report.classification)
            if report.classification != normalized_classification:
                report.classification = normalized_classification
                updated += 1

            normalized_urgency = normalize_urgency(report.urgency)
            if report.urgency != normalized_urgency:
                report.urgency = normalized_urgency
                updated += 1

            for field_name in text_fields:
                value = getattr(report, field_name, None)
                if not isinstance(value, str) or not value.strip():
                    continue

                corrected = speech_to_text_adapter.fix_domain_terms(value)
                corrected = corrected.replace("concern?e", "concernee")
                corrected = corrected.replace("s'?loigner", "s'eloigner")
                corrected = corrected.replace("?lectrocution", "electrocution")
                corrected = corrected.replace("arr?t", "arret")
                if corrected != value:
                    setattr(report, field_name, corrected)
                    updated += 1

            if not report.recommended_action or not report.urgency or not report.danger_type:
                try:
                    collected_data = {
                        "classification": report.classification,
                        "description": report.description,
                        "event_datetime": report.event_datetime,
                        "location": report.location,
                        "observed_person": report.observed_person,
                        "declarant": report.declarant,
                        "immediate_action": report.immediate_action,
                        "risk_analysis": report.risk_analysis,
                    }
                    report_ai = report_agent.quick_enrich(collected_data, str(report.description or ""))
                    report.ai_title = report.ai_title or report_ai.get("title")
                    report.urgency = normalize_urgency(report.urgency or report_ai.get("urgency"))
                    report.danger_type = report.danger_type or report_ai.get("danger_type")
                    report.recommended_action = report.recommended_action or report_ai.get("recommended_action")
                    report.rag_sources = report.rag_sources or report_ai.get("rag_sources")
                    report.agent_trace = report.agent_trace or {"mode": "startup_auto_report_agent", "report": report_ai}
                    updated += 1
                except Exception:
                    pass

        if updated:
            db.commit()

        return updated

    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Report | None:
        return db.get(Report, report_id)

    @staticmethod
    def _location_dashboard_label(location: str | None) -> str:
        value = (location or "Non renseignee").strip()
        zone_match = re.search(r"\bzone\s+(\d{1,2})\s*-\s*([^,]+)", value, flags=re.IGNORECASE)
        if zone_match:
            return f"Zone {zone_match.group(1)} - {zone_match.group(2).strip()}"

        parts = [part.strip() for part in value.split(",") if part.strip()]
        if len(parts) >= 2:
            return parts[-1]
        return value

    @staticmethod
    def _is_open_status(status: str | None) -> bool:
        return normalize_status(status) not in {"Traité", "Annulé"}

    @staticmethod
    def dashboard_data(db: Session) -> dict[str, Any]:
        reports = ReportService.get_all(db)
        total = len(reports)
        today = datetime.now().date()

        dashboard_reports: list[dict[str, Any]] = []
        for report in reports:
            urgency = display_urgency(report.urgency)
            status = normalize_status(report.status)
            classification = normalize_classification(report.classification)
            sap_ready = normalize_sap_ready(report.sap_payload)
            location_label = ReportService._location_dashboard_label(report.location)
            priority_score = urgency_rank(urgency) + (3 if report.immediate_danger else 0)

            dashboard_reports.append(
                {
                    "id": report.id,
                    "report_number": report.report_number,
                    "reclamant": report.reclamant_name or report.declarant or "Non renseigné",
                    "classification": classification,
                    "location": report.location,
                    "location_label": location_label,
                    "event_datetime": report.event_datetime,
                    "created_at": report.created_at.isoformat(timespec="seconds") if report.created_at else None,
                    "immediate_danger": bool(report.immediate_danger),
                    "status": status,
                    "urgency": urgency,
                    "danger_type": report.danger_type or "Non renseigné",
                    "recommended_action": report.recommended_action or "Non renseigné",
                    "source": report.source or "Non renseigné",
                    "sap_ready": sap_ready,
                    "priority_score": priority_score,
                    "pdf_url": f"/reports/{report.id}/pdf",
                }
            )

        immediate = sum(1 for report in dashboard_reports if report["immediate_danger"])
        open_reports = sum(1 for report in dashboard_reports if report["status"] not in {"Traité", "Annulé"})
        sap_ready_count = sum(1 for report in dashboard_reports if report["sap_ready"])
        created_today = sum(
            1 for report in reports
            if getattr(report, "created_at", None) and report.created_at.date() == today
        )
        high_priority = sum(1 for report in dashboard_reports if report["urgency"] in {"HIGH", "CRITICAL"})
        waiting_sap = max(0, total - sap_ready_count)

        by_status: dict[str, int] = {}
        by_classification: dict[str, int] = {"Situation dangereuse": 0, "Acte dangereux": 0}
        by_urgency: dict[str, int] = {}
        by_location: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_danger_type: dict[str, int] = {}

        for report in dashboard_reports:
            by_status[report["status"]] = by_status.get(report["status"], 0) + 1
            by_classification[report["classification"]] = by_classification.get(report["classification"], 0) + 1
            by_urgency[report["urgency"]] = by_urgency.get(report["urgency"], 0) + 1
            by_location[report["location_label"]] = by_location.get(report["location_label"], 0) + 1
            by_source[report["source"]] = by_source.get(report["source"], 0) + 1
            by_danger_type[report["danger_type"]] = by_danger_type.get(report["danger_type"], 0) + 1

        by_classification = {key: value for key, value in by_classification.items() if value > 0}
        latest = dashboard_reports[:100]
        priority_queue = sorted(
            [report for report in dashboard_reports if report["priority_score"] > 0],
            key=lambda report: (report["priority_score"], report["id"]),
            reverse=True,
        )[:8]

        return {
            "kpis": {
                "total": total,
                "open_reports": open_reports,
                "immediate_danger": immediate,
                "sap_ready": sap_ready_count,
                "created_today": created_today,
                "high_priority": high_priority,
                "waiting_sap": waiting_sap,
            },
            "charts": {
                "by_status": by_status,
                "by_classification": by_classification,
                "by_urgency": by_urgency,
                "by_location": by_location,
                "by_source": by_source,
                "by_danger_type": by_danger_type,
            },
            "latest": latest,
            "priority_queue": priority_queue,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Report]:
        return (
            db.query(Report)
            .order_by(Report.id.desc())
            .all()
        )











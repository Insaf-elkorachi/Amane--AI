from typing import Any

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    report_number: str
    classification: str
    description: str
    event_datetime: str
    location: str
    observed_person: str | None = None
    declarant: str
    reclamant_name: str | None = None
    immediate_action: str
    risk_analysis: str
    immediate_danger: bool = False
    status: str = "nouveau"

    session_id: str | None = None
    language: str | None = None
    source: str | None = None

    ai_title: str | None = None
    urgency: str | None = None
    danger_type: str | None = None
    recommended_action: str | None = None

    raw_collected_data: dict[str, Any] | None = None
    transcript_history: list[dict[str, Any]] | None = None
    rag_sources: list[str] | None = None
    agent_trace: dict[str, Any] | None = None
    sap_payload: dict[str, Any] | None = None



class ManualReportCreate(BaseModel):
    classification: str
    description: str
    event_datetime: str
    location: str
    observed_person: str | None = None
    declarant: str
    reclamant_name: str | None = None
    immediate_action: str
    risk_analysis: str
    immediate_danger: bool = False
    status: str = "nouveau"
    urgency: str | None = None
    danger_type: str | None = None
    recommended_action: str | None = None

class ReportResponse(ReportCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(50), unique=True, nullable=False)

    classification = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    event_datetime = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)

    observed_person = Column(String(255), nullable=True)
    declarant = Column(String(150), nullable=False)
    reclamant_name = Column(String(150), nullable=True)
    immediate_action = Column(Text, nullable=False)
    risk_analysis = Column(Text, nullable=False)

    immediate_danger = Column(Boolean, default=False)
    status = Column(String(50), default="nouveau")

    session_id = Column(String(120), nullable=True)
    language = Column(String(30), nullable=True)
    source = Column(String(80), nullable=True)

    ai_title = Column(String(255), nullable=True)
    urgency = Column(String(50), nullable=True)
    danger_type = Column(String(120), nullable=True)
    recommended_action = Column(Text, nullable=True)

    raw_collected_data = Column(JSON, nullable=True)
    transcript_history = Column(JSON, nullable=True)
    rag_sources = Column(JSON, nullable=True)
    agent_trace = Column(JSON, nullable=True)
    sap_payload = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

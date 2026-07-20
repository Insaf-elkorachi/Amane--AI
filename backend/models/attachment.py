from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

from core.database import Base


class Attachment(Base):

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)

    report_id = Column(
        Integer,
        ForeignKey("reports.id")
    )

    file_path = Column(String(255))

    file_type = Column(String(50))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
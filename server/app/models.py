from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database import Base


class PDFDocument(Base):
    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, unique=True, index=True)
    original_name = Column(String, nullable=False)
    topic = Column(String, nullable=True, index=True)
    path = Column(String, nullable=False)
    num_pages = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_open = Column(Boolean, default=False)
    current_page = Column(Integer, default=1)

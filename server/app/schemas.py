from typing import Optional, Literal
from pydantic import BaseModel


class PDFBase(BaseModel):
    id: int
    filename: str
    original_name: str
    topic: Optional[str] = None
    path: str
    num_pages: int
    is_open: bool
    current_page: int

    class Config:
        from_attributes = True


class PDFListResponse(BaseModel):
    items: list[PDFBase]


class PDFUploadResponse(PDFBase):
    pass


class PDFOpenRequest(BaseModel):
    page: Optional[int] = None


class PDFPageRequest(BaseModel):
    mode: Literal["next", "prev", "set"] = "next"
    page: Optional[int] = None


class PDFClassifyRequest(BaseModel):
    topic: str

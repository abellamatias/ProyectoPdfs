from pathlib import Path
from typing import List, Optional
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader

from ..database import get_db
from .. import models
from ..config import settings
from ..services.dewey import classify_file
from ..schemas import (
    PDFBase,
    PDFListResponse,
    PDFUploadResponse,
    PDFOpenRequest,
    PDFPageRequest,
    PDFClassifyRequest,
)

router = APIRouter()


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFD", value)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


@router.get("/", response_model=PDFListResponse)
def list_pdfs(topic: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    # Se obtiene todo y se filtra en Python para soportar coincidencias parciales y
    # normalización sin acentos y sin distinción de mayúsculas/minúsculas.
    raw_items: List[models.PDFDocument] = (
        db.query(models.PDFDocument)
        .order_by(models.PDFDocument.created_at.desc())
        .all()
    )

    needle_raw = q or topic or ""
    needle = _normalize_text(needle_raw)
    if not needle:
        return {"items": raw_items}

    filtered: List[models.PDFDocument] = []
    for it in raw_items:
        hay_topic = _normalize_text(it.topic)
        hay_name = _normalize_text(it.original_name)
        if needle in hay_topic or needle in hay_name:
            filtered.append(it)
    return {"items": filtered}


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    storage_dir = settings.PDF_STORAGE_DIR
    storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = file.filename.replace(" ", "_")
    dest_path = storage_dir / safe_name

    i = 1
    while dest_path.exists():
        dest_path = storage_dir / f"{dest_path.stem}_{i}.pdf"
        i += 1

    content = await file.read()
    dest_path.write_bytes(content)

    try:
        reader = PdfReader(dest_path.as_posix())
        num_pages = len(reader.pages)
    except Exception:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No se pudo leer el PDF")

    # Clasificación automática con Dewey
    try:
        dewey_topic = classify_file(dest_path)
    except Exception:
        dewey_topic = None

    doc = models.PDFDocument(
        filename=dest_path.name,
        original_name=file.filename,
        path=dest_path.as_posix(),
        num_pages=num_pages,
        topic=dewey_topic,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{pdf_id}", response_model=PDFBase)
def get_pdf(pdf_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    return doc


@router.get("/{pdf_id}/file")
async def get_pdf_file(pdf_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    path = Path(doc.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=doc.original_name,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store",
            "Content-Disposition": f"inline; filename=\"{doc.original_name}\"",
        },
    )


@router.post("/{pdf_id}/open", response_model=PDFBase)
async def open_pdf(pdf_id: int, payload: PDFOpenRequest, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    doc.is_open = True
    if payload.page:
        doc.current_page = max(1, min(payload.page, doc.num_pages))
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{pdf_id}/close", response_model=PDFBase)
async def close_pdf(pdf_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    doc.is_open = False
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{pdf_id}/page", response_model=PDFBase)
async def change_page(pdf_id: int, payload: PDFPageRequest, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")

    if payload.mode == "next":
        doc.current_page = min(doc.current_page + 1, doc.num_pages)
    elif payload.mode == "prev":
        doc.current_page = max(doc.current_page - 1, 1)
    elif payload.mode == "set" and payload.page:
        doc.current_page = max(1, min(payload.page, doc.num_pages))

    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{pdf_id}/classify", response_model=PDFBase)
async def classify_pdf(pdf_id: int, payload: PDFClassifyRequest, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    doc.topic = payload.topic
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{pdf_id}")
async def delete_pdf(pdf_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.PDFDocument, pdf_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    # Borrar archivo físico si existe
    try:
        p = Path(doc.path)
        if p.exists():
            p.unlink()
    except Exception:
        # Continuar aunque no se pueda borrar el archivo
        pass
    # Borrar registro
    db.delete(doc)
    db.commit()
    return {"ok": True}

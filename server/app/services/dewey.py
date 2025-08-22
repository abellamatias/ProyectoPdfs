from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import re
from PyPDF2 import PdfReader
from ..config import settings

try:
    import requests  # type: ignore
except Exception:  # requests puede no estar instalado aún en tiempo de import
    requests = None  # type: ignore


def extract_text_from_pdf(path: Path, max_pages: int = 5) -> str:
    try:
        reader = PdfReader(path.as_posix())
        texts: list[str] = []
        for i, page in enumerate(reader.pages):
            if i >= max_pages:
                break
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""


_DEWEY_RULES: list[tuple[str, str, list[str]]] = [
    ("005", "Informática", [
        r"\bcomputaci[oó]n\b", r"\binform[aá]tica\b", r"\balgoritmo(s)?\b", r"\bprogramaci[oó]n\b",
        r"\bsoftware\b", r"\bdatos\b", r"\binteligencia artificial\b", r"\bIA\b",
    ]),
    ("510", "Matemáticas", [r"\bmatem[aá]tica(s)?\b", r"\bc[aá]lculo\b", r"\b[aá]lgebra\b", r"\bgeometr[ií]a\b"]),
    ("530", "Física", [r"\bf[ií]sica\b", r"\benerg[ií]a\b", r"\bmec[aá]nica\b", r"\btermodin[aá]mica\b"]),
    ("540", "Química", [r"\bqu[ií]mica\b", r"\breacci[oó]n(es)?\b", r"\bat[oó]mo(s)?\b", r"\bmole[cú]la(s)?\b"]),
    ("570", "Biología", [r"\bbiolog[ií]a\b", r"\becolog[ií]a\b", r"\bgen[eé]tica\b", r"\borganismo(s)?\b"]),
    ("610", "Medicina", [r"\bmedicina\b", r"\bsalud\b", r"\bcl[ií]nico\b", r"\bterapia\b", r"\benh?fermedad(es)?\b"]),
    ("620", "Ingeniería", [r"\bingenier[ií]a\b", r"\bindustrial\b", r"\bmaterial(es)?\b", r"\bdiseño\b"]),
    ("780", "Música", [r"\bm[uú]sica\b", r"\bcomposici[oó]n\b", r"\binstrumento(s)?\b"]),
    ("796", "Deporte", [r"\bdeporte(s)?\b", r"\bf[uú]tbol\b", r"\bbaloncesto\b", r"\batletismo\b"]),
    ("320", "Ciencia política", [r"\bpol[ií]tica\b", r"\bestado\b", r"\bgobierno\b", r"\belecci[oó]n(es)?\b"]),
    ("330", "Economía", [r"\beconom[ií]a\b", r"\bfinanza(s)?\b", r"\bmercado\b", r"\bmacroeconom[ií]a\b"]),
    ("100", "Filosofía", [r"\bfilosof[ií]a\b", r"\b[eé]tica\b", r"\bl[oó]gica\b"]),
    ("200", "Religión", [r"\breligi[oó]n\b", r"\bbiblia\b", r"\bteolog[ií]a\b"]),
    ("400", "Lenguas", [r"\bling[uü][ií]stica\b", r"\bgram[aá]tica\b", r"\bidoma(s)?\b"]),
    ("800", "Literatura", [r"\bliteratura\b", r"\bpoes[ií]a\b", r"\bnarrativa\b", r"\bnovela\b"]),
    ("900", "Historia y geografía", [r"\bhistoria\b", r"\bgeograf[ií]a\b", r"\barqueolog[ií]a\b"]),
]


def classify_dewey_from_text(text: str) -> Optional[Tuple[str, str]]:
    if not text:
        return None
    haystack = text.lower()
    for code, label, patterns in _DEWEY_RULES:
        for pat in patterns:
            if re.search(pat, haystack):
                return code, label
    return None


def _label_from_dewey_code(code: str) -> Optional[str]:
    for c, label, _patterns in _DEWEY_RULES:
        if c == code:
            return label
    return None


def classify_file(path: Path) -> str:
    # Intento 1: usar servicio externo
    try:
        if requests is not None:
            url = settings.CLASSIFIER_API_URL
            with open(path, "rb") as fh:
                files = {"file": (path.name, fh, "application/pdf")}
                resp = requests.post(url, files=files, timeout=30)
            if resp.ok:
                data = resp.json()
                # Preferir `final_general` si existe para retornar `code:name`
                final_general = data.get("final_general") or {}
                code = str(final_general.get("code") or "").strip()
                name = str(final_general.get("name") or "").strip()
                if code and name:
                    return f"{code}:{name}"

                # Fallback a `final_pred` si no vino `final_general`
                final_pred = str(data.get("final_pred") or "").strip()
                if final_pred:
                    # Sin mapeo local: devolver el código tal cual
                    return final_pred
    except Exception:
        # Continuar al fallback local si falla el servicio externo
        pass

    # Fallback local: reglas simples por texto
    text = extract_text_from_pdf(path)
    found = classify_dewey_from_text(text)
    if found:
        _code, label = found
        return label
    # Fallback genérico sin código
    return "Obras generales"



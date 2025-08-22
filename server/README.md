# Backend (FastAPI)

Requisitos: Python 3.11+

Instalación:

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r server/requirements.txt
```

Ejecución:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir server
```

Endpoints principales:
- `POST /api/pdfs/upload`: subir PDF
- `GET /api/pdfs`: listar PDFs
- `POST /api/pdfs/{id}/open`: abrir PDF
- `POST /api/pdfs/{id}/close`: cerrar PDF
- `POST /api/pdfs/{id}/page`: cambiar página
- `POST /api/pdfs/{id}/classify`: clasificar por tema
- `GET /api/pdfs/{id}/file`: descargar/servir PDF
- `WS /ws/gestures/{client_id}`: canal simple para mensajes de gestos

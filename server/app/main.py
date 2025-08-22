from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import pdfs, ws
from .database import init_db
from .config import settings, ensure_dirs

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_dirs()
    yield


app = FastAPI(title="PDF Gesture Reader API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurar directorios antes de montar estáticos
ensure_dirs()

app.include_router(pdfs.router, prefix="/api/pdfs", tags=["pdfs"])
app.include_router(ws.router, prefix="/ws", tags=["ws"])

app.mount(settings.PDFS_STATIC_MOUNT, StaticFiles(directory=settings.PDF_STORAGE_DIR), name="pdfs")


# Nota: lógica de inicio migrada a lifespan

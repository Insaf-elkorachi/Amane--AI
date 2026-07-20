import socket
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import Base, SessionLocal, engine
from models.attachment import Attachment
from models.conversation import Conversation
from models.message import Message
from models.report import Report
from routers.chat import router as chat_router
from routers.reports import router as reports_router
from routers.rag import router as rag_router
from routers.tts import router as tts_router
from routers.voice import router as voice_router
from routers.vision import router as vision_router
from services.report_service import ReportService, ensure_report_schema


Base.metadata.create_all(bind=engine)
ensure_report_schema()


def normalize_report_data_on_startup() -> None:
    db = SessionLocal()
    try:
        ReportService.normalize_existing_reports(db)
    finally:
        db.close()


normalize_report_data_on_startup()

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def get_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())


app = FastAPI(
    title="AMANE API",
    version="0.1.0",
)

app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(vision_router)
app.include_router(reports_router)
app.include_router(rag_router)
app.include_router(tts_router)

if FRONTEND_DIR.exists():
    app.mount(
        "/app",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="app",
    )


@app.get("/")
def home():
    return RedirectResponse(url="/app/")


@app.get("/qr")
def qr_page():
    return RedirectResponse(url="/app/qr.html")


@app.get("/api/network")
def network_info(request: Request):
    public_url = settings.PUBLIC_APP_URL.strip().rstrip("/")
    if public_url:
        if public_url.endswith("/app"):
            base_url = public_url[:-4].rstrip("/")
            app_url = f"{public_url}/"
        else:
            base_url = public_url
            app_url = f"{public_url}/app/"
        return {
            "host": request.url.hostname or "",
            "public": True,
            "app_url": app_url,
            "qr_url": f"{base_url}/qr",
        }

    port = request.url.port or 8000
    scheme = request.url.scheme
    host = get_lan_ip()
    return {
        "host": host,
        "public": False,
        "app_url": f"{scheme}://{host}:{port}/app/",
        "qr_url": f"{scheme}://{host}:{port}/qr",
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AMANE API",
    }








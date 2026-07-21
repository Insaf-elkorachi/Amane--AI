from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from agents.vision_risk_agent import vision_risk_agent
from core.database import get_db
from services.conversation_service import conversation_service


UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "risk_photos"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024

router = APIRouter(
    prefix="/api/vision",
    tags=["AMANE Vision"],
)


@router.post("/classify-risk")
async def classify_risk_photo(
    session_id: str = Form(...),
    analysis_language: str = Form("ar"),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    content_type = photo.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format image non supporte. Utilisez JPG, PNG ou WEBP.",
        )

    data = await photo.read()
    if not data:
        raise HTTPException(status_code=400, detail="Image vide.")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image trop grande, maximum 8 Mo.")

    extension = Path(photo.filename or "photo.jpg").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        extension = ".jpg" if content_type == "image/jpeg" else ".png"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = UPLOAD_DIR / f"{uuid4().hex}{extension}"
    image_path.write_bytes(data)

    vision_result = vision_risk_agent.classify(image_path, content_type=content_type, analysis_language=analysis_language)
    normalized_analysis_language = (analysis_language or "ar").strip().lower()
    photo_conversation_language = {"fr": "fr", "en": "en", "ar": "darija"}.get(normalized_analysis_language)
    transcript = vision_risk_agent.to_conversation_message(vision_result)
    conversation_result = conversation_service.process_message(
        session_id=session_id,
        message=transcript,
        db=db,
        preferred_language=photo_conversation_language,
    )

    response = vision_risk_agent.format_detailed_response(vision_result, language=analysis_language)
    conversation_result["response"] = response
    conversation_result["data"]["photo_analysis"] = vision_result

    return {
        "session_id": session_id,
        "vision": vision_result,
        "step": conversation_result["step"],
        "response": conversation_result["response"],
        "completed": conversation_result["completed"],
        "emergency": conversation_result["emergency"],
        "collected_data": conversation_result["data"],
    }

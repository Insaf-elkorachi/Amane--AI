from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ai.llm import llm_service
from core.config import settings
from speech.speech_to_text import speech_to_text_adapter


router = APIRouter(prefix="/api/stt", tags=["AMANE Speech To Text"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("fr"),
) -> dict[str, str]:
    if not llm_service.client:
        raise HTTPException(status_code=503, detail="Transcription OpenAI non disponible")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    normalized_language = (language or "fr").lower().strip()
    if normalized_language in {"darija", "ar-ma", "ma"}:
        normalized_language = "ar"
    if normalized_language not in {"ar", "fr", "en"}:
        normalized_language = "fr"

    filename = audio.filename or "amane-voice.webm"
    prompt = (
        "AMANE SONASID Nador HSE. "
        "Moroccan Darija, French and Arabic safety reporting. "
        "Examples: بغيت نصرح بوضعية خطيرة, situation dangereuse, acte dangereux, "
        "casque, EPI, consignation, balisage, laminoir, Nador."
    )

    def run_transcription(model: str):
        audio_file = BytesIO(audio_bytes)
        audio_file.name = filename
        return llm_service.client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language=normalized_language,
            prompt=prompt,
        )

    errors: list[str] = []
    response = None
    for model in [settings.OPENAI_STT_MODEL, "whisper-1"]:
        if response is not None:
            break
        if model in {None, ""}:
            continue
        try:
            candidate = run_transcription(str(model))
            candidate_text = (getattr(candidate, "text", "") or "").strip()
            if candidate_text:
                response = candidate
                break
            errors.append(f"{model}: empty transcription")
        except Exception as exc:
            errors.append(f"{model}: {exc}")

    text = (getattr(response, "text", "") or "").strip() if response is not None else ""
    if not text:
        detail = "Aucune parole detectee. Verifiez le micro, parlez plus pres, puis reessayez."
        if errors:
            detail += " Details: " + " | ".join(errors[:2])
        raise HTTPException(status_code=422, detail=detail)

    text = speech_to_text_adapter.fix_domain_terms(text)
    return {"text": text, "language": normalized_language}

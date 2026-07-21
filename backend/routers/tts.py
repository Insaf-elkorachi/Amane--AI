from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ai.llm import llm_service
from core.config import settings
from speech.text_to_speech import text_to_speech_adapter


class TTSRequest(BaseModel):
    text: str
    lang: str | None = None


router = APIRouter(prefix="/api/tts", tags=["AMANE Text To Speech"])


@router.post("/speak")
def speak(payload: TTSRequest) -> Response:
    if not settings.TTS_ENABLED or not llm_service.client:
        raise HTTPException(status_code=503, detail="TTS IA non disponible")

    speech_text = text_to_speech_adapter.prepare_speech_text(payload.text)
    if not speech_text:
        raise HTTPException(status_code=400, detail="Texte vocal vide")

    try:
        kwargs = {
            "model": settings.OPENAI_TTS_MODEL,
            "voice": settings.OPENAI_TTS_VOICE,
            "input": speech_text,
            "response_format": "mp3",
        }
        if text_to_speech_adapter.is_darija(payload.text):
            kwargs["instructions"] = (
                "Le texte fourni est une translitteration phonetique francaise d'arabe/darija. "
                "Lis-le exactement avec une prononciation francaise, jamais anglaise. "
                "Regles: ou se prononce comme le son francais ou; ch comme dans chat; kh est un son guttural doux; gh est guttural; "
                "a, i, e se lisent a la francaise; ne prononce jamais ou comme ao ou ow. "
                "Prononce Amane court et clair, Sonasid clairement, Nador clairement, H S E lettre par lettre. "
                "Ne traduis pas, ne reformule pas, lis seulement le texte avec accent francais marocain naturel."
            )

        audio = llm_service.client.audio.speech.create(**kwargs)
        content = getattr(audio, "content", None)
        if content is None and hasattr(audio, "read"):
            content = audio.read()
        if not content:
            raise RuntimeError("R?ponse audio vide")
        return Response(content=content, media_type="audio/mpeg")
    except TypeError:
        audio = llm_service.client.audio.speech.create(
            model=settings.OPENAI_TTS_MODEL,
            voice=settings.OPENAI_TTS_VOICE,
            input=speech_text,
            response_format="mp3",
        )
        content = getattr(audio, "content", None) or (audio.read() if hasattr(audio, "read") else None)
        if not content:
            raise HTTPException(status_code=500, detail="R?ponse audio vide")
        return Response(content=content, media_type="audio/mpeg")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur TTS IA: {exc}") from exc


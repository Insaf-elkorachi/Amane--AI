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

    speech_text = text_to_speech_adapter.prepare_speech_text(payload.text, payload.lang)
    if not speech_text:
        raise HTTPException(status_code=400, detail="Texte vocal vide")

    try:
        kwargs = {
            "model": settings.OPENAI_TTS_MODEL,
            "voice": settings.OPENAI_TTS_VOICE,
            "input": speech_text,
            "response_format": "mp3",
        }
        requested_lang = (payload.lang or "").lower()
        if requested_lang.startswith("fr"):
            kwargs["instructions"] = (
                "Lis le texte en francais clair et professionnel. "
                "Ne melange pas avec l'arabe ni avec la darija. "
                "Prononce A-mane en deux syllabes, sans r final. "
                "Prononce Sonasid clairement, Nador clairement, H S E lettre par lettre. "
                "Ne prends pas d'accent anglais et ne reformule pas."
            )
        elif requested_lang.startswith("en"):
            kwargs["instructions"] = (
                "Read the text in clear professional English. "
                "Do not mix with Arabic, Darija, or French. "
                "Pronounce A-mane in two syllables, without a final r. Pronounce H S E letter by letter. "
                "Do not translate or rephrase."
            )
        elif requested_lang.startswith("ar") or text_to_speech_adapter.is_arabic_text(payload.text):
            kwargs["instructions"] = (
                "Lis le texte en arabe clair et naturel. "
                "Ne melange pas avec la darija ni avec le francais, sauf les sigles et noms officiels. "
                "Prononce \u0623\u0645\u0627\u0646 comme un nom court, sans r final. "
                "Prononce \u0625\u062a\u0634 \u0625\u0633 \u0625\u064a lettre par lettre. Ne traduis pas et ne reformule pas."
            )
        elif text_to_speech_adapter.is_darija(payload.text):
            kwargs["instructions"] = (
                "Le texte fourni est une version vocale en darija marocaine. "
                "Lis-le avec une prononciation marocaine naturelle, comme de l'arabe marocain, pas comme du francais. "
                "Prononce \u0623\u0645\u0627\u0646 comme un nom court, sans r final. "
                "Prononce \u0625\u062a\u0634 \u0625\u0633 \u0625\u064a lettre par lettre. Ne traduis pas et ne reformule pas."
            )
        else:
            kwargs["instructions"] = (
                "Lis le texte en francais clair et professionnel. "
                "Prononce A-mane en deux syllabes, sans r final. "
                "Prononce Sonasid clairement, Nador clairement, H S E lettre par lettre. "
                "Ne prends pas d'accent anglais et ne reformule pas."
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


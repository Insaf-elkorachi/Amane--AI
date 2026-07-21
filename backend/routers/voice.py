from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.voice import VoiceMessageRequest, VoiceMessageResponse
from services.conversation_service import conversation_service
from services.voice_pipeline_service import voice_pipeline_service


router = APIRouter(
    prefix="/api/voice",
    tags=["AMANE Voice Pipeline"],
)


@router.post("/message", response_model=VoiceMessageResponse)
def voice_message(
    payload: VoiceMessageRequest,
    db: Session = Depends(get_db),
) -> VoiceMessageResponse:
    try:
        result = voice_pipeline_service.process_voice_message(
            session_id=payload.session_id,
            transcript=payload.transcript,
            source=payload.source,
            preferred_language=payload.preferred_language,
            db=db,
        )

        return VoiceMessageResponse(
            session_id=payload.session_id,
            step=result["step"],
            response=result["response"],
            completed=result["completed"],
            emergency=result["emergency"],
            collected_data=result["data"],
            pipeline=result["pipeline"],
            agent_trace=result.get("agent_trace", {}),
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Information obligatoire manquante : {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pipeline vocal AMANE : {exc}",
        ) from exc


@router.delete("/session/{session_id}")
def reset_voice_session(session_id: str) -> dict[str, object]:
    deleted = conversation_service.reset_session(session_id)

    return {
        "session_id": session_id,
        "reset": deleted,
        "message": (
            "Session vocale reinitialisee."
            if deleted
            else "Aucune session vocale trouvee."
        ),
    }


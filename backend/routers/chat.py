from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.chat import ChatRequest, ChatResponse
from services.conversation_service import conversation_service


router = APIRouter(
    prefix="/api/chat",
    tags=["AMANE Conversation"],
)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        result = conversation_service.process_message(
            session_id=payload.session_id,
            message=payload.message,
            db=db,
        )

        return ChatResponse(
            session_id=payload.session_id,
            step=result["step"],
            response=result["response"],
            completed=result["completed"],
            emergency=result["emergency"],
            collected_data=result["data"],
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Information obligatoire manquante : {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Erreur lors du traitement de la conversation : "
                f"{exc}"
            ),
        ) from exc


@router.delete("/session/{session_id}")
def reset_chat_session(
    session_id: str,
) -> dict[str, object]:
    deleted = conversation_service.reset_session(
        session_id
    )

    return {
        "session_id": session_id,
        "reset": deleted,
        "message": (
            "Session réinitialisée."
            if deleted
            else "Aucune session trouvée."
        ),
    }
from fastapi import APIRouter

from ai.rag import rag_service


router = APIRouter(
    prefix="/api/rag",
    tags=["AMANE RAG"],
)


@router.get("/search")
def search_knowledge(q: str) -> dict[str, object]:
    results = rag_service.retrieve(q)
    return {
        "query": q,
        "results": results,
    }

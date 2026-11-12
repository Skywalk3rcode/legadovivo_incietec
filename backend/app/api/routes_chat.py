from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_titular_id, ensure_titular_access
from app.services.ai_service import AIService
from app.db.mongodb import get_mongo_db
from app.db.postgres import get_db
from app.models.mongo_schemas import ChatMessage

router = APIRouter()


class ChatQueryRequest(BaseModel):
    message: str = Field(..., example="¿Cómo conociste a mamá?")
    titular_name: Optional[str] = None
    titular_id: Optional[str] = None


class ChatQueryResponse(BaseModel):
    response: str
    sources: List[str]
    confidence: float
    matched_memories: int


@router.post("/", response_model=ChatQueryResponse)
async def query_legacy_chat(
    req: ChatQueryRequest,
    default_titular_id: str = Depends(get_current_titular_id),
    db_session: Session = Depends(get_db),
):
    """
    Endpoint del Chat del Legado:
    - Realiza búsqueda de similitud en ChromaDB.
    - Aplica Cero Alucinación: si no hay memoria cercana, responde con la sugerencia forzada.
    - Si existe, genera respuesta imitando la personalidad y muletillas del titular con Ollama.
    """
    active_titular_id = req.titular_id or default_titular_id
    ensure_titular_access(active_titular_id, default_titular_id, db_session)

    try:
        result = await AIService.rag_chat(
            titular_id=active_titular_id,
            user_message=req.message,
            titular_name=req.titular_name or "el titular"
        )

        # Opcional: Persistir el diálogo en MongoDB para auditoría de la sesión de chat
        db = get_mongo_db()
        if db is not None:
            await db.chat_sessions.update_one(
                {"titular_id": active_titular_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                {"sender": "beneficiario", "message": req.message},
                                {"sender": "legado", "message": result["response"], "sources": result["sources"]}
                            ]
                        }
                    }
                },
                upsert=True
            )

        return ChatQueryResponse(
            response=result["response"],
            sources=result["sources"],
            confidence=result["confidence"],
            matched_memories=result["matched_memories"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la inferencia RAG: {str(e)}"
        )


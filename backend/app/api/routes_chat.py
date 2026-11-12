import os
from pathlib import Path
from typing import List, Optional
import httpx
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.deps import get_current_titular_id, ensure_titular_access
from app.services.ai_service import AIService
from app.db.mongodb import get_mongo_db
from app.db.postgres import get_db
from app.models.mongo_schemas import ChatMessage
from app.core.config import settings

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


class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    titular_id: Optional[str] = None


@router.post("/speech")
async def synthesize_legacy_voice(
    req: SpeechRequest,
    current_user_id: str = Depends(get_current_titular_id),
    db_session: Session = Depends(get_db),
):
    """Generates a response in the titular's explicitly authorized reference voice."""
    titular_id = req.titular_id or current_user_id
    ensure_titular_access(titular_id, current_user_id, db_session)

    db = get_mongo_db()
    if db is None:
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    profile = await db.style_profiles.find_one({"titular_id": titular_id})
    if not profile or not profile.get("voice_cloning_consent"):
        raise HTTPException(status_code=409, detail="El titular aún no autorizó una voz sintética para este legado.")
    capsule_id = profile.get("voice_sample_capsule_id")
    if not capsule_id:
        raise HTTPException(status_code=409, detail="El titular aún no seleccionó una grabación como referencia de voz.")

    capsule = await db.capsules.find_one(
        {"_id": capsule_id, "titular_id": titular_id},
        {"audio_path": 1, "audio_filename": 1, "audio_content_type": 1},
    )
    if not capsule or not capsule.get("audio_path"):
        raise HTTPException(status_code=404, detail="No se encontró el audio de referencia elegido.")

    audio_root = Path(os.getenv("AUDIO_STORAGE_DIR", "uploads/audio")).resolve()
    reference_path = (audio_root / Path(capsule["audio_path"]).name).resolve()
    if reference_path.parent != audio_root or not reference_path.is_file():
        raise HTTPException(status_code=404, detail="El audio de referencia ya no está disponible.")

    try:
        async with httpx.AsyncClient(timeout=900.0) as client:
            response = await client.post(
                f"{settings.VOICE_TTS_URL.rstrip('/')}/synthesize",
                data={"text": req.text, "language_id": "es"},
                files={"reference_audio": (
                    Path(capsule.get("audio_filename") or reference_path.name).name,
                    reference_path.read_bytes(),
                    capsule.get("audio_content_type") or "application/octet-stream",
                )},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="El motor de voz no está iniciado. Sigue los pasos de configuración de voz del proyecto.") from exc

    if response.status_code != 200:
        detail = "No se pudo generar la voz sintética."
        try:
            detail = response.json().get("detail") or detail
        except ValueError:
            pass
        raise HTTPException(status_code=503, detail=detail)

    return Response(
        content=response.content,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


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


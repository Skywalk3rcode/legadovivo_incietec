from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_titular_id
from app.models.mongo_schemas import MemoryCapsuleCreate, MemoryCapsuleInDB, StyleProfile
from app.services.ai_service import AIService
from app.db.mongodb import get_mongo_db

router = APIRouter()


@router.post("/", response_model=MemoryCapsuleInDB, status_code=status.HTTP_201_CREATED)
async def create_memory_capsule(
    capsule_in: MemoryCapsuleCreate,
    titular_id: str = Depends(get_current_titular_id)
):
    """
    Ingesta una nueva cápsula de memoria:
    1. La guarda en MongoDB.
    2. Calcula embeddings y la indexa en ChromaDB.
    3. Re-entrena/actualiza el perfil estilístico lingüístico en el Learning Loop.
    """
    try:
        capsule = await AIService.ingest_capsule(titular_id, capsule_in)
        return capsule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar e indexar la cápsula: {str(e)}"
        )


@router.get("/", response_model=List[MemoryCapsuleInDB])
async def list_memory_capsules(
    titular_id: str = Depends(get_current_titular_id)
):
    """Obtiene la biblioteca de cápsulas de memoria del titular desde MongoDB."""
    db = get_mongo_db()
    capsules = []
    if db is not None:
        cursor = db.capsules.find({"titular_id": titular_id}).sort("created_at", -1)
        async for doc in cursor:
            capsules.append(MemoryCapsuleInDB(**doc))
    return capsules


@router.get("/style-profile", response_model=StyleProfile)
async def get_style_profile(
    titular_id: str = Depends(get_current_titular_id)
):
    """Obtiene el perfil lingüístico sintetizado (muletillas, tono, calidez) del titular."""
    profile = await AIService.get_user_style_profile(titular_id)
    return profile


import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_titular_id, ensure_titular_access, oauth2_scheme
from app.core.security import verify_supabase_token
from app.db.postgres import get_db
from app.models.mongo_schemas import MemoryCapsuleCreate, MemoryCapsuleInDB, StyleProfile, StyleProfileUpdate
from app.services.ai_service import AIService
from app.db.mongodb import get_mongo_db

router = APIRouter()
MAX_AUDIO_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/ogg", "audio/wav", "audio/mpeg", "audio/mp4", "audio/aac", "audio/x-m4a"}
ALLOWED_AUDIO_EXTENSIONS = {".webm", ".ogg", ".wav", ".mp3", ".m4a", ".aac", ".mp4"}


def _audio_root() -> Path:
    root = Path(os.getenv("AUDIO_STORAGE_DIR", "uploads/audio")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def _find_capsule(db, capsule_id: str, titular_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    return await db.capsules.find_one({"_id": capsule_id, "titular_id": titular_id})


@router.post("/{capsule_id}/audio", response_model=MemoryCapsuleInDB)
async def upload_capsule_audio(
    capsule_id: str,
    audio: UploadFile = File(...),
    titular_id: str = Depends(get_current_titular_id),
):
    db = get_mongo_db()
    capsule = await _find_capsule(db, capsule_id, titular_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="No se encontró la cápsula.")

    extension = Path(audio.filename or "").suffix.lower()
    content_type = (audio.content_type or "").split(";")[0].lower()
    if content_type not in ALLOWED_AUDIO_TYPES or extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Formato de audio no compatible.")

    data = await audio.read(MAX_AUDIO_BYTES + 1)
    if not data or len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="El audio debe pesar menos de 25 MB.")

    filename = f"{uuid.uuid4().hex}{extension}"
    ( _audio_root() / filename ).write_bytes(data)
    await db.capsules.update_one(
        {"_id": capsule_id, "titular_id": titular_id},
        {"$set": {"audio_path": filename, "audio_filename": Path(audio.filename or filename).name, "audio_content_type": content_type}},
    )
    updated = await db.capsules.find_one({"_id": capsule_id, "titular_id": titular_id})
    return MemoryCapsuleInDB(**updated)


@router.get("/{capsule_id}/audio")
async def get_capsule_audio(
    capsule_id: str,
    titular_id: Optional[str] = Query(default=None),
    current_user_id: str = Depends(get_current_titular_id),
    db_session: Session = Depends(get_db),
):
    active_titular_id = ensure_titular_access(titular_id or current_user_id, current_user_id, db_session)
    capsule = await _find_capsule(get_mongo_db(), capsule_id, active_titular_id)
    if not capsule or not capsule.get("audio_path"):
        raise HTTPException(status_code=404, detail="Esta cápsula no tiene audio.")
    path = (_audio_root() / Path(capsule["audio_path"]).name).resolve()
    if path.parent != _audio_root():
        raise HTTPException(status_code=404, detail="Audio no encontrado.")
    return FileResponse(path, media_type=capsule.get("audio_content_type") or "application/octet-stream", filename=capsule.get("audio_filename"))


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
    titular_id: Optional[str] = Query(default=None),
    current_user_id: str = Depends(get_current_titular_id),
    db_session: Session = Depends(get_db),
):
    """Obtiene la biblioteca de cápsulas de memoria del titular desde MongoDB."""
    active_titular_id = ensure_titular_access(titular_id or current_user_id, current_user_id, db_session)
    db = get_mongo_db()
    capsules = []
    if db is not None:
        cursor = db.capsules.find({"titular_id": active_titular_id}).sort("created_at", -1)
        async for doc in cursor:
            capsules.append(MemoryCapsuleInDB(**doc))
    return capsules


@router.get("/style-profile", response_model=StyleProfile)
async def get_style_profile(
    titular_id: str = Depends(get_current_titular_id),
    token: str = Depends(oauth2_scheme),
):
    """Obtiene preferencias guardadas o inicializa las elegidas durante el registro."""
    db = get_mongo_db()
    if db is not None:
        stored = await db.style_profiles.find_one({"titular_id": titular_id})
        if stored:
            return StyleProfile(**stored)

    payload = verify_supabase_token(token or "") or {}
    raw_user = payload.get("raw_payload") or {}
    metadata = raw_user.get("user_metadata") or {}
    chosen_profile = metadata.get("style_profile")
    if chosen_profile:
        profile = StyleProfile(titular_id=titular_id, **chosen_profile, is_customized=True)
        return await AIService.save_user_style_profile(profile)

    profile = await AIService.get_user_style_profile(titular_id)
    return profile


@router.put("/style-profile", response_model=StyleProfile)
async def update_style_profile(
    update: StyleProfileUpdate,
    titular_id: str = Depends(get_current_titular_id),
):
    """Guarda el perfil lingüístico editable del titular autenticado."""
    if update.voice_cloning_consent and not update.voice_sample_capsule_id:
        raise HTTPException(status_code=422, detail="Selecciona una grabación antes de autorizar la voz sintética.")
    if update.voice_sample_capsule_id:
        db = get_mongo_db()
        if db is None:
            raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
        sample = await db.capsules.find_one(
            {"_id": update.voice_sample_capsule_id, "titular_id": titular_id, "audio_path": {"$exists": True, "$ne": None}},
            {"_id": 1},
        )
        if not sample:
            raise HTTPException(status_code=422, detail="La grabación elegida no pertenece a este legado o ya no tiene audio.")
    profile = StyleProfile(titular_id=titular_id, **update.model_dump(), is_customized=True)
    try:
        return await AIService.save_user_style_profile(profile)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


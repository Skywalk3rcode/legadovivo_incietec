from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MemoryCapsuleCreate(BaseModel):
    title: str = Field(..., example="Mi primer viaje a Cusco con mi hermano")
    content: str = Field(
        ...,
        example="Recuerdo que llovía a cántaros cuando llegamos a la plaza. Mi hermano Carlos llevaba un poncho verde..."
    )
    category: str = Field(default="Anécdotas", example="Infancia, Consejos, Anécdotas, Valores")
    tags: List[str] = Field(default_factory=list, example=["familia", "viajes", "juventud"])
    emotional_tone: Optional[str] = Field(default="nostálgico y cariñoso", example="alegre, reflexivo, protector")
    is_private: bool = Field(default=False, description="Si es sólo visible para ciertos beneficiarios")


class MemoryCapsuleInDB(MemoryCapsuleCreate):
    id: str = Field(..., alias="_id")
    titular_id: str
    vector_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    audio_path: Optional[str] = None
    audio_filename: Optional[str] = None
    audio_content_type: Optional[str] = None

    class Config:
        populate_by_name = True


class ChatMessage(BaseModel):
    sender: str = Field(..., example="beneficiario o legado") # "user" | "assistant"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: List[str] = Field(default_factory=list, description="IDs de cápsulas consultadas")


class ChatSession(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    titular_id: str
    beneficiary_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class StyleProfile(BaseModel):
    """Perfil lingüístico y emocional sintetizado a partir de los textos del titular."""
    titular_id: str
    typical_phrases: List[str] = Field(
        default_factory=list,
        description="Muletillas y expresiones frecuentes (ej: 'mijito lindo', 'escúchame bien', 'fíjate tú')"
    )
    formality_level: str = Field(
        default="cercano y afectuoso",
        description="Muy formal, coloquial, cariñoso, solemne"
    )
    warmth_score: float = Field(default=0.9, ge=0.0, le=1.0)
    sentiment_tendency: str = Field(default="positivo y reflexivo")
    sample_excerpts: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


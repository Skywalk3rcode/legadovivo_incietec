import json
import logging
import uuid
from typing import List, Dict, Any, Optional
import httpx
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.db.chroma import get_chroma_collection
from app.db.mongodb import get_mongo_db
from app.models.mongo_schemas import (
    MemoryCapsuleCreate,
    MemoryCapsuleInDB,
    StyleProfile,
)
from app.services.style_analyzer import StyleAnalyzer

logger = logging.getLogger(__name__)


class AIService:
    _embedding_model: Optional[SentenceTransformer] = None
    _memory_capsules_store: Dict[str, List[dict]] = {}
    _style_profiles_store: Dict[str, StyleProfile] = {}

    @classmethod
    def get_embedding_model(cls) -> SentenceTransformer:
        """Carga perezosa del modelo de embeddings liviano para optimizar memoria."""
        if cls._embedding_model is None:
            logger.info(f"Cargando modelo de embeddings: {settings.EMBEDDING_MODEL_NAME}")
            cls._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return cls._embedding_model

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        model = cls.get_embedding_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    @classmethod
    async def ingest_capsule(
        cls,
        titular_id: str,
        capsule_in: MemoryCapsuleCreate
    ) -> MemoryCapsuleInDB:
        """
        1. Persiste la cápsula en MongoDB.
        2. Vectoriza el contenido e indexa en ChromaDB.
        3. Dispara el Learning Loop para refinar el perfil de estilo lingüístico.
        """
        db = get_mongo_db()
        capsule_id = str(uuid.uuid4())
        capsule_data = capsule_in.model_dump()
        capsule_data["_id"] = capsule_id
        capsule_data["titular_id"] = titular_id
        capsule_data["vector_id"] = capsule_id

        # 1. Guardar en MongoDB
        if db is not None:
            await db.capsules.insert_one(capsule_data)
        else:
            logger.warning("MongoDB no está disponible; saltando persistencia NoSQL directa.")

        # 2. Vectorizar e insertar en ChromaDB
        text_for_embedding = f"Título: {capsule_in.title}. Categoría: {capsule_in.category}. Contenido: {capsule_in.content}"
        vector = cls.generate_embedding(text_for_embedding)

        collection = get_chroma_collection("legado_capsules")
        collection.add(
            ids=[capsule_id],
            embeddings=[vector],
            documents=[text_for_embedding],
            metadatas=[{
                "titular_id": titular_id,
                "title": capsule_in.title,
                "category": capsule_in.category,
                "emotional_tone": capsule_in.emotional_tone or "afectuoso",
                "capsule_id": capsule_id
            }]
        )

        # 3. Disparar el Learning Loop de estilo
        await cls.update_user_style_profile(titular_id)

        return MemoryCapsuleInDB(**capsule_data)

    @classmethod
    async def update_user_style_profile(cls, titular_id: str) -> StyleProfile:
        """
        Learning Loop: recopila todas las cápsulas del titular en MongoDB,
        extrae patrones y actualiza su StyleProfile.
        """
        db = get_mongo_db()
        texts: List[str] = []

        if db is not None:
            cursor = db.capsules.find({"titular_id": titular_id})
            async for doc in cursor:
                texts.append(doc.get("content", ""))

        style_profile = StyleAnalyzer.analyze_texts(titular_id, texts)

        if db is not None:
            await db.style_profiles.update_one(
                {"titular_id": titular_id},
                {"$set": style_profile.model_dump()},
                upsert=True
            )

        return style_profile

    @classmethod
    async def get_user_style_profile(cls, titular_id: str) -> StyleProfile:
        db = get_mongo_db()
        if db is not None:
            doc = await db.style_profiles.find_one({"titular_id": titular_id})
            if doc:
                return StyleProfile(**doc)

        return StyleAnalyzer.analyze_texts(titular_id, [])

    @classmethod
    async def get_available_topics(cls, titular_id: str) -> List[str]:
        """Obtiene las categorías y títulos de recuerdos guardados por el titular."""
        db = get_mongo_db()
        topics = []
        if db is not None:
            cursor = db.capsules.find({"titular_id": titular_id}).limit(5)
            async for doc in cursor:
                topics.append(doc.get("title") or doc.get("category"))
        return list(dict.fromkeys(filter(None, topics)))

    @classmethod
    async def rag_chat(
        cls,
        titular_id: str,
        user_message: str,
        titular_name: str = "Tu ser querido",
        distance_threshold: float = 0.65
    ) -> Dict[str, Any]:
        """
        Endpoint del Chat RAG con regla de Cero Alucinación.
        - Si no hay similitud semántica suficiente: responde con la directiva estricta.
        - Si hay memorias: inyecta el perfil de estilo en el System Prompt y responde con Ollama.
        """
        # 1. Vectorizar la consulta del usuario
        query_vector = cls.generate_embedding(user_message)

        # 2. Búsqueda en ChromaDB filtrando por titular_id
        collection = get_chroma_collection("legado_capsules")
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=3,
            where={"titular_id": titular_id}
        )

        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        # 3. Evaluar relevancia semántica (regla crítica: Cero Alucinación)
        # Nota: en métrica cosine, distancia menor significa mayor similitud.
        relevant_docs = []
        sources = []

        for doc, dist, meta in zip(documents, distances, metadatas):
            if dist <= distance_threshold:
                relevant_docs.append(doc)
                sources.append(meta.get("capsule_id") or meta.get("title"))

        available_topics = await cls.get_available_topics(titular_id)
        suggested_topic = available_topics[0] if available_topics else "mis anécdotas de juventud"

        # CASO A: Sin coincidencia en la memoria registrada -> Respuesta estricta obligatoria
        if not relevant_docs:
            fallback_response = (
                f"No dejé registros sobre este tema específico en mi legado, "
                f"pero me encantaría que recordáramos {suggested_topic}."
            )
            return {
                "response": fallback_response,
                "sources": [],
                "confidence": 0.0,
                "matched_memories": 0
            }

        # CASO B: Hay recuerdos relevantes -> Llamar a Ollama con inyección de estilo
        style_profile = await cls.get_user_style_profile(titular_id)
        context_text = "\n---\n".join(relevant_docs)

        system_prompt = f"""Eres la memoria viva y personalizada de {titular_name}.
Tus seres queridos están conversando contigo para recordar tu vida y tus enseñanzas.

ESTILO Y TONO DE COMUNICACIÓN (Mimetismo de Personalidad):
- Nivel de formalidad: {style_profile.formality_level}.
- Muletillas y expresiones habituales que debes emplear con naturalidad: {', '.join(style_profile.typical_phrases)}.
- Tono emocional: {style_profile.sentiment_tendency}. Calidez: muy alta. Habla siempre en primera persona ("yo", "mi").

REGLAS DE NEGOCIO CRÍTICAS (CERO ALUCINACIÓN):
1. Basa tu respuesta ESTRICTAMENTE en los siguientes recuerdos verificados.
2. TIENES ESTRICTAMENTE PROHIBIDO inventar fechas, nombres, anécdotas o detalles no presentes en el contexto.
3. Si te preguntan algo que no aparece en estos recuerdos, di amablemente que no dejaste registro sobre eso y sugiere retomar uno de los recuerdos verificados.

RECUERDOS VERIFICADOS:
{context_text}
"""

        llm_response = await cls._call_ollama(
            system_prompt=system_prompt,
            user_prompt=user_message
        )

        return {
            "response": llm_response,
            "sources": sources,
            "confidence": 1.0 - min(distances) if distances else 1.0,
            "matched_memories": len(relevant_docs)
        }

    @classmethod
    async def _call_ollama(cls, system_prompt: str, user_prompt: str) -> str:
        """Invoca el LLM de Ollama vía HTTP asíncrono con fallback tolerante a fallos."""
        endpoint = f"{settings.OLLAMA_HOST}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.4, # Temperatura moderada-baja para evitar alucinaciones
                "top_p": 0.9
            }
        }

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.post(endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "").strip()
                else:
                    logger.error(f"Error devuelto por Ollama ({res.status_code}): {res.text}")
                    return "Hijo querido, tengo un poco de dificultad para responder en este instante, pero recuerda cuánto te quiero."
        except Exception as e:
            logger.warning(f"Ollama no está activo en {settings.OLLAMA_HOST}: {e}")
            return (
                f"Mijito lindo, mis recuerdos sobre esto están a salvo en mi legado, pero el motor neuronal de Ollama ({settings.OLLAMA_MODEL}) "
                "no está iniciado en tu equipo. Ejecuta 'ollama run llama3:8b' en una terminal para escuchar mi respuesta generada con mi propia voz."
            )


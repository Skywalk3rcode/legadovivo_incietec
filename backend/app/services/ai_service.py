import json
import logging
import re
import unicodedata
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

_CHAT_STOP_WORDS = {
    "que", "como", "cual", "cuando", "donde", "por", "para", "con", "sin", "del", "las", "los",
    "una", "uno", "unos", "unas", "esto", "esa", "ese", "sus", "mis", "tus", "fue", "hay", "sobre",
    "recuerdo", "memoria", "cuentame", "dime", "hablame", "mi", "me", "tu", "te", "el", "la", "de", "y",
    "papa", "padre", "mama", "madre", "hermano", "hermana", "abuelo", "abuela", "hijo", "hija", "tio", "tia", "familia",
}


def _title_match_score(query: str, title: str) -> float:
    def terms(value: str) -> set[str]:
        normalized = unicodedata.normalize("NFD", value.lower())
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return {word for word in re.findall(r"[a-z0-9]+", normalized) if len(word) > 2 and word not in _CHAT_STOP_WORDS}

    query_terms = terms(query)
    if not query_terms:
        return 0.0
    title_terms = terms(title)
    return len(query_terms & title_terms) / len(query_terms)


_DEATH_CLAIM_PHRASES = (
    "fallecio", "fallecido", "fallecida", "murio", "muerto", "muerta", "en paz descanse",
    "dios lo tenga en gloria", "dios la tenga en gloria", "ya no esta con nosotros", "en el cielo",
)


def _contains_death_claim(text: str) -> bool:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return any(phrase in normalized for phrase in _DEATH_CLAIM_PHRASES)


_FAMILY_RELATIONS = {
    "papa", "padre", "mama", "madre", "hermano", "hermana", "abuelo", "abuela",
    "hijo", "hija", "tio", "tia", "primo", "prima", "esposo", "esposa",
}


def _has_unsupported_family_relation(response: str, context: str) -> bool:
    def relations(text: str) -> set[str]:
        normalized = unicodedata.normalize("NFD", text.lower())
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        words = set(re.findall(r"[a-z0-9]+", normalized))
        return {word for word in words if word in _FAMILY_RELATIONS or word.rstrip("s") in _FAMILY_RELATIONS}

    return bool(relations(response) - relations(context))


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
        matches = []
        audio_only_sources: Dict[str, str] = {}
        mongo_db = get_mongo_db()
        for position, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas)):
            if dist <= distance_threshold:
                capsule_id = meta.get("capsule_id")
                capsule = None
                if mongo_db is not None and capsule_id:
                    capsule = await mongo_db.capsules.find_one(
                        {"_id": capsule_id, "titular_id": titular_id},
                        {"title": 1, "content": 1, "audio_path": 1}
                    )
                title = (capsule or {}).get("title") or meta.get("title") or ""
                title_score = _title_match_score(user_message, title)
                content = ((capsule or {}).get("content") or "").strip()
                normalized_content = " ".join(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFD", content.lower()).encode("ascii", "ignore").decode("ascii")))
                is_audio_only = bool((capsule or {}).get("audio_path")) and (
                    len(content) < 24 or normalized_content in {"deje un audio", "audio del recuerdo", "grabacion adjunta"}
                )
                if is_audio_only and title_score < 0.5:
                    continue
                if is_audio_only and capsule_id:
                    audio_only_sources[capsule_id] = title
                matches.append((doc, dist, meta, position, title_score))

        # If the user names a memory, prioritize its title match over broader semantic matches.
        matches.sort(key=lambda match: (-(match[4] if match[4] >= 0.5 else 0.0), match[1], match[3]))
        relevant_docs = [match[0] for match in matches]
        sources = [match[2].get("capsule_id") or match[2].get("title") for match in matches]

        # CASO A: Sin coincidencia en la memoria registrada -> Respuesta estricta obligatoria
        if not relevant_docs:
            fallback_response = "No encontré un recuerdo registrado que responda a eso. Prueba con el título de una cápsula o guarda ese recuerdo primero."
            return {
                "response": fallback_response,
                "sources": [],
                "confidence": 0.0,
                "matched_memories": 0
            }

        if sources and sources[0] in audio_only_sources:
            title = audio_only_sources[sources[0]]
            return {
                "response": f"Encontré una grabación sobre «{title}». No hay texto adicional guardado para resumirla; puedes reproducir el audio original.",
                "sources": [sources[0]],
                "confidence": 1.0 - min(distances) if distances else 1.0,
                "matched_memories": 1,
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
3. No infieras si una persona está viva o falleció. Solo puedes decirlo si el recuerdo lo afirma explícitamente.
4. No inventes ni supongas hermanos, hijos, relaciones, profesiones, creencias o parentescos que no estén escritos en el contexto.
5. Si la pregunta pide información ausente, di que no hay un recuerdo registrado sobre ese dato. No rellenes los vacíos con una historia probable.

RECUERDOS VERIFICADOS:
{context_text}
"""

        llm_response = await cls._call_ollama(
            system_prompt=system_prompt,
            user_prompt=user_message
        )
        if llm_response and _has_unsupported_family_relation(llm_response, context_text):
            llm_response = "Los recuerdos consultados no mencionan ese parentesco. No puedo suponerlo ni inventarlo."
        elif llm_response and _contains_death_claim(llm_response):
            # Even if another memory mentions a death, do not let Ollama transfer
            # that fact to a different relative. Let the user inspect the source.
            llm_response = "Los recuerdos consultados no permiten confirmar a quién se refiere ese dato. No voy a suponer quién falleció."
        if llm_response is None:
            db = get_mongo_db()
            best_capsule = None
            if db is not None and sources:
                best_capsule = await db.capsules.find_one(
                    {"_id": sources[0], "titular_id": titular_id},
                    {"content": 1}
                )
            original_text = best_capsule.get("content") if best_capsule else relevant_docs[0]
            llm_response = (
                "Ollama no está iniciado, así que te comparto el recuerdo tal como fue guardado:\n\n"
                f"{original_text}"
            )

        return {
            "response": llm_response,
            "sources": sources,
            "confidence": 1.0 - min(distances) if distances else 1.0,
            "matched_memories": len(relevant_docs)
        }

    @classmethod
    async def _call_ollama(cls, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Invoca Ollama y devuelve None si el servicio no está disponible."""
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
            return None


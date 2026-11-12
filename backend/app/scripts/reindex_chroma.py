import asyncio

from app.db.chroma import get_chroma_collection
from app.db.mongodb import close_mongo, connect_mongo, get_mongo_db
from app.services.ai_service import AIService


async def main() -> None:
    await connect_mongo()
    try:
        db = get_mongo_db()
        if db is None:
            raise RuntimeError("MongoDB no está disponible; no se reindexó ninguna cápsula.")

        cursor = db.capsules.find({"titular_id": {"$exists": True, "$nin": [None, ""]}})
        documents = []
        async for capsule in cursor:
            titular_id = str(capsule.get("titular_id") or "")
            capsule_id = str(capsule.get("vector_id") or capsule.get("_id") or "")
            if not titular_id or not capsule_id:
                continue

            title = str(capsule.get("title") or "")
            category = str(capsule.get("category") or "")
            content = str(capsule.get("content") or "")
            text = f"Título: {title}. Categoría: {category}. Contenido: {content}"
            metadata = {
                "titular_id": titular_id,
                "title": title,
                "category": category,
                "emotional_tone": str(capsule.get("emotional_tone") or "afectuoso"),
                "capsule_id": capsule_id,
            }
            documents.append((capsule_id, text, metadata))

        if documents:
            model = AIService.get_embedding_model()
            vectors = model.encode([item[1] for item in documents], normalize_embeddings=True).tolist()
            collection = get_chroma_collection("legado_capsules")
            collection.upsert(
                ids=[item[0] for item in documents],
                embeddings=vectors,
                documents=[item[1] for item in documents],
                metadatas=[item[2] for item in documents],
            )

        print(f"Cápsulas reindexadas sin borrar registros: {len(documents)}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
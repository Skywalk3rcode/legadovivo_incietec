import asyncio
import logging
from app.db.mongodb import connect_mongo, close_mongo, get_mongo_db
from app.services.ai_service import AIService
from app.models.mongo_schemas import MemoryCapsuleCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

TITULAR_ID = "titular-demo-12345"

SAMPLE_CAPSULES = [
    MemoryCapsuleCreate(
        title="El viaje en tren a Cusco con mi hermano Carlos",
        content="Mijito lindo, te cuento que en 1982 viajamos con Carlos a Cusco. Llovía a cántaros cuando bajamos del tren y nos compramos dos ponchos de lana gruesa en el mercado de San Pedro. Reímos tanto tomando mate de coca caliente junto a un fogón.",
        category="Anécdotas",
        tags=["viajes", "hermanos", "juventud", "cusco"],
        emotional_tone="nostálgico y risueño"
    ),
    MemoryCapsuleCreate(
        title="El secreto familiar para el estofado de los domingos",
        content="Oye, escúchame bien: el gran secreto del estofado nunca fue el vino tinto, sino dejar dorar la cebolla roja con una pizca de azúcar y laurel por al menos veinte minutos a fuego muy bajito. Con todo mi cariño te dejo esta enseñanza para cuando cocines a tus hijos.",
        category="Cocina y Familia",
        tags=["recetas", "abuela", "tradición", "comida"],
        emotional_tone="afectuoso y protector"
    ),
    MemoryCapsuleCreate(
        title="Consejo sobre cómo afrontar las pérdidas y la adversidad",
        content="Fíjate bien lo que te voy a decir, corazón: en la vida habrá momentos donde las cosas no saldrán como soñaste. Cuando eso pase, respira hondo, abraza a los que tienes cerca y nunca pierdas la decencia ni la bondad. El trabajo honesto y la calma siempre abren caminos.",
        category="Consejos y Valores",
        tags=["consejos", "resiliencia", "valores", "vida"],
        emotional_tone="solemne y muy cálido"
    )
]

async def seed():
    logger.info("Iniciando carga de recuerdos de demostración...")
    await connect_mongo()
    
    for cap in SAMPLE_CAPSULES:
        ingested = await AIService.ingest_capsule(TITULAR_ID, cap)
        logger.info(f"Cápsula indexada con éxito: '{ingested.title}' (ID: {ingested.id})")
        
    profile = await AIService.get_user_style_profile(TITULAR_ID)
    logger.info("Perfil lingüístico generado:")
    logger.info(f"- Muletillas: {profile.typical_phrases}")
    logger.info(f"- Nivel de formalidad: {profile.formality_level}")
    logger.info(f"- Calidez: {profile.warmth_score}")
    
    await close_mongo()
    logger.info("Carga de datos completada.")

if __name__ == "__main__":
    asyncio.run(seed())


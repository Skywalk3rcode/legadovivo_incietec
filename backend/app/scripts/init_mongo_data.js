// Script para materializar la base de datos legadovivo_nosql en MongoDB
use legadovivo_nosql;

// Insertar documento inicial en capsules para que MongoDB cree físicamente la base de datos
db.capsules.insertOne({
  _id: "capsule-bienvenida-001",
  titular_id: "titular-demo-12345",
  title: "Mi primer recuerdo en LegadoVivo",
  content: "Mijito lindo, bienvenido a mi legado. He creado este espacio para dejarte mis recuerdos, anécdotas y aprendizajes con todo mi cariño.",
  category: "Familia y Tradición",
  tags: ["bienvenida", "familia", "enseñanza"],
  emotional_tone: "muy afectuoso y cálido",
  created_at: new Date()
});

// Insertar perfil de estilo inicial en style_profiles
db.style_profiles.insertOne({
  titular_id: "titular-demo-12345",
  typical_phrases: ["mijito lindo", "oye", "te cuento", "con todo mi cariño", "escúchame bien"],
  formality_level: "cálido, cercano y profundamente afectuoso",
  warmth_score: 0.95,
  sentiment_tendency: "nostálgico, protector y sereno",
  last_updated: new Date()
});

// Insertar sesión inicial de chat
db.chat_sessions.insertOne({
  titular_id: "titular-demo-12345",
  beneficiary_id: "beneficiario-demo-001",
  messages: [
    {
      sender: "legado",
      message: "Mijito lindo, qué alegría que estés aquí conversando con mis recuerdos.",
      timestamp: new Date()
    }
  ],
  created_at: new Date()
});

// Crear índices
db.capsules.createIndex({ titular_id: 1 });
db.capsules.createIndex({ created_at: -1 });
db.style_profiles.createIndex({ titular_id: 1 }, { unique: true });
db.chat_sessions.createIndex({ titular_id: 1 });

print("========================================================");
print("¡Base de datos legadovivo_nosql MATERIALIZADA en MongoDB!");
print("Colecciones creadas: capsules, style_profiles, chat_sessions.");
print("Ya es 100% visible en MongoDB Compass y en 'show dbs'.");
print("========================================================");


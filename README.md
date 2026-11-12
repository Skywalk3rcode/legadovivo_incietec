# LegadoVivo — MVP (Arquitectura Nativa sin Docker)

Plataforma de preservación de recuerdos y mimetismo de personalidad en IA con **Cero Alucinación** y **Doble Rol Contextual**, funcionando de forma **100% nativa en disco sin necesidad de Docker**.

---

## 🏛️ Nueva Arquitectura Local (Cero Contenedores)

```
                         [ Beneficiario / Titular ]
                                     │
                     ┌───────────────┴──────────────┐
                     │  Frontend SPA (React + Vite) │
                     │  Tailwind CSS + TypeScript   │
                     │  • Dashboard Doble Rol       │
                     │  • Síntesis y Dictado de Voz │
                     └───────────────┬──────────────┘
                                     │ HTTP / REST (/api)
                     ┌───────────────▼──────────────┐
                     │    FastAPI Core Microservice  │
                     └───────┬──────────────┬───────┘
                             │              │
           ┌─────────────────┴────┐   ┌─────┴──────────────────┐
           │                      │   │                        │
  ┌────────▼────────┐   ┌─────────▼───▼──┐            ┌────────▼────────┐
  │ SQLite Nativo   │   │  NoSQL Local   │            │ ChromaDB Embeb. │
  │ (SQLAlchemy)    │   │  (JSON / Mongo)│            │ (En disco)      │
  │ • Usuarios      │   │ • Cápsulas     │            └────────┬────────┘
  │ • Conexiones    │   │ • Sesiones     │                     │
  │ • Planes Legado │   │ • Perfiles     │            ┌────────▼────────┐
  │ • Auditoría     │   │                │            │ Ollama Local    │
  └─────────────────┘   └────────────────┘            │ (Llama 3 /      │
                                                      │  Mistral)       │
                                                      └─────────────────┘
```

* **SQL Transaccional**: `backend/data/legadovivo.db` (SQLite nativo vía SQLAlchemy, soporta usuarios, roles, JWT y vinculación de familiares).
* **Base Vectorial**: `backend/data/chroma_db/` (ChromaDB embebido en disco con distancia coseno para RAG).
* **Almacén Documental**: `backend/data/nosql_store.json` (o MongoDB nativo si está iniciado en Windows).
* **LLM Local**: `Ollama` de escritorio en `http://localhost:11434`.

---

## 🚀 Puesta en Marcha en 2 Pasos (Sin Docker)

### 1. Iniciar el Backend (FastAPI)
En una terminal PowerShell en la raíz del proyecto:

```powershell
.\start-backend.ps1
```
*(o haz doble clic en `start-backend.bat`)*.

El backend creará automáticamente los archivos en `backend\data` y quedará escuchando en:
👉 **`http://localhost:8080`** (Documentación Swagger interactiva: `http://localhost:8080/docs`).

### 2. Iniciar el Frontend (React + Vite)
En otra terminal:

```powershell
cd frontend
npm run dev
```

Abre en tu navegador:
👉 **`http://localhost:5173`**

---

## 🧠 Características Principales

1. **Doble Rol Contextual**:
   - Pestaña **"Mi Legado" (Titular)**: Redacta cápsulas de vida, genera códigos de invitación (`LEG-XXXXXX`) y administra quién puede escuchar sus recuerdos.
   - Pestaña **"Mis Seres Queridos" (Beneficiario)**: Ingresa códigos familiares y chatea con el legado de sus seres queridos con voz y texto.
2. **Regla Estricta de CERO ALUCINACIÓN**:
   - Si no hay recuerdos sobre la pregunta, la IA tiene prohibido inventar y responde:
     > *"No dejé registros sobre este tema específico en mi legado, pero me encantaría que recordáramos [tema cercano]."*
3. **Mimetismo de Voz y Personalidad**:
   - Extrae muletillas (`"mijito"`, `"oye"`, `"te cuento"`) y calidez para inyectarlos en el prompt de Ollama.
   - Permite al titular autorizar una grabación propia como referencia para leer respuestas con voz sintética personalizada. También conserva la voz del dispositivo como alternativa.
   - Para instalar y arrancar el motor local de voz, sigue [`voice-engine/README.md`](voice-engine/README.md). El motor se mantiene separado del entorno principal.

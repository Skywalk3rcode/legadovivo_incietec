# LegadoVivo — MVP

Plataforma de preservación de recuerdos y mimetismo de personalidad en IA con **Cero Alucinación** y **Doble Rol Contextual** para la interacción post-mortem con seres queridos.

---

## 🏛️ Arquitectura del Sistema

```
                         [ Beneficiario / Titular ]
                                     │
                     ┌───────────────┴──────────────┐
                     │  Frontend SPA (React + Vite) │
                     │  Tailwind CSS + TypeScript   │
                     │  • AuthContext (JWT)         │
                     │  • Dashboard Doble Rol       │
                     │  • Síntesis y Dictado de Voz │
                     └───────────────┬──────────────┘
                                     │ HTTP / REST Bearer Token (/api)
                     ┌───────────────▼──────────────┐
                     │    FastAPI Core Microservice  │
                     └───────┬──────────────┬───────┘
                             │              │
           ┌─────────────────┴────┐   ┌─────┴──────────────────┐
           │                      │   │                        │
  ┌────────▼────────┐   ┌─────────▼───▼──┐            ┌────────▼────────┐
  │ PostgreSQL 16   │   │  MongoDB 7.0   │            │   ChromaDB      │
  │ (SQLAlchemy)    │   │  (Motor NoSQL) │            │  Vector Store   │
  │ - User (BCrypt) │   │ - Cápsulas     │            └────────┬────────┘
  │ - LegacyConnect │   │ - Sesiones     │                     │
  │ - LegacyPlan    │   │ - Perfiles     │            ┌────────▼────────┐
  │ - AuditLog      │   └────────────────┘            │  Ollama Local   │
  └─────────────────┘                                 │  (Llama 3 /     │
                                                      │   Mistral)      │
                                                      └─────────────────┘
```

---

## 👥 Concepto de Negocio: Doble Rol Contextual

Cada usuario registrado en **LegadoVivo** posee una única cuenta pero disfruta de dos interfaces dentro de su Dashboard:

1. **"Mi Legado" (Rol Titular)**:
   - Captura anécdotas, recetas y enseñanzas de vida.
   - Genera **Códigos de Invitación Alfanuméricos** (`LEG-XXXXXX`) protegidos criptográficamente.
   - Administra la lista de familiares autorizados para acceder a su memoria viva.
2. **"Mis Seres Queridos" (Rol Beneficiario)**:
   - Ingresa códigos de vinculación provistos por familiares.
   - Visualiza las tarjetas de todos los titulares a los que está conectado.
   - Accede con un clic al **Chat RAG** exclusivo de cada familiar para conversar con sus recuerdos.

---

## 🔑 Endpoints de la API REST

### 1. Autenticación & Seguridad (`/api/auth`)
* `POST /api/auth/register`: Registro con hashing de contraseñas vía BCrypt y emisión de JWT.
* `POST /api/auth/login`: Autenticación y obtención de Bearer Token.
* `GET /api/auth/me`: Perfil del usuario activo mediante la dependencia `get_current_user`.

### 2. Vinculación & Conexiones (`/api/legacy`)
* `POST /api/legacy/generate-code`: Genera un código de invitación para beneficiarios.
* `POST /api/legacy/link`: Vincula al usuario logueado con el titular dueño del código.
* `GET /api/legacy/my-connections`: Lista de legados a los que tiene acceso el usuario (Seres Queridos).
* `GET /api/legacy/my-beneficiaries`: Lista de familiares vinculados al legado del usuario.

### 3. Recuerdos & Chat Neuronal
* `POST /api/capsules/`: Ingesta, vectorización en ChromaDB y actualización del Learning Loop.
* `GET /api/capsules/`: Biblioteca de recuerdos del titular.
* `GET /api/capsules/style-profile`: Síntesis de muletillas y nivel de afecto.
* `POST /api/chat/`: Chat RAG con Ollama y regla estricta de **Cero Alucinación**.

---

## 🚀 Puesta en Marcha Rápida

### Opción 1: Todo en Contenedores (Docker Compose)
```bash
docker compose up -d --build
```
Descargar modelo en Ollama:
```bash
docker exec -it legadovivo_ollama ollama pull llama3:8b
```

### Opción 2: Frontend en Desarrollo (React 18 + Vite)
```bash
cd frontend
npm install
npm run dev
```
Abre en tu navegador: **`http://localhost:5173`**
* Credenciales Demo: `alberto@legadovivo.com` / `clave123` (con botón de autocompletado en `/login`).

---

## 🧪 Pruebas Automatizadas
* **`backend/tests/test_rag_and_style.py`**: Valida el extractor lingüístico y la regla forzada de Cero Alucinación.
* **`backend/tests/test_auth_and_connections.py`**: Valida el hashing BCrypt, firma JWT y generación de códigos únicos.

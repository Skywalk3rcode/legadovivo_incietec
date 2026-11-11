# LegadoVivo — MVP

Plataforma de preservación de recuerdos y mimetismo de personalidad en IA con **Cero Alucinación** y **Doble Rol Contextual** para la interacción post-mortem con seres queridos.

> **Rama de trabajo activa:** `master` (la rama `main` solo contiene documentación inicial mínima).

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
                     │  • Monitor de Salud y Estado │
                     └───────────────┬──────────────┘
                                     │ HTTP / REST Bearer Token (/api)
                     ┌───────────────▼──────────────┐
                     │    FastAPI Core Microservice  │
                     │  • /api/health (Diagnóstico) │
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
  │ (Fallback SQLite│                                 │  (Llama 3 8B)   │
  │  en local)      │                                 │                 │
  └─────────────────┘                                 └─────────────────┘
```

---

## 👥 Concepto de Negocio: Doble Rol Contextual

Cada usuario registrado en **LegadoVivo** posee una única cuenta pero disfruta de dos interfaces dinámicas dentro de su Dashboard:

1. **"Mi Legado" (Rol Titular)**:
   - Captura anécdotas, recetas y enseñanzas de vida redactadas con sus propias palabras.
   - Genera **Códigos de Invitación Alfanuméricos** únicos (`LEG-XXXXXX`) protegidos criptográficamente.
   - Administra la lista de familiares autorizados para acceder a su memoria viva.
   - Gestiona las reglas de activación de su Plan de Legado (confirmación manual, temporizador de inactividad, etc.).

2. **"Mis Seres Queridos" (Rol Beneficiario)**:
   - Ingresa los códigos de vinculación provistos por sus familiares.
   - Visualiza las tarjetas de todos los titulares a los que está conectado.
   - Accede con un solo clic al **Chat RAG** exclusivo de cada familiar para conversar con sus recuerdos.

---

## 🔍 Estados del Sistema: Distinción Crítica de Diagnóstico

Para garantizar una depuración fiable y no confundir respuestas simuladas con inferencia real, el sistema distingue cinco estados:

| Estado | Significado Técnico | Cómo comprobarlo |
|---|---|---|
| **1. Contenedor iniciado** | El proceso de Docker está en ejecución pero los servicios internos pueden seguir arrancando. | `docker compose ps` muestra estado `Up`. |
| **2. Servicio listo** | El servicio superó su healthcheck (`pg_isready`, `mongosh ping`, heartbeat de Chroma, tags de Ollama). | `docker compose ps` muestra `(healthy)` en todos los contenedores. |
| **3. Base inicializada** | Las tablas SQL (`Base.metadata.create_all()`) y colecciones de MongoDB/ChromaDB existen. | Verificado en `/api/health` en la sección `dependencies.database.tables_found`. |
| **4. Modelo descargado** | Los pesos de `llama3:8b` están presentes en el volumen `ollama_data`. | `docker exec -it legadovivo_ollama ollama list` muestra `llama3:8b`. |
| **5. Petición respondida por Ollama** | El backend vectorizó la pregunta, encontró recuerdos en ChromaDB e invocó a Ollama para sintetizar la respuesta con personalidad. | La respuesta del chat incluye `llm_status: "generated"` y `model_used: "llama3:8b"`. Si no hay recuerdos, aplica Cero Alucinación (`llm_status: "no_memories"`). Si el backend o Ollama fallan, el frontend o el API indican explícitamente `mock_simulation` o `ollama_unavailable`. |

---

## 🚀 Puesta en Marcha en Windows

### Opción 1: Infraestructura en Contenedores con Docker Compose (Recomendada)

Esta opción levanta PostgreSQL, MongoDB, ChromaDB, Ollama y la API FastAPI sin necesidad de instalar bases de datos en Windows.

#### Requisitos Previos:
- **Windows 10/11** con [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución (asegúrate de que el icono en la barra de tareas esté en verde: *"Engine running"*).
- **Node.js 18+** instalado en Windows para el frontend ([Descargar Node.js](https://nodejs.org/)).

#### Paso a Paso:

1. **Abrir PowerShell en la raíz del repositorio (`legadovivo_incietec-master`):**
   ```powershell
   # Verificar que Docker responde
   docker info
   ```

2. **Iniciar toda la infraestructura de backend:**
   ```powershell
   docker compose up -d --build
   ```
   *El contenedor auxiliar `ollama_pull` descargará automáticamente el modelo `llama3:8b` una vez que Ollama esté saludable.*

3. **Verificar el estado de salud de los contenedores:**
   ```powershell
   docker compose ps
   ```
   Todos los servicios (`legadovivo_postgres`, `legadovivo_mongodb`, `legadovivo_chromadb`, `legadovivo_ollama`, `legadovivo_backend`) deben figurar como `healthy` o `Up`.

4. **Verificar manualmente los modelos en Ollama:**
   ```powershell
   docker exec -it legadovivo_ollama ollama list
   ```
   *Debe figurar `llama3:8b`.* Si por algún motivo de red no se descargó automáticamente:
   ```powershell
   docker exec -it legadovivo_ollama ollama pull llama3:8b
   ```

5. **Iniciar el Frontend (React + Vite):**
   En una nueva ventana de terminal:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

6. **Abrir la aplicación en tu navegador:**
   - Frontend: **`http://localhost:5173`**
   - Documentación Interactiva Swagger de la API: **`http://localhost:8080/docs`**
   - Diagnóstico detallado de dependencias: **`http://localhost:8080/api/health`**
   - Credenciales Demo precargadas en login: `alberto@legadovivo.com` / `clave123`.

#### Gestión del Ciclo de Vida de Contenedores:
- **Ver logs en tiempo real:**
  ```powershell
  docker compose logs -f backend
  docker compose logs -f ollama
  ```
- **Pausar/Detener contenedores preservando datos:**
  ```powershell
  docker compose stop
  ```
- **Reanudar contenedores detenidos:**
  ```powershell
  docker compose start
  ```
- **Bajar contenedores sin borrar volúmenes:**
  ```powershell
  docker compose down
  ```
  > ⚠️ **IMPORTANTE:** Nunca uses `docker compose down -v` a menos que desees eliminar permanentemente todas las memorias, usuarios y modelos descargados.

#### Persistencia de Volúmenes Docker:
Los datos residen en volúmenes Docker gestionados fuera del ciclo de vida del contenedor:
- `postgres_data`: Tablas de usuarios, contraseñas hash, planes de legado y conexiones familiares.
- `mongo_data`: Documentos NoSQL de cápsulas de memoria, perfiles lingüísticos y sesiones de chat.
- `chroma_data`: Vectores cosine indexados para búsqueda semántica RAG.
- `ollama_data`: Pesos descargados de los modelos de lenguaje (evita volver a descargar ~4.7 GB).

---

### Opción 2: Desarrollo Local sin Docker (Nativo en Windows)

Si prefieres ejecutar el backend directamente en Windows mediante Python, la aplicación cuenta con conmutación por contingencia automática (*resilient fallback*).

#### Requisitos a Proveer por el Usuario:
- **Python 3.11 o 3.12** instalado con la casilla *"Add python.exe to PATH"* marcada.
- **Node.js 18+** y `npm`.
- **Ollama para Windows** ([ollama.com](https://ollama.com/download/windows)) iniciado y con el modelo descargado:
  ```powershell
  ollama run llama3:8b
  ```
- *(Opcional)* Servidores locales de PostgreSQL 16 y MongoDB 7. Si no están instalados:
  - **SQL**: El backend conmutará automáticamente a SQLite local en `legadovivo_dev.db` (en la raíz del proyecto).
  - **ChromaDB**: Utilizará almacenamiento persistente local en `chroma_storage/`.
  - **MongoDB**: Operará con la memoria reactiva de demostración.

#### Arranque Rápido con Scripts de Windows:

- **Usando el Launcher Interactivo (`start.bat`):**
  Doble clic en `start.bat` o ejecútalo desde PowerShell:
  - Opción `[1]`: Inicia el Frontend en `http://localhost:5173`.
  - Opción `[2]`: Levanta la infraestructura Docker verificando prerrequisitos.
  - Opción `[3]`: Prepara el entorno virtual venv e inicia FastAPI en `http://localhost:8080`.
  - Opción `[4]`: Consulta el estado de `/api/health` e imprime el diagnóstico en consola.

- **Arranque manual del Backend con PowerShell:**
  ```powershell
  cd backend
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install --upgrade pip
  pip install -r requirements.txt
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
  ```

#### Rutas de Almacenamiento Local:
- Base de datos relacional SQLite de desarrollo: `<raiz_del_proyecto>\legadovivo_dev.db`
- Almacenamiento de embeddings ChromaDB local: `<raiz_del_proyecto>\chroma_storage\`

---

## 🗄️ Esquema de Base de Datos: `create_all()` vs Migraciones Alembic

Al iniciar el backend, se ejecuta:
```python
Base.metadata.create_all(bind=engine)
```
- **¿Por qué basta para desarrollo?** `create_all()` inspecciona los metadatos de SQLAlchemy y genera las tablas faltantes (`users`, `legacy_connections`, `legacy_plans`, `audit_logs`) tanto en PostgreSQL como en SQLite sin requerir pasos manuales de configuración.
- **¿Cuándo se requiere Alembic?** `create_all()` no altera tablas existentes si se modifican, eliminan o agregan columnas a modelos existentes. Para entornos productivos o cambios de esquema con datos persistidos, `alembic` se encuentra preinstalado en `backend/requirements.txt` y se configura mediante:
  ```bash
  alembic init alembic
  alembic revision --autogenerate -m "cambio_en_esquema"
  alembic upgrade head
  ```

---

## 🔑 Endpoints de la API REST

### 1. Autenticación & Seguridad (`/api/auth`)
* `POST /api/auth/register`: Registro con hashing de contraseñas vía BCrypt y emisión de JWT.
* `POST /api/auth/login`: Autenticación con verificación BCrypt y emisión de Bearer Token.
* `GET /api/auth/me`: Perfil del usuario autenticado vía `get_current_user`.

### 2. Vinculación & Conexiones (`/api/legacy`)
* `POST /api/legacy/generate-code`: Genera un código de invitación criptográfico para beneficiarios.
* `POST /api/legacy/link`: Vincula al usuario activo como beneficiario con el titular dueño del código.
* `GET /api/legacy/my-connections`: Lista de legados autorizados para el beneficiario (Seres Queridos).
* `GET /api/legacy/my-beneficiaries`: Lista de familiares vinculados al legado del titular.

### 3. Recuerdos & Chat Neuronal
* `POST /api/capsules/`: Ingesta, cálculo de embeddings en ChromaDB y actualización del Learning Loop de estilo.
* `GET /api/capsules/`: Biblioteca de recuerdos del titular.
* `GET /api/capsules/style-profile`: Síntesis lingüística de muletillas, calidez y tono.
* `POST /api/chat/`: Chat RAG con Ollama y regla estricta de Cero Alucinación. Retorna:
  - `response`: Texto de la respuesta.
  - `sources`: Títulos de los recuerdos verificados utilizados.
  - `confidence`: Nivel de similitud semántica.
  - `matched_memories`: Número de recuerdos coincidentes.
  - `llm_status`: `"generated"` (Ollama real), `"no_memories"` (Cero Alucinación), `"model_not_found"` o `"ollama_unavailable"`.
  - `model_used`: Nombre del modelo LLM ejecutado.

### 4. Salud & Diagnóstico del Sistema
* `GET /api/health` y `GET /health`: Diagnóstico exhaustivo que reporta el estado individual de PostgreSQL, MongoDB, ChromaDB y Ollama (indicando si el servicio responde y si el modelo está descargado).

---

## 🧪 Pruebas Automatizadas

Para ejecutar la suite de pruebas del backend:
```powershell
cd backend
pytest tests/ -v
```

* **`backend/tests/test_rag_and_style.py`**: Valida el extractor lingüístico de modismos y la regla forzada de Cero Alucinación.
* **`backend/tests/test_auth_and_connections.py`**: Valida el hashing BCrypt, la generación de JWT y el formato de códigos de invitación (`LEG-XXXXXX`).

---

## 🛠️ Solución de Problemas Comunes en Windows

1. **Docker reporta `error during connect: ... open //./pipe/docker_engine`:**
   - Docker Desktop no está iniciado. Ábrelo desde el menú de inicio y espera a que la barra de estado indique *"Engine running"*.
2. **Conflicto de puertos (Ej. `port 5432 is already allocated`):**
   - Tienes una instancia local de PostgreSQL o MongoDB ocupando el puerto. Puedes cambiar los puertos en el archivo `.env` (ej. `POSTGRES_PORT=5433`, `API_PORT=8081`).
3. **El Frontend muestra el aviso `"Modo Demostración Local"`:**
   - Significa que el frontend no pudo comunicarse con el backend en `http://localhost:8080/api`. Revisa con `docker compose ps` si el contenedor `legadovivo_backend` está saludable o si ocurrió algún error en los logs (`docker compose logs backend`).
4. **El Chat indica `"Ollama Inaccesible"` o `"Modelo no descargado"`:**
   - Comprueba que el contenedor `legadovivo_ollama` esté activo y descarga el modelo con:
     ```powershell
     docker exec -it legadovivo_ollama ollama pull llama3:8b
     ```
5. **En PowerShell aparece `cannot be loaded because running scripts is disabled on this system`:**
   - Habilita la ejecución de scripts para el usuario actual:
     ```powershell
     Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
     ```

# Arquitectura del Sistema RAG Estado Peru

**Versión:** 1.0
**Última actualización:** Enero 2025

---

## Resumen Ejecutivo

**RAG Estado Peru** es un sistema de Retrieval-Augmented Generation (RAG) construido desde cero (sin LangChain) para responder preguntas sobre documentos públicos peruanos con citas verificables.

**Stack Tecnológico:**
- **Backend:** FastAPI, Pydantic, Python 3.11+
- **Vector Store:** ChromaDB con persistencia
- **Embeddings:** SentenceTransformers (multilingual)
- **LLMs:** Groq (principal) + Google Gemini (fallback)
- **Contenedores:** Docker + Docker Compose

**Características Principales:**
- Búsqueda híbrida (vectorial + keyword)
- Multi-proveedor LLM con fallback automático
- Guardrails (grounding check, PII scrubbing, refusal policy)
- Cache de respuestas con TTL
- Routing inteligente de modelos
- Sistema de evaluación integrado

---

## Estructura del Proyecto

```
rag-estado-peru/
├── packages/
│   └── rag_core/                 # Núcleo del sistema RAG
│       ├── __init__.py
│       ├── config.py             # Configuración centralizada
│       ├── loaders.py            # Carga de PDFs y HTML
│       ├── chunker.py            # División de documentos
│       ├── vectorstore.py        # Embeddings y búsqueda híbrida
│       ├── generator.py          # Generación con LLMs
│       ├── pipeline.py           # Orquestador principal
│       ├── cache.py              # Cache de respuestas
│       ├── router.py             # Routing de modelos
│       ├── providers/            # Proveedores LLM
│       │   ├── __init__.py
│       │   ├── base.py           # Interfaz abstracta
│       │   ├── groq.py           # Proveedor Groq
│       │   ├── gemini.py         # Proveedor Gemini
│       │   └── factory.py        # Fábrica de proveedores
│       ├── guardrails/           # Seguridad y validación
│       │   ├── __init__.py
│       │   ├── grounding_check.py
│       │   ├── refusal_policy.py
│       │   └── pii_scrubber.py
│       └── eval/                 # Sistema de evaluación
│           ├── __init__.py
│           ├── dataset.py
│           ├── metrics.py
│           └── report.py
├── services/
│   └── api/                      # API REST
│       ├── __init__.py
│       ├── main.py               # FastAPI app
│       ├── schemas.py            # Modelos Pydantic
│       └── static/
│           └── index.html        # UI web básica
├── scripts/                      # Herramientas CLI
│   ├── ingest.py                 # Ingesta de documentos
│   ├── query.py                  # Consultas CLI
│   ├── eval_run.py               # Ejecutar evaluación
│   ├── build_eval_set.py         # Crear dataset de eval
│   ├── debug_chunks.py           # Debug de chunks
│   └── test_pipeline.py          # Test del pipeline
├── tests/                        # Tests unitarios
│   ├── __init__.py
│   ├── test_chunker.py
│   ├── test_guardrails.py
│   └── test_api_smoke.py
├── data/
│   ├── raw/                      # PDFs originales
│   ├── processed/                # Datos procesados
│   └── chroma/                   # Vector store persistente
├── reports/                      # Reportes de evaluación
├── .github/
│   └── workflows/
│       └── ci.yml                # Pipeline CI/CD
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── .env                          # Variables de entorno
```

---

## Componentes del Sistema

### 1. Configuración (`config.py`)

**Propósito:** Gestión centralizada de configuración usando Pydantic Settings.

**Librerías:**
- `pydantic_settings.BaseSettings`
- `functools.lru_cache`

**Clase Principal:** `Settings`

```python
class Settings(BaseSettings):
    # LLM Providers
    google_api_key: str = ""
    groq_api_key: str = ""

    # Modelos
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_provider: str = "groq"  # groq, gemini, auto

    # Embeddings
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # RAG Parameters
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_results: int = 5

    # Hybrid Search
    hybrid_search: bool = True
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
```

**Integración:** Usado por todos los componentes vía `get_settings()` (singleton con cache LRU).

---

### 2. Cargadores de Documentos (`loaders.py`)

**Propósito:** Extracción de texto de PDFs y HTML.

**Librerías:**
- `pdfplumber` - Extracción de texto de PDFs
- `beautifulsoup4` - Parsing de HTML
- `hashlib` - Generación de hashes de contenido

**Clases:**

| Clase | Descripción |
|-------|-------------|
| `Document` | Dataclass con `content`, `metadata`, `content_hash` |
| `PDFLoader` | Extrae texto página por página de PDFs |
| `HTMLLoader` | Scraping de HTML (URLs o archivos locales) |

**Funciones:**
- `load_documents_from_directory(path)` → Lista de Document

**Uso:**
```python
loader = PDFLoader("documento.pdf")
documents = loader.load()  # List[Document]
```

---

### 3. Chunker (`chunker.py`)

**Propósito:** Dividir documentos en chunks manejables con overlap.

**Librerías:**
- `dataclasses`
- `uuid`

**Clase Principal:** `TextChunker`

**Algoritmo:**
1. Dividir texto en chunks de tamaño fijo (default: 512 chars)
2. Aplicar overlap (default: 50 chars) para contexto
3. Cortar en límites de palabras (no cortar palabras)
4. Generar ID único: `{source}::p{page}::c{index}::{uuid[:8]}`

**Output:** `Chunk` dataclass con:
- `chunk_id` - Identificador único
- `content` - Texto del chunk
- `metadata` - Incluye `chunk_index`, `chunk_start`, `chunk_end`

---

### 4. Vector Store (`vectorstore.py`)

**Propósito:** Almacenamiento de embeddings y búsqueda híbrida.

**Librerías:**
- `chromadb` - Base de datos vectorial
- `sentence_transformers` - Modelo de embeddings
- `unicodedata`, `re` - Normalización de texto

**Clases:**

| Clase | Descripción |
|-------|-------------|
| `EmbeddingModel` | Wrapper para SentenceTransformers (lazy loading) |
| `VectorStore` | ChromaDB con búsqueda híbrida |

**Métodos Principales:**

```python
class VectorStore:
    def add_chunks(chunks: List[Chunk]) -> int
    def search(query: str, top_k: int) -> List[dict]
    def _vector_search(query, top_k) -> List[dict]
    def _keyword_search(query, top_k) -> List[dict]
    def _merge_results(vector, keyword, top_k, weights) -> List[dict]
    def count() -> int
    def clear()
```

**Búsqueda Híbrida:**

```
┌─────────────────────────────────────────────────────┐
│                 search(query)                        │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐        │
│  │ _vector_search  │    │ _keyword_search │        │
│  │ (embeddings)    │    │ (BM25-like)     │        │
│  └────────┬────────┘    └────────┬────────┘        │
│           │                      │                  │
│           └──────────┬───────────┘                  │
│                      ▼                              │
│           ┌─────────────────┐                       │
│           │ _merge_results  │                       │
│           │ 70% vector      │                       │
│           │ 30% keyword     │                       │
│           └─────────────────┘                       │
└─────────────────────────────────────────────────────┘
```

**Keyword Search - Scoring:**
- Token hits: +1 por cada match
- Phrase matches: +1.5x por bigrama/trigrama
- Exact match: +2.0x bonus
- Score final normalizado 0-1

---

### 5. Generador (`generator.py`)

**Propósito:** Generación de respuestas usando LLMs.

**Librerías:**
- `json` - Parsing de respuestas
- Providers internos (Groq, Gemini)

**Clase Principal:** `MultiProviderGenerator`

**Características:**
- Interfaz unificada para múltiples LLMs
- Fallback automático entre proveedores
- Output estructurado en JSON
- Streaming support (SSE)
- Enriquecimiento de citas desde chunks

**System Prompt:**
```
Eres un asistente especializado en documentos públicos peruanos.
Responde SOLO con información de los documentos proporcionados.
Formato JSON obligatorio con: answer, citations, confidence, refusal.
```

**Response Structure:**
```json
{
    "answer": "La respuesta...",
    "citations": [
        {"quote": "texto citado", "source": "doc.pdf", "page": 7}
    ],
    "confidence": 0.95,
    "refusal": false,
    "notes": "opcional"
}
```

---

### 6. Pipeline (`pipeline.py`)

**Propósito:** Orquestador principal del flujo RAG.

**Clase Principal:** `RAGPipeline`

**Flujo de Query:**

```
┌─────────────────────────────────────────────────────────────┐
│                    pipeline.query(question)                  │
├─────────────────────────────────────────────────────────────┤
│  1. normalize_query()        → Limpiar acentos, espacios    │
│  2. cache.get()              → Verificar cache              │
│  3. pii_scrubber.scrub()     → Limpiar PII (logs)          │
│  4. refusal_policy (pre)     → Rechazar off-topic          │
│  5. vector_store.search()    → Búsqueda híbrida            │
│  6. router.route()           → Seleccionar modelo          │
│  7. generator.generate()     → Generar respuesta           │
│  8. grounding_checker.check()→ Verificar fundamentación    │
│  9. refusal_policy (post)    → Rechazar alucinaciones      │
│  10. cache.set()             → Guardar en cache            │
│  11. return response         → Respuesta final             │
└─────────────────────────────────────────────────────────────┘
```

**Flujo de Ingesta:**
```python
def ingest_directory(directory):
    documents = load_documents_from_directory(directory)
    chunks = chunk_documents(documents, chunk_size, overlap)
    self.vector_store.add_chunks(chunks)
```

---

### 7. Cache (`cache.py`)

**Propósito:** Reducir llamadas a API para queries repetidas.

**Librerías:**
- `json` - Persistencia
- `threading.Lock` - Thread safety
- `hashlib` - Normalización de queries

**Clase Principal:** `ResponseCache` (singleton)

**Características:**
- TTL: 24 horas por defecto
- LRU eviction: elimina 20% más antiguo al llenarse
- Persistencia JSON (sobrevive reinicios)
- Normalización de queries para mejor hit rate

**Estadísticas:**
- hits, misses, saves
- ~40% reducción de llamadas API

---

### 8. Router (`router.py`)

**Propósito:** Seleccionar modelo óptimo según complejidad.

**Clase Principal:** `ModelRouter` (singleton)

**Scoring de Complejidad:**
```python
# Indicadores que aumentan complejidad
+0.3  "analizar", "comparar", "evaluar"
+0.2  "por qué", "cómo"
+0.15 "explicar", "diferencia"

# Indicadores que reducen complejidad
-0.2  "qué es", "definición"
-0.15 "cuál es el plazo", "dónde"

# Normalización por longitud
score += min(len(query) / 200, 0.2)
```

**Tiers:**
| Tier | Complejidad | Groq | Gemini |
|------|-------------|------|--------|
| LITE | < 0.5 | llama-3.1-8b | gemini-2.0-flash-lite |
| STANDARD | >= 0.5 | llama-3.3-70b | gemini-2.5-flash |

---

### 9. Proveedores LLM (`providers/`)

#### Base (`base.py`)
```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(prompt, model, max_tokens, temperature) -> LLMResponse

    @abstractmethod
    def generate_stream(...) -> Generator[str]

    @abstractmethod
    def is_available() -> bool
```

#### Groq (`groq.py`)
- **API:** OpenAI-compatible
- **Endpoint:** `https://api.groq.com/openai/v1`
- **Modelos:** llama-3.3-70b, llama-3.1-8b, mixtral-8x7b
- **Ventaja:** Ultra-baja latencia (LPU)

#### Gemini (`gemini.py`)
- **SDK:** `google-generativeai`
- **Modelos:** gemini-2.5-flash, gemini-2.0-flash-lite
- **Rol:** Proveedor de fallback

#### Factory (`factory.py`)
```python
get_provider(name: str) -> LLMProvider
get_available_providers() -> List[str]
get_provider_with_fallback(primary, fallback) -> LLMProvider
```

---

### 10. Guardrails (`guardrails/`)

#### Grounding Check (`grounding_check.py`)

**Propósito:** Verificar que la respuesta está fundamentada en el contexto.

**Algoritmo:**
1. Extraer claims (oraciones) de la respuesta
2. Para cada claim:
   - Extraer frases clave (sustantivos, términos técnicos)
   - Buscar en contexto (60% peso)
   - Calcular similitud semántica (40% peso)
3. grounding_ratio = claims_soportados / total_claims
4. is_grounded si ratio >= 0.3

**Parámetros:**
- `min_similarity`: 0.2 (permisivo para paráfrasis)
- `min_grounding_ratio`: 0.3 (30% de claims respaldados)

#### Refusal Policy (`refusal_policy.py`)

**Razones de Rechazo:**
| Razón | Condición |
|-------|-----------|
| NO_CONTEXT | < 1 chunk recuperado |
| LOW_RELEVANCE | score promedio < 0.1 |
| UNGROUNDED | grounding_score < 0.1 |
| OFF_TOPIC | Detecta "receta", "fútbol", etc. |

**Override por Confianza:**
Si `llm_confidence >= 0.5` y tiene citas → aceptar con advertencia.

#### PII Scrubber (`pii_scrubber.py`)

**Patrones Detectados:**
- DNI: 8 dígitos
- RUC: 11 dígitos (prefijos 10, 15, 17, 20)
- Teléfono: +51 o 9XXXXXXXX
- Email: formato estándar
- Tarjeta de crédito: XXXX-XXXX-XXXX-XXXX
- IP: XXX.XXX.XXX.XXX

---

### 11. Sistema de Evaluación (`eval/`)

#### Dataset (`dataset.py`)
```python
@dataclass
class EvalItem:
    question: str
    expected_sources: List[str]
    gold_answer: str
    category: str
    difficulty: str  # easy, medium, hard
```

**Formato:** JSONL (JSON Lines)

#### Metrics (`metrics.py`)

| Métrica | Descripción |
|---------|-------------|
| Hit@K | ¿Fuente esperada en top-K? |
| Precision | % de fuentes recuperadas correctas |
| Recall | % de fuentes esperadas recuperadas |
| Faithfulness | Grounding score |
| Answer Relevance | Confianza del LLM |
| Latency | Tiempo de respuesta (ms) |

**Umbrales:**
- Hit@K >= 70%
- Faithfulness >= 70%

#### Report (`report.py`)
- Output JSON (machine-readable)
- Output Markdown (human-readable)
- Análisis de fortalezas/debilidades

---

### 12. API REST (`services/api/`)

#### Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio |
| `/stats` | GET | Estadísticas del sistema |
| `/query` | POST | Query RAG sincrónica |
| `/query/stream` | POST | Query con streaming (SSE) |
| `/ingest` | POST | Ingestar documentos |
| `/clear` | DELETE | Limpiar vector store |
| `/cache/clear` | DELETE | Limpiar cache |
| `/debug/chunks` | POST | Ver chunks recuperados |
| `/debug/settings` | GET | Ver configuración |
| `/debug/llm` | POST | Test LLM sin guardrails |
| `/debug/pdf-search` | POST | Buscar texto en PDF |

#### Schemas (`schemas.py`)

```python
class QueryRequest(BaseModel):
    question: str  # min 3 chars
    top_k: int = 5  # 1-20

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    sources_used: int
    model: str
    confidence: float
    latency_ms: int
    from_cache: bool

class Citation(BaseModel):
    source: str
    page: int
    quote: str
    relevance_score: float
```

---

### 13. Scripts CLI (`scripts/`)

| Script | Comando | Descripción |
|--------|---------|-------------|
| `ingest.py` | `python scripts/ingest.py --directory ./data/raw` | Ingestar PDFs |
| `query.py` | `python scripts/query.py "pregunta"` | Query desde CLI |
| `query.py` | `python scripts/query.py --interactive` | Modo REPL |
| `eval_run.py` | `python scripts/eval_run.py --report` | Ejecutar evaluación |
| `debug_chunks.py` | `python scripts/debug_chunks.py "query"` | Debug de retrieval |

---

### 14. Tests (`tests/`)

| Test | Cobertura |
|------|-----------|
| `test_chunker.py` | División de documentos, IDs únicos, overlap |
| `test_guardrails.py` | PII detection, grounding, refusal |
| `test_api_smoke.py` | Endpoints disponibles, validación |

---

## Dependencias

### Core
```
fastapi>=0.109.0
uvicorn[standard]
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

### LLM Providers
```
google-generativeai>=0.3.0
openai>=1.0.0
```

### Vector & Embeddings
```
chromadb>=0.4.22
sentence-transformers>=2.2.2
```

### Document Processing
```
pypdf>=3.17.0
pdfplumber>=0.10.3
beautifulsoup4>=4.12.0
lxml>=5.1.0
```

### Development
```
pytest>=7.4.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
ruff>=0.1.0
```

---

## Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INGESTA                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   PDF/HTML  ──→  PDFLoader  ──→  Chunker  ──→  EmbeddingModel       │
│                  HTMLLoader       │              │                   │
│                                   ▼              ▼                   │
│                              [Chunks]  ──→  ChromaDB                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           QUERY                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   User Query                                                         │
│       │                                                              │
│       ▼                                                              │
│   ┌─────────┐    ┌─────────┐    ┌──────────────┐                   │
│   │ Cache   │───▶│ Return  │    │ PII Scrubber │                   │
│   │ Hit?    │yes │ Cached  │    │ (for logs)   │                   │
│   └────┬────┘    └─────────┘    └──────────────┘                   │
│        │no                                                          │
│        ▼                                                             │
│   ┌──────────────┐                                                  │
│   │ Refusal      │──refused──▶ Return Refusal                      │
│   │ Policy (pre) │                                                  │
│   └──────┬───────┘                                                  │
│          │ok                                                         │
│          ▼                                                           │
│   ┌──────────────────────────────────────┐                          │
│   │           VectorStore.search()        │                         │
│   │  ┌────────────┐  ┌────────────────┐  │                         │
│   │  │ Vector     │  │ Keyword        │  │                         │
│   │  │ Search     │  │ Search         │  │                         │
│   │  └─────┬──────┘  └───────┬────────┘  │                         │
│   │        │                 │           │                          │
│   │        └────────┬────────┘           │                          │
│   │                 ▼                    │                          │
│   │          Merge Results               │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│   ┌──────────────────────────────────────┐                          │
│   │           Model Router               │                          │
│   │   Complexity Score → Model Selection │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│   ┌──────────────────────────────────────┐                          │
│   │      MultiProviderGenerator          │                          │
│   │  ┌─────────┐     ┌─────────┐        │                          │
│   │  │  Groq   │────▶│ Gemini  │        │                          │
│   │  │(primary)│fail │(fallback)│        │                          │
│   │  └─────────┘     └─────────┘        │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│   ┌──────────────────────────────────────┐                          │
│   │         Grounding Checker            │                          │
│   │   Verify answer matches context      │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│   ┌──────────────────────────────────────┐                          │
│   │       Refusal Policy (post)          │                          │
│   │   Accept / Warn / Refuse             │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│   ┌──────────────────────────────────────┐                          │
│   │           Save to Cache              │                          │
│   └──────────────────┬───────────────────┘                          │
│                      │                                               │
│                      ▼                                               │
│              Return Response                                         │
│              {answer, citations, confidence, ...}                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuración de Producción

### Variables de Entorno (`.env`)

```bash
# LLM Providers (al menos uno requerido)
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Modelos
GEMINI_MODEL=gemini-2.5-flash
GROQ_MODEL=openai/gpt-oss-120b
LLM_PROVIDER=auto  # auto, groq, gemini

# Embeddings
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# RAG Parameters
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Hybrid Search
HYBRID_SEARCH=true
VECTOR_WEIGHT=0.7
KEYWORD_WEIGHT=0.3

# Paths
CHROMA_PERSIST_DIR=/app/data/chroma
```

### Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data/raw:/app/data/raw
      - ./data/chroma:/app/data/chroma
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### CI/CD (GitHub Actions)

```yaml
jobs:
  lint:    # ruff check
  test:    # pytest
  docker:  # Build image
  evaluate: # Run evaluation (optional)
```

---

## Métricas de Performance

| Métrica | Valor Típico |
|---------|--------------|
| Retrieval (hybrid) | 50-200ms |
| LLM Generation (Groq) | 1-3s |
| LLM Generation (Gemini) | 2-5s |
| Total Latency (cold) | 1.5-8s |
| Total Latency (cached) | <100ms |
| Cache Hit Rate | 30-40% |
| Memory Usage | ~2GB |

---

## Patrones de Diseño Utilizados

1. **Singleton** - Settings, Cache, Router, Provider Factory
2. **Factory** - Creación de proveedores LLM
3. **Strategy** - Proveedores LLM intercambiables
4. **Template Method** - Flujo de query en Pipeline
5. **Decorator** - Middleware CORS en FastAPI

---

## Uso Rápido

### Instalación
```bash
git clone <repo>
cd rag-estado-peru
pip install -e .
cp .env.example .env
# Editar .env con API keys
```

### Ingestar Documentos
```bash
python scripts/ingest.py --directory ./data/raw
```

### Consultar
```bash
# CLI
python scripts/query.py "¿Qué es la NORMA XV?"

# API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la NORMA XV?"}'
```

### Docker
```bash
docker compose up --build
# API disponible en http://localhost:8000
```

---

## Archivos No Utilizados

Después del análisis, **todos los archivos del proyecto están siendo utilizados activamente**:

- `/packages/rag_core/` - Núcleo del sistema, 100% utilizado
- `/services/api/` - API REST, 100% utilizado
- `/scripts/` - Herramientas CLI, todas funcionales
- `/tests/` - Tests unitarios ejecutados en CI
- `/.github/workflows/` - Pipeline CI/CD activo

El único directorio que podría considerarse "auxiliar" es `/rag_estado_peru.egg-info/` que es generado automáticamente por `pip install -e .` y no necesita versionarse.

---

## Conclusión

El sistema RAG Estado Peru es una implementación completa y production-ready que demuestra:

1. **Arquitectura modular** - Componentes desacoplados y testables
2. **Multi-proveedor** - No hay vendor lock-in
3. **Búsqueda híbrida** - Mejor recall que solo vectorial
4. **Guardrails robustos** - Prevención de alucinaciones
5. **Evaluación integrada** - Métricas de calidad
6. **DevOps ready** - Docker, CI/CD, health checks

El sistema está diseñado para escalar y adaptarse a nuevos documentos, proveedores LLM, o requisitos de negocio.

# Arquitectura del Sistema

## Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE                                 │
│                    (API REST / CLI)                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Service                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  /health    │  │  /query     │  │  /ingest                │ │
│  └─────────────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└──────────────────────────┼─────────────────────┼────────────────┘
                           │                     │
                           ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                       RAG Pipeline                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CONSULTA                               │   │
│  │  Query → Embedding → Retriever → Generator → Guardrails  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    INGESTA                                │   │
│  │  Docs → Loader → Chunker → Embeddings → Vector Store     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                           │                     │
              ┌────────────┴─────────┐   ┌──────┴───────┐
              ▼                      ▼   ▼              ▼
      ┌──────────────┐        ┌──────────────┐  ┌─────────────┐
      │   ChromaDB   │        │   Gemini     │  │  Sentence   │
      │ Vector Store │        │   2.5 Flash  │  │ Transformers│
      └──────────────┘        └──────────────┘  └─────────────┘
```

---

## Componentes Principales

### 1. API Layer (`services/api/`)

| Archivo | Responsabilidad |
|---------|-----------------|
| `main.py` | FastAPI app, endpoints, lifecycle |
| `schemas.py` | Pydantic models para request/response |

**Endpoints:**
- `GET /health` - Health check
- `GET /stats` - Estadísticas del sistema
- `POST /query` - Consulta RAG
- `POST /ingest` - Ingesta de documentos
- `DELETE /clear` - Limpia vector store

### 2. RAG Core (`packages/rag_core/`)

#### 2.1 Loaders (`loaders.py`)
- `PDFLoader`: Extrae texto de PDFs con pdfplumber
- `HTMLLoader`: Parsea HTML local o desde URL
- `load_documents_from_directory()`: Carga masiva

#### 2.2 Chunker (`chunker.py`)
- `TextChunker`: Divide documentos en chunks
- Parámetros: `chunk_size=512`, `chunk_overlap=50`
- Preserva metadata del documento origen

#### 2.3 Vector Store (`vectorstore.py`)
- `EmbeddingModel`: Wrapper para sentence-transformers
- `VectorStore`: ChromaDB con persistencia
- Operaciones: `add_chunks()`, `search()`, `count()`, `clear()`

#### 2.4 Generator (`generator.py`)
- `GeminiGenerator`: Genera respuestas con Gemini
- Output JSON estructurado
- Manejo de errores y parsing

#### 2.5 Guardrails (`guardrails/`)
- `GroundingChecker`: Verifica fundamentación
- `RefusalPolicy`: Política de rechazo
- `PIIScrubber`: Detecta y redacta PII

#### 2.6 Pipeline (`pipeline.py`)
- `RAGPipeline`: Orquesta todo el flujo
- Integra guardrails
- Métodos: `ingest_directory()`, `query()`, `get_stats()`

---

## Flujo de Datos

### Ingesta

```
1. PDF/HTML en data/raw/
         │
         ▼
2. Loader extrae texto + metadata
   - PDFLoader: texto por página
   - HTMLLoader: texto por sección
         │
         ▼
3. Chunker divide en fragmentos
   - 512 caracteres por chunk
   - 50 caracteres de overlap
   - Preserva: source, page, chunk_index
         │
         ▼
4. EmbeddingModel genera vectores
   - Modelo: paraphrase-multilingual-MiniLM-L12-v2
   - Dimensión: 384
         │
         ▼
5. ChromaDB almacena
   - IDs únicos por chunk
   - Vectores + metadata + texto
   - Persistencia en data/chroma/
```

### Consulta

```
1. Query del usuario
         │
         ▼
2. PIIScrubber (para logs)
   - Detecta DNI, RUC, emails, etc.
   - Genera versión segura para logs
         │
         ▼
3. RefusalPolicy (pre-check)
   - ¿Query fuera de tema?
   - Si sí → refusal inmediato
         │
         ▼
4. EmbeddingModel genera vector de query
         │
         ▼
5. VectorStore.search()
   - Busca top-k chunks similares
   - Retorna: content, metadata, score
         │
         ▼
6. RefusalPolicy (relevance check)
   - ¿Chunks relevantes? (score > 0.3)
   - Si no → refusal
         │
         ▼
7. GeminiGenerator
   - Construye prompt con contexto
   - Genera respuesta JSON
   - Parsea y valida
         │
         ▼
8. GroundingChecker
   - Verifica que respuesta use contexto
   - Calcula grounding_score
         │
         ▼
9. RefusalPolicy (post-check)
   - ¿Grounding suficiente? (> 0.5)
   - Si no → refusal post-generación
         │
         ▼
10. Respuesta final
    - answer, citations, confidence
    - guardrails info
    - latency_ms
```

---

## Configuración

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | API key de Gemini | Requerido |
| `GEMINI_MODEL` | Modelo a usar | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| `CHROMA_PERSIST_DIR` | Directorio de ChromaDB | `./data/chroma` |
| `CHUNK_SIZE` | Tamaño de chunk | `512` |
| `CHUNK_OVERLAP` | Overlap entre chunks | `50` |
| `TOP_K_RESULTS` | Chunks a recuperar | `5` |

### Archivos de Configuración

- `.env` - Variables de entorno (no versionar)
- `.env.example` - Template de variables
- `pyproject.toml` - Dependencias y metadata

---

## Decisiones de Diseño

### ¿Por qué ChromaDB?
- Setup simple (pip install)
- Persistencia local sin servidor
- Suficiente para volumen de MVP
- Buena integración con Python

### ¿Por qué Sentence Transformers?
- 100% local, sin costos de API
- Modelo multilingüe (español)
- Balance velocidad/calidad
- ~120MB de modelo

### ¿Por qué Gemini 2.5 Flash?
- Tier gratuito generoso
- Buen soporte de español
- Contexto largo
- SDK oficial Python

### ¿Por qué guardrails separados?
- Modularidad (pueden desactivarse)
- Testeable independientemente
- Extensible (agregar más checks)
- Transparencia en decisiones

---

## Escalabilidad

### Actual (MVP)
- 1-100 documentos
- 10K-100K chunks
- Latencia: 1-5 segundos
- Usuarios: 1-10 concurrentes

### Futuro
| Componente | Actual | Escalado |
|------------|--------|----------|
| Vector Store | ChromaDB local | Qdrant/Pinecone |
| Embeddings | Local CPU | GPU / API |
| LLM | Gemini API | Self-hosted |
| API | Single instance | K8s + load balancer |

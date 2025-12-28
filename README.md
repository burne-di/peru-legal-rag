# RAG Estado Perú

### Sistema de Preguntas y Respuestas con citas verificables sobre normativa pública peruana

[![CI](https://github.com/username/rag-estado-peru/actions/workflows/ci.yml/badge.svg)](https://github.com/username/rag-estado-peru/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema **RAG (Retrieval-Augmented Generation)** end-to-end para responder preguntas sobre **documentos públicos del Estado Peruano** (normativa tributaria, resoluciones, comunicados en PDF/HTML), retornando respuestas **fundamentadas con citas verificables**.

---

## Competencias Demostradas

### GenAI / AI Engineering
- Pipeline RAG completo (ingesta → embeddings → retrieval → generación)
- Prompt engineering con output JSON estructurado
- **Guardrails**: anti-alucinación (grounding check), política de rechazo, sanitización PII
- Evaluación offline con métricas de calidad RAG

### Ingeniería de Software
- Arquitectura modular y reutilizable (`packages/rag_core`)
- API REST con FastAPI + Pydantic
- Docker/Compose para despliegue
- CI/CD con GitHub Actions
- Testing unitario y smoke tests
- Documentación de gobernanza y riesgos

---

## Demo Rápida

```bash
# 1. Clonar e instalar
git clone https://github.com/username/rag-estado-peru.git
cd rag-estado-peru
pip install -e .

# 2. Configurar API key de Gemini
cp .env.example .env
# Editar .env con tu GOOGLE_API_KEY

# 3. Ingestar documentos
python scripts/ingest.py

# 4. Hacer consultas
python scripts/query.py -i
```

**Ejemplo de consulta:**
```
📝 Tu pregunta: ¿Cuál es el plazo para presentar una reclamación tributaria?

📌 RESPUESTA:
El plazo para presentar una reclamación tributaria es de 20 días hábiles
contados desde el día siguiente de la notificación del acto administrativo.

📚 FUENTES:
[1] Codigo-Tributario-Sunat.pdf - Página 45
    Relevancia: 92%
```

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE                                 │
│                    (API REST / CLI)                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Service                            │
│         /health    /query    /ingest    /stats                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       RAG Pipeline                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Query → PII Scrub → Retrieval → Generator → Grounding Check│ │
│  │                                              → Refusal Policy│ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                    │                   │
        ┌───────────┴───────┐   ┌───────┴───────┐
        ▼                   ▼   ▼               ▼
   ┌──────────┐      ┌──────────┐      ┌─────────────┐
   │ ChromaDB │      │  Gemini  │      │  Sentence   │
   │  Vector  │      │2.5 Flash │      │ Transformers│
   │  Store   │      │          │      │ (Embeddings)│
   └──────────┘      └──────────┘      └─────────────┘
```

### Flujo de Consulta con Guardrails

1. **Query** → Recibe pregunta del usuario
2. **PII Scrubber** → Detecta y redacta información sensible (DNI, RUC, emails)
3. **Refusal Policy (pre)** → Rechaza queries fuera de tema
4. **Retrieval** → Busca chunks relevantes en ChromaDB
5. **Generator** → Genera respuesta JSON estructurada con Gemini
6. **Grounding Check** → Verifica que respuesta esté fundamentada
7. **Refusal Policy (post)** → Rechaza si grounding < 50%
8. **Response** → Retorna answer + citations + confidence

---

## Estructura del Proyecto

```
rag-estado-peru/
├── packages/rag_core/           # Lógica central RAG
│   ├── config.py                # Configuración con pydantic-settings
│   ├── loaders.py               # Carga PDF y HTML
│   ├── chunker.py               # División en chunks con overlap
│   ├── vectorstore.py           # ChromaDB + embeddings
│   ├── generator.py             # Gemini con output JSON
│   ├── pipeline.py              # Orquestador principal
│   ├── guardrails/              # Validación y seguridad
│   │   ├── grounding_check.py   # Anti-alucinación
│   │   ├── refusal_policy.py    # Política de rechazo
│   │   └── pii_scrubber.py      # Sanitización PII
│   └── eval/                    # Evaluación de calidad
│       ├── dataset.py           # Dataset de evaluación
│       ├── metrics.py           # Hit@K, Faithfulness, etc.
│       └── report.py            # Generación de reportes
│
├── services/api/                # API FastAPI
│   ├── main.py                  # Endpoints
│   └── schemas.py               # Pydantic models
│
├── scripts/                     # CLI utilities
│   ├── ingest.py                # Ingesta de documentos
│   ├── query.py                 # Consultas interactivas
│   ├── eval_run.py              # Ejecutar evaluación
│   └── build_eval_set.py        # Crear dataset de eval
│
├── tests/                       # Tests
│   ├── test_chunker.py
│   ├── test_guardrails.py
│   └── test_api_smoke.py
│
├── docs/                        # Documentación
│   ├── architecture.md          # Arquitectura detallada
│   ├── governance.md            # Principios éticos y usos
│   ├── risk_assessment.md       # Evaluación de riesgos
│   ├── prompt_contract.md       # Contrato de prompts
│   ├── decisions.md             # ADRs
│   └── dataset_sources.md       # Fuentes de datos
│
├── data/
│   ├── raw/                     # PDFs/HTMLs originales
│   ├── processed/               # Chunks procesados
│   └── chroma/                  # Vector store persistido
│
├── .github/workflows/ci.yml     # GitHub Actions
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Stack Tecnológico

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **LLM** | Google Gemini 2.5 Flash | Tier gratuito, buen soporte español |
| **Embeddings** | sentence-transformers (multilingual) | 100% local, sin costos |
| **Vector Store** | ChromaDB | Simple, persistencia local |
| **API** | FastAPI + Pydantic | Async, validación automática |
| **Contenedores** | Docker + Compose | Reproducibilidad |
| **CI/CD** | GitHub Actions | Lint, tests, build |

---

## API Endpoints

### `GET /health`
Health check del servicio.

### `GET /stats`
Estadísticas del sistema (chunks indexados, modelo, config).

### `POST /query`
Consulta RAG con citas.

**Request:**
```json
{
  "question": "¿Cuál es el plazo para presentar una reclamación?",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "El plazo es de 20 días hábiles...",
  "citations": [
    {
      "quote": "veinte (20) días hábiles",
      "source": "Codigo-Tributario-Sunat.pdf",
      "page": 45,
      "relevance_score": 0.92
    }
  ],
  "confidence": 0.85,
  "refusal": false,
  "latency_ms": 1234,
  "guardrails": {
    "grounding_score": 0.88,
    "is_grounded": true
  }
}
```

### `POST /ingest`
Ingesta documentos al vector store.

---

## Guardrails Implementados

### 1. Grounding Check (Anti-alucinación)
Verifica que cada afirmación en la respuesta esté respaldada por el contexto recuperado.
- Extrae claims de la respuesta
- Compara con chunks del contexto
- Calcula `grounding_score` (0-1)

### 2. Refusal Policy
Rechaza respuestas cuando:
- No hay chunks relevantes (score < 0.3)
- Query fuera de tema (recetas, deportes, etc.)
- Grounding insuficiente (< 0.5)

### 3. PII Scrubber
Detecta y redacta información sensible:
- DNI peruano (8 dígitos)
- RUC (11 dígitos)
- Teléfonos, emails, tarjetas

---

## Evaluación de Calidad

### Métricas
- **Hit@K**: ¿Fuente correcta en top-k?
- **Faithfulness**: ¿Respuesta fiel al contexto?
- **Answer Relevance**: ¿Responde la pregunta?
- **Latency**: Tiempo de respuesta

### Ejecutar Evaluación
```bash
# Crear dataset de ejemplo
python scripts/eval_run.py --create-sample

# Ejecutar evaluación
python scripts/eval_run.py --report
```

### Umbrales de Aceptación
- Hit@K ≥ 70%
- Faithfulness ≥ 70%

---

## Ejecución

### Desarrollo Local
```bash
# Instalar
pip install -e ".[dev]"

# Ingestar documentos
python scripts/ingest.py --directory ./data/raw

# Consultas interactivas
python scripts/query.py -i

# API
uvicorn services.api.main:app --reload
```

### Docker
```bash
# Construir y levantar
docker compose up --build

# Swagger UI
open http://localhost:8000/docs
```

### Makefile
```bash
make install      # Instalar dependencias
make ingest       # Ingestar documentos
make query        # Modo interactivo
make run-api      # Levantar API
make test         # Ejecutar tests
make docker-up    # Docker compose up
make eval         # Ejecutar evaluación
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [architecture.md](docs/architecture.md) | Arquitectura técnica detallada |
| [governance.md](docs/governance.md) | Principios éticos, usos permitidos/prohibidos |
| [risk_assessment.md](docs/risk_assessment.md) | Evaluación de riesgos y mitigaciones |
| [prompt_contract.md](docs/prompt_contract.md) | Formato de entrada/salida del LLM |
| [decisions.md](docs/decisions.md) | ADRs (Architecture Decision Records) |
| [dataset_sources.md](docs/dataset_sources.md) | Fuentes de datos públicos |

---

## Roadmap

- [x] **Hito 0**: Skeleton + /health
- [x] **Hito 1**: Ingesta + ChromaDB
- [x] **Hito 2**: /query con citas JSON
- [x] **Hito 3**: Guardrails + evaluación
- [x] **Hito 4**: CI + Docker + documentación
- [ ] **Backlog**: Reranking, filtros por entidad, caché

---

## Contribuir

1. Fork el repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

---

## Licencia

MIT License - ver [LICENSE](LICENSE)

---

## Autor

Desarrollado como proyecto de portafolio para demostrar competencias en **AI Engineering / GenAI**.

**Contacto:** [Tu información aquí]

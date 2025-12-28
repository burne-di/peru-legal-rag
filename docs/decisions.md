# Decisiones de Diseño (ADR)

Este documento registra las decisiones arquitectónicas del proyecto siguiendo el formato ADR (Architecture Decision Records).

---

## ADR-001: LLM - Google Gemini

**Estado:** Aceptado
**Fecha:** 2024-12

### Contexto
Necesitamos un LLM para generación de respuestas. El proyecto requiere una opción sin costos para desarrollo y demostración.

### Decisión
Usar **Google Gemini** (gemini-1.5-flash o gemini-pro) a través de la API gratuita.

### Razones
- Tier gratuito generoso (60 QPM en flash)
- Soporte nativo para español
- SDK oficial para Python (`google-generativeai`)
- Contexto largo (hasta 1M tokens en algunos modelos)

### Alternativas consideradas
| Opción | Pros | Contras |
|--------|------|---------|
| OpenAI GPT | Calidad alta | Costo desde el primer request |
| Ollama local | 100% privado | Requiere GPU, más lento |
| Groq | Muy rápido, free tier | Límites más restrictivos |

### Consecuencias
- Dependencia de servicio externo (no 100% local)
- Necesita API key (configurar en `.env`)

---

## ADR-002: Vector Store - ChromaDB

**Estado:** Aceptado
**Fecha:** 2024-12

### Contexto
Necesitamos almacenar embeddings para búsqueda semántica.

### Decisión
Usar **ChromaDB** como vector store local.

### Razones
- Instalación simple (`pip install chromadb`)
- Persistencia local en disco
- Sin infraestructura externa
- Buena integración con LangChain
- Suficiente para volumen de MVP

### Alternativas consideradas
| Opción | Pros | Contras |
|--------|------|---------|
| Qdrant | Más features, prod-ready | Más complejo de configurar |
| Pinecone | Managed, escalable | Requiere cuenta, cloud |
| FAISS | Muy rápido | Sin persistencia nativa |

---

## ADR-003: Embeddings - Sentence Transformers

**Estado:** Aceptado
**Fecha:** 2024-12

### Contexto
Necesitamos generar embeddings para documentos y queries.

### Decisión
Usar **sentence-transformers** con modelo multilingüe local.

### Modelo elegido
`paraphrase-multilingual-MiniLM-L12-v2`

### Razones
- 100% local, sin costos de API
- Soporte multilingüe (español incluido)
- Balance velocidad/calidad
- ~120MB de modelo

### Alternativas consideradas
| Opción | Pros | Contras |
|--------|------|---------|
| OpenAI embeddings | Alta calidad | Costo por token |
| Gemini embeddings | Integrado | Límites de API |
| BGE-M3 | Estado del arte | Modelo más pesado |

---

## ADR-004: Framework RAG - LangChain

**Estado:** Aceptado
**Fecha:** 2024-12

### Contexto
Elegir framework para orquestar el pipeline RAG.

### Decisión
Usar **LangChain** como framework principal.

### Razones
- Ecosistema maduro y documentado
- Abstracciones para loaders, splitters, retrievers
- Comunidad activa
- Facilita integración de componentes

### Alternativas consideradas
| Opción | Pros | Contras |
|--------|------|---------|
| LlamaIndex | Especializado en RAG | Curva de aprendizaje |
| Haystack | Enterprise-ready | Más verboso |
| Custom | Control total | Más tiempo de desarrollo |

---

## ADR-005: Estrategia de Chunking

**Estado:** Propuesto
**Fecha:** 2024-12

### Contexto
Definir cómo dividir documentos largos en chunks para indexación.

### Decisión
Usar chunking por **tokens con overlap**, preservando metadata.

### Parámetros iniciales
- `chunk_size`: 512 tokens
- `chunk_overlap`: 50 tokens
- Separadores: párrafos > oraciones > palabras

### Metadata a preservar
- `source`: archivo origen
- `page`: número de página (si aplica)
- `chunk_id`: identificador único
- `title`: título del documento

### Razones
- Balance entre contexto y precisión
- Overlap evita cortar información relevante
- Metadata permite citas verificables

---

## ADR-006: Estructura de Respuesta con Citas

**Estado:** Propuesto
**Fecha:** 2024-12

### Contexto
Las respuestas deben incluir citas verificables a los documentos fuente.

### Decisión
Formato de respuesta estructurado:

```json
{
  "answer": "Texto de la respuesta...",
  "citations": [
    {
      "text": "Fragmento citado exacto",
      "source": "nombre_documento.pdf",
      "page": 15
    }
  ],
  "confidence": 0.85
}
```

### Razones
- Trazabilidad completa
- Permite verificación humana
- Reduce alucinaciones (el modelo debe citar)

---

## Decisiones Pendientes

- [ ] Estrategia de evaluación (métricas RAGAS específicas)
- [ ] Manejo de documentos HTML vs PDF
- [ ] Límites de rate limiting para Gemini
- [ ] Estrategia de caché para embeddings

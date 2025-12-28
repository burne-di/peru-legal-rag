"""
FastAPI Application - RAG Estado Peru API
"""
import sys
from pathlib import Path

# Agregar packages al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from packages.rag_core import RAGPipeline, __version__
from .schemas import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
    StatsResponse,
    HealthResponse,
    Citation,
)


# Pipeline global
pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y cleanup del pipeline"""
    global pipeline
    print("Inicializando RAG Pipeline...")
    pipeline = RAGPipeline()
    print(f"Pipeline listo. Chunks indexados: {pipeline.get_stats()['total_chunks']}")
    yield
    print("Cerrando aplicación...")


app = FastAPI(
    title="RAG Estado Peru API",
    description="Sistema de Preguntas y Respuestas sobre normativa pública peruana",
    version=__version__,
    lifespan=lifespan,
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Verifica el estado del servicio"""
    return HealthResponse(status="healthy", version=__version__)


@app.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Obtiene estadísticas del sistema RAG"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline no inicializado")
    return StatsResponse(**pipeline.get_stats())


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Realiza una consulta RAG.

    Busca en los documentos indexados y genera una respuesta
    con citas verificables.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline no inicializado")

    if pipeline.get_stats()["total_chunks"] == 0:
        raise HTTPException(
            status_code=400,
            detail="No hay documentos indexados. Use /ingest primero."
        )

    try:
        result = pipeline.query(request.question, top_k=request.top_k)

        # Convertir citations al schema
        citations = [
            Citation(
                source=c["source"],
                page=c.get("page"),
                excerpt=c["excerpt"],
                relevance_score=c.get("relevance_score", 0)
            )
            for c in result.get("citations", [])
        ]

        return QueryResponse(
            answer=result["answer"],
            citations=citations,
            sources_used=result["sources_used"],
            model=result.get("model")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
async def ingest(request: IngestRequest):
    """
    Ingesta documentos PDF al vector store.

    Puede ingestar un directorio completo o un archivo específico.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline no inicializado")

    try:
        if request.directory:
            result = pipeline.ingest_directory(request.directory)
        elif request.file_path:
            result = pipeline.ingest_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Debe especificar 'directory' o 'file_path'"
            )

        return IngestResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear", tags=["RAG"])
async def clear_index():
    """Elimina todos los documentos del vector store"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline no inicializado")

    pipeline.clear()
    return {"status": "success", "message": "Vector store limpiado"}


if __name__ == "__main__":
    import uvicorn
    from packages.rag_core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

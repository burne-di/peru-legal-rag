"""
Pydantic schemas para la API
"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request para consulta RAG"""
    question: str = Field(..., min_length=3, description="Pregunta a responder")
    top_k: int | None = Field(None, ge=1, le=20, description="Número de chunks a recuperar")


class Citation(BaseModel):
    """Una cita de un documento"""
    source: str
    page: int | None
    excerpt: str
    relevance_score: float


class QueryResponse(BaseModel):
    """Response de consulta RAG"""
    answer: str
    citations: list[Citation]
    sources_used: int
    model: str | None = None


class IngestRequest(BaseModel):
    """Request para ingesta de documentos"""
    directory: str | None = Field(None, description="Directorio con PDFs a ingestar")
    file_path: str | None = Field(None, description="Ruta a un PDF específico")


class IngestResponse(BaseModel):
    """Response de ingesta"""
    status: str
    documents: int | None = None
    pages: int | None = None
    chunks: int | None = None
    total_indexed: int | None = None
    message: str | None = None


class StatsResponse(BaseModel):
    """Estadísticas del sistema"""
    total_chunks: int
    embedding_model: str
    llm_model: str
    chunk_size: int
    top_k: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str

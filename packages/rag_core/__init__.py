"""
RAG Core - Lógica central del sistema RAG
"""

__version__ = "0.1.0"

from .cache import ResponseCache, get_cache
from .chunker import Chunk, TextChunker, chunk_documents
from .config import Settings, get_settings
from .generator import GeminiGenerator
from .loaders import (
    Document,
    HTMLLoader,
    PDFLoader,
    load_documents_from_directory,
    load_from_url,
)
from .pipeline import RAGPipeline
from .router import ModelRouter, get_router
from .vectorstore import EmbeddingModel, VectorStore

__all__ = [
    "Chunk",
    "Document",
    "EmbeddingModel",
    "GeminiGenerator",
    "HTMLLoader",
    "ModelRouter",
    "PDFLoader",
    "RAGPipeline",
    "ResponseCache",
    "Settings",
    "TextChunker",
    "VectorStore",
    "chunk_documents",
    "get_cache",
    "get_router",
    "get_settings",
    "load_documents_from_directory",
    "load_from_url",
]

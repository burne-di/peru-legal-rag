"""
RAG Core - Lógica central del sistema RAG
"""

__version__ = "0.1.0"

from .config import get_settings, Settings
from .loaders import PDFLoader, HTMLLoader, Document, load_documents_from_directory, load_from_url
from .chunker import TextChunker, Chunk, chunk_documents
from .vectorstore import VectorStore, EmbeddingModel
from .generator import GeminiGenerator
from .pipeline import RAGPipeline

__all__ = [
    "get_settings",
    "Settings",
    "PDFLoader",
    "HTMLLoader",
    "Document",
    "load_documents_from_directory",
    "load_from_url",
    "TextChunker",
    "Chunk",
    "chunk_documents",
    "VectorStore",
    "EmbeddingModel",
    "GeminiGenerator",
    "RAGPipeline",
]

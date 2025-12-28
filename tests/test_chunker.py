"""
Tests para el módulo de chunking
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.rag_core.loaders import Document
from packages.rag_core.chunker import TextChunker, chunk_documents, Chunk


class TestTextChunker:
    """Tests para TextChunker"""

    def test_basic_chunking(self):
        """Divide texto correctamente"""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        doc = Document(
            content="Este es un texto de prueba. " * 10,
            metadata={"source": "test.pdf", "page": 1}
        )

        chunks = chunker.split_document(doc)

        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(len(c.content) <= 120 for c in chunks)  # Con margen

    def test_preserves_metadata(self):
        """Preserva metadata del documento original"""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        doc = Document(
            content="Texto de prueba suficientemente largo para dividir en chunks.",
            metadata={"source": "documento.pdf", "page": 5, "custom": "value"}
        )

        chunks = chunker.split_document(doc)

        for chunk in chunks:
            assert chunk.metadata["source"] == "documento.pdf"
            assert chunk.metadata["page"] == 5
            assert "chunk_index" in chunk.metadata

    def test_chunk_ids_are_unique(self):
        """Los chunk_ids son únicos"""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        doc = Document(
            content="Texto " * 50,
            metadata={"source": "test.pdf", "page": 1}
        )

        chunks = chunker.split_document(doc)
        chunk_ids = [c.chunk_id for c in chunks]

        assert len(chunk_ids) == len(set(chunk_ids))

    def test_overlap_works(self):
        """El overlap funciona correctamente"""
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)

        doc = Document(
            content="ABCDEFGHIJ" * 10,  # 100 caracteres
            metadata={"source": "test.pdf", "page": 1}
        )

        chunks = chunker.split_document(doc)

        # Con overlap, debería haber más chunks
        assert len(chunks) >= 4

    def test_empty_document(self):
        """Maneja documentos vacíos"""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)

        doc = Document(
            content="   ",
            metadata={"source": "empty.pdf", "page": 1}
        )

        chunks = chunker.split_document(doc)

        assert len(chunks) == 0

    def test_small_document(self):
        """Documento más pequeño que chunk_size"""
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100)

        doc = Document(
            content="Texto corto.",
            metadata={"source": "small.pdf", "page": 1}
        )

        chunks = chunker.split_document(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "Texto corto."


class TestChunkDocuments:
    """Tests para la función chunk_documents"""

    def test_multiple_documents(self):
        """Procesa múltiples documentos"""
        docs = [
            Document(content="Documento uno " * 20, metadata={"source": "doc1.pdf", "page": 1}),
            Document(content="Documento dos " * 20, metadata={"source": "doc2.pdf", "page": 1}),
        ]

        chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=20)

        # Verifica que hay chunks de ambos documentos
        sources = set(c.metadata["source"] for c in chunks)
        assert "doc1.pdf" in sources
        assert "doc2.pdf" in sources

    def test_empty_list(self):
        """Maneja lista vacía"""
        chunks = chunk_documents([], chunk_size=100, chunk_overlap=20)
        assert chunks == []

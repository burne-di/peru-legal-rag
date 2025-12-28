"""
RAG Pipeline - Orquesta todo el flujo de ingesta y consulta con guardrails
"""
import time
from pathlib import Path
from .loaders import load_documents_from_directory, PDFLoader
from .chunker import chunk_documents
from .vectorstore import VectorStore
from .generator import GeminiGenerator
from .config import get_settings
from .guardrails import GroundingChecker, RefusalPolicy, PIIScrubber


class RAGPipeline:
    """Pipeline completo de RAG con guardrails"""

    def __init__(self, enable_guardrails: bool = True):
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.generator = GeminiGenerator()

        # Guardrails
        self.enable_guardrails = enable_guardrails
        if enable_guardrails:
            self.grounding_checker = GroundingChecker()
            self.refusal_policy = RefusalPolicy()
            self.pii_scrubber = PIIScrubber()

    def ingest_directory(self, directory: str | Path) -> dict:
        """
        Ingesta todos los PDFs de un directorio.

        Returns:
            dict con estadísticas de la ingesta
        """
        print(f"=== Iniciando ingesta desde: {directory} ===")

        # 1. Cargar documentos
        print("\n1. Cargando documentos...")
        documents = load_documents_from_directory(directory)
        print(f"   Total páginas cargadas: {len(documents)}")

        if not documents:
            return {"status": "error", "message": "No se encontraron documentos"}

        # 2. Dividir en chunks
        print("\n2. Dividiendo en chunks...")
        chunks = chunk_documents(
            documents,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        print(f"   Total chunks generados: {len(chunks)}")

        # 3. Añadir al vector store
        print("\n3. Generando embeddings y almacenando...")
        added = self.vector_store.add_chunks(chunks)

        print(f"\n=== Ingesta completada ===")
        print(f"   Documentos procesados: {len(set(d.metadata['source'] for d in documents))}")
        print(f"   Páginas procesadas: {len(documents)}")
        print(f"   Chunks indexados: {added}")
        print(f"   Total en vector store: {self.vector_store.count()}")

        return {
            "status": "success",
            "documents": len(set(d.metadata['source'] for d in documents)),
            "pages": len(documents),
            "chunks": added,
            "total_indexed": self.vector_store.count()
        }

    def ingest_file(self, file_path: str | Path) -> dict:
        """Ingesta un solo archivo PDF"""
        loader = PDFLoader(file_path)
        documents = loader.load()

        chunks = chunk_documents(
            documents,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )

        added = self.vector_store.add_chunks(chunks)

        return {
            "status": "success",
            "file": str(file_path),
            "pages": len(documents),
            "chunks": added
        }

    def query(self, question: str, top_k: int | None = None) -> dict:
        """
        Responde una pregunta usando RAG con guardrails.

        Args:
            question: Pregunta del usuario
            top_k: Número de chunks a recuperar

        Returns:
            dict con answer, citations, confidence, refusal, etc.
        """
        start_time = time.time()
        top_k = top_k or self.settings.top_k_results

        # 1. Scrub PII de la query (para logs)
        if self.enable_guardrails:
            clean_query, pii_found = self.pii_scrubber.scrub(question)
            if pii_found:
                print(f"⚠ PII detectado en query: {len(pii_found)} elementos")

        # 2. Buscar chunks relevantes
        relevant_chunks = self.vector_store.search(question, top_k=top_k)

        # 3. Evaluar política de rechazo (pre-generación)
        if self.enable_guardrails:
            refusal_result = self.refusal_policy.evaluate(
                chunks=relevant_chunks,
                query=question
            )

            if refusal_result.should_refuse:
                return {
                    **self.refusal_policy.format_refusal_response(refusal_result),
                    "sources_used": len(relevant_chunks),
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "guardrails": {
                        "pre_refusal": True,
                        "reason": refusal_result.reason.value
                    }
                }

        # 4. Generar respuesta
        response = self.generator.generate(question, relevant_chunks)

        # 5. Verificar grounding (post-generación)
        if self.enable_guardrails and not response.get("refusal"):
            grounding_result = self.grounding_checker.check(
                answer=response["answer"],
                context_chunks=relevant_chunks
            )

            # Evaluar nuevamente con grounding score
            post_refusal = self.refusal_policy.evaluate(
                chunks=relevant_chunks,
                grounding_score=grounding_result.score,
                query=question
            )

            if post_refusal.should_refuse:
                return {
                    **self.refusal_policy.format_refusal_response(post_refusal),
                    "sources_used": len(relevant_chunks),
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "guardrails": {
                        "grounding_score": grounding_result.score,
                        "grounding_details": grounding_result.details,
                        "ungrounded_claims": grounding_result.ungrounded_claims[:3],
                        "post_refusal": True
                    }
                }

            # Agregar info de guardrails a la respuesta
            response["guardrails"] = {
                "grounding_score": grounding_result.score,
                "grounding_details": grounding_result.details,
                "is_grounded": grounding_result.is_grounded
            }

        # 6. Scrub PII de la respuesta (para logs)
        if self.enable_guardrails:
            response_for_log = self.pii_scrubber.scrub_for_logs(response)
            # El response original va al usuario, el scrubbed a logs
            response["_log_safe"] = response_for_log

        # Actualizar latencia total
        response["latency_ms"] = int((time.time() - start_time) * 1000)

        return response

    def get_stats(self) -> dict:
        """Retorna estadísticas del pipeline"""
        return {
            "total_chunks": self.vector_store.count(),
            "embedding_model": self.settings.embedding_model,
            "llm_model": self.settings.gemini_model,
            "chunk_size": self.settings.chunk_size,
            "top_k": self.settings.top_k_results,
            "guardrails_enabled": self.enable_guardrails
        }

    def clear(self):
        """Limpia el vector store"""
        self.vector_store.clear()

"""
Generator - Generación de respuestas con Gemini y citas (JSON estructurado)
"""
import json
import re
import time
import google.generativeai as genai
from .config import get_settings


# Prompt que fuerza output JSON estructurado
SYSTEM_PROMPT = """Eres un asistente especializado en normativa pública peruana.
Tu función es responder preguntas basándote ÚNICAMENTE en los documentos proporcionados.

REGLAS ESTRICTAS:
1. SOLO responde usando información de los documentos proporcionados
2. SIEMPRE incluye citas textuales exactas de los documentos
3. Si NO hay información suficiente, establece "refusal": true
4. Sé preciso y conciso
5. Responde en español

DEBES responder ÚNICAMENTE con un JSON válido con esta estructura exacta:
{
  "answer": "tu respuesta aquí",
  "citations": [
    {
      "quote": "cita textual exacta del documento",
      "source": "nombre del documento",
      "page": número de página
    }
  ],
  "confidence": 0.0 a 1.0,
  "refusal": false,
  "notes": "opcional: limitaciones o aclaraciones"
}

IMPORTANTE:
- "citations" debe contener citas TEXTUALES de los documentos, no paráfrasis
- "confidence" debe reflejar qué tan seguro estás (0.0 = nada, 1.0 = total)
- Si no encuentras información, usa "refusal": true y "citations": []
- NO agregues texto fuera del JSON"""


class GeminiGenerator:
    """Generador de respuestas usando Google Gemini con output JSON"""

    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        self.model_name = settings.gemini_model

    def generate(
        self,
        query: str,
        context_chunks: list[dict],
        max_tokens: int = 1024
    ) -> dict:
        """
        Genera una respuesta estructurada basada en la query y el contexto.

        Args:
            query: Pregunta del usuario
            context_chunks: Lista de chunks recuperados con content y metadata
            max_tokens: Máximo de tokens en la respuesta

        Returns:
            dict con answer, citations, confidence, refusal, latency_ms, etc.
        """
        start_time = time.time()

        # Construir contexto con metadata
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk["metadata"].get("source", "Desconocido")
            page = chunk["metadata"].get("page", "?")
            context_parts.append(
                f"[Documento {i}: {source}, Página {page}]\n{chunk['content']}"
            )

        context_text = "\n\n---\n\n".join(context_parts)

        # Construir prompt
        prompt = f"""{SYSTEM_PROMPT}

DOCUMENTOS DE REFERENCIA:
{context_text}

PREGUNTA DEL USUARIO:
{query}

Responde SOLO con el JSON estructurado:"""

        # Generar respuesta
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.2,  # Más baja para JSON consistente
                )
            )
            raw_response = response.text
        except Exception as e:
            return self._error_response(str(e), time.time() - start_time)

        # Parsear JSON de la respuesta
        parsed = self._parse_json_response(raw_response)

        # Calcular latencia
        latency_ms = int((time.time() - start_time) * 1000)

        # Enriquecer con metadata de chunks
        enriched_citations = self._enrich_citations(
            parsed.get("citations", []),
            context_chunks
        )

        # Calcular confidence basado en scores de retrieval si no viene
        if parsed.get("confidence") is None:
            parsed["confidence"] = self._calculate_confidence(context_chunks)

        return {
            "answer": parsed.get("answer", "Error al procesar respuesta"),
            "citations": enriched_citations,
            "confidence": parsed.get("confidence", 0.0),
            "refusal": parsed.get("refusal", False),
            "notes": parsed.get("notes"),
            "sources_used": len(context_chunks),
            "model": self.model_name,
            "latency_ms": latency_ms,
            "raw_llm_response": raw_response if parsed.get("_parse_error") else None
        }

    def _parse_json_response(self, text: str) -> dict:
        """
        Extrae y parsea JSON de la respuesta del LLM.
        Maneja casos donde el LLM agrega texto extra.
        """
        # Intentar parsear directamente
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Buscar JSON en el texto
        json_patterns = [
            r'\{[\s\S]*\}',  # Cualquier cosa entre { }
            r'```json\s*([\s\S]*?)\s*```',  # Bloque de código
            r'```\s*([\s\S]*?)\s*```',  # Bloque de código sin especificar
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Si es un grupo de captura, usar el grupo
                    json_str = match if isinstance(match, str) else match[0]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Si no se pudo parsear, retornar respuesta como texto plano
        return {
            "answer": text,
            "citations": [],
            "confidence": 0.5,
            "refusal": False,
            "_parse_error": True
        }

    def _enrich_citations(
        self,
        llm_citations: list[dict],
        context_chunks: list[dict]
    ) -> list[dict]:
        """
        Enriquece las citas del LLM con metadata de los chunks.
        """
        enriched = []

        for citation in llm_citations:
            enriched_citation = {
                "quote": citation.get("quote", ""),
                "source": citation.get("source", "Desconocido"),
                "page": citation.get("page"),
                "source_uri": None,
                "relevance_score": 0.0
            }

            # Buscar chunk correspondiente para agregar metadata
            source_name = citation.get("source", "").lower()
            for chunk in context_chunks:
                chunk_source = chunk["metadata"].get("source", "").lower()
                if source_name in chunk_source or chunk_source in source_name:
                    enriched_citation["source_uri"] = chunk["metadata"].get("source_path")
                    enriched_citation["relevance_score"] = chunk.get("score", 0)
                    break

            enriched.append(enriched_citation)

        # Si no hay citas del LLM, crear citas de los chunks usados
        if not enriched and context_chunks:
            for chunk in context_chunks[:3]:  # Top 3 chunks
                enriched.append({
                    "quote": chunk["content"][:150] + "...",
                    "source": chunk["metadata"].get("source", "Desconocido"),
                    "page": chunk["metadata"].get("page"),
                    "source_uri": chunk["metadata"].get("source_path"),
                    "relevance_score": chunk.get("score", 0)
                })

        return enriched

    def _calculate_confidence(self, chunks: list[dict]) -> float:
        """
        Calcula un score de confianza basado en los chunks recuperados.
        """
        if not chunks:
            return 0.0

        # Promedio de scores de similitud
        scores = [chunk.get("score", 0) for chunk in chunks]
        avg_score = sum(scores) / len(scores)

        # Ajustar por cantidad de chunks con buen score
        high_quality_chunks = sum(1 for s in scores if s > 0.7)
        quality_bonus = min(high_quality_chunks * 0.05, 0.15)

        confidence = min(avg_score + quality_bonus, 1.0)
        return round(confidence, 2)

    def _error_response(self, error_msg: str, elapsed: float) -> dict:
        """Respuesta en caso de error"""
        return {
            "answer": f"Error al generar respuesta: {error_msg}",
            "citations": [],
            "confidence": 0.0,
            "refusal": True,
            "notes": "Error interno del sistema",
            "sources_used": 0,
            "model": self.model_name,
            "latency_ms": int(elapsed * 1000),
            "error": error_msg
        }

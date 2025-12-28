"""
Tests para guardrails
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.rag_core.guardrails import (
    GroundingChecker,
    RefusalPolicy,
    RefusalReason,
    PIIScrubber,
)


class TestGroundingChecker:
    """Tests para GroundingChecker"""

    def test_grounded_response(self):
        """Respuesta fundamentada en contexto"""
        checker = GroundingChecker()

        answer = "El plazo es de 20 días hábiles según la normativa."
        context = [
            {"content": "El plazo para presentar recursos es de 20 días hábiles."}
        ]

        result = checker.check(answer, context)

        assert result.score > 0.3
        assert len(result.ungrounded_claims) == 0 or result.is_grounded

    def test_ungrounded_response(self):
        """Respuesta no fundamentada"""
        checker = GroundingChecker()

        answer = "La tasa de interés es del 15% anual compuesto."
        context = [
            {"content": "El plazo para presentar recursos es de 20 días hábiles."}
        ]

        result = checker.check(answer, context)

        # Debería tener score bajo
        assert result.score < 0.7

    def test_empty_answer(self):
        """Respuesta vacía o muy corta"""
        checker = GroundingChecker()

        answer = "Ok"
        context = [{"content": "Contenido del documento."}]

        result = checker.check(answer, context)

        # Sin claims verificables, debería considerarse grounded
        assert result.is_grounded


class TestRefusalPolicy:
    """Tests para RefusalPolicy"""

    def test_no_chunks(self):
        """Rechaza si no hay chunks"""
        policy = RefusalPolicy()

        result = policy.evaluate(chunks=[])

        assert result.should_refuse
        assert result.reason == RefusalReason.NO_CONTEXT

    def test_low_relevance(self):
        """Rechaza si chunks tienen baja relevancia"""
        policy = RefusalPolicy(min_relevance_score=0.5)

        chunks = [
            {"content": "texto", "score": 0.1},
            {"content": "texto", "score": 0.2},
        ]

        result = policy.evaluate(chunks=chunks)

        assert result.should_refuse
        assert result.reason == RefusalReason.LOW_RELEVANCE

    def test_off_topic(self):
        """Detecta queries fuera de tema"""
        policy = RefusalPolicy()

        result = policy.evaluate(
            chunks=[{"content": "texto", "score": 0.8}],
            query="Dame una receta de cocina"
        )

        assert result.should_refuse
        assert result.reason == RefusalReason.OFF_TOPIC

    def test_acceptable_response(self):
        """Acepta respuesta válida"""
        policy = RefusalPolicy()

        chunks = [
            {"content": "texto relevante", "score": 0.8},
        ]

        result = policy.evaluate(chunks=chunks, grounding_score=0.9)

        assert not result.should_refuse
        assert result.reason == RefusalReason.NONE

    def test_format_refusal_response(self):
        """Formatea respuesta de rechazo correctamente"""
        policy = RefusalPolicy()

        result = policy.evaluate(chunks=[])
        response = policy.format_refusal_response(result)

        assert "answer" in response
        assert response["refusal"] is True
        assert response["citations"] == []
        assert response["confidence"] == 0.0


class TestPIIScrubber:
    """Tests para PIIScrubber"""

    def test_detect_dni(self):
        """Detecta DNI peruano"""
        scrubber = PIIScrubber()

        text = "Mi DNI es 12345678 y mi nombre es Juan"
        matches = scrubber.detect(text)

        assert len(matches) == 1
        assert matches[0].type == "dni"
        assert matches[0].value == "12345678"

    def test_detect_ruc(self):
        """Detecta RUC peruano"""
        scrubber = PIIScrubber()

        text = "La empresa tiene RUC 20123456789"
        matches = scrubber.detect(text)

        assert len(matches) == 1
        assert matches[0].type == "ruc"

    def test_detect_email(self):
        """Detecta correo electrónico"""
        scrubber = PIIScrubber()

        text = "Contacto: juan@empresa.com.pe"
        matches = scrubber.detect(text)

        assert len(matches) == 1
        assert matches[0].type == "email"

    def test_detect_phone(self):
        """Detecta teléfono peruano"""
        scrubber = PIIScrubber()

        text = "Llámame al 987654321"
        matches = scrubber.detect(text)

        assert len(matches) == 1
        assert matches[0].type == "phone"

    def test_scrub_text(self):
        """Remueve PII del texto"""
        scrubber = PIIScrubber()

        text = "DNI: 12345678, Email: test@mail.com"
        scrubbed, matches = scrubber.scrub(text)

        assert "12345678" not in scrubbed
        assert "test@mail.com" not in scrubbed
        assert "[DNI_REDACTED]" in scrubbed
        assert "[EMAIL_REDACTED]" in scrubbed
        assert len(matches) == 2

    def test_scrub_for_logs(self):
        """Limpia dict para logs"""
        scrubber = PIIScrubber()

        data = {
            "query": "Info sobre DNI 12345678",
            "nested": {
                "email": "user@test.com"
            }
        }

        scrubbed = scrubber.scrub_for_logs(data)

        assert "12345678" not in scrubbed["query"]
        assert "user@test.com" not in scrubbed["nested"]["email"]

    def test_no_pii(self):
        """Texto sin PII"""
        scrubber = PIIScrubber()

        text = "Este texto no contiene información personal"
        scrubbed, matches = scrubber.scrub(text)

        assert scrubbed == text
        assert len(matches) == 0

    def test_custom_patterns(self):
        """Usa solo patrones seleccionados"""
        scrubber = PIIScrubber(patterns_to_use=["email"])

        text = "DNI: 12345678, Email: test@mail.com"
        matches = scrubber.detect(text)

        # Solo debería detectar email
        assert len(matches) == 1
        assert matches[0].type == "email"

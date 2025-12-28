# Contrato de Prompts

## Objetivo

Este documento define el formato de entrada y salida del sistema RAG,
asegurando consistencia y validabilidad de las respuestas.

---

## Estructura de Respuesta (JSON)

El LLM **DEBE** retornar un JSON con la siguiente estructura:

```json
{
  "answer": "string - Respuesta concisa a la pregunta",
  "citations": [
    {
      "quote": "string - Cita textual exacta del documento",
      "source": "string - Nombre del documento fuente",
      "page": "number | null - Número de página"
    }
  ],
  "confidence": "number - Score de 0.0 a 1.0",
  "refusal": "boolean - true si no puede responder",
  "notes": "string | null - Limitaciones o aclaraciones opcionales"
}
```

---

## Reglas de Validación

### Campo `answer`
- **Requerido:** Siempre
- **Tipo:** String no vacío
- **Longitud:** 10-2000 caracteres
- **Idioma:** Español

### Campo `citations`
- **Requerido:** Si `refusal=false`
- **Tipo:** Array de objetos
- **Mínimo:** 1 cita si hay respuesta
- **Máximo:** 5 citas recomendado

### Campo `quote`
- **Requerido:** En cada citation
- **Tipo:** String
- **Contenido:** Texto EXACTO del documento
- **Longitud:** 20-500 caracteres

### Campo `confidence`
- **Requerido:** Siempre
- **Tipo:** Number
- **Rango:** 0.0 a 1.0
- **Interpretación:**
  - 0.0-0.3: Baja confianza
  - 0.3-0.7: Confianza moderada
  - 0.7-1.0: Alta confianza

### Campo `refusal`
- **Requerido:** Siempre
- **Tipo:** Boolean
- **Cuándo es `true`:**
  - No hay información en documentos
  - Pregunta fuera de alcance
  - Contexto insuficiente

### Campo `notes`
- **Requerido:** No
- **Tipo:** String o null
- **Uso:** Limitaciones, ambigüedades, aclaraciones

---

## System Prompt

```text
Eres un asistente especializado en normativa pública peruana.
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
- NO agregues texto fuera del JSON
```

---

## Ejemplos de Respuestas Válidas

### Respuesta exitosa:
```json
{
  "answer": "El plazo para presentar una reclamación tributaria es de 20 días hábiles contados desde el día siguiente de la notificación.",
  "citations": [
    {
      "quote": "El plazo para interponer reclamación contra actos de la Administración Tributaria es de veinte (20) días hábiles",
      "source": "Codigo-Tributario-Sunat.pdf",
      "page": 45
    }
  ],
  "confidence": 0.92,
  "refusal": false,
  "notes": null
}
```

### Respuesta con refusal:
```json
{
  "answer": "No encontré información sobre requisitos de visa en los documentos disponibles.",
  "citations": [],
  "confidence": 0.0,
  "refusal": true,
  "notes": "Los documentos indexados son sobre normativa tributaria. Para información de visas, consulte el Ministerio de Relaciones Exteriores."
}
```

### Respuesta con baja confianza:
```json
{
  "answer": "El documento menciona plazos de prescripción, pero no especifica claramente el caso consultado.",
  "citations": [
    {
      "quote": "La acción de la Administración Tributaria para determinar la obligación tributaria prescribe a los cuatro (4) años",
      "source": "Codigo-Tributario-Sunat.pdf",
      "page": 23
    }
  ],
  "confidence": 0.45,
  "refusal": false,
  "notes": "La información encontrada puede no aplicar exactamente al caso consultado. Se recomienda verificar con un especialista."
}
```

---

## Validación Post-Generación

El sistema aplica las siguientes validaciones después de recibir la respuesta:

1. **Parse JSON:** Intenta extraer JSON válido
2. **Schema validation:** Verifica campos requeridos
3. **Grounding check:** Verifica que citas existan en contexto
4. **Refusal policy:** Evalúa si debería haber rechazado

Si alguna validación falla, el sistema puede:
- Retornar respuesta con `_parse_error: true`
- Aplicar refusal post-generación
- Agregar notas sobre inconsistencias

---

## Versionado

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-12 | Versión inicial |

# Evaluación de Riesgos

## Matriz de Riesgos

| ID | Riesgo | Probabilidad | Impacto | Nivel | Mitigación |
|----|--------|--------------|---------|-------|------------|
| R1 | Alucinaciones | Media | Alto | **ALTO** | Guardrails, grounding check |
| R2 | Información desactualizada | Alta | Medio | **ALTO** | Versionado de docs, fecha de ingesta |
| R3 | Mal uso (asesoría legal) | Media | Alto | **ALTO** | Disclaimers, refusal policy |
| R4 | Fuga de PII | Baja | Alto | **MEDIO** | PII scrubber, no persistencia |
| R5 | Sesgo en respuestas | Baja | Medio | **BAJO** | Solo docs oficiales |
| R6 | Disponibilidad API | Media | Bajo | **BAJO** | Health checks, retry |

---

## Riesgos Detallados

### R1: Alucinaciones del LLM

**Descripción:** El modelo genera información no presente en los documentos.

**Impacto:**
- Usuario toma decisiones basadas en información falsa
- Pérdida de confianza en el sistema
- Posibles consecuencias legales

**Mitigaciones implementadas:**
1. `GroundingChecker`: Verifica que respuesta esté en contexto
2. `RefusalPolicy`: Rechaza si grounding < 50%
3. Temperatura baja (0.2) en generación
4. Prompt explícito: "SOLO usa información de los documentos"

**Monitoreo:**
- Métrica: `grounding_score` en cada respuesta
- Alerta si promedio < 0.7

---

### R2: Información Desactualizada

**Descripción:** Documentos indexados no reflejan normativa vigente.

**Impacto:**
- Respuestas técnicamente correctas pero obsoletas
- Usuario aplica normas derogadas

**Mitigaciones implementadas:**
1. Metadata incluye fecha de ingesta
2. Campo `source_uri` para verificación
3. Disclaimer en respuestas

**Mitigaciones pendientes:**
- [ ] Alerta de antigüedad de documentos
- [ ] Integración con feeds de normativa

---

### R3: Mal Uso como Asesoría Legal

**Descripción:** Usuario interpreta respuestas como consejo legal vinculante.

**Impacto:**
- Decisiones incorrectas
- Responsabilidad del desarrollador
- Daño a terceros

**Mitigaciones implementadas:**
1. Disclaimer en documentación
2. `notes` en respuesta con limitaciones
3. Refusal para preguntas sobre "qué debo hacer"

**Mitigaciones pendientes:**
- [ ] Disclaimer dinámico en respuestas sensibles
- [ ] Detección de queries de alto riesgo

---

### R4: Fuga de PII

**Descripción:** Información personal aparece en logs o respuestas.

**Impacto:**
- Violación de privacidad
- Incumplimiento normativo

**Mitigaciones implementadas:**
1. `PIIScrubber` detecta DNI, RUC, emails, teléfonos
2. Logs usan versión scrubbed (`_log_safe`)
3. Queries no se persisten

**Cobertura actual:**
- DNI: ✓
- RUC: ✓
- Teléfono: ✓
- Email: ✓
- Direcciones: Parcial

---

## Plan de Contingencia

### Si se detecta alucinación grave:
1. Registrar query y respuesta
2. Analizar chunks recuperados
3. Ajustar grounding_threshold si necesario
4. Documentar en changelog

### Si documento está desactualizado:
1. Remover de índice
2. Obtener versión actualizada
3. Re-ingestar
4. Verificar respuestas afectadas

### Si hay reporte de PII expuesto:
1. Identificar fuente (query o documento)
2. Actualizar patrones de PIIScrubber
3. Revisar logs históricos
4. Notificar si corresponde

---

## Revisión de Riesgos

**Frecuencia:** Trimestral o ante incidentes

**Checklist de revisión:**
- [ ] Revisar métricas de grounding
- [ ] Verificar antigüedad de documentos
- [ ] Auditar logs por PII
- [ ] Evaluar nuevos riesgos identificados

# Gobernanza del Sistema RAG

## Principios Éticos

### 1. Transparencia
- El sistema **siempre** indica las fuentes de sus respuestas
- Las citas son verificables contra los documentos originales
- Se declara explícitamente cuando no hay información suficiente

### 2. Exactitud
- Solo se utilizan documentos oficiales y públicos
- Las respuestas están fundamentadas en el contexto recuperado
- Se implementan guardrails para evitar alucinaciones

### 3. Privacidad
- No se almacenan datos personales de usuarios
- Las queries son procesadas pero no persistidas
- PII detectado en logs es automáticamente redactado

### 4. Accesibilidad
- El sistema responde en español
- Las respuestas son claras y concisas
- Se proporciona contexto cuando hay ambigüedad

---

## Usos Permitidos

### Casos de uso aprobados:
- Consulta de normativa pública
- Búsqueda de información en documentos oficiales
- Verificación de requisitos legales/tributarios
- Investigación académica sobre legislación

### Usuarios objetivo:
- Ciudadanos buscando información pública
- Profesionales (abogados, contadores)
- Estudiantes e investigadores
- Funcionarios públicos

---

## Usos NO Permitidos

### Explícitamente prohibido:
- Asesoría legal formal (el sistema NO reemplaza a un abogado)
- Decisiones judiciales o administrativas
- Generación de documentos legales vinculantes
- Interpretación autoritativa de leyes

### Disclaimer obligatorio:
> Este sistema es una herramienta de consulta informativa. Las respuestas
> NO constituyen asesoría legal. Para decisiones importantes, consulte
> con un profesional calificado.

---

## Manejo de Datos Sensibles

### PII (Información Personal Identificable)
El sistema detecta y redacta:
- DNI peruano (8 dígitos)
- RUC (11 dígitos)
- Números de teléfono
- Correos electrónicos
- Números de tarjetas

### Logging seguro
- Logs no contienen PII sin redactar
- Queries de usuarios no se persisten
- Respuestas no se almacenan

---

## Limitaciones Conocidas

### Técnicas:
1. **Cobertura documental**: Solo responde sobre documentos indexados
2. **Actualización**: Documentos deben re-indexarse manualmente
3. **Idioma**: Optimizado para español peruano
4. **Formato**: Mejor rendimiento en PDFs estructurados

### Funcionales:
1. No interpreta intención legal
2. No compara legislación entre períodos
3. No predice cambios normativos
4. No genera documentos

---

## Responsabilidades

### Del desarrollador:
- Mantener documentos actualizados
- Monitorear calidad de respuestas
- Corregir errores reportados
- Documentar cambios significativos

### Del usuario:
- Verificar información crítica
- No usar como fuente única para decisiones
- Reportar respuestas incorrectas
- Respetar términos de uso

---

## Proceso de Reporte de Problemas

1. **Respuesta incorrecta**: Abrir issue con query y respuesta
2. **Alucinación detectada**: Prioridad alta, incluir contexto
3. **Documento faltante**: Sugerir fuente pública a indexar
4. **Vulnerabilidad**: Contacto privado (no público)

---

## Auditoría y Métricas

### Métricas monitoreadas:
- Tasa de refusal (respuestas rechazadas)
- Grounding score promedio
- Latencia de respuesta
- Cobertura documental

### Revisión periódica:
- Evaluación de calidad: Mensual
- Actualización de documentos: Según disponibilidad
- Revisión de guardrails: Trimestral

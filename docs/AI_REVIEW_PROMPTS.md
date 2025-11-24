# Prompts para Revisión de AIs

**Proyecto:** https://github.com/rrojashub-source/agente-musica-mp3
**Fecha:** 23 Noviembre 2025
**Score Actual:** 85/100

---

## 1. GPT-4 / ChatGPT - Arquitectura General

```
Analiza este proyecto de GitHub como un arquitecto de software senior:

https://github.com/rrojashub-source/agente-musica-mp3

Es un Music Manager en Python/PyQt6 con:
- GUI moderna con visualizer
- YouTube + Spotify search
- Download queue concurrente
- SQLite database thread-safe
- Playlist management

Por favor evalúa:
1. Arquitectura general (separación de concerns, patrones)
2. Estructura de carpetas (¿es profesional?)
3. Calidad del código (¿hay code smells?)
4. Seguridad (¿ves vulnerabilidades?)
5. Performance (¿ves bottlenecks potenciales?)

Dame una puntuación del 1-100 y lista de mejoras prioritarias.
Sé crítico y directo, necesito feedback honesto.
```

---

## 2. Claude (claude.ai) - Code Review Detallado

```
Haz un code review exhaustivo de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Enfócate en estos archivos clave:
- src/database/manager.py (thread-safety)
- src/core/download_queue.py (concurrencia)
- src/gui/widgets/visualizer_widget.py (performance)
- src/main.py (arquitectura principal)

Busca específicamente:
1. Race conditions
2. Memory leaks
3. Error handling incompleto
4. Código duplicado
5. Violaciones de SOLID principles

Para cada problema encontrado, sugiere el fix específico con código.
```

---

## 3. Gemini - UX/UI Review

```
Analiza la experiencia de usuario de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Es un Music Manager GUI. Revisa:

1. Flujo de usuario (¿es intuitivo?)
2. Organización de tabs/widgets
3. Feedback visual (¿el usuario sabe qué está pasando?)
4. Accesibilidad (shortcuts, tooltips)
5. Consistencia visual

Basándote en los archivos de GUI en src/gui/, sugiere:
- 3 mejoras de UX prioritarias
- 3 mejoras de UI prioritarias

Compara con apps similares (Spotify, iTunes) y dime qué falta.
```

---

## 4. Perplexity - Competencia y Mercado

```
Investiga el mercado de music managers para este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Preguntas:
1. ¿Qué competidores existen? (MusicBee, foobar2000, etc.)
2. ¿Qué features tienen ellos que este proyecto NO tiene?
3. ¿Qué precio cobran? (¿hay modelo freemium?)
4. ¿Cuál sería el diferenciador de este proyecto?
5. ¿Qué features agregarías para hacerlo competitivo?

Dame un análisis de mercado breve y actionable.
```

---

## 5. GPT-4 - Testing & QA

```
Analiza la estrategia de testing de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Revisa la carpeta tests/ y evalúa:

1. Cobertura de tests (¿qué falta testear?)
2. Calidad de los tests existentes
3. ¿Hay tests de integración?
4. ¿Hay tests de UI/E2E?
5. ¿Qué tests críticos agregarías?

Sugiere 5 tests específicos que debería agregar con código ejemplo.
```

---

## 6. Claude - Documentación

```
Evalúa la documentación de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Archivos a revisar:
- README.md
- PROJECT_ID.md
- CLAUDE.md
- docs/plans/ROADMAP_COMERCIAL_V2.md

Evalúa:
1. ¿Un nuevo desarrollador puede entender el proyecto en 10 min?
2. ¿Las instrucciones de instalación son claras?
3. ¿Falta documentación de API interna?
4. ¿Los docstrings son suficientes?
5. ¿Qué documentación agregarías?

Puntuación de documentación: X/100
```

---

## 7. Cualquier AI - Revisión Rápida General

```
Dame una revisión rápida (5 minutos) de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

En bullet points:
- 3 cosas que están BIEN
- 3 cosas que están MAL
- 3 cosas que FALTAN
- Puntuación general: X/100
- ¿Lo comprarías como usuario? ¿Por qué?

Sé brutalmente honesto.
```

---

## 8. GPT-4 - Seguridad

```
Haz una auditoría de seguridad de este proyecto:

https://github.com/rrojashub-source/agente-musica-mp3

Busca:
1. Injection vulnerabilities (SQL, command)
2. Manejo de credenciales (API keys)
3. Input validation
4. Dependencias con vulnerabilidades conocidas
5. Exposición de datos sensibles

Usa OWASP Top 10 como referencia.
Puntuación de seguridad: X/100
```

---

## Cómo Usar Estos Prompts

1. **Copia el prompt** que quieras usar
2. **Pégalo en la AI** correspondiente
3. **Espera el análisis**
4. **Guarda las sugerencias** en un documento
5. **Prioriza** las mejoras más mencionadas

---

## Registro de Reviews

| AI | Fecha | Score | Feedback Principal |
|----|-------|-------|-------------------|
| GPT-4 | | /100 | |
| Claude | | /100 | |
| Gemini | | /100 | |
| Perplexity | | N/A | |

---

**Tip:** Después de recibir feedback, vuelve aquí y actualiza la tabla con los scores y comentarios principales.

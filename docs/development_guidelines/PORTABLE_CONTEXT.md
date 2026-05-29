# Contexto portable — Octopus

> Leer esto **primero** al abrir el repo en otro PC. Indica qué documentos cargar para recuperar todo el contexto del proyecto sin pérdida.

---

## Documentos a leer al abrir el repo (en orden)

| # | Documento | Contiene |
|---|-----------|----------|
| 1 | `docs/README.md` | Índice general + enlaces |
| 2 | `docs/architecture/HANDOFF.md` | **Contexto general** completo y autosuficiente |
| 3 | `docs/architecture/DECISIONS.md` | **Decisiones** técnicas cerradas (ADRs) |
| 4 | `docs/architecture/ROADMAP.md` | **Roadmap** + orden de implementación + camino crítico |
| 5 | `docs/architecture/SPRINT_0_1_ISSUES.md` | **Issues iniciales** detallados (Sprint 0 y 1) |
| 6 | `docs/architecture/CRITICAL_NODES.md` | Nodos críticos (Scope Gate, ToolRunner, AI base) |
| 7 | `docs/architecture/ASSUMPTIONS_AND_RISKS.md` | Suposiciones + riesgos + mitigaciones |
| 8 | `docs/development_guidelines/IMPLEMENTATION_RULES.md` | **Reglas** vinculantes del implementador |
| 9 | `docs/architecture/SONNET_HANDOFF_PROMPT.md` | **Prompt de handoff** listo para arrancar |

---

## Qué documento contiene qué

- **Contexto general / arquitectura:** `HANDOFF.md`
- **Arquitectura detallada + nodos críticos:** `HANDOFF.md` + `CRITICAL_NODES.md`
- **Decisiones cerradas:** `DECISIONS.md`
- **Reglas de trabajo:** `IMPLEMENTATION_RULES.md` + `AI_WORKFLOW.md`
- **Roadmap / orden:** `ROADMAP.md`
- **Issues iniciales:** `SPRINT_0_1_ISSUES.md`
- **Prompt de handoff:** `SONNET_HANDOFF_PROMPT.md`
- **Suposiciones / riesgos:** `ASSUMPTIONS_AND_RISKS.md`

---

## Cómo continuar en otro PC

1. **Clonar** el repo.
2. **Instalar dependencias del sistema** (ver `CLAUDE_CODE_SETUP.md`: Node/npm/npx).
3. **Instalar plugins** recomendados (Caveman, Superpowers, Context7).
4. Ejecutar **`/reload-plugins`**.
5. Ejecutar **`/mcp`** (verificar que ningún MCP falla; si Context7 da `ENOENT`, instalar npm/npx).
6. Abrir **`docs/architecture/SONNET_HANDOFF_PROMPT.md`** y cargar su contexto.
7. Pedir al modelo que implemente **únicamente el siguiente issue pendiente** (no avanzar más).

---

## Estado del proyecto

Sprint 0 en progreso. OCT-001, OCT-002, OCT-003, OCT-004 completados. Próximo issue pendiente: **OCT-020** (Imagen worker + Dramatiq + cola Redis).

> Mantener este archivo actualizado con el "siguiente issue pendiente" conforme avance el desarrollo, para que cualquier PC retome el estado correcto.

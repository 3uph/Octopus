---
description: Implementar un issue concreto del backlog Octopus (issue por issue)
argument-hint: ISSUE_ID "ISSUE_TITLE"
---

# /implement-issue

Implementa el issue **{{ISSUE_ID}} — {{ISSUE_TITLE}}** del proyecto Octopus.

> Placeholders: `ISSUE_ID` (ej. `OCT-001`), `ISSUE_TITLE` (ej. `Estructura de monorepo + ADRs base`).

## Pasos

1. **Localiza el issue** en `docs/architecture/SPRINT_0_1_ISSUES.md` (o en el roadmap correspondiente, `docs/architecture/ROADMAP.md`, si es posterior a Sprint 1).
2. **Lee** sus campos: objetivo, contexto, dependencias, archivos/módulos, subtareas, criterios de aceptación, tests mínimos, qué NO tocar.
3. **Verifica dependencias**: si un issue dependiente no está hecho, **para y avisa**.
4. **Implementa SOLO este issue.**
   - Toca únicamente los archivos/módulos permitidos.
   - **No** toques lo marcado como "NO tocar".
   - Respeta `IMPLEMENTATION_RULES.md` (sin shell=True, args como lista, validar inputs, secretos cifrados, logs redactados, multi-tenant, Alembic, prompts en `prompts/`).
5. **Verifica criterios de aceptación** uno a uno.
6. **Ejecuta los tests mínimos** del issue si existen (con mocks/fixtures, nunca recon real).
7. **Para ante ambigüedad** o si una suposición parece incorrecta — pregunta, no improvises.

## Restricciones

- No ejecutes herramientas ofensivas.
- No te saltes el Scope Gate.
- No hagas commits.
- No avances al siguiente issue.

## Salida

Resume: archivos creados/modificados, criterios verificados, tests ejecutados, pendientes.

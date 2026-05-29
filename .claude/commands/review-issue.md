---
description: Revisar un issue terminado del backlog Octopus
argument-hint: ISSUE_ID
---

# /review-issue

Revisa el issue **{{ISSUE_ID}}** ya implementado. Revisión, no implementación.

## Checklist

1. **Criterios de aceptación:** comparar el resultado contra los criterios definidos en `docs/architecture/SPRINT_0_1_ISSUES.md` (o roadmap). Marcar cada uno cumple / no cumple.
2. **Scope de archivos:** comprobar que **no** se tocaron archivos fuera del alcance del issue (revisar "archivos/módulos" y "NO tocar").
3. **No adelanto:** comprobar que **no** se avanzó al siguiente issue.
4. **Sin secretos:** comprobar que no se añadieron `.env`, tokens, credenciales ni claves. Verificar que `.gitignore` los cubre.
5. **Sin recon ofensivo:** comprobar que no se ejecutaron herramientas ofensivas (revisar comandos/historial).
6. **Reglas:** verificar cumplimiento de `IMPLEMENTATION_RULES.md` (sin shell=True, args como lista, validación, multi-tenant, Alembic, prompts separados).
7. **Tests:** comprobar que los tests mínimos existen y pasan.

## Salida

- Veredicto: aprobado / cambios requeridos.
- Lista de **pendientes** (qué falta para cerrar el issue).
- No hagas commits. No implementes los cambios; solo repórtalos.

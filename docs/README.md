# Octopus — Documentación

Plataforma web privada para recon ofensivo, auditoría externa, OSINT corporativo y bug bounty.

## Project handoff / implementation docs

Documentación de transferencia para el modelo implementador (lista antes de empezar a codificar):

- [HANDOFF.md](architecture/HANDOFF.md) — handoff completo y autosuficiente (resumen, arquitectura, decisiones, suposiciones, riesgos, orden, reglas, primer prompt).
- [DECISIONS.md](architecture/DECISIONS.md) — decisiones técnicas cerradas (ADRs).
- [ROADMAP.md](architecture/ROADMAP.md) — orden de implementación por sprints + camino crítico.
- [SPRINT_0_1_ISSUES.md](architecture/SPRINT_0_1_ISSUES.md) — detalle completo de issues Sprint 0 y 1.
- [CRITICAL_NODES.md](architecture/CRITICAL_NODES.md) — nodos críticos (Scope Gate, ToolRunner base, AI base) y política de tests.
- [ASSUMPTIONS_AND_RISKS.md](architecture/ASSUMPTIONS_AND_RISKS.md) — suposiciones y riesgos con mitigaciones.
- [SONNET_HANDOFF_PROMPT.md](architecture/SONNET_HANDOFF_PROMPT.md) — primer prompt para el modelo implementador (copiar/pegar, inicia OCT-001).
- [development_guidelines/IMPLEMENTATION_RULES.md](development_guidelines/IMPLEMENTATION_RULES.md) — reglas vinculantes del implementador.

## Claude Code portable setup

Cómo retomar el desarrollo en otro PC con el mismo contexto, plugins y flujo:

- [CLAUDE_CODE_SETUP.md](development_guidelines/CLAUDE_CODE_SETUP.md) — dependencias del sistema, plugins recomendados, MCPs, troubleshooting, qué (no) commitear.
- [PORTABLE_CONTEXT.md](development_guidelines/PORTABLE_CONTEXT.md) — qué documentos leer al abrir el repo + cómo continuar en otro PC.
- [AI_WORKFLOW.md](development_guidelines/AI_WORKFLOW.md) — flujo de trabajo obligatorio issue-by-issue.
- [.claude/commands/start-octopus.md](../.claude/commands/start-octopus.md) — arrancar sesión con contexto.
- [.claude/commands/implement-issue.md](../.claude/commands/implement-issue.md) — implementar un issue concreto.
- [.claude/commands/review-issue.md](../.claude/commands/review-issue.md) — revisar un issue terminado.

> Estado: fase de diseño. Sin código de aplicación implementado. Siguiente paso: cambiar al modelo implementador y ejecutar OCT-001.

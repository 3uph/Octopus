---
description: Arrancar sesión de Claude Code en el repo Octopus con el contexto correcto
---

# /start-octopus

Estás abriendo el proyecto **Octopus** (plataforma privada de recon ofensivo, auditoría externa, OSINT corporativo y bug bounty). Antes de hacer nada:

## 1. Carga de contexto (leer en orden)

1. `docs/development_guidelines/PORTABLE_CONTEXT.md`
2. `docs/development_guidelines/IMPLEMENTATION_RULES.md`
3. `docs/architecture/ROADMAP.md`
4. `docs/architecture/SPRINT_0_1_ISSUES.md`

## 2. Reglas de la sesión

- Trabaja **únicamente** sobre el issue que indique el usuario.
- **No** avances al siguiente issue sin confirmación.
- **No** ejecutes herramientas ofensivas (recon real). Tests con mocks/fixtures.
- **No** hagas commits.
- **No** te saltes el Scope Gate.
- Ante ambigüedad: **para y pregunta**.

## 3. Al terminar

Resume:
- Archivos modificados.
- Criterios de aceptación verificados.
- Qué queda pendiente.

Luego espera instrucciones. No continúes solo.

---

> Si no sabes qué issue está pendiente, consulta el estado en `PORTABLE_CONTEXT.md` y pregunta al usuario antes de implementar.

# HANDOFF — Proyecto Octopus
### Documento de transferencia para modelo implementador

> Propósito: permitir que un modelo más barato (Sonnet) implemente el proyecto issue por issue sin perder contexto. Este documento es autosuficiente.

Documentos relacionados:
- `DECISIONS.md` — decisiones técnicas cerradas (ADRs).
- `ROADMAP.md` — orden de implementación por sprints.
- `SPRINT_0_1_ISSUES.md` — detalle de issues Sprint 0 y 1.
- `CRITICAL_NODES.md` — nodos críticos y su política de tests.
- `ASSUMPTIONS_AND_RISKS.md` — suposiciones y riesgos.
- `SONNET_HANDOFF_PROMPT.md` — primer prompt listo para copiar.
- `../development_guidelines/IMPLEMENTATION_RULES.md` — reglas vinculantes.

---

## 1. Resumen ejecutivo (≤30 líneas)

```
Octopus = plataforma web privada para recon ofensivo, auditoría externa,
OSINT corporativo y bug bounty. Uso local / servidor propio.

Gestiona empresas, programas y auditorías. El usuario pega el scope (texto
de HackerOne/Bugcrowd/Intigriti o doc cliente); la herramienta lo parsea,
lo normaliza, exige confirmación humana, y solo entonces permite recon.

4 modos de ejecución: passive-only, medium/safe-active, active/manual
(requiere confirmación explícita), y dry-run (no ejecuta nada).

Toda ejecución de herramientas pasa por el SCOPE GATE — servicio central
que valida cada target contra in-scope / out-of-scope / reglas. Out-of-scope
= bloqueo duro. Es la pieza de seguridad crítica.

Integra herramientas externas (subfinder, httpx, dnsx, nuclei, katana, gau,
nmap, ffuf, etc.) como módulos aislados (tool runners), nunca con shell.

Módulo de inteligencia corporativa (separado del recon técnico): marcas,
productos, proveedores cloud/SaaS/identity, dominios legacy, tech stack
inferido. Cada dato tiene confianza (high/medium/low) y actionability.
NUNCA convierte contexto en target activo sin Scope Gate + revisión humana.

IA = copiloto de apoyo (resume scope, agrupa endpoints, analiza JS, genera
hipótesis de hunting). NUNCA decide scope, ataca, ni genera reportes finales
sin revisión. Prompts versionados en archivos, no inline.

Stack: Docker Compose, FastAPI + Python, Next.js, PostgreSQL, Redis,
Dramatiq (workers). SQLAlchemy + Alembic.

Diseño: modular, segmentado para edición asistida por IA (un módulo = una
carpeta = una responsabilidad), escalable desde el inicio, multi-tenant
lógico, auditoría completa de acciones, seguridad por defecto.

Backlog: ~60 issues (OCT-001..133) ordenados por dependencias.
```

---

## 2. Arquitectura final decidida

**Patrón:** monorepo modular, multi-servicio, orientado a jobs.

**Servicios Docker:**
- `frontend` — Next.js (app router). Solo consume API. Sin lógica de negocio.
- `api` — FastAPI. Orquesta entidades, scope, jobs, permisos. **Imagen ligera, sin binarios de recon.**
- `worker` — Dramatiq. **Única capa autorizada a ejecutar binarios externos.** Imagen pesada con tools. Escalable horizontalmente.
- `scheduler` — (futuro) tareas periódicas.
- `postgres` — datos estructurados.
- `redis` — broker de cola + cache.

**Capas backend:**
- `core/` — config, security, logging (con redacción), permissions.
- `api/` — routes + dependencies. Sin lógica de negocio pesada.
- `models/` — SQLAlchemy (1 fichero por agregado).
- `schemas/` — Pydantic in/out.
- `services/` — lógica reutilizable entre módulos.
- `modules/<x>/` — dominios autocontenidos con su README. **No se importan entre sí directamente** (comunican vía services).
- `workers/` — jobs, queues, schedules.
- `tool_runners/` — ejecución segura de binarios (base + por familia).
- `database/` — migrations (Alembic) + repositories.

**Nodos arquitectónicos críticos (máxima inversión en tests):**
1. **Scope Gate** (`modules/scope_gate/`) — valida todo target. Seguridad.
2. **Base ToolRunner** (`tool_runners/base/`) — sanitización, allowlist, sin shell.
3. **AI module** (`modules/ai/`) — providers + redacción de secrets.

**Flujo:** scope pegado → parser → confirmación humana → planificación de job → Scope Gate valida → dry-run → worker → tool runner → normalización → scoring → dashboard. IA copiloto bajo demanda.

**Modelo de relación:** `Company 1─N Program 1─N Audit`. Assets/jobs cuelgan de `Program` (aislamiento). Intelligence cuelga de `Company` (transversal). `Program.type` distingue auditoría externa vs bug bounty (misma maquinaria, distinta gobernanza).

---

## 3. Decisiones técnicas tomadas

| Decisión | Elección | Razón |
|----------|----------|-------|
| Backend | FastAPI + Python | Pedido; async, pydantic, DX |
| Frontend | Next.js (app router) | Pedido; SSR opcional, estructura por features |
| DB | PostgreSQL | Pedido; JSONB para campos volátiles |
| ORM/migraciones | SQLAlchemy 2.0 + Alembic | Estándar maduro |
| Job framework | **Dramatiq** | Más simple que Celery, buen DX para este tamaño |
| Broker/cache | Redis | Pedido |
| Colas | `passive`, `medium`, `active`, `intelligence`, `ai` | Aislar impacto entre modos |
| Auth | Login local desde Fase 1, password hash argon2/bcrypt | Pedido |
| RBAC | Roles `admin/operator/viewer` | Control básico |
| Multi-tenant | Filtro lógico por columna (`company_id`/`program_id`) | Suficiente; schema-per-tenant diferido |
| Confianza intelligence | Enum reutilizable `high/medium/low` (no tabla) | Evita joins |
| Secretos | Cifrados en DB (`Setting.is_secret`) + `.env` | Nunca en claro/logs |
| Tool execution | Subprocess sin `shell=True`, args como lista, allowlist | Anti command-injection |
| IA prompts | Archivos versionados en `prompts/`, nunca inline | Segmentación |
| LLM provider | Abstracción intercambiable (local Ollama / API externa) | Privacidad configurable |
| Modo active | Nunca por defecto; dry-run + confirmación obligatorios | Seguridad |

Detalle ampliado en `DECISIONS.md`.

---

## 4. Suposiciones

1. Mono-usuario o pocos usuarios al inicio; RBAC completo pero sin SSO.
2. Despliegue local/localhost por defecto; dashboard no expuesto públicamente.
3. Scope se importa por **texto pegado** inicialmente (no API oficial de plataformas en Fase 1).
4. Volumen moderado al inicio (decenas–cientos de programas, miles de assets), escalable después.
5. LLM: soporte para local y externo; el usuario decide por config. Redacción de secrets siempre activa antes de envío externo.
6. Binarios de recon se instalan en la imagen `worker`; pesados (nmap, amass, massdns) pueden ir en capa separada.
7. Leaks/secrets detectados → solo detección + `requires_review`, nunca uso automático.
8. Intelligence nunca crea targets activos sin Scope Gate + confirmación humana.
9. `Audit` se modela como entidad separada (ronda dentro de Program), pero un Program puede funcionar sin audits.
10. Retención de raw outputs: política a definir; volúmenes dedicados desde el inicio.
11. El usuario está autorizado para auditar los objetivos que carga (responsabilidad del operador, no de la herramienta).

> Si el implementador encuentra que una suposición es incorrecta, debe **detenerse y preguntar**, no improvisar. Detalle en `ASSUMPTIONS_AND_RISKS.md`.

---

## 5. Riesgos principales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Fallo del Scope Gate → tocar fuera de scope | **Crítico** | Tests exhaustivos primero; ambiguo→review; bloqueo duro out-of-scope |
| Command injection en tool runners | **Crítico** | Sin shell, args lista, allowlist, sanitización, tests de inyección |
| Modo active mal gobernado → daño/ruido | Alto | Nunca default, dry-run obligatorio, confirmación humana, rate limits |
| Fuga de datos a LLM externo | Alto | Redacción de secrets + aviso + opción LLM local |
| Acoplamiento entre módulos rompe segmentación | Medio | Comunicación vía services; READMEs; revisar imports |
| Modelo de datos prematuro → migraciones dolorosas | Medio | Alembic desde día 1; JSONB para volátiles |
| Falsos positivos de intelligence tratados como hechos | Medio | Confianza + actionability obligatorias |
| Crecimiento de raw outputs en disco | Bajo | Retención + volúmenes dedicados |

---

## 6. Orden recomendado de implementación

```
Sprint 0 (infra):     OCT-001 → 002 → 003,004 → 020 → 021
Sprint 1 (núcleo):    OCT-010 → 011 → 012,013 ; 014 ; 015 → 016 → 017 → 018
Sprint 2 (scope):     OCT-022 → 023 → 025,026 ; 050 → 024
Sprint 3 (pasivo):    OCT-027,028 → 029 → 030 → 031 → 032
Sprint 4 (intel):     OCT-033 → 034 → 035,036
Sprint 5 (dns/http):  OCT-040 → 041 → 042 → 043
Sprint 6 (dashboard): OCT-060 → 061 → 062,063,064,065,066
... (resto según backlog: crawling, scanning, scoring, IA, import, reporting, hardening)
```

Nodos a blindar con tests antes de construir encima: **OCT-026 (Scope Gate)**, **OCT-021 (ToolRunner base)**, **OCT-050 (AI base)**. Detalle en `ROADMAP.md` y `CRITICAL_NODES.md`.

---

## 7 & 8. Sprint 0 y Sprint 1 — detalle a nivel de subtareas

> El detalle completo de cada issue (ID, nombre, objetivo, contexto, dependencias, archivos/módulos, subtareas, criterios de aceptación, tests mínimos, qué NO tocar) está en `SPRINT_0_1_ISSUES.md`.

Resumen de cobertura:
- **Sprint 0:** OCT-001 (estructura+ADRs), OCT-002 (Docker Compose base), OCT-003 (config+logging redacción), OCT-004 (SQLAlchemy+Alembic), OCT-020 (worker+Dramatiq), OCT-021 (ToolRunner base — crítico).
- **Sprint 1:** OCT-010 (User), OCT-011 (login), OCT-012 (RBAC), OCT-013 (AuditLog), OCT-014 (Setting cifrado), OCT-015 (Company/Program/Audit), OCT-016 (CRUD Company), OCT-017 (CRUD Program/Audit), OCT-018 (scope raw + ScopeChangeLog).

---

## 9. Reglas para el modelo implementador

> Vinculantes. Versión completa en `../development_guidelines/IMPLEMENTATION_RULES.md`.

1. **Issue por issue.** Implementar solo el issue asignado.
2. **No tocar módulos no relacionados.** Si parece necesario, detenerse y preguntar.
3. **No refactors globales sin permiso.**
4. **No ejecutar herramientas ofensivas.** Tests con mocks/fixtures.
5. **No saltarse el Scope Gate.**
6. **Mantener arquitectura modular.** Módulos comunican vía `services/`.
7. **Prompts de IA separados** en `prompts/<tarea>/`, nunca inline.
8. **Seguridad por defecto.** Sin `shell=True`; args como lista; validar inputs; secretos cifrados; logs redactados; active nunca por defecto.
9. **Tests obligatorios** por issue; cobertura alta en nodos críticos.
10. **Migraciones Alembic** para todo cambio de esquema.
11. **Multi-tenant siempre** (filtro por company/program).
12. **Sin código fuera de alcance.**
13. **Ante ambigüedad: parar y preguntar.**
14. **Respetar ADRs.**

---

## 10. Primer prompt exacto para el modelo implementador (Fase 0)

> Versión lista para copiar en `SONNET_HANDOFF_PROMPT.md`.

```
Eres el modelo implementador del proyecto Octopus: una plataforma web
privada de recon ofensivo, auditoría externa, OSINT corporativo y bug
bounty. Trabajas issue por issue siguiendo un backlog ya diseñado.

Antes de empezar, lee y respeta el documento de handoff (resumen, 
arquitectura, decisiones técnicas, suposiciones, riesgos y reglas).

REGLAS VINCULANTES:
1. Implementa SOLO el issue asignado. No adelantes otros issues.
2. No toques módulos no relacionados. Si crees que hace falta, PARA y pregunta.
3. No hagas refactors globales sin permiso.
4. No ejecutes herramientas ofensivas; en tests usa mocks/fixtures.
5. Nunca saltes el Scope Gate. Toda ejecución de tools pasa por él.
6. Mantén la arquitectura modular: un módulo = una responsabilidad; los
   módulos no se importan entre sí (comunican vía services/).
7. Prompts de IA siempre en prompts/<tarea>/ como archivos, nunca inline.
8. Seguridad por defecto: sin shell=True, args como lista, validar inputs,
   secretos cifrados, logs redactados, modo active nunca por defecto.
9. Migraciones Alembic para todo cambio de esquema.
10. Multi-tenant siempre (filtro por company_id/program_id).
11. Ante ambigüedad o suposición incorrecta: PARA y pregunta.
12. Respeta los ADRs: FastAPI, Next.js, PostgreSQL, SQLAlchemy+Alembic,
    Dramatiq, Redis, multi-tenant por columna, LLM provider abstracto.

STACK: Docker Compose · FastAPI/Python · Next.js · PostgreSQL · Redis ·
Dramatiq · SQLAlchemy + Alembic.

PRIMER ISSUE — OCT-001 · Estructura de monorepo + ADRs base
Objetivo: crear el árbol de carpetas completo (vacío, con .gitkeep y un
README por módulo) y documentar las decisiones en ADRs.

Subtareas:
1. Crear el árbol backend/app/{core,api,models,schemas,services,modules,
   workers,tool_runners,database,utils}, frontend/src/{app,components,
   features,lib,services,hooks,types}, prompts/, infra/{docker,compose,
   scripts}, data/, docs/{architecture,decisions,development_guidelines}.
   (Respeta la estructura detallada del handoff.)
2. README.md en cada modules/<x>/ con una frase: responsabilidad + qué tocar.
3. ADRs: ADR-001 Dramatiq, ADR-002 Next.js, ADR-003 SQLAlchemy+Alembic,
   ADR-004 multi-tenant por columna, ADR-005 LLM provider abstracto.
4. docs/development_guidelines/ con las 14 reglas del implementador.
5. .gitignore (incluye data/ y .env).

Criterios de aceptación:
- El árbol coincide con la estructura del planning.
- Cada módulo tiene README.
- Los 5 ADRs existen y están redactados.
- Guidelines presentes.

Tests mínimos: un test que verifique la existencia de carpetas y READMEs clave.

NO toques: lógica de negocio, dependencias de runtime, Dockerfiles
(esos llegan en OCT-002).

Cuando termines OCT-001, resume qué creaste y espera la asignación de
OCT-002. No avances solo.
```

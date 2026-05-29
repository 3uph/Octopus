# Decisiones Técnicas Cerradas — Proyecto Octopus

> Estas decisiones están **cerradas**. Cambiarlas requiere un nuevo ADR aprobado. El modelo implementador debe respetarlas (ver `../development_guidelines/IMPLEMENTATION_RULES.md`, regla 17).

---

## Stack

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-01 | **FastAPI + Python** | Backend. Async, pydantic, buena DX. |
| D-02 | **Next.js** (app router) | Frontend. Estructura por features, SSR opcional. Solo consume API. |
| D-03 | **PostgreSQL** | Base de datos. JSONB para campos volátiles. |
| D-04 | **SQLAlchemy 2.0 + Alembic** | ORM + migraciones. Migraciones desde el día 1. |
| D-05 | **Dramatiq** | Framework de jobs/workers. Más simple que Celery, suficiente para el tamaño. |
| D-06 | **Redis** | Broker de cola + cache. |
| D-07 | **Docker Compose** | Orquestación de servicios (frontend, api, worker, postgres, redis, scheduler futuro). |

---

## Arquitectura / multi-tenant

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-08 | **Multi-tenant lógico por columna** | Filtro por `company_id` / `program_id`. Schema-per-tenant diferido. Assets/jobs por `program_id`; intelligence por `company_id`. |
| D-09 | **Worker = única capa autorizada a ejecutar binarios externos** | Imagen `worker` pesada con tools. Ningún otro servicio ejecuta binarios de recon. |
| D-10 | **API ligera sin binarios de recon** | Imagen `api` mínima. Builds rápidos, superficie de ataque reducida. |
| D-11 | **Relación de dominio** | `Company 1─N Program 1─N Audit`. `Program.type` distingue auditoría externa vs bug bounty (misma maquinaria, distinta gobernanza). |

---

## Nodos críticos (ver `CRITICAL_NODES.md`)

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-12 | **Scope Gate como nodo crítico** (`modules/scope_gate/`) | Servicio central que valida todo target contra in/out-of-scope/reglas. Out-of-scope = bloqueo duro. Pieza de seguridad #1. |
| D-13 | **Base ToolRunner como nodo crítico** (`tool_runners/base/`) | Interfaz `plan/run/parse` + sanitización + allowlist. Toda ejecución de binario hereda de aquí. |
| D-14 | **AI module como nodo crítico** (`modules/ai/`) | Providers + redacción de secrets antes de envío externo. |

---

## Seguridad de ejecución

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-15 | **ToolRunner sin `shell=True`** | Anti command-injection. |
| D-16 | **Ejecución de comandos con args como lista** | Nunca concatenar strings con input de usuario. Allowlist de binarios. |
| D-17 | **Secretos cifrados** | `Setting.is_secret` cifrado en DB + `.env`. Nunca en claro ni en logs. |
| D-18 | **Modo active nunca por defecto** | Requiere dry-run + confirmación humana. |

---

## IA

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-19 | **IA con provider abstracto** | Intercambiable: LLM local (Ollama) o API externa. Privacidad configurable. |
| D-20 | **Prompts versionados en `prompts/`** | Archivos versionados por tarea. Nunca inline en código. |
| D-21 | **IA = copiloto, nunca autoridad** | No decide scope, no ataca, no confirma vulns sin evidencia, no genera reportes finales sin revisión. Redacción de secrets obligatoria antes de envío externo. |

---

## Otras decisiones

| # | Decisión | Detalle / Razón |
|---|----------|-----------------|
| D-22 | Colas separadas | `passive`, `medium`, `active`, `intelligence`, `ai`. Aislar impacto entre modos. |
| D-23 | Auth local desde Fase 1 | Password hash argon2/bcrypt. RBAC `admin/operator/viewer`. |
| D-24 | Confianza intelligence como enum | `high/medium/low` reutilizable, no tabla. Evita joins. |
| D-25 | Auditoría completa | `AuditLog` (acciones) + `ToolRun` (ejecuciones de herramientas). |

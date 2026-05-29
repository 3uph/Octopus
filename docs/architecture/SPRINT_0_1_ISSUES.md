# Sprint 0 y Sprint 1 — Issues detallados

> Formato por issue: ID · Nombre · Objetivo · Contexto · Dependencias · Archivos/módulos · Subtareas · Criterios de aceptación · Tests mínimos · Qué NO tocar.
> Reglas vinculantes: `../development_guidelines/IMPLEMENTATION_RULES.md`. Decisiones: `DECISIONS.md`. Nodos críticos: `CRITICAL_NODES.md`.

---

# SPRINT 0 — Infra y fundaciones

---

## OCT-001 · Estructura de monorepo + ADRs base
- **Objetivo:** crear el árbol de carpetas completo (vacío) y documentar decisiones.
- **Contexto:** la segmentación es requisito central — cada módulo debe ser localizable por un asistente IA. Sin esto, todo lo demás se desordena.
- **Dependencias:** ninguna.
- **Archivos/módulos:** `backend/app/{core,api,models,schemas,services,modules,workers,tool_runners,database,utils}/`, `frontend/src/{app,components,features,lib,services,hooks,types}/`, `prompts/`, `infra/{docker,compose,scripts}/`, `data/`, `docs/{architecture,decisions,development_guidelines}/`.
- **Subtareas:**
  1. Crear árbol completo con `.gitkeep` en carpetas vacías.
  2. `README.md` en cada `modules/<x>/` (1 frase: responsabilidad + qué tocar).
  3. ADR-001 job framework (Dramatiq), ADR-002 frontend (Next.js), ADR-003 ORM (SQLAlchemy+Alembic), ADR-004 multi-tenant (filtro lógico), ADR-005 LLM (provider abstracto).
  4. `docs/development_guidelines/` con las reglas del implementador.
  5. `.gitignore` (incluye `data/` y `.env`).
- **Criterios de aceptación:** árbol coincide con la estructura del planning; cada módulo tiene README; 5 ADRs presentes; guidelines presentes.
- **Tests mínimos:** test que verifica existencia de carpetas y READMEs clave (estructura).
- **NO tocar:** lógica, dependencias de runtime, Dockerfiles.

---

## OCT-002 · Docker Compose base
- **Objetivo:** levantar postgres + redis + api (skeleton) + frontend (skeleton) que arrancan y responden healthcheck.
- **Contexto:** base reproducible antes de cualquier feature. Imagen `api` ligera; worker se añade en OCT-020.
- **Dependencias:** OCT-001.
- **Archivos/módulos:** `infra/docker/{api.Dockerfile,frontend.Dockerfile}`, `infra/compose/docker-compose.yml`, `infra/compose/docker-compose.override.yml`, `.env.example`, endpoint `/health` mínimo.
- **Subtareas:**
  1. `api.Dockerfile` (Python + FastAPI, sin binarios recon).
  2. `frontend.Dockerfile` (Next.js).
  3. `docker-compose.yml`: servicios postgres, redis, api, frontend con healthchecks y `depends_on`.
  4. `override.yml` para dev (hot reload, puertos solo `127.0.0.1`).
  5. `.env.example` con todas las variables (DB, Redis, secret key, modo default).
  6. Endpoint `GET /health` en api.
- **Criterios de aceptación:** `docker compose up` levanta los 4 servicios; api responde `/health` 200; frontend sirve página vacía; postgres/redis healthy; puertos no expuestos fuera de localhost.
- **Tests mínimos:** test de integración que hace request a `/health`; healthchecks pasan.
- **NO tocar:** imagen worker con binarios (OCT-020), migraciones, modelos.

---

## OCT-003 · Config core + logging con redacción
- **Objetivo:** settings tipados desde `.env` y logger que redacta secrets/tokens.
- **Contexto:** ninguna feature debe hardcodear config ni loguear secretos. Requisito de seguridad transversal.
- **Dependencias:** OCT-002.
- **Archivos/módulos:** `backend/app/core/config/`, `backend/app/core/logging/`.
- **Subtareas:**
  1. `Settings` (pydantic-settings) con carga desde `.env`, tipado, valores por defecto seguros.
  2. Logger central con formateador que redacta patrones (tokens, API keys, passwords, `Authorization`, credenciales).
  3. Función helper de redacción reutilizable.
- **Criterios de aceptación:** settings accesibles vía dependency; sin valores hardcodeados en código; logger redacta en cualquier nivel.
- **Tests mínimos:** test de redacción (input con token → output sin token); test de carga de settings desde env.
- **NO tocar:** rutas de negocio, modelos, auth.

---

## OCT-004 · Setup SQLAlchemy + Alembic + sesión DB
- **Objetivo:** ORM, conexión, dependency de sesión, migración inicial vacía.
- **Contexto:** base de persistencia. Migraciones desde día 1 (decisión cerrada).
- **Dependencias:** OCT-002.
- **Archivos/módulos:** `backend/app/database/` (engine, session), `backend/app/database/migrations/` (Alembic env), `backend/app/api/dependencies/db.py`.
- **Subtareas:**
  1. Engine + sessionmaker (async o sync — coherente con FastAPI; decidir y documentar en ADR).
  2. Base declarativa con mixin `id` (UUID), `created_at`, `updated_at`.
  3. Configurar Alembic (env.py lee settings).
  4. Dependency `get_db` para inyección.
  5. Migración inicial vacía + verificar `alembic upgrade head`.
  6. Healthcheck de DB.
- **Criterios de aceptación:** `alembic upgrade head` corre limpio en contenedor; dependency de sesión disponible; mixin base reutilizable.
- **Tests mínimos:** test que abre sesión y hace `SELECT 1`; test que la migración aplica.
- **NO tocar:** modelos de dominio concretos (issues posteriores).

---

## OCT-020 · Imagen worker + Dramatiq + cola Redis
- **Objetivo:** servicio worker que consume cola y procesa un job de prueba (sin tools reales).
- **Contexto:** la capa de ejecución. Solo el worker ejecutará binarios (más adelante). Aquí solo la infraestructura.
- **Dependencias:** OCT-002.
- **Archivos/módulos:** `infra/docker/worker.Dockerfile`, `backend/app/workers/{jobs,queues}/`, compose (servicio worker).
- **Subtareas:**
  1. `worker.Dockerfile` (base + placeholder para binarios; capa de tools documentada pero vacía aún).
  2. Configurar Dramatiq con broker Redis.
  3. Definir colas `passive`, `medium`, `active`, `intelligence`, `ai`.
  4. Job de prueba (`echo`/`ping`) encolable.
  5. Servicio `worker` en compose, escalable.
- **Criterios de aceptación:** worker arranca; consume y ejecuta job de prueba; colas definidas; `docker compose up --scale worker=2` funciona.
- **Tests mínimos:** test que encola job de prueba y verifica ejecución/resultado.
- **NO tocar:** tool runners reales, modelos de ScanJob/ToolRun (Sprint 3).

---

## OCT-021 · Base ToolRunner (interfaz + sanitización) — CRÍTICO
- **Objetivo:** clase base segura que todo runner futuro hereda. **Nodo crítico de seguridad.**
- **Contexto:** previene command injection. Define `plan/run/parse`. Ningún binario se ejecuta fuera de esta base. Ver `CRITICAL_NODES.md`.
- **Dependencias:** OCT-020.
- **Archivos/módulos:** `backend/app/tool_runners/base/`.
- **Subtareas:**
  1. Clase abstracta `ToolRunner` con `plan(targets, scope, mode) -> ToolRunPlan`, `run(plan) -> raw_path`, `parse(raw) -> records`.
  2. **Allowlist** de binarios permitidos.
  3. Sanitización de targets por tipo (dominio/IP/URL/CIDR) con regex estricta.
  4. Constructor de comando: args como **lista**, nunca string; **nunca `shell=True`**.
  5. Timeouts y límite de tamaño de output.
  6. Hook de registro (placeholder para ToolRun, que llega en OCT-028).
- **Criterios de aceptación:** no es posible ejecutar binario fuera de allowlist; targets maliciosos rechazados por sanitización; sin `shell=True` en el código.
- **Tests mínimos:** **tests de inyección** (`; rm -rf`, `$(...)`, backticks, `&&`, espacios, unicode) → rechazados; test de allowlist (binario no listado → error); test de timeout.
- **NO tocar:** runners concretos (subfinder, etc.), ejecución real de red.

---

# SPRINT 1 — Núcleo: auth, tenancy, entidades, scope raw

---

## OCT-010 · Modelo User + migración
- **Objetivo:** tabla `User`.
- **Contexto:** base de auth. Roles definidos desde el inicio.
- **Dependencias:** OCT-004.
- **Archivos/módulos:** `models/user.py`, `schemas/user.py`, migración Alembic.
- **Subtareas:**
  1. Modelo `User` (username, email, password_hash, role enum admin/operator/viewer, is_active, last_login_at).
  2. Schemas pydantic (create/read, sin exponer hash).
  3. Migración + constraints únicos.
- **Criterios de aceptación:** migración aplica; username/email únicos; schema de lectura nunca incluye hash.
- **Tests mínimos:** test de creación; test de unicidad (duplicado falla).
- **NO tocar:** endpoints de auth (OCT-011), RBAC (OCT-012).

---

## OCT-011 · Login local + hashing + sesión/JWT
- **Objetivo:** autenticación local funcional.
- **Contexto:** requisito de seguridad desde Fase 1. Dashboard no usable sin login.
- **Dependencias:** OCT-010, OCT-003.
- **Archivos/módulos:** `core/security/` (hashing, token), `api/routes/auth.py`, `api/dependencies/auth.py`.
- **Subtareas:**
  1. Hashing con argon2/bcrypt.
  2. Endpoint login (verifica credenciales, emite token/sesión).
  3. Endpoint logout.
  4. Dependency `current_user` que protege rutas.
  5. Actualizar `last_login_at`.
- **Criterios de aceptación:** login válido devuelve credencial; inválido devuelve 401; rutas protegidas rechazan sin auth; password nunca en logs (verificar con redactor de OCT-003).
- **Tests mínimos:** login OK; login fallido; acceso a ruta protegida sin token → 401; con token → 200.
- **NO tocar:** RBAC fino (OCT-012), UI (OCT-060).

---

## OCT-012 · RBAC + dependency de permisos
- **Objetivo:** control de acceso por rol + base de aislamiento por tenant.
- **Contexto:** viewer no debe mutar; operator/admin sí. Base para separación por empresa/programa.
- **Dependencias:** OCT-011.
- **Archivos/módulos:** `core/permissions/`, `api/dependencies/`.
- **Subtareas:**
  1. Dependency `require_role(...)`.
  2. Helper de filtro por tenant (reutilizable en repositorios).
  3. Mapa de permisos por rol.
- **Criterios de aceptación:** viewer bloqueado en mutaciones; admin acceso total; filtro tenant disponible para queries.
- **Tests mínimos:** matriz rol×acción (allow/deny) cubierta.
- **NO tocar:** lógica de negocio de módulos concretos.

---

## OCT-013 · Modelo AuditLog + middleware de auditoría
- **Objetivo:** registrar toda acción mutante.
- **Contexto:** requisito de seguridad — quién/qué/cuándo, detalles redactados.
- **Dependencias:** OCT-004, OCT-011.
- **Archivos/módulos:** `models/audit_log.py`, `core/logging/`, `api/dependencies/`.
- **Subtareas:**
  1. Modelo `AuditLog` (user_id, action, entity_type, entity_id, mode, details_redacted jsonb, ip, created_at).
  2. Mecanismo (dependency/middleware) que registra mutaciones.
  3. Aplicar redacción de OCT-003 a `details`.
- **Criterios de aceptación:** cada POST/PUT/DELETE genera AuditLog; GET no; detalles redactados.
- **Tests mínimos:** mutación → entrada creada; secret en payload → redactado en log.
- **NO tocar:** ToolRun audit (OCT-028/031).

---

## OCT-014 · Modelo Setting (jerárquico, secretos cifrados)
- **Objetivo:** settings global/company/program con secretos cifrados.
- **Contexto:** API keys y config sensible. Nunca en claro.
- **Dependencias:** OCT-004.
- **Archivos/módulos:** `models/setting.py`, `core/security/` (cifrado simétrico).
- **Subtareas:**
  1. Modelo `Setting` (scope enum, scope_id, key, value jsonb, is_secret).
  2. Cifrado/descifrado de valores `is_secret` (clave desde `.env`).
  3. Resolución jerárquica (program > company > global).
- **Criterios de aceptación:** secret cifrado en DB; descifrado solo en runtime; nunca en logs; resolución jerárquica correcta.
- **Tests mínimos:** guardar secret → cifrado en DB; leer → descifra; resolución jerárquica.
- **NO tocar:** UI settings (OCT-066).

---

## OCT-015 · Modelos Company / Program / Audit + migración
- **Objetivo:** entidades núcleo de gobernanza.
- **Contexto:** `Company 1─N Program 1─N Audit`. Base de todo el dominio.
- **Dependencias:** OCT-004.
- **Archivos/módulos:** `models/{company,program,audit}.py`, `schemas/*`, migración.
- **Subtareas:**
  1. `Company` (name_legal, name_commercial, description).
  2. `Program` (company_id FK, name, type enum, platform enum, program_url, status enum, scope_last_reviewed_at).
  3. `Audit` (program_id FK, title, objective, status, started_at, ended_at).
  4. Schemas + migración + cascadas.
- **Criterios de aceptación:** migración aplica; enums correctos; relaciones y cascadas definidas; tenant por company_id/program_id.
- **Tests mínimos:** crear company→program→audit; cascada al borrar; enum inválido rechazado.
- **NO tocar:** scope, assets (issues siguientes).

---

## OCT-016 · CRUD Company (API + repositorio)
- **Objetivo:** endpoints CRUD de empresa.
- **Contexto:** primer dominio funcional end-to-end.
- **Dependencias:** OCT-015, OCT-013.
- **Archivos/módulos:** `modules/companies/`, `api/routes/companies.py`, `database/repositories/company.py`.
- **Subtareas:**
  1. Repositorio (CRUD + filtro tenant).
  2. Service.
  3. Routes con validación pydantic + auth + RBAC.
  4. AuditLog en mutaciones.
- **Criterios de aceptación:** CRUD completo; viewer no muta; AuditLog generado; filtro tenant aplicado.
- **Tests mínimos:** CRUD happy path; viewer bloqueado; validación de input inválido.
- **NO tocar:** frontend (OCT-061), programs.

---

## OCT-017 · CRUD Program / Audit (API + repositorio)
- **Objetivo:** endpoints CRUD de programa y auditoría.
- **Contexto:** `Program.type` distingue auditoría vs bug bounty.
- **Dependencias:** OCT-016.
- **Archivos/módulos:** `modules/programs/`, `modules/audits/`, `api/routes/{programs,audits}.py`, repositorios.
- **Subtareas:**
  1. Repositorios + services para Program y Audit.
  2. Routes con validación, auth, RBAC, AuditLog.
  3. Transiciones de estado (planning→active→paused→closed).
- **Criterios de aceptación:** crear program bajo company; tipos/plataformas válidos; transición de estado controlada; AuditLog.
- **Tests mínimos:** CRUD; transición válida/inválida; tenant aislado.
- **NO tocar:** scope parsing (Sprint 2).

---

## OCT-018 · Persistencia de scope raw + esqueleto ScopeChangeLog
- **Objetivo:** guardar el texto de scope pegado, sin parsear.
- **Contexto:** el parser llega en Sprint 2; aquí solo se persiste el raw y se prepara el histórico.
- **Dependencias:** OCT-017.
- **Archivos/módulos:** `models/scope_*` (campo raw + ScopeChangeLog), `modules/programs/`.
- **Subtareas:**
  1. Campo/tabla para scope raw por programa.
  2. Modelo `ScopeChangeLog` (before/after jsonb, changed_by, change_type).
  3. Endpoint para pegar/actualizar scope raw → registra cambio.
- **Criterios de aceptación:** raw scope persiste; cada cambio genera ScopeChangeLog; AuditLog.
- **Tests mínimos:** guardar raw; actualizar → genera changelog.
- **NO tocar:** parser, Scope Gate, normalización (Sprint 2).

---

> **Hito Sprint 1:** login + empresa + programa + auditoría + scope raw + auditoría de acciones funcionando end-to-end.

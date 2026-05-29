# ADR-004 — Multi-tenancy: filtro lógico por columna

**Estado:** Aprobado  
**Fecha:** 2026-05-29

## Decisión

Se usa **multi-tenant lógico por columna** (`company_id` / `program_id`), no schema-per-tenant ni database-per-tenant.

## Contexto

El sistema gestiona datos de múltiples empresas y programas. Necesita aislamiento lógico desde el inicio, con posibilidad de crecer.

## Razón

- Schema-per-tenant o database-per-tenant añade complejidad operativa innecesaria para el tamaño inicial.
- Filtro por columna es suficiente para el volumen esperado y más fácil de mantener.
- Permite escalar a schema-per-tenant en el futuro si es necesario (nuevo ADR).

## Consecuencias

- Assets/jobs filtran por `program_id`.
- Intelligence filtra por `company_id`.
- Toda query de datos incluye filtro de tenant (obligatorio).
- Dependency de tenant en `api/dependencies/` reutilizable en repositories.
- Schema-per-tenant es una opción diferida; no se implementa ahora.

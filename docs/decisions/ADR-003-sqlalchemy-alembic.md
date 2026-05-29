# ADR-003 — ORM y migraciones: SQLAlchemy 2.0 + Alembic

**Estado:** Aprobado  
**Fecha:** 2026-05-29

## Decisión

Se usa **SQLAlchemy 2.0** como ORM y **Alembic** para migraciones. Base de datos: PostgreSQL.

## Contexto

El sistema necesita persistencia relacional escalable, con soporte de JSONB para campos volátiles y migraciones controladas desde el día 1.

## Razón

- SQLAlchemy 2.0 tiene API moderna y soporta async nativo (ver ADR-006).
- Alembic es el estándar de facto para migraciones con SQLAlchemy.
- JSONB de PostgreSQL permite campos flexibles sin sacrificar integridad.
- Alternativas (Tortoise ORM, SQLModel) tienen menos madurez o acoplamiento mayor.

## Consecuencias

- Modelos en `backend/app/models/` (1 fichero por agregado).
- Migraciones en `backend/app/database/migrations/`.
- **Nunca modificar tablas sin migración Alembic.**
- Base declarativa con mixin `id` (UUID v4), `created_at`, `updated_at`.
- Repositories en `backend/app/database/repositories/` para acceso a datos.

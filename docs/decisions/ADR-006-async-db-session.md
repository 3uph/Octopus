# ADR-006 — DB session: async SQLAlchemy (AsyncSession)

**Estado:** Aprobado  
**Fecha:** 2026-05-29  
**Issue:** OCT-004

## Decisión

Se usa **async SQLAlchemy** (SQLAlchemy 2.0 async API con `asyncpg` como driver) en lugar de sync.

## Contexto

OCT-004 requiere decidir entre async y sync para la sesión de DB (ver ASSUMPTIONS_AND_RISKS.md).

## Razón

- FastAPI es async-first; usar async SQLAlchemy evita bloquear el event loop.
- SQLAlchemy 2.0 async API es madura y estable.
- `asyncpg` es el driver async más rápido para PostgreSQL.
- Mejor throughput bajo carga sin thread pool overhead.

## Consecuencias

- `create_async_engine` + `AsyncSession` en `backend/app/database/`.
- Driver: `asyncpg` (postgresql+asyncpg://).
- Dependency FastAPI: `AsyncSession` con `async for` o `yield`.
- Tests de DB: `pytest-asyncio` + `AsyncSession` en memoria o contra DB real en contenedor.
- Cambiar a sync requeriría nuevo ADR y migración de código.

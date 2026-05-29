# ADR-001 — Job framework: Dramatiq

**Estado:** Aprobado  
**Fecha:** 2026-05-29

## Decisión

Se usa **Dramatiq** como framework de jobs/workers (no Celery, no RQ).

## Contexto

El sistema necesita un broker de cola para ejecutar recon jobs de forma asíncrona y desacoplada. Los candidatos evaluados fueron Celery, RQ y Dramatiq.

## Razón

- Dramatiq tiene una API más simple y menos magic que Celery (sin `CELERY_*` config dispersa).
- Mejor DX: decoradores limpios, tipos predecibles, middlewares composables.
- RQ es más simple pero tiene menos features (retry, priorities, middlewares).
- Dramatiq es suficiente para el volumen inicial y escala bien.

## Consecuencias

- Broker: Redis (compartido con cache).
- Colas: `passive`, `medium`, `active`, `intelligence`, `ai` — separadas para aislar impacto.
- Workers: stateless, escalables horizontalmente con `docker compose --scale worker=N`.
- Cambiar a otro framework requeriría nuevo ADR aprobado.

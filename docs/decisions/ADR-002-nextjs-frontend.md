# ADR-002 — Frontend: Next.js (app router)

**Estado:** Aprobado  
**Fecha:** 2026-05-29

## Decisión

Se usa **Next.js con app router** para el frontend (no React+Vite standalone, no otro framework).

## Contexto

El frontend es un dashboard interno. Necesita ser mantenible, modular y fácil de editar con IA.

## Razón

- Next.js con app router provee estructura por features clara.
- SSR opcional para páginas que lo necesiten.
- Ecosistema TypeScript maduro.
- Estructura `src/features/<x>/` mapea directamente a la segmentación modular del proyecto.
- Solo consume la API (FastAPI); sin lógica de negocio en frontend.

## Consecuencias

- Frontend en `frontend/src/` con estructura por features.
- `src/app/` para rutas Next.js.
- `src/components/` para componentes reutilizables.
- `src/features/<x>/` para lógica por dominio.
- TypeScript por defecto.
- No se usa React+Vite standalone. No se usa otro meta-framework.

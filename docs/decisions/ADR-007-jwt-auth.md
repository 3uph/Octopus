# ADR-007 — Auth: JWT (stateless tokens)

**Estado:** Aprobado  
**Fecha:** 2026-05-29  
**Issue:** OCT-011

## Decisión

Se usa **JWT** (JSON Web Tokens) para autenticación, no sesiones server-side.

## Contexto

OCT-011 requería decidir entre JWT stateless vs sesión server-side (ver ASSUMPTIONS_AND_RISKS.md).

## Razón

- API-first: JWT encaja mejor con clientes API y futura CLI.
- Stateless: sin persistencia de sesión en Redis o DB para auth.
- Estándar ampliamente soportado; python-jose es maduro.
- Para este volumen y uso (herramienta privada, pocos usuarios), los trade-offs de revocación son aceptables.

## Consecuencias

- Tokens firmados con `SECRET_KEY` de settings.
- Expiración configurable (`JWT_EXPIRE_MINUTES`, default 480 = 8h).
- Logout es client-side (el token expira). No revocación activa en esta fase.
- Futuro: si se necesita revocación inmediata, añadir blocklist en Redis (nuevo ADR).
- Algoritmo: HS256.

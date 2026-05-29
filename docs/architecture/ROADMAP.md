# Roadmap de Implementación — Proyecto Octopus

> Orden recomendado de ejecución del backlog (~60 issues, OCT-001..133), ordenado por dependencias. Detalle de Sprint 0 y 1 en `SPRINT_0_1_ISSUES.md`.

---

## Nodos críticos — leer primero

Tres issues son nodos reutilizados por casi todo lo demás. Requieren **tests fuertes** antes de construir encima (detalle y política en `CRITICAL_NODES.md`):

- **OCT-021 · Base ToolRunner** — toda ejecución de binario hereda de aquí.
- **OCT-026 · Scope Gate** — valida todo target; seguridad #1.
- **OCT-050 · AI base** — providers + redacción de secrets.

> **Regla dura:** OCT-026 (Scope Gate) y OCT-021 (ToolRunner base) deben tener **tests fuertes y aprobados ANTES de permitir cualquier ejecución real de herramientas** (es decir, antes de OCT-030 y posteriores). Sin esa cobertura, no se habilita recon real.

---

## Sprint 0 — Infra y fundaciones

```
OCT-001 → 002 → 003,004 → 020 → 021
```

- **OCT-001** Estructura de monorepo + ADRs base
- **OCT-002** Docker Compose base (postgres, redis, api, frontend skeleton)
- **OCT-003** Config core + logging con redacción
- **OCT-004** Setup SQLAlchemy + Alembic + sesión DB
- **OCT-020** Imagen worker + Dramatiq + cola Redis
- **OCT-021** Base ToolRunner (interfaz + sanitización) — **crítico**

---

## Sprint 1 — Núcleo: auth, tenancy, entidades, scope raw

```
OCT-010 → 011 → 012,013 ; 014 ; 015 → 016 → 017 → 018
```

- **OCT-010** Modelo User + migración
- **OCT-011** Login local + hashing + sesión/JWT
- **OCT-012** RBAC + dependency de permisos
- **OCT-013** Modelo AuditLog + middleware de auditoría
- **OCT-014** Modelo Setting (jerárquico, secretos cifrados)
- **OCT-015** Modelos Company / Program / Audit + migración
- **OCT-016** CRUD Company (API + repositorio)
- **OCT-017** CRUD Program / Audit (API + repositorio)
- **OCT-018** Persistencia de scope raw + esqueleto ScopeChangeLog

**Hito Sprint 1:** login + empresa + programa + auditoría + scope raw + auditoría de acciones funcionando end-to-end.

---

## Orden general de los siguientes sprints

```
Sprint 2 (scope):     OCT-022 → 023 → 025,026 ; 050 → 024
Sprint 3 (pasivo):    OCT-027,028 → 029 → 030 → 031 → 032
Sprint 4 (intel):     OCT-033 → 034 → 035,036
Sprint 5 (dns/http):  OCT-040 → 041 → 042 → 043
Sprint 6 (dashboard): OCT-060 → 061 → 062,063,064,065,066
Sprint 7 (crawl/JS):  OCT-070 → 071 → 072 → 073,074
Sprint 8 (scanning):  OCT-080 → 081 → 082 ; 083
Sprint 9 (scoring):   OCT-090 → 091,092
Sprint 10 (IA):       OCT-050 (si no antes) → 100
Sprint 11+ (resto):   import (110→111→112 ; 113),
                      reporting (120→121 ; 122),
                      hardening (130→131,132,133)
```

> Nota: **OCT-050 (AI base)** se adelanta a Sprint 2 porque lo necesitan OCT-024, OCT-036 y OCT-073.

---

## Grafo de dependencias (camino crítico)

```
OCT-001 → 002 → 003,004
004 → 010 → 011 → 012,013
011 → 014
004 → 015 → 016 → 017 → 018 → 022 → 023 → 025,026
002 → 020 → 021
014,003 → 050        (IA base, adelantada)
023+050 → 024
017,021 → 027,028 → 029 → 030 → 031 → 032   (recon pasivo)
016 → 033 → 034 → 035(+026), 036(+050)       (intelligence)
027 → 040 → 041 → 042 → 043                   (DNS+HTTP)
011 → 060 → 061 → 062,063,064,065,066         (dashboard)
031 → 070 → 071 → 072 → 073,074               (crawling+JS)
028 → 080 → 081 → 082 ; 028+026 → 083         (scanning)
041,072 → 090 → 091,092                        (scoring)
050,090 → 100
070 → 110 → 111 → 112 ; 070 → 113             (import)
015 → 120 → 121 ; 120+050 → 122               (reporting)
032,043 → 130 → 131,132,133                    (hardening)
```

---

## Épicas (mapeo a fases)

`E0` Setup · `E1` Núcleo+Auth · `E2` Scope · `E3` Recon pasivo · `E4` Intelligence · `E5` DNS+HTTP · `E6` Dashboard · `E7` Crawling+JS · `E8` Scanning · `E9` Scoring · `E10` IA · `E11` Import · `E12` Reporting · `E13` Hardening

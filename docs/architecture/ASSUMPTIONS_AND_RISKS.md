# Suposiciones y Riesgos — Proyecto Octopus

> **IMPORTANTE:** Si el modelo implementador detecta que cualquiera de estas suposiciones es **incorrecta** o no aplica, debe **DETENERSE y PREGUNTAR**. No improvisar decisiones de arquitectura o seguridad.

---

## Suposiciones

1. **Usuarios:** mono-usuario o pocos usuarios al inicio; RBAC completo pero sin SSO.
2. **Despliegue:** local/localhost por defecto; dashboard no expuesto públicamente.
3. **Importación de scope:** por **texto pegado** inicialmente (no API oficial de plataformas en Fase 1).
4. **Volumen:** moderado al inicio (decenas–cientos de programas, miles de assets), escalable después.
5. **LLM:** soporte para local y externo; el usuario decide por config. Redacción de secrets siempre activa antes de envío externo.
6. **Binarios de recon:** se instalan en la imagen `worker`; los pesados (nmap, amass, massdns) pueden ir en capa separada.
7. **Leaks/secrets detectados:** solo detección + `requires_review`, nunca uso automático.
8. **Intelligence:** nunca crea targets activos sin Scope Gate + confirmación humana.
9. **Audit:** entidad separada (ronda dentro de Program), pero un Program puede funcionar sin audits.
10. **Retención de raw outputs:** política a definir; volúmenes dedicados desde el inicio.
11. **Autorización:** el usuario está autorizado para auditar los objetivos que carga (responsabilidad del operador, no de la herramienta).

---

## Riesgos principales y mitigaciones

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Fallo del Scope Gate → tocar fuera de scope | **Crítico** | Tests exhaustivos primero (ver `CRITICAL_NODES.md`); ambiguo→review; bloqueo duro out-of-scope |
| Command injection en tool runners | **Crítico** | Sin shell, args como lista, allowlist, sanitización, tests de inyección |
| Modo active mal gobernado → daño/ruido | Alto | Nunca default, dry-run obligatorio, confirmación humana, rate limits |
| Fuga de datos a LLM externo | Alto | Redacción de secrets + aviso + opción LLM local |
| Acoplamiento entre módulos rompe segmentación | Medio | Comunicación vía services; READMEs; revisar imports |
| Modelo de datos prematuro → migraciones dolorosas | Medio | Alembic desde día 1; JSONB para campos volátiles |
| Falsos positivos de intelligence tratados como hechos | Medio | Confianza (high/medium/low) + actionability obligatorias |
| Crecimiento de raw outputs en disco | Bajo | Retención + volúmenes dedicados |

---

## Decisiones pendientes (resolver antes o durante implementación)

- Sesión DB async vs sync (documentar en ADR durante OCT-004).
- LLM por defecto: local vs externo vs ambos configurable (afecta OCT-050).
- Política concreta de retención de raw outputs.
- Auth: JWT vs sesión server-side (decidir en OCT-011).
- Volumen real esperado (afecta índices/paginación/particionado).

> Cualquier decisión pendiente que bloquee un issue → **parar y preguntar**.

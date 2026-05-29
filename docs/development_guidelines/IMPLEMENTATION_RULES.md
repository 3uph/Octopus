# Reglas del Modelo Implementador — Proyecto Octopus

> **Vinculantes.** Aplican a cualquier modelo o persona que implemente issues del backlog (OCT-NNN). Pensadas para un modelo implementador (p. ej. Sonnet) que trabaja issue por issue.

---

## Reglas de proceso

### 1. Trabajar issue por issue
Implementar **solo** el issue asignado. No adelantar trabajo de otros issues. Al terminar, resumir lo hecho y esperar la asignación del siguiente. No avanzar solo.

### 2. No modificar módulos no relacionados
Tocar únicamente los archivos/módulos listados en el issue. Si un cambio parece requerir tocar otro módulo, **detenerse y preguntar** — no improvisar.

### 3. No hacer refactors globales sin permiso
Cambios de formato, estructura o renombrados fuera del alcance del issue requieren aprobación explícita.

### 16. Parar y preguntar ante ambigüedad
Ante ambigüedad, suposición que parece incorrecta, o decisión de arquitectura/seguridad no cubierta: **detenerse y preguntar**. Nunca improvisar en estos casos.

### 17. Respetar ADRs
Las decisiones técnicas en `../architecture/DECISIONS.md` están **cerradas**. Cambiarlas requiere un nuevo ADR aprobado.

---

## Reglas de seguridad (críticas)

### 4. No ejecutar herramientas ofensivas
Durante el desarrollo **no** se lanzan binarios de recon contra objetivos reales. Los tests usan mocks/fixtures.

### 5. No saltarse el Scope Gate
Toda ejecución de tool runner pasa por `modules/scope_gate/`. **Prohibido** construir rutas que lo eviten. Out-of-scope explícito = bloqueo duro.

### 8. Mantener seguridad por defecto
- Modo active **nunca** por defecto; requiere dry-run + confirmación humana.
- Dry-run siempre disponible.
- Datos sensibles nunca expuestos.

### 9. No usar `shell=True`
Ejecución de procesos **nunca** con `shell=True`.

### 10. Usar args como lista
Construir comandos con args como **lista**, jamás concatenando strings con input de usuario. Allowlist de binarios obligatoria.

### 11. Validar inputs
Validar **todo** input con pydantic / sanitización estricta por tipo (dominio/IP/URL/CIDR) antes de usarlo.

### 12. Cifrar secretos
API keys y valores sensibles cifrados en DB (`Setting.is_secret`). Nunca en claro. Clave desde `.env`.

### 13. Redactar logs
Logs **nunca** contienen tokens, credenciales ni secretos. Usar el redactor central (`core/logging/`).

---

## Reglas de arquitectura

### 6. Mantener arquitectura modular
Un módulo = una responsabilidad. Los módulos **no se importan entre sí directamente**; comunican vía `services/`. Respetar la estructura de carpetas del planning.

### 7. Mantener prompts de IA separados
Todo prompt vive en `prompts/<tarea>/` como archivo versionado. **Nunca** hardcodear prompts en el código.

### 14. Usar Alembic para cambios de esquema
**Nunca** modificar tablas sin migración Alembic. Migraciones desde el día 1.

### 15. Mantener multi-tenant por `company_id` / `program_id`
Toda query de datos filtra por tenant. Assets/jobs por `program_id`; intelligence por `company_id`.

---

## Reglas de calidad

- **Tests obligatorios** por issue (los "tests mínimos" definidos en cada issue).
- **Cobertura alta** en nodos críticos: Scope Gate (OCT-026), ToolRunner base (OCT-021), AI base (OCT-050). Ver `../architecture/CRITICAL_NODES.md`.
- **Sin código fuera de alcance**: no crear ficheros/carpetas no listados salvo necesidad estricta; si es necesario, documentarlo.

---

## Resumen de prohibiciones

| Prohibido | Por qué |
|-----------|---------|
| Ejecutar tools ofensivas en dev | Daño/ruido a objetivos reales |
| Saltar el Scope Gate | Tocar fuera de scope |
| `shell=True` | Command injection |
| Concatenar args como string | Command injection |
| Prompts inline | Rompe segmentación IA |
| Importar módulos entre sí | Rompe modularidad |
| Cambiar esquema sin Alembic | Migraciones inconsistentes |
| Secretos en claro o en logs | Fuga de credenciales |
| Modo active por defecto | Ejecución peligrosa no autorizada |
| Refactor global sin permiso | Cambios fuera de alcance |
| Improvisar ante ambigüedad | Decisiones erróneas de arquitectura/seguridad |

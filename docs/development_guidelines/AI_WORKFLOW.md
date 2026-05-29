# Flujo de trabajo con IA — Octopus (obligatorio)

> Disciplina de desarrollo asistido por IA. Complementa `IMPLEMENTATION_RULES.md`. Si trabajas en otro PC, empieza **siempre** leyendo `PORTABLE_CONTEXT.md`.

---

## Ciclo por issue (obligatorio)

1. **Un issue por ejecución.** Trabajar solo el issue indicado por el usuario.
2. **Leer antes de implementar:** `SPRINT_0_1_ISSUES.md` (o el roadmap correspondiente para issues posteriores) + las reglas.
3. **Implementar** solo los archivos/módulos permitidos por el issue.
4. **Verificar criterios de aceptación** del issue uno a uno.
5. **Ejecutar tests/comprobaciones** si existen (los "tests mínimos" del issue).
6. **Resumir** los archivos modificados y los criterios verificados.
7. **No avanzar** al siguiente issue sin confirmación explícita del usuario.

---

## Prohibiciones durante el flujo

- **No** hacer commits automáticamente.
- **No** ejecutar herramientas ofensivas (recon real). Tests con mocks/fixtures.
- **No** saltarse el **Scope Gate**.
- **No** tocar módulos fuera del alcance del issue.
- **No** improvisar ante ambigüedad → **parar y preguntar**.

---

## Uso de plugins

- **Superpowers:** mantener disciplina issue-by-issue (planes, TDD, verificación antes de declarar completo).
- **Context7:** usar **solo cuando haga falta documentación actualizada** de una librería/framework. No usar por defecto.
- **Caveman:** comunicación comprimida; opcional, no afecta al código.

---

## Regla de oro

> Empezar sesión en otro PC → leer `PORTABLE_CONTEXT.md` → cargar contexto → implementar **un** issue → verificar → resumir → esperar confirmación.

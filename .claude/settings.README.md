# .claude/settings.json — notas

Configuración **project-scoped** y conservadora para Claude Code. Sin secretos, sin rutas absolutas personales.

- `defaultMode: ask` → confirma antes de editar/escribir/ejecutar.
- `deny` bloquea comandos peligrosos (`rm -rf`, `sudo`) y **herramientas ofensivas de recon** (nmap, nuclei, subfinder, httpx, ffuf, etc.) — coherente con la regla "no ejecutar herramientas ofensivas en dev".
- `deny` impide leer `.env`, claves `.pem`/`.key`.

> El formato exacto de `permissions` puede variar entre versiones de Claude Code. Si una clave no es reconocida, **ajustar manualmente** según la versión instalada (`/config` o documentación). Este archivo es un punto de partida seguro, no exhaustivo.

No commitear este settings si en algún momento se le añaden secretos. Hoy no contiene ninguno.

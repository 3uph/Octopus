# Claude Code — Setup portable (Octopus)

> Cómo dejar Claude Code listo en otro PC tras clonar el repo. No incluye secretos. Ver también `PORTABLE_CONTEXT.md` y `AI_WORKFLOW.md`.

---

## Qué viaja con el repo y qué no

- **NO viaja automáticamente:** los plugins/MCPs instalados localmente en Claude Code. Viven en la config del usuario (`~/.claude.json`, `~/.claude/plugins/...`), fuera del repo. Hay que reinstalarlos en cada PC.
- **SÍ viaja:** el contexto del proyecto, porque está versionado en `docs/architecture/` y `docs/development_guidelines/`. Clonar el repo recupera todo el planning, decisiones, roadmap, issues y reglas.
- **SÍ viaja (no secreto):** `.claude/settings.json`, `.claude/commands/`, `.mcp.example.json`.

---

## Dependencias del sistema (Kali / Debian)

```bash
sudo apt update
sudo apt install -y nodejs npm
node -v
npm -v
npx -v
```

> **Nota:** Context7 necesita `npx`. Si Context7 falla con `ENOENT`, falta `npm`/`npx` — instálalos con el comando de arriba y vuelve a probar.

---

## Plugins recomendados

| Plugin | Para qué |
|--------|----------|
| **Caveman** | Comunicación comprimida (ahorra tokens). |
| **Superpowers** | Disciplina de trabajo issue-by-issue, planes, TDD, verificación. |
| **Context7** | Documentación actualizada de librerías bajo demanda (requiere `npx`). |

### Comandos de instalación

```
/plugin install superpowers@claude-plugins-official
/plugin install context7@claude-plugins-official
/reload-plugins
/mcp
```

> Caveman se instaló desde su marketplace propio. Si no está disponible, omítelo — no es bloqueante para el desarrollo.

---

## Troubleshooting

- `/mcp` muestra el estado de los MCPs, incluidos los fallidos.
- **Context7 `ENOENT`** → falta `npm`/`npx`. Instala Node (sección dependencias) y `/reload-plugins`.
- Tras instalar o cambiar plugins: `/reload-plugins`.
- Si un MCP queda "failed", revisa que su binario/cmd exista en el PATH del sistema.

---

## Qué NO commitear (seguridad)

- `.env` y `.env.*`
- tokens, credenciales, claves privadas
- `~/.claude.json` (config de usuario, fuera del repo de todos modos)
- `.mcp.json` **si contiene secretos** (usar `.mcp.example.json` para el ejemplo)
- cualquier clave/keystore

## Qué SÍ commitear

- `docs/` (todo el contexto del proyecto)
- `.claude/settings.json` (si no contiene secretos)
- `.claude/commands/` (comandos reutilizables)
- `.mcp.example.json` (plantilla sin secretos)
- scripts de bootstrap seguros, si se crean

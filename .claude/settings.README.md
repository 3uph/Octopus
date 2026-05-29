# .claude/settings.json — notas

Configuración **project-scoped** para Claude Code. Sin secretos, sin rutas absolutas personales.

## defaultMode: dontAsk

`dontAsk` permite trabajar sin pedir confirmación constante en operaciones normales de desarrollo (leer archivos, escribir código, ejecutar tests, git status, etc.). Esto agiliza el flujo issue-by-issue sin interrupciones en operaciones seguras.

**No usar `bypassPermissions` en este proyecto.** Ese modo desactiva todas las protecciones, incluidas las de `deny`. `dontAsk` solo elimina las confirmaciones; las reglas `deny` siguen activas.

## Reglas deny (siempre bloqueadas)

Las siguientes operaciones están bloqueadas **permanentemente**, independientemente del `defaultMode`:

### Privilegios y destructivos
- `sudo` — sin escalada de privilegios
- `rm -rf` — sin borrado recursivo forzado

### Herramientas ofensivas de recon (bloqueo total)
- `nmap`, `masscan`, `naabu` — port scanning
- `nuclei` — vulnerability scanning
- `subfinder`, `assetfinder`, `amass`, `dnsx` — subdomain enumeration
- `httpx` — HTTP probing
- `ffuf`, `feroxbuster` — fuzzing
- `katana` — crawling activo
- `gau`, `waybackurls` — URL harvesting activo
- `gowitness` — screenshots
- `trufflehog`, `gitleaks` — secret scanning
- `arjun` — parameter discovery

### Lectura de secretos
- `.env`, `.env.*` — variables de entorno
- `*.pem`, `*.key`, `*.keystore` — certificados y claves
- `id_rsa`, `id_ed25519` — claves SSH

## Lo que NO está bloqueado (flujo normal de dev)

Leer código, escribir archivos, ejecutar `pytest`, `git status`, `docker compose`, `python`, `pip`, etc. — todo funciona sin confirmación.

## Cambiar esta configuración

Si necesitas ajustar permisos, edita este archivo y ejecuta `/doctor` para validar. No elimines reglas de `deny` sin motivo explícito. No uses `bypassPermissions`.

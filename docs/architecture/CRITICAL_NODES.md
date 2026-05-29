# Nodos Críticos — Proyecto Octopus

> Tres issues son nodos reutilizados por casi todo el sistema. Concentran el riesgo de seguridad y de arquitectura. Requieren la mayor inversión en tests y una política de bloqueo estricta.

---

## OCT-026 · Scope Gate (`modules/scope_gate/`)

### Por qué es crítico
Servicio central por el que pasa **toda** ejecución de herramientas. Valida cada target contra in-scope / out-of-scope / reglas del programa. Es la pieza de seguridad #1: un fallo aquí significa tocar objetivos fuera de scope — el peor fallo posible de la herramienta.

### Qué tests requiere
- Dado `(target, program)` devuelve `in | out | ambiguous | blocked` correctamente.
- Out-of-scope **explícito** = bloqueo duro (nunca ejecutable).
- Wildcards y subdominios resueltos correctamente contra el scope.
- Casos ambiguos → `requires_review`, nunca asumidos como permitidos.
- Targets que intentan eludir el gate (variaciones de dominio, IDN/punycode, mayúsculas, espacios, IPs vs dominios) → bloqueados o marcados.
- Cobertura alta obligatoria (es el nodo con prioridad de tests #1).

### Qué NO se permite hasta que esté cubierto
- **No habilitar ninguna ejecución real de herramientas** (OCT-030 y posteriores) hasta que Scope Gate tenga tests fuertes y aprobados.
- Ningún tool runner puede ejecutarse sin pasar por el Scope Gate.
- Intelligence no puede promover hallazgos a target activo sin Scope Gate + confirmación humana (OCT-035).

---

## OCT-021 · Base ToolRunner (`tool_runners/base/`)

### Por qué es crítico
Clase base de la que hereda **todo** runner de herramienta externa. Concentra la defensa contra command injection. Toda invocación de binario pasa por aquí. Un fallo = ejecución arbitraria de comandos.

### Qué tests requiere
- **Tests de inyección**: `;`, `&&`, `|`, `$(...)`, backticks, `> /etc/...`, espacios, saltos de línea, unicode/IDN → todos rechazados o neutralizados.
- Allowlist de binarios: binario no listado → error, nunca ejecuta.
- Sanitización por tipo de target (dominio/IP/URL/CIDR) con regex estricta.
- Verificación de que **nunca** se usa `shell=True`.
- Args construidos siempre como **lista**, no string.
- Timeouts y límite de tamaño de output aplicados.

### Qué NO se permite hasta que esté cubierto
- **No habilitar ninguna ejecución real de herramientas** hasta que ToolRunner base tenga tests fuertes y aprobados.
- Ningún runner concreto (subfinder, httpx, nuclei, etc.) se implementa antes de que la base esté validada.

---

## OCT-050 · AI base (`modules/ai/`)

### Por qué es crítico
Punto único de contacto con LLMs (local o externo). Concentra el riesgo de fuga de datos sensibles a proveedores externos. Reutilizado por scope parser (OCT-024), intelligence (OCT-036), JS analysis (OCT-073) y reporting (OCT-122).

### Qué tests requiere
- **Redacción de secrets** antes de enviar a LLM externo: tokens, API keys, credenciales, PII sensible → eliminados del input.
- Provider intercambiable (local Ollama / API externa) sin cambiar el código que lo consume.
- Aviso explícito cuando se envía a proveedor externo.
- `AIAnalysis` registra tokens/coste y marca `human_reviewed=false`.
- Degradación limpia si el LLM no está disponible.
- La IA **nunca** decide scope, ataca, ni genera output accionable sin marca de revisión.

### Qué NO se permite hasta que esté cubierto
- Ningún módulo invoca un LLM directamente; todo pasa por `modules/ai/`.
- No habilitar envío a proveedor externo sin la capa de redacción probada.
- No usar salida de IA como decisión automática de scope o target.

---

## Regla transversal

> **OCT-026 (Scope Gate) y OCT-021 (ToolRunner base) deben tener tests fuertes y aprobados ANTES de permitir cualquier ejecución real de herramientas.** Sin esa cobertura, el recon real (OCT-030+) queda bloqueado.

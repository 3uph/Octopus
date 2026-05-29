# ADR-005 — IA: provider LLM abstracto e intercambiable

**Estado:** Aprobado  
**Fecha:** 2026-05-29

## Decisión

El módulo de IA (`modules/ai/`) usa una **abstracción de provider** intercambiable entre LLM local (Ollama/llama.cpp) y API externa (Anthropic/OpenAI). La elección concreta se configura por `.env`, no hardcodeada.

## Contexto

Se quiere usar IA como copiloto pero sin obligar a enviar datos a un proveedor externo. Privacidad configurable.

## Razón

- Privacidad: datos sensibles de clientes no deben ir a APIs externas sin configuración explícita.
- Flexibilidad: puede empezar con Ollama local y escalar a API externa si es necesario.
- Testabilidad: un provider mock permite tests sin LLM real.

## Consecuencias

- Interface `LLMProvider` en `modules/ai/providers/`.
- Implementaciones: `OllamaProvider`, `AnthropicProvider`, `MockProvider` (tests).
- Selección por variable de entorno `LLM_PROVIDER` en `.env`.
- **Redacción de secrets obligatoria antes de enviar datos a proveedor externo.**
- Prompts versionados en `prompts/` como archivos, nunca inline en código.
- IA nunca decide scope, nunca lanza ataques, nunca genera reportes finales sin revisión humana.

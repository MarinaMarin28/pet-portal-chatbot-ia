# Instrucciones de trabajo — Pet Portal Chatbot IA

Este documento define el flujo de trabajo **antes de comenzar cualquier feature** y el
protocolo de **commit/push**. Es vinculante para personas y agentes de IA.

## Flujo obligatorio al iniciar un feature

1. **Actualizar la rama principal:** ejecutar `git pull` de la rama `main`.
2. **Crear la rama de trabajo** con la estructura:
   ```
   feature/TP_<descripcion>
   ```
   - `<descripcion>` es una descripción corta del feature (separada por guiones bajos o guiones, en minúsculas).
   - Ejemplo: `feature/TP_chatbot_precios` o `feature/TP-chatbot-fixes`.
3. Implementar el cambio respetando las convenciones del repositorio
   (ver `AGENTS.md` y `README.md`).

## Antes de hacer commit

- **Preguntar siempre al usuario** si quiere hacer commit y push.
  No commitear ni pushear sin confirmación explícita.
- Antes de commitear, revisar:
  - `git status` (solo archivos intencionales, sin secretos en `.env`),
  - `git diff` (revisar el alcance real del cambio).
- Validar el cambio:
  - Chatbot: `python -m py_compile main.py director.py catalog.py llm.py prompts.py config.py`.

## Mensaje de commit

El mensaje de commit debe usar la estructura:

```
TP:<descripcion de los cambios>
```

- `<descripcion de los cambios>` describe qué se hizo, en presente, conciso.
- Ejemplo: `TP:corrige modelo de Ollama y quita el guau de los mensajes de error`.
- Si hay detalles adicionales, se agregan como cuerpo después de la primera línea (separado por línea en blanco).

## Push

- Al hacer push se envía la rama `feature/TP_<descripcion>` (no `main`) al remoto.
- No mezclar ni forzar push sin autorización explícita.

## Regla general

**Nunca** commitar, pushear, ni crear pull requests sin que el usuario lo pida o confirme.
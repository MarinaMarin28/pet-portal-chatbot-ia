# Propósito

Este repositorio contiene el microservicio **Chatbot de Pet Portal**, el asistente
virtual que orienta a los clientes de la clínica veterinaria (especialidades,
horarios, productos, centros y turnos) y deriva consultas libres a un modelo de
lenguaje local vía Ollama.

Este documento define cómo trabajar en el proyecto de forma consistente y segura.
Aplica tanto a personas como a agentes de IA que colaboren en la base de código.

## Alcance del proyecto

El microservicio está construido con Python, FastAPI, LangChain y Ollama.

Convenciones principales:

- El código fuente vive en la raíz del repositorio (`main.py`, `director.py`,
  `catalog.py`, `llm.py`, `prompts.py`, `config.py`).
- La conversación la orquesta `director.py` (opciones y datos deterministas); el
  LLM solo participa en la clasificación de intención de consultas libres.
- El catálogo de datos (especialidades, horarios, productos, centros) se consulta
  bajo demanda al backend NestJS vía `GET /chat/catalogo` (dueño de la BD).
- Toda la copy y los prompts viven en `prompts.py`, separados de la lógica.
- La configuración sensible vive en `.env` (no versionado); `.env.example` es la
  plantilla versionada.
- No existe runner de tests en este proyecto: la validación mínima es la compilación
  del código y un smoke test levantando el servidor.

## Orden de lectura obligatorio

Antes de ejecutar cambios o proponer una solución, el agente debe leer en este orden:

1. `AGENTS.md`
2. `INSTRUCCIONES.md` (flujo de trabajo y protocolo de commit/push)
3. `README.md` (stack, versiones y setup desde cero)
4. Los archivos afectados (`director.py`, `prompts.py`, `catalog.py`, `llm.py`,
   `config.py`, `main.py`)

Si un archivo requerido no existe, el agente debe trabajar solo con el contexto
disponible y no asumir información faltante.

## Estructura del proyecto

```text
.
├── main.py          # App FastAPI: POST /api/v1/chat y POST /api/v1/chat-libre
├── director.py      # Orquestador híbrido: clasifica intención y arma la respuesta
├── catalog.py       # Cliente HTTP del catálogo del backend (GET /chat/catalogo)
├── llm.py           # Instancia del modelo local vía Ollama (LangChain)
├── prompts.py       # Copy del flujo guiado y prompts del clasificador
├── config.py        # Lectura de configuración desde variables de entorno
├── requirements.txt # Dependencias pines
├── .env.example     # Plantilla de configuración (versionada)
└── .env             # Configuración local (NO versionada)
```

Responsabilidades por área:

- `main.py`: define los endpoints `POST /api/v1/chat` (orquestado) y
  `POST /api/v1/chat-libre` (respaldo directo al modelo). Es el contrato con el
  frontend y con el backend NestJS.
- `director.py`: decide la intención del usuario (LLM con fallback por palabras
  clave), consulta el catálogo según la intención y devuelve una respuesta
  estructurada (`mensaje`, `tipo`, `opciones`, `acciones`, `datos`, `url`,
  `guardarConsulta`) que el front renderiza como burbujas, chips o acciones.
- `catalog.py`: cliente HTTP del catálogo del backend. Consulta bajo demanda
  `especialidades`, `horarios` (con `especialidad`), `productos` y `centros`.
  Ante errores o respuestas no `200`, devuelve `[]` y registra la advertencia.
- `llm.py`: instancia del modelo local vía Ollama (LangChain), con temperatura baja
  para respuestas más precisas en el flujo guiado.
- `prompts.py`: textos del flujo guiado (saludo, menú, especialidades, horarios,
  productos, centros, turnos, fallbacks) y el prompt del clasificador de intención.
- `config.py`: carga `.env` con `python-dotenv` y expone `IP_PC_LINUX`,
  `OLLAMA_PORT`, `MODEL_NAME`, `OLLAMA_URL`, `BACKEND_API_URL`, `CHATBOT_TOKEN`,
  `APP_HOST` y `APP_PORT`.

## Principios de trabajo

- Preferir cambios pequeños, verificables y de bajo riesgo.
- Entender el flujo existente antes de modificarlo.
- Evitar abstracciones innecesarias.
- No romper el contrato de los endpoints (`/api/v1/chat` y `/api/v1/chat-libre`)
  ni el formato de la respuesta estructurada sin justificación.
- No hardcodear textos ni prompts dentro de la lógica de orquestación: viven en
  `prompts.py`.
- No inventar recursos, intenciones ni flujos que no estén definidos en los
  archivos de contexto.

## Reglas para agentes de IA

Los agentes deben:

- Trabajar con contexto local, no con suposiciones amplias.
- Modificar solo lo necesario para resolver el objetivo.
- Mantener trazables las decisiones importantes.
- Explicar brevemente qué cambió, por qué cambió y cómo se validó.

Los agentes no deben:

- Reestructurar todo el proyecto sin necesidad.
- Agregar dependencias nuevas sin una razón clara y sin actualizar
  `requirements.txt`.
- Mezclar refactors amplios con cambios funcionales.
- Asumir archivos, módulos o flujos que no existen en el repositorio.

## Convenciones técnicas

### Python

- Tipar explícitamente funciones e interfaces públicas (hints).
- Evitar `Any` salvo justificación clara.
- Mantener consistencia con el estilo del proyecto (nombres en español para
  funciones de dominio, mensajes en español).
- Mantener `from __future__ import annotations` donde se use tipado diferido.

### LLM / Ollama

- `llm.py` centraliza la instancia del modelo; no crear instancias nuevas en otros
  archivos.
- Los prompts viven en `prompts.py` y son versionables.
- La salida del modelo se trata como entrada no confiable: el clasificador valida
  la intención contra un conjunto conocido antes de usarla.
- Todo flujo con LLM debe tener fallback determinista (por ejemplo, palabras clave).

### Catálogo

- El chatbot consulta los datos al backend, nunca accede a la BD directamente.
- Ante cualquier error de catálogo se devuelve `[]` y el director muestra el
  mensaje de fallback correspondiente.

## Validación mínima esperada

Antes de considerar un cambio como terminado:

- Ejecutar la validación más pequeña que confirme el comportamiento tocado.
- Compilar los archivos: `python -m py_compile main.py director.py catalog.py llm.py prompts.py config.py`.
- Si el cambio toca el servidor, levantar un smoke test:
  `uvicorn main:app --host 127.0.0.1 --port 8001` y verificar que responde.

## Límites y cautelas

- No asumir componentes que todavía no están implementados.
- No documentar como existente algo que solo está planificado.
- No introducir infraestructura de IA antes de definir el caso de uso y su contrato.
- No mezclar bases documentales con decisiones de implementación temporales.

## Nota final

Este archivo debe evolucionar con el proyecto. Si el microservicio agrega nuevos
endpoints, intenciones, recursos de catálogo o capas de IA, actualizar este
documento para reflejar la arquitectura real.
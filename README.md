# Pet Portal Chatbot IA

Microservicio de IA del proyecto Pet Portal. Su objetivo es actuar como asistente virtual del centro veterinario para responder consultas sobre especialidades, horarios, productos, centros de atención, vacunación y flujo de turnos, con un diseño guiado y con respaldo de datos del backend.

## Objetivo del servicio

El chatbot está diseñado para:

- orientar al usuario sobre servicios y catálogo del negocio,
- responder de forma estructurada y no libre en flujos deterministas,
- colaborar con el frontend y con el backend para completar reservas o derivaciones,
- usar LLM local para clasificar intenciones y apoyar casos de consulta libre.

## Arquitectura de solución

```text
Frontend React
   |
   v
Backend NestJS (pet-portal-api)
   |
   +--> /chat/catalogo   (catálogo del negocio)
   +--> /chat/interaccionar (puente de mayor nivel)
   |
   v
Chatbot FastAPI (este repositorio)
   |-- main.py          # API de entrada
   |-- director.py      # orquestador y flujo guiado
   |-- catalog.py       # cliente del backend
   |-- llm.py           # integración con Ollama / LangChain
   |-- prompts.py       # copy, prompts y mensajes del asistente
   |
   +--> Ollama local (LLM)
```

## Componentes clave

- `main.py`: expone `POST /api/v1/chat` y `POST /api/v1/chat-libre`
- `director.py`: orquesta la conversación, identifica intención y guía el flujo de turnos
- `catalog.py`: consulta `GET /chat/catalogo` del backend para obtener especialidades, horarios, productos y centros
- `llm.py`: conecta LangChain con Ollama usando un modelo local
- `prompts.py`: centraliza la copy y los prompts del flujo guiado
- `config.py`: configuración desde variables de entorno

## Stack y dependencia de IA

- Python 3.11+
- FastAPI
- Uvicorn
- LangChain Core / Community
- Pydantic
- httpx
- Ollama
- modelo recomendado: `qwen3:1.7b`

El diseño es híbrido:

- flujo guiado determinista para opciones de negocio,
- LLM usado con baja temperatura para clasificación y respaldo de consultas abiertas,
- backend como fuente de verdad del catálogo.

## AI engineering y orquestación

Este repositorio implementa un patrón de orquestación del tipo:

1. el usuario escribe una consulta,
2. el backend y el frontend la envían al chatbot por medio de `POST /api/v1/chat`,
3. el `director.py` decide si la intención es especialidad, producto, centro, cronograma o reserva,
4. el servicio consulta el catálogo del backend,
5. devuelve una respuesta estructurada a la UI para renderizar chips, redirecciones o mensajes,
6. si el caso es libre o ambiguo, usa LLM para clasificación.

Es importante destacar que el microservicio no es un almacén de negocio ni una capa de persistencia: está diseñado como un orquestador del flujo conversacional, con contexto y herramienta/comunicación sobre datos ya gobernados por el backend.

## MCP / herramientas / servidores

El repositorio refleja una arquitectura orientada a herramientas y contexto, aunque no define un servidor MCP formal completo en la entrega actual. En términos del Trabajo Práctico, la intención es que el componente de IA actúe como una capa de orquestación sobre datos del negocio y servicios externos, con un enfoque compatible con un modelo MCP-like.

En la práctica del proyecto se observa lo siguiente:

- catálogo de negocio consumido desde backend (`/chat/catalogo`),
- flujo de herramientas de negocio y contexto dentro del director,
- uso de LLM local para clasificación y respuesta en lenguaje natural,
- posibilidad de ampliarse con herramientas externas (por ejemplo, servicios complementarios de agenda o integración con terceros) a través de la misma capa de orquestación.

La implementación actual es sólida para el curso, pero no debe presentarse como un despliegue formal de dos servidores MCP externos completos si no existe evidencia de ejecución directa de esos servicios dentro del repositorio.

## Endpoints principales

```http
POST /api/v1/chat
POST /api/v1/chat-libre
```

Respuesta esperada del endpoint principal:

```json
{
  "mensaje": "string",
  "tipo": "inicio | opciones | informacion | error | autenticacion | redireccion | texto_libre",
  "opciones": ["string"],
  "acciones": [{ "etiqueta": "string", "url": "string", "accion": "string" }],
  "datos": [],
  "url": null,
  "guardarConsulta": false
}
```

## Variables de entorno

```env
IP_PC_LINUX=
OLLAMA_PORT=11434
MODEL_NAME=qwen3:1.7b
BACKEND_API_URL=http://localhost:8080
CHATBOT_TOKEN=
APP_HOST=0.0.0.0
APP_PORT=8001
```

## Setup rápido

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Iniciar Ollama
ollama serve
ollama pull qwen3:1.7b

# Ejecutar servicio
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Verificación rápida

```bash
curl http://localhost:8001/docs
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "", "opcion": "inicio"}'
```

## Estado de cumplimiento con el TP

Este microservicio cumple con la expectativa general del Trabajo Práctico en cuanto a:

- IA orientada a negocio,
- orquestación con LangChain + Ollama,
- uso de contexto y flujo guiado,
- integración con backend y app frontend,
- documentación técnica y funcional.

La principal brecha no es técnica sino de cierre documental: debe definirse explícitamente qué parte del funcionamiento es determinista, qué parte es inferencia de IA, y qué parte todavía requiere validación funcional como caso de uso final.

## Conclusión

El chatbot de Pet Portal tiene una base muy clara para cumplir con la propuesta del TP: combina orquestación, contexto del negocio, LLM local y flujo guiado con una experiencia útil para clientes y personal. La principal tarea restante es cerrar la narrativa documental y dejar explícita la diferencia entre lo que está resuelto, lo que está parcialmente validado y lo que se deja como trabajo futuro.

# pet-portal-chatbot-ia

Microservicio **Chatbot de Pet Portal**: asistente virtual del centro médico
veterinario que orienta a los clientes sobre especialidades, horarios, productos,
centros de atención y turnos, y deriva consultas libres a un modelo de lenguaje
local vía Ollama.

El chatbot no accede a la base de datos: consulta el catálogo bajo demanda al
backend NestJS (`pet-portal-api`) mediante el endpoint interno
`GET /chat/catalogo`, y el frontend (`pet-portal-front`) lo consume a través del
backend (`POST /chat/interaccionar`), que actúa como puente hacia
`POST /api/v1/chat` de este microservicio.

## Arquitectura

```
Frontend (React)  -->  Backend NestJS (pet-portal-api)  -->  Chatbot (este repo)
                                                              |      |
                                                              v      v
                                                     Catálogo (BD)  Ollama (LLM local)
```

- `main.py`: app FastAPI con `POST /api/v1/chat` (orquestado) y `POST /api/v1/chat-libre` (respaldo).
- `director.py`: orquestador híbrido. Clasifica la intención (LLM con fallback por
  palabras clave), consulta el catálogo y devuelve una respuesta estructurada.
- `catalog.py`: cliente HTTP del catálogo del backend (`especialidades`, `horarios`,
  `productos`, `centros`).
- `llm.py`: modelo local vía Ollama (LangChain), temperatura baja.
- `prompts.py`: copy del flujo guiado y prompts del clasificador.
- `config.py`: configuración desde variables de entorno.

## Stack y versiones

| Componente | Versión |
| --- | --- |
| Python | 3.11+ (recomendado) |
| FastAPI | 0.141.1 |
| Uvicorn | 0.52.3 |
| LangChain core | 1.5.5 |
| LangChain community | 0.4.2 |
| LangChain classic | 1.0.8 |
| httpx | 0.28.1 |
| Pydantic | 2.13.4 |
| python-dotenv | 1.2.2 |
| Ollama | última estable (por ejemplo, 0.5.x) |
| Modelo Ollama | `qwen3:1.7b` |

Las dependencias exactas están pines en `requirements.txt`. El proyecto está
pensado para Python 3.11 o superior (los paquetes de IA y numéricos de la lista
de dependencias lo requieren).

## Prerequisitos

1. **Backend NestJS corriendo** en `http://localhost:8080` (o ajustar
   `BACKEND_API_URL`), con el endpoint `GET /chat/catalogo` disponible.
2. **Ollama instalado y corriendo**, con el modelo `qwen3:1.7b` descargado:

   ```bash
   # instalar Ollama (Linux/Windows/macOS): https://ollama.com
   ollama serve
   ollama pull qwen3:1.7b
   ```

   El chatbot se conecta a Ollama en `IP_PC_LINUX:OLLAMA_PORT` (por defecto
   `127.0.0.1:11434`). Si Ollama corre en otra máquina de la red, indicar su IP.

## Setup desde cero

```bash
# 1. Entorno virtual e instalación de dependencias
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# 2. Configuración
cp .env.example .env
# Editar .env:
#   IP_PC_LINUX=127.0.0.1          # IP de la máquina donde corre Ollama
#   OLLAMA_PORT=11434
#   MODEL_NAME=qwen3:1.7b          # debe coincidir con un modelo descargado en Ollama
#   BACKEND_API_URL=http://localhost:8080
#   CHATBOT_TOKEN=<token igual al CHATBOT_TOKEN del backend pet-portal-api>
#   APP_HOST=0.0.0.0
#   APP_PORT=8001

# 3. Levantar el servidor
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

> **Importante:** `CHATBOT_TOKEN` debe ser el **mismo valor** que el `CHATBOT_TOKEN`
> configurado en `pet-portal-api` (en `.env.local` para desarrollo). Si no
> coinciden, el catálogo responde `401` y el chatbot muestra mensajes de
> "no cargamos especialidades/productos".

## Variables de entorno (`.env.example`)

| Variable | Default | Descripción |
| --- | --- | --- |
| `IP_PC_LINUX` | `127.0.0.1` | IP de la máquina donde corre Ollama |
| `OLLAMA_PORT` | `11434` | Puerto de Ollama |
| `MODEL_NAME` | `qwen3:1.7b` | Modelo de Ollama a usar |
| `BACKEND_API_URL` | `http://localhost:8080` | URL del backend NestJS |
| `CHATBOT_TOKEN` | *(vacío)* | Token compartido con el backend para `GET /chat/catalogo` |
| `APP_HOST` | `0.0.0.0` | Host del servidor del chatbot |
| `APP_PORT` | `8001` | Puerto del servidor del chatbot |

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/chat` | Endpoint principal, orquestado. Devuelve respuesta estructurada para el front. |
| `POST` | `/api/v1/chat-libre` | Respaldo (sin orquestación): usa el modelo directo con contexto. |

La respuesta de `/api/v1/chat` tiene la forma:

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

## Verificación rápida

```bash
curl http://localhost:8001/docs          # Swagger UI
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "", "opcion": "inicio"}'
```

## Convenciones

- La copy y los prompts viven en `prompts.py`.
- El catálogo se consulta al backend; nunca acceder a la BD directamente.
- No hay runner de tests: validar con `python -m py_compile *.py` y un smoke test.
- Flujo de trabajo y commit/push: ver `INSTRUCCIONES.md`.
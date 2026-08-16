from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import APP_HOST, APP_PORT
from director import procesar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

app = FastAPI(title="Microservicio Chatbot Pet Portal")


class MensajeHistorial(BaseModel):
    rol: str
    contenido: str


class ChatPayload(BaseModel):
    sesionId: str | None = None
    mensaje: str = ""
    opcion: str | None = None
    especialidadId: str | None = None
    historial: list[MensajeHistorial] = []
    usuarioLogueado: bool = False


class ChatLibrePayload(BaseModel):
    mensaje: str
    contexto: str = ""


@app.post("/api/v1/chat")
async def chat(payload: ChatPayload):
    """Endpoint principal: el chatbot dirige la conversación y devuelve una
    respuesta estructurada (mensaje, tipo, opciones, acciones, datos) para que
    el front la renderice. Lo consume el backend NestJS."""
    try:
        historial = [
            {"rol": m.rol, "contenido": m.contenido} for m in payload.historial
        ]
        return await procesar(
            {
                "sesionId": payload.sesionId,
                "mensaje": payload.mensaje,
                "opcion": payload.opcion,
                "especialidadId": payload.especialidadId,
                "historial": historial,
                "usuarioLogueado": payload.usuarioLogueado,
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error procesando chat: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudo procesar el mensaje")


@app.post("/api/v1/chat-libre")
async def chat_libre(payload: ChatLibrePayload):
    """Endpoint de respaldo (sin orquestación). Mantiene compatibilidad con
    versiones anteriores que pasaban contexto y usaban el modelo directo."""
    from langchain_core.prompts import ChatPromptTemplate

    from llm import llm

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Sos el asistente virtual (un perrito amigable) de una clínica veterinaria.\n"
            "Para responder con total precisión, usá ÚNICAMENTE la siguiente información oficial:\n"
            "---------------------\n"
            "{contexto_clinica}\n"
            "---------------------\n"
            "Reglas estrictas:\n"
            "1. Respondé de forma corta (máximo 3 oraciones), alegre, empática y profesional en español.\n"
            "2. Si la respuesta NO se encuentra en la información oficial, decilo con amabilidad "
            "y ofrecé que un humano se contactará."
        )),
        ("user", "{mensaje_cliente}"),
    ])
    try:
        cadena = prompt | llm
        respuesta = await cadena.ainvoke({
            "mensaje_cliente": payload.mensaje,
            "contexto_clinica": payload.contexto or "(sin información adicional)",
        })
        return {"respuesta": respuesta}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error en chat-libre: %s", exc)
        return {
            "respuesta": "¡Guau! Me cuesta conectar con mi cerebro, intenta de nuevo."
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
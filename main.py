import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
import uvicorn

load_dotenv()

app = FastAPI(title="Microservicio Chatbot con Contexto")

IP_PC_LINUX = os.getenv("IP_PC_LINUX", "127.0.0.1")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b")
OLLAMA_URL = f"http://{IP_PC_LINUX}:{OLLAMA_PORT}"

# Inicializamos el modelo
llm = Ollama(base_url=OLLAMA_URL, model=MODEL_NAME, temperature=0.3) # Bajamos la temperatura para que sea más preciso

# 2. Modificamos el Prompt para que acepte un bloque de CONTEXTO real
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "Sos el asistente virtual (un perrito amigable) de una clínica veterinaria.\n"
        "El usuario seleccionó la opción 'Otros' para hacer una consulta general.\n"
        "Para responder con total precisión, utilizá ÚNICAMENTE la siguiente información oficial de la clínica:\n"
        "---------------------\n"
        "{contexto_clinica}\n"
        "---------------------\n"
        "Reglas estrictas:\n"
        "1. Responde de forma corta (máximo 3 oraciones), alegre, empática y profesional en español.\n"
        "2. Si la respuesta NO se encuentra en la información oficial provista, dile amablemente que no tenés esa información exacta y que un humano se contactará con él."
    )),
    ("user", "{mensaje_cliente}")
])

chain = prompt | llm

# 3. Ampliamos el modelo de datos para recibir el contexto desde NestJS
class ChatPayload(BaseModel):
    mensaje: str
    contexto: str # <-- Nuevo campo obligatorio opcional

@app.post("/api/v1/chat-libre")
async def procesar_chat_libre(payload: ChatPayload):
    try:
        # Ejecutamos LangChain inyectando el mensaje y el contexto real
        respuesta_ia = chain.invoke({
            "mensaje_cliente": payload.mensaje,
            "contexto_clinica": payload.contexto
        })
        return {"respuesta": respuesta_ia}
        
    except Exception as e:
        print(f"Error en LangChain: {e}")
        return {"respuesta": "¡Guau! Me cuesta conectar con mi cerebro, intenta de nuevo."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

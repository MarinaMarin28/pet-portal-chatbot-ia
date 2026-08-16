import os
from dotenv import load_dotenv

load_dotenv()

IP_PC_LINUX = os.getenv("IP_PC_LINUX", "127.0.0.1")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:1.7b")
OLLAMA_URL = f"http://{IP_PC_LINUX}:{OLLAMA_PORT}"

# URL del backend NestJS (dueño de la BD) al que el chatbot consulta el catálogo.
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8080")
# Token compartido para el endpoint interno de catálogo (X-Chatbot-Token).
CHATBOT_TOKEN = os.getenv("CHATBOT_TOKEN", "")

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8001"))
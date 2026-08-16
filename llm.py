from config import OLLAMA_URL, MODEL_NAME
from langchain_community.llms import Ollama

# Modelo local vía Ollama. Temperatura baja para respuestas más precisas y
# menos inventiva en el flujo guiado.
llm = Ollama(base_url=OLLAMA_URL, model=MODEL_NAME, temperature=0.2)
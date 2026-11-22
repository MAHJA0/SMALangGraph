"""Configuración central del modelo y de los parámetros del tutor."""

from langchain_ollama import ChatOllama

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen3:8b"   # para desarrollo; cambiar a qwen3:8b al evaluar calidad
TEMPERATURE = 0.3
NUM_CTX = 8192
KEEP_ALIVE = "10m"
MAX_ATTEMPTS = 2          # intentos de refuerzo (se usa en la Etapa 5)
DOMAIN_THRESHOLD = 70     # calificación mínima para considerar dominio (Etapa 5)


def get_model(temperature: float = TEMPERATURE, modelo: str = MODEL_NAME) -> ChatOllama:
    """Devuelve el modelo de chat local configurado para el tutor."""
    return ChatOllama(
        model=modelo,
        base_url=OLLAMA_URL,
        temperature=temperature,
        num_ctx=NUM_CTX,
        keep_alive=KEEP_ALIVE,
    )
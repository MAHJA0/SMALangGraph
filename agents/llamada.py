"""Llamada común al modelo: prompt de sistema más mensaje del usuario."""

import re

from langchain_core.messages import HumanMessage, SystemMessage

_BLOQUE_RAZONAMIENTO = re.compile(r"<think>.*?</think>", re.DOTALL)
_RAZONAMIENTO_SIN_APERTURA = re.compile(r"^.*?</think>", re.DOTALL)


def limpiar_razonamiento(texto: str) -> str:
    """Quita el razonamiento interno del modelo, con o sin etiqueta de apertura."""
    texto = _BLOQUE_RAZONAMIENTO.sub("", texto)
    if "</think>" in texto:
        texto = _RAZONAMIENTO_SIN_APERTURA.sub("", texto, count=1)
    return texto.strip()


def invocar(model, sistema: str, usuario: str) -> str:
    """Pide una respuesta al modelo y devuelve solo el texto final, sin razonamiento interno."""
    mensajes = [SystemMessage(content=sistema), HumanMessage(content=usuario)]
    respuesta = model.invoke(mensajes)
    texto = respuesta.content if isinstance(respuesta.content, str) else str(respuesta.content)
    return limpiar_razonamiento(texto)
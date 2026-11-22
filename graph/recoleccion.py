"""Nodos sin LLM para recoger las respuestas del estudiante.

Las respuestas vacías se aceptan: se marcan como "(sin respuesta)" y el evaluador las puntúa con 0.
"""

import re

from langgraph.types import interrupt

from state import TutorState

SIN_RESPUESTA = "(sin respuesta)"
_PATRON_PREGUNTA = re.compile(r"^\s*\d+[.)]\s+(.+)$", re.MULTILINE)


def dividir_preguntas(texto: str) -> list[str]:
    """Separa el texto del examinador en una lista, una pregunta por elemento.

    Si no encuentra preguntas numeradas, devuelve el texto completo como una sola pregunta.
    """
    preguntas = [p.strip() for p in _PATRON_PREGUNTA.findall(texto)]
    if not preguntas and texto.strip():
        return [texto.strip()]
    return preguntas


def formatear_respuestas(respuestas: list[str]) -> str:
    """Numera las respuestas y marca las vacías, para que el evaluador las vea claramente."""
    return "\n".join(
        f"{i}. {r.strip() or SIN_RESPUESTA}" for i, r in enumerate(respuestas, start=1)
    )


def recolectar_respuestas(state: TutorState) -> dict:
    """Pausa el grafo y espera una respuesta por pregunta; cualquiera puede quedar vacía.

    Este nodo se vuelve a ejecutar al reanudar, así que no llama al modelo
    ni escribe nada antes del interrupt.
    """
    preguntas = dividir_preguntas(state.get("questions", ""))

    recibidas = interrupt({"preguntas": preguntas})

    if not isinstance(recibidas, list):
        recibidas = [str(recibidas)]
    respuestas = [str(r) for r in recibidas][: len(preguntas)]
    respuestas += [""] * (len(preguntas) - len(respuestas))

    return {
        "respuestas": respuestas,
        "student_answers": formatear_respuestas(respuestas),
    }
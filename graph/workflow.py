"""Construcción del grafo de LangGraph del tutor."""

import re

from langgraph.graph import StateGraph, START, END

from agents.evaluador import crear_nodo_evaluador
from agents.examinador import crear_nodo_examinador
from agents.profesor import crear_nodo_profesor
from config.settings import DOMAIN_THRESHOLD, MAX_ATTEMPTS
from graph.recoleccion import recolectar_respuestas
from state import TutorState

_PATRON_PUNTUACION = re.compile(r"Puntuación final:\s*(\d+(?:\.\d+)?)")


def obtener_puntuacion(evaluacion: str) -> float | None:
    """Devuelve la última 'Puntuación final' del texto del evaluador, o None si no existe."""
    coincidencias = _PATRON_PUNTUACION.findall(evaluacion or "")
    return float(coincidencias[-1]) if coincidencias else None


def preparar_refuerzo(state: TutorState) -> dict:
    """Incrementa el contador de refuerzos antes de volver a explicar el tema."""
    return {"intentos": state.get("intentos", 0) + 1}


def decidir_refuerzo(state: TutorState) -> str:
    """Ruta tras la evaluación: refuerzo si no hay dominio y quedan intentos; si no, fin."""
    puntuacion = obtener_puntuacion(state.get("evaluation", ""))
    if puntuacion is None:
        return END  # sin calificación legible no se refuerza
    if puntuacion >= DOMAIN_THRESHOLD:
        return END
    if state.get("intentos", 0) >= MAX_ATTEMPTS:
        return END
    return "preparar_refuerzo"


def build_graph(model, checkpointer):
    """Crea y compila el grafo con ciclo de refuerzo.

    El checkpointer es obligatorio: sin él, las pausas con interrupt no funcionan.
    """
    builder = StateGraph(TutorState)

    builder.add_node("profesor", crear_nodo_profesor(model))
    builder.add_node("examinador", crear_nodo_examinador(model))
    builder.add_node("recolectar_respuestas", recolectar_respuestas)
    builder.add_node("evaluador", crear_nodo_evaluador(model))
    builder.add_node("preparar_refuerzo", preparar_refuerzo)

    builder.add_edge(START, "profesor")
    builder.add_edge("profesor", "examinador")
    builder.add_edge("examinador", "recolectar_respuestas")
    builder.add_edge("recolectar_respuestas", "evaluador")
    builder.add_conditional_edges(
        "evaluador",
        decidir_refuerzo,
        {"preparar_refuerzo": "preparar_refuerzo", END: END},
    )
    builder.add_edge("preparar_refuerzo", "profesor")

    return builder.compile(checkpointer=checkpointer)
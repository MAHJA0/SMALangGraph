"""Pruebas del grafo con modelo falso y checkpointer en memoria (no requieren Ollama)."""

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from graph.workflow import build_graph

CONFIG = {"configurable": {"thread_id": "prueba"}}


def modelo_falso() -> FakeListChatModel:
    """Responde en el orden: profesor, examinador, evaluador."""
    return FakeListChatModel(
        responses=[
            "Explicación falsa.",
            "### PREGUNTAS\n1. P1 larga\n2. P2 larga\n\n### RÚBRICA\nPregunta 1 | x | y | 50",
            "Puntuación final: 80",
        ]
    )


def test_el_grafo_se_pausa_para_pedir_respuestas():
    resultado = build_graph(modelo_falso(), InMemorySaver()).invoke({"topic": "X"}, CONFIG)

    assert "__interrupt__" in resultado
    assert resultado["__interrupt__"][0].value["preguntas"] == ["P1 larga", "P2 larga"]


def test_al_reanudar_con_respuestas_termina_la_evaluacion():
    graph = build_graph(modelo_falso(), InMemorySaver())
    graph.invoke({"topic": "X"}, CONFIG)

    resultado = graph.invoke(Command(resume=["respuesta uno", "respuesta dos"]), CONFIG)

    assert "__interrupt__" not in resultado
    assert resultado["evaluation"] == "Puntuación final: 80"


def test_respuestas_vacias_no_bloquean_la_sesion():
    graph = build_graph(modelo_falso(), InMemorySaver())
    graph.invoke({"topic": "X"}, CONFIG)

    resultado = graph.invoke(Command(resume=["", ""]), CONFIG)

    assert "__interrupt__" not in resultado
    assert resultado["evaluation"] == "Puntuación final: 80"
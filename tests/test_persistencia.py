"""Prueba de persistencia: una sesión pausada sobrevive a cerrar y reabrir la conexión.

No necesita Ollama: usa un grafo mínimo con interrupt.
"""

import sqlite3
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class Estado(TypedDict, total=False):
    valor: str
    respuesta: str


def pedir(state: Estado) -> dict:
    respuesta = interrupt({"preguntas": ["¿Cuál es el valor?"]})
    return {"respuesta": respuesta[0]}


def construir_grafo(checkpointer):
    builder = StateGraph(Estado)
    builder.add_node("pedir", pedir)
    builder.add_edge(START, "pedir")
    builder.add_edge("pedir", END)
    return builder.compile(checkpointer=checkpointer)


def test_sesion_pausada_sobrevive_reinicio(tmp_path):
    ruta = tmp_path / "sesiones.db"
    config = {"configurable": {"thread_id": "sesion-prueba"}}

    # Primera "ejecución del programa": se pausa y se cierra la conexión.
    conexion = sqlite3.connect(ruta, check_same_thread=False)
    grafo = construir_grafo(SqliteSaver(conexion))
    grafo.invoke({"valor": "a"}, config)
    conexion.close()

    # Segunda "ejecución": conexión nueva al mismo archivo.
    conexion = sqlite3.connect(ruta, check_same_thread=False)
    try:
        grafo = construir_grafo(SqliteSaver(conexion))
        assert grafo.get_state(config).next == ("pedir",)

        grafo.invoke(Command(resume=["ok"]), config)

        estado = grafo.get_state(config)
        assert estado.values["respuesta"] == "ok"
        assert estado.next == ()
    finally:
        conexion.close()
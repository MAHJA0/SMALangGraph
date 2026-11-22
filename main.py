"""Punto de entrada del tutor. Etapa 6: sesiones persistentes en SQLite."""

import json
import logging
import sqlite3
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from config.settings import get_model
from graph.workflow import build_graph

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

TEMA_POR_DEFECTO = "Algoritmos de ordenamiento"
RUTA_DB = Path("data") / "sesiones.db"
DIR_PARCIALES = Path("data") / "parciales"


def ruta_parcial(thread_id: str) -> Path:
    """Archivo donde se guardan las respuestas de la ronda en curso, una a una."""
    return DIR_PARCIALES / f"{thread_id}.json"


def cargar_parciales(thread_id: str) -> list[str]:
    ruta = ruta_parcial(thread_id)
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return []


def guardar_parciales(thread_id: str, respuestas: list[str]) -> None:
    DIR_PARCIALES.mkdir(parents=True, exist_ok=True)
    ruta_parcial(thread_id).write_text(json.dumps(respuestas, ensure_ascii=False), encoding="utf-8")


def borrar_parciales(thread_id: str) -> None:
    ruta_parcial(thread_id).unlink(missing_ok=True)


def pedir_respuestas(preguntas: list[str], thread_id: str) -> list[str]:
    """Pide las preguntas una por una y guarda cada respuesta al instante.

    Si la sesión se interrumpe, al reabrirla las respuestas ya escritas se reutilizan
    y solo se piden las que faltan.
    """
    respuestas = cargar_parciales(thread_id)
    print("\n(Si no sabes una pregunta, deja la respuesta en blanco y pulsa Enter.)")
    for numero, pregunta in enumerate(preguntas, start=1):
        print(f"\n{numero}. {pregunta}")
        if numero <= len(respuestas):
            print(f"Tu respuesta (guardada): {respuestas[numero - 1]}")
            continue
        respuestas.append(input("Tu respuesta: ").strip())
        guardar_parciales(thread_id, respuestas)
    return respuestas


def pedir_sesion() -> tuple[str, bool]:
    """Devuelve (thread_id, es_nueva). Enter sin escribir crea una sesión nueva."""
    entrada = input("ID de sesión (Enter para una nueva): ").strip()
    if entrada:
        return entrada, False
    return uuid.uuid4().hex[:8], True


def preguntas_pendientes(graph, config) -> list[str] | None:
    """Si la sesión está pausada esperando respuestas, devuelve sus preguntas."""
    snapshot = graph.get_state(config)
    for tarea in snapshot.tasks:
        for interrupcion in tarea.interrupts:
            return interrupcion.value["preguntas"]
    return None


def main() -> None:
    """Crea o retoma una sesión guardada en SQLite."""
    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(RUTA_DB, check_same_thread=False)

    try:
        graph = build_graph(get_model(), SqliteSaver(conexion))
        thread_id, es_nueva = pedir_sesion()
        config = {"configurable": {"thread_id": thread_id}}
        print(f"\nSesión: {thread_id}")

        try:
            if es_nueva:
                tema = input("Tema a estudiar: ").strip() or TEMA_POR_DEFECTO
                graph.invoke({"topic": tema}, config)
            elif not graph.get_state(config).values:
                print("No existe una sesión con ese ID.")
                return

            estado = graph.get_state(config).values
            print("\n=== Explicación ===")
            print(estado.get("explanation", ""))

            preguntas = preguntas_pendientes(graph, config)
            if preguntas is None and estado.get("evaluation"):
                # Sesión completada: mostrar lo que se respondió y la última evaluación.
                if estado.get("student_answers"):
                    print("\n=== Tus respuestas ===")
                    print(estado["student_answers"])
                print("\n=== Última evaluación ===")
                print(estado["evaluation"])
                return

            # Cada pausa pide respuestas; un refuerzo vuelve a pausar el grafo.
            while preguntas:
                respuestas = pedir_respuestas(preguntas, thread_id)
                graph.invoke(Command(resume=respuestas), config)
                borrar_parciales(thread_id)

                estado = graph.get_state(config).values
                print("\n=== Evaluación ===")
                print(estado.get("evaluation", ""))

                preguntas = preguntas_pendientes(graph, config)
                if preguntas:
                    print("\n=== Refuerzo: nueva explicación ===")
                    print(estado.get("explanation", ""))
        except Exception as error:
            print("\nNo se pudo completar la sesión con Ollama.")
            print("Comprueba que el servicio esté activo: systemctl status ollama")
            print(f"Detalle: {error}")
    finally:
        conexion.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSesión guardada. Puedes retomarla con su ID.")
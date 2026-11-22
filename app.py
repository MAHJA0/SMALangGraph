"""Interfaz gráfica del tutor con Streamlit. Usa el mismo grafo y la misma base SQLite que main.py."""

import json
import sqlite3
import uuid
from pathlib import Path

import streamlit as st
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from config.settings import MAX_ATTEMPTS, get_model
from graph.workflow import build_graph

RUTA_DB = Path("data") / "sesiones.db"
DIR_PARCIALES = Path("data") / "parciales"
TEMA_POR_DEFECTO = "Algoritmos de ordenamiento"


# ---------- Recursos y sesiones ----------


@st.cache_resource
def obtener_recursos():
    """Crea el grafo y la conexión una sola vez para toda la aplicación."""
    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(RUTA_DB, check_same_thread=False)
    grafo = build_graph(get_model(), SqliteSaver(conexion))
    return grafo, conexion


def config_de(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def listar_sesiones(conexion) -> list[str]:
    """IDs de sesión, de la más reciente a la más antigua."""
    try:
        filas = conexion.execute(
            "SELECT thread_id FROM checkpoints GROUP BY thread_id ORDER BY MAX(rowid) DESC"
        ).fetchall()
    except sqlite3.OperationalError:
        return []  # la tabla todavía no existe
    return [fila[0] for fila in filas]


def tema_de(grafo, thread_id: str) -> str:
    return grafo.get_state(config_de(thread_id)).values.get("topic", "Sin tema")


def preguntas_pendientes(grafo, config) -> list[str] | None:
    """Si la sesión está pausada esperando respuestas, devuelve sus preguntas."""
    snapshot = grafo.get_state(config)
    for tarea in snapshot.tasks:
        for interrupcion in tarea.interrupts:
            return interrupcion.value["preguntas"]
    return None


# ---------- Respuestas guardadas una por una ----------


def ruta_parcial(thread_id: str) -> Path:
    return DIR_PARCIALES / f"{thread_id}.json"


def clave_respuesta(thread_id: str, intento: int, indice: int) -> str:
    return f"r_{thread_id}_{intento}_{indice}"


def cargar_parciales(thread_id: str, intento: int, cantidad: int) -> list[str]:
    """Respuestas ya guardadas para este intento; vacías si no hay."""
    vacias = [""] * cantidad
    ruta = ruta_parcial(thread_id)
    if not ruta.exists():
        return vacias
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if datos.get("intento") != intento:
        return vacias
    return (datos.get("respuestas", []) + vacias)[:cantidad]


def guardar_respuesta(thread_id: str, intento: int, indice: int, cantidad: int) -> None:
    """Callback: escribe en disco solo la respuesta que cambió."""
    respuestas = cargar_parciales(thread_id, intento, cantidad)
    respuestas[indice] = st.session_state[clave_respuesta(thread_id, intento, indice)]
    DIR_PARCIALES.mkdir(parents=True, exist_ok=True)
    datos = {"intento": intento, "respuestas": respuestas}
    ruta_parcial(thread_id).write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def borrar_parciales(thread_id: str) -> None:
    ruta_parcial(thread_id).unlink(missing_ok=True)


# ---------- Interfaz ----------


def mostrar_sidebar(conexion, grafo) -> None:
    with st.sidebar:
        st.header("Sesiones")
        if st.button("➕ Nueva sesión", use_container_width=True):
            st.session_state.thread_id = uuid.uuid4().hex[:8]

        actual = st.session_state.thread_id
        for tid in listar_sesiones(conexion):
            tipo = "primary" if tid == actual else "secondary"
            if st.button(tema_de(grafo, tid), key=f"ses_{tid}", type=tipo, use_container_width=True):
                st.session_state.thread_id = tid

        st.divider()
        id_ingresado = st.text_input("Abrir por ID")
        if st.button("Abrir", use_container_width=True) and id_ingresado.strip():
            st.session_state.thread_id = id_ingresado.strip()


def main() -> None:
    st.set_page_config(page_title="Tutor académico", page_icon="🎓")

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    grafo, conexion = obtener_recursos()
    mostrar_sidebar(conexion, grafo)

    tid = st.session_state.thread_id
    if not tid:
        st.title("Tutor académico")
        st.info("Crea una sesión nueva o elige una de la barra lateral.")
        return

    config = config_de(tid)
    valores = grafo.get_state(config).values

    # Sesión nueva: todavía no hay tema generado.
    if not valores:
        st.title("Nueva sesión")
        st.caption(f"ID: {tid}")
        tema = st.text_input("Tema a estudiar", value=TEMA_POR_DEFECTO)
        if st.button("Generar explicación y preguntas", type="primary"):
            with st.spinner("Generando con el modelo local... puede tardar un poco."):
                try:
                    grafo.invoke({"topic": tema.strip() or TEMA_POR_DEFECTO}, config)
                except Exception as error:
                    st.error(
                        "No se pudo generar la sesión con Ollama. "
                        "Comprueba que el servicio esté activo (systemctl status ollama)."
                    )
                    st.caption(f"Detalle: {error}")
                    return
            st.rerun()
        return

    # Encabezado: primero el tema, debajo el ID.
    st.title(valores.get("topic", "Sesión"))
    st.caption(f"ID: {tid}")

    st.subheader("Explicación")
    st.markdown(valores.get("explanation", ""))

    preguntas = preguntas_pendientes(grafo, config)
    intento = valores.get("intentos", 0) + 1

    if preguntas:
        st.subheader(f"Preguntas (intento {intento} de {MAX_ATTEMPTS + 1})")
        st.caption("Cada respuesta se guarda al salir de su caja. Si no sabes una, déjala en blanco.")

        cantidad = len(preguntas)
        previas = cargar_parciales(tid, intento, cantidad)
        for indice, pregunta in enumerate(preguntas):
            clave = clave_respuesta(tid, intento, indice)
            argumentos = {
                "key": clave,
                "on_change": guardar_respuesta,
                "args": (tid, intento, indice, cantidad),
            }
            etiqueta = f"{indice + 1}. {pregunta}"
            if clave in st.session_state:
                st.text_area(etiqueta, **argumentos)
            else:
                st.text_area(etiqueta, value=previas[indice], **argumentos)

        if st.button("Enviar respuestas", type="primary"):
            respuestas = [
                st.session_state.get(clave_respuesta(tid, intento, i), previas[i]).strip()
                for i in range(cantidad)
            ]
            with st.spinner("Evaluando tus respuestas..."):
                try:
                    grafo.invoke(Command(resume=respuestas), config)
                except Exception as error:
                    st.error("No se pudo evaluar. Revisa que Ollama esté activo.")
                    st.caption(f"Detalle: {error}")
                    return
            borrar_parciales(tid)
            st.rerun()

        if valores.get("evaluation"):
            with st.expander("Evaluación del intento anterior"):
                st.markdown(valores["evaluation"])
        return

    # Sesión completada.
    if valores.get("student_answers"):
        st.subheader("Tus respuestas")
        st.text(valores["student_answers"])
    if valores.get("evaluation"):
        st.subheader("Evaluación")
        st.markdown(valores["evaluation"])


main()
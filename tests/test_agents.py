"""Pruebas de los agentes y de la llamada común, con modelo falso."""

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from agents.evaluador import crear_nodo_evaluador
from agents.examinador import crear_nodo_examinador, separar_preguntas_y_rubrica
from agents.llamada import invocar, limpiar_razonamiento


def test_invocar_quita_el_bloque_de_razonamiento():
    modelo = FakeListChatModel(responses=["<think>interno</think>Respuesta limpia"])
    assert invocar(modelo, "sistema", "usuario") == "Respuesta limpia"


def test_limpiar_razonamiento_sin_etiqueta_de_apertura():
    texto = "Okay, the user wants something.\nLet me think.\n</think>\n\nhola"
    assert limpiar_razonamiento(texto) == "hola"


def test_limpiar_razonamiento_sin_etiquetas_no_cambia_el_texto():
    assert limpiar_razonamiento("Texto normal.") == "Texto normal."


def test_separar_con_formato_correcto():
    texto = "### PREGUNTAS\n1. P1\n2. P2\n\n### RÚBRICA\nPregunta 1 | x | y | 100"
    preguntas, rubrica = separar_preguntas_y_rubrica(texto)
    assert preguntas == "1. P1\n2. P2"
    assert rubrica == "Pregunta 1 | x | y | 100"


def test_separar_sin_secciones_devuelve_el_texto_completo():
    preguntas, rubrica = separar_preguntas_y_rubrica("texto libre")
    assert preguntas == "texto libre"
    assert rubrica == ""


def test_examinador_devuelve_preguntas_y_rubrica():
    modelo = FakeListChatModel(
        responses=["### PREGUNTAS\n1. P1\n\n### RÚBRICA\nPregunta 1 | x | y | 100"]
    )
    resultado = crear_nodo_examinador(modelo)({"topic": "X", "explanation": "E"})
    assert "P1" in resultado["questions"]
    assert "Pregunta 1 | x | y | 100" in resultado["criteria"]


def test_evaluador_sin_respuestas_no_llama_al_modelo():
    modelo = FakeListChatModel(responses=["no debería usarse"])
    resultado = crear_nodo_evaluador(modelo)({"topic": "X", "student_answers": "  "})
    assert resultado["evaluation"].startswith("No se recibieron")
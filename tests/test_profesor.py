"""Pruebas de la limpieza de la explicación (sin LLM)."""

from agents.profesor import limpiar_explicacion


def test_quita_lineas_que_copian_el_prompt():
    texto = (
        "1. **Introducción**: qué problema resuelve el tema. Define cada término clave.\n"
        "La pila guarda elementos en orden LIFO."
    )
    assert limpiar_explicacion(texto) == "La pila guarda elementos en orden LIFO."


def test_quita_el_conteo_de_palabras():
    assert limpiar_explicacion("Texto útil.\n\n*(847 palabras)*") == "Texto útil."


def test_conserva_el_contenido_normal():
    texto = "Una lista enlazada guarda nodos.\n\nCada nodo apunta al siguiente."
    assert limpiar_explicacion(texto) == texto
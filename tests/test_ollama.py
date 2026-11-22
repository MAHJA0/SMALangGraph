"""Prueba con Ollama real. Se omite si el servicio no está disponible."""

import pytest

from agents.examinador import crear_nodo_examinador
from config.settings import get_model


@pytest.mark.ollama
def test_examinador_con_modelo_real():
    modelo = get_model()
    try:
        modelo.invoke("ping")
    except Exception as error:
        pytest.skip(f"Ollama no está disponible: {error}")

    resultado = crear_nodo_examinador(modelo)(
        {"topic": "Búsqueda binaria", "explanation": "Dividir el arreglo a la mitad."}
    )
    assert resultado["questions"]
    assert resultado["criteria"]
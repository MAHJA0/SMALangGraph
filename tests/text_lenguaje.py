"""Pruebas de la detección del lenguaje (sin LLM)."""

from agents.lenguaje import detectar_lenguaje


def test_detecta_c_mas_mas():
    assert detectar_lenguaje("Punteros en C++") == "C++"


def test_detecta_python_sin_importar_mayusculas():
    assert detectar_lenguaje("listas en python") == "Python"


def test_sin_lenguaje_usa_python():
    assert detectar_lenguaje("Algoritmos de ordenamiento") == "Python"
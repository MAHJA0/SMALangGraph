"""Pruebas de la división de preguntas y del formato de respuestas (sin LLM)."""

from graph.recoleccion import SIN_RESPUESTA, dividir_preguntas, formatear_respuestas


def test_dividir_extrae_las_preguntas_numeradas():
    texto = "1. ¿Qué es X?\n2. ¿Por qué Y?\n3. Escribe Z."
    assert dividir_preguntas(texto) == ["¿Qué es X?", "¿Por qué Y?", "Escribe Z."]


def test_dividir_sin_numeracion_devuelve_el_texto_completo():
    assert dividir_preguntas("Pregunta única") == ["Pregunta única"]


def test_formatear_marca_las_respuestas_vacias():
    assert formatear_respuestas(["respuesta", "  "]) == f"1. respuesta\n2. {SIN_RESPUESTA}"


def test_formatear_no_descarta_ninguna_respuesta():
    assert formatear_respuestas(["", ""]) == f"1. {SIN_RESPUESTA}\n2. {SIN_RESPUESTA}"
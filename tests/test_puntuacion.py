"""Pruebas del cálculo de la puntuación final (sin LLM)."""

from agents.evaluador import recalcular_puntuacion


def test_recalcula_la_puntuacion_con_los_puntos_de_la_rubrica():
    texto = "Pregunta 1: 5 de 30\nJustificación.\nPregunta 2: 0 de 40\nPregunta 3: 20 de 30"
    resultado = recalcular_puntuacion(texto)
    assert resultado.endswith("Puntuación final: 25")


def test_reemplaza_una_puntuacion_final_escrita_por_el_modelo():
    texto = "Pregunta 1: 10 de 50\nPregunta 2: 10 de 50\nPuntuación final: 1.67"
    resultado = recalcular_puntuacion(texto)
    assert "1.67" not in resultado
    assert "Puntuación final: 20" in resultado


def test_sin_lineas_por_pregunta_no_cambia_el_texto():
    assert recalcular_puntuacion("Puntuación final: 80") == "Puntuación final: 80"
"""Pruebas del estado compartido."""

from state import TutorState


def test_estado_tiene_los_campos_esperados():
    campos = set(TutorState.__annotations__)
    assert campos == {
        "topic",
        "language",
        "explanation",
        "questions",
        "criteria",
        "respuestas",
        "student_answers",
        "evaluation",
        "intentos",
    }
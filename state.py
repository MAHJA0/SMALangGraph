"""Estado compartido del tutor académico multiagente."""

from typing import TypedDict


class TutorState(TypedDict, total=False):
    """Datos que los nodos se pasan entre sí durante una sesión de estudio."""

    topic: str
    language: str            # lenguaje de programación detectado del tema
    explanation: str
    questions: str
    criteria: str            # rúbrica: solo para el evaluador, nunca se muestra al estudiante
    respuestas: list[str]    # una respuesta por pregunta; puede ser cadena vacía
    student_answers: str     # las mismas respuestas numeradas, para el evaluador
    evaluation: str
    intentos: int            # refuerzos ya realizados (Etapa 5)
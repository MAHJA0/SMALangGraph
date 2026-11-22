"""Nodo Examinador: genera preguntas y su rúbrica a partir de la explicación."""

import logging
import re
from typing import Callable

from agents.llamada import invocar
from state import TutorState

logger = logging.getLogger(__name__)

SISTEMA_EXAMINADOR = """Eres un examinador universitario de programación.
Generas preguntas para comprobar si un estudiante entendió una explicación.
Genera exactamente 3 preguntas: 1) conceptual, 2) de análisis y 3) de código.

Lenguaje de programación: {lenguaje}.
Las preguntas y la rúbrica deben referirse SOLO a {lenguaje}. No uses otro lenguaje.

Reglas para las preguntas:
- La pregunta 1 (conceptual) pide explicar un concepto con tus palabras y justificarlo.
- La pregunta 2 (análisis) pide explicar una diferencia, un error común o una complejidad.
  NO pide analizar código, NO incluye fragmentos de código y NO menciona «el siguiente código».
  Toda la información necesaria debe estar en el texto de la pregunta.
- La pregunta 3 (código) pide escribir una función corta en {lenguaje}, relacionada con uno de los conceptos explicados.
- Reparte las preguntas entre los distintos conceptos de la explicación; no te quedes con uno solo.
- Cada pregunta debe ser una sola línea numerada, sin bloques de código.

Reglas para la rúbrica:
- Cada criterio debe nombrar un concepto concreto de la explicación (un tipo de estructura, una operación o una complejidad).
- No uses criterios genéricos como «respuesta correcta».

Escribe TODO en español. Usa exactamente este formato y no escribas nada fuera de estas dos secciones:

### PREGUNTAS
1. ...
2. ...
3. ...

### RÚBRICA
Una línea por pregunta, con este formato exacto:
Pregunta N | Criterio | Respuesta esperada | Puntos

Los puntos de las 3 preguntas deben sumar 100.
No incluyas razonamiento interno."""

_PATRON_PREGUNTAS = re.compile(
    r"###\s*PREGUNTAS\s*(.*?)(?=###\s*RÚBRICA|\Z)", re.DOTALL | re.IGNORECASE
)
_PATRON_RUBRICA = re.compile(r"###\s*RÚBRICA\s*(.*)", re.DOTALL | re.IGNORECASE)


def separar_preguntas_y_rubrica(texto: str) -> tuple[str, str]:
    """Separa la respuesta del modelo en preguntas y rúbrica.

    Si faltan las secciones, devuelve el texto completo como preguntas y una
    rúbrica vacía, y lo registra en el log.
    """
    coincidencia_preguntas = _PATRON_PREGUNTAS.search(texto)
    coincidencia_rubrica = _PATRON_RUBRICA.search(texto)

    if not coincidencia_preguntas or not coincidencia_rubrica:
        logger.warning("El examinador no devolvió las secciones esperadas.")
        return texto.strip(), ""

    return coincidencia_preguntas.group(1).strip(), coincidencia_rubrica.group(1).strip()


def crear_nodo_examinador(model) -> Callable[[TutorState], dict]:
    """Devuelve el nodo del examinador con el modelo inyectado."""

    def examinador(state: TutorState) -> dict:
        lenguaje = state.get("language", "Python")
        usuario = (
            f"Tema: {state['topic']}\n\n"
            f"Explicación:\n{state.get('explanation', '')}"
        )
        sistema = SISTEMA_EXAMINADOR.format(lenguaje=lenguaje)
        texto = invocar(model, sistema, usuario)
        preguntas, rubrica = separar_preguntas_y_rubrica(texto)
        return {"questions": preguntas, "criteria": rubrica}

    return examinador
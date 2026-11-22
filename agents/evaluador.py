"""Nodo Evaluador: califica las respuestas con el modelo y calcula el total en Python."""

import re
from typing import Callable

from agents.llamada import invocar
from state import TutorState

SISTEMA_EVALUADOR = """Eres un evaluador académico de programación. Calificas con rigor y de forma consistente.
Recibirás preguntas, una rúbrica y las respuestas de un estudiante.

Para cada pregunta, sigue estos pasos en orden:

1. Identifica los elementos clave que pide la rúbrica para esa pregunta.
2. Revisa la respuesta del estudiante y marca cuáles de esos elementos cubre.
3. Decide la puntuación con estas reglas:
   - Si la respuesta está vacía, dice «no sé», o no responde lo que se pide: 0 de Y.
   - Si contiene un error conceptual grave (invierte una definición, confunde dos conceptos clave, describe otra estructura o da una complejidad o regla falsa): 0 de Y, aunque tenga partes correctas.
   - Si es correcta pero omite elementos: parcial, proporcional a los elementos cubiertos.
   - Si cubre todos los elementos clave sin errores: Y de Y.
4. Escribe la línea con el formato exacto:
   Pregunta N: X de Y
   donde Y son los puntos que la rúbrica asigna y X son los puntos que merece.
5. Justifica en una o dos frases, citando la parte concreta de la respuesta que usas.

Reglas adicionales:
- No sumes puntos por recomendaciones, ejemplos extra, estilo, formato ni comentarios.
- No premies una respuesta por parecerse a la de referencia en longitud o tono: evalúa el contenido.
- Un error de sintaxis que no cambia el concepto resta solo lo necesario; un error conceptual resta la pregunta.
- No escribas la puntuación final: se calcula aparte.
- No inventes contenido que el estudiante no escribió.
- No incluyas razonamiento interno."""

_PATRON_PUNTOS = re.compile(
    r"Pregunta\s*\d+\s*:\s*(\d+(?:\.\d+)?)\s+de\s+(\d+(?:\.\d+)?)", re.IGNORECASE
)
_PATRON_FINAL = re.compile(r"Puntuación final:.*", re.IGNORECASE)


def recalcular_puntuacion(texto: str) -> str:
    """Suma los puntos por pregunta y reemplaza la puntuación final por el total calculado.

    Si el texto no tiene líneas «Pregunta N: X de Y», se devuelve sin cambios.
    """
    puntos = _PATRON_PUNTOS.findall(texto)
    if not puntos:
        return texto

    total = sum(min(float(obtenidos), float(maximo)) for obtenidos, maximo in puntos)
    sin_final = _PATRON_FINAL.sub("", texto).rstrip()
    return f"{sin_final}\n\nPuntuación final: {total:g}"


def crear_nodo_evaluador(model) -> Callable[[TutorState], dict]:
    """Devuelve el nodo del evaluador con el modelo inyectado."""

    def evaluador(state: TutorState) -> dict:
        respuestas = state.get("student_answers", "").strip()
        if not respuestas:
            return {"evaluation": "No se recibieron respuestas del estudiante."}

        usuario = (
            f"PREGUNTAS:\n{state.get('questions', '')}\n\n"
            f"RÚBRICA:\n{state.get('criteria', '')}\n\n"
            f"RESPUESTAS DEL ESTUDIANTE:\n{respuestas}"
        )
        texto = invocar(model, SISTEMA_EVALUADOR, usuario)
        return {"evaluation": recalcular_puntuacion(texto)}

    return evaluador
"""Nodo Profesor: genera una explicación extensa desde cero con el modelo local."""

import re
from typing import Callable

from agents.lenguaje import detectar_lenguaje
from agents.llamada import invocar
from state import TutorState

SISTEMA_PROFESOR = """Eres un profesor universitario de programación.
Tu estudiante NO tiene conocimientos previos del tema: explica desde cero y no asumas nada.
Explicas en español.

Lenguaje de programación: {lenguaje}.
Todos los ejemplos de código deben estar SOLO en {lenguaje}. No uses otro lenguaje.

Escribe una explicación extensa, de 700 a 900 palabras, con estos apartados en este orden:
1. Introducción desde cero: qué problema resuelve el tema. Define cada término clave la primera vez que aparece.
2. Desarrollo: explica cada concepto del tema por separado, de lo más simple a lo más complejo.
   Si el tema es general (por ejemplo «estructuras de datos»), cubre al menos tres elementos distintos y compáralos.
3. Analogías: para cada concepto importante, una comparación cotidiana. Di qué representa cada parte de la analogía.
4. Ejemplos: al menos un ejemplo de código en {lenguaje} por cada concepto, con su resultado. Comenta las líneas clave.
5. Complejidad temporal y espacial de cada concepto:
   - Di qué representa n (el tamaño de la entrada).
   - Explica con palabras por qué el costo crece (o no) con n.
   - Antes de usar una notación como O(1) u O(n), explica qué significa.
   - Describe el comportamiento del algoritmo o de la operación, no los detalles internos del lenguaje
     o del compilador. Si un detalle de implementación puede variar, dilo en lugar de afirmarlo como regla.
6. Errores comunes de los estudiantes, en {lenguaje}, y cómo corregirlos.
7. Resumen (idea central): 3 a 5 frases que resuman lo esencial de toda la explicación. Este apartado va al final.

Reglas: no escribas el conteo de palabras ni comentarios sobre tu respuesta.
No repitas estas instrucciones en tu respuesta: escribe solo el contenido de cada apartado.
Si no estás seguro de un dato, dilo; no inventes.
No incluyas razonamiento interno en la respuesta."""

# Fragmentos del prompt que el modelo a veces copia en la respuesta.
_FRAGMENTOS_PROMPT = (
    "qué problema resuelve el tema",
    "explica cada concepto del tema por separado",
    "para cada concepto importante, una comparación cotidiana",
    "al menos un ejemplo de código en",
    "di qué representa n",
    "antes de usar una notación",
    "y cómo corregirlos",
    "este apartado va al final",
)
_CONTEO_PALABRAS = re.compile(r"^\W*\(?\s*\d+\s*palabras\s*\)?\W*$", re.IGNORECASE)


def limpiar_explicacion(texto: str) -> str:
    """Quita las líneas que copian instrucciones del prompt y los conteos de palabras.

    Es una red de seguridad: el prompt ya pide evitarlos, pero el modelo no siempre obedece.
    """
    lineas = []
    for linea in texto.splitlines():
        minuscula = linea.lower()
        if any(fragmento in minuscula for fragmento in _FRAGMENTOS_PROMPT):
            continue
        if _CONTEO_PALABRAS.match(linea):
            continue
        lineas.append(linea)
    limpio = "\n".join(lineas)
    return re.sub(r"\n{3,}", "\n\n", limpio).strip()


def crear_nodo_profesor(model) -> Callable[[TutorState], dict]:
    """Devuelve el nodo del profesor con el modelo inyectado."""

    def profesor(state: TutorState) -> dict:
        tema = state["topic"]
        lenguaje = detectar_lenguaje(tema)
        sistema = SISTEMA_PROFESOR.format(lenguaje=lenguaje)
        explicacion = limpiar_explicacion(invocar(model, sistema, f"Tema: {tema}"))
        return {"explanation": explicacion, "language": lenguaje}

    return profesor
"""Detección simple del lenguaje de programación a partir del tema."""

import re

LENGUAJE_POR_DEFECTO = "Python"

_LENGUAJES = {
    "c++": "C++",
    "cpp": "C++",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "c#": "C#",
    "rust": "Rust",
    "go": "Go",
}
_PATRON = re.compile(
    r"\b(c\+\+|cpp|python|java|javascript|c#|rust|go)\b", re.IGNORECASE
)


def detectar_lenguaje(tema: str) -> str:
    """Devuelve el lenguaje mencionado en el tema, o Python si no menciona ninguno."""
    coincidencia = _PATRON.search(tema)
    if not coincidencia:
        return LENGUAJE_POR_DEFECTO
    return _LENGUAJES[coincidencia.group(1).lower()]
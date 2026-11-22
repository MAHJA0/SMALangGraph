"""Prueba de conexión con Ollama: envía una pregunta corta al modelo local."""

import sys

from config.settings import MODEL_NAME, get_model


def main() -> int:
    """Pregunta al modelo y muestra la respuesta o un mensaje claro de error."""
    modelo = get_model()
    try:
        respuesta = modelo.invoke("Explica en una frase qué es un algoritmo.")
    except Exception as error:
        print(f"No se pudo obtener respuesta de Ollama con el modelo {MODEL_NAME}.")
        print("Comprueba que el servicio esté activo: systemctl status ollama")
        print(f"Detalle: {error}")
        return 1

    print(f"Modelo: {MODEL_NAME}")
    print(respuesta.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
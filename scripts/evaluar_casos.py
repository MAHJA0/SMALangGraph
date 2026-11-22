"""Evalúa al evaluador con los casos de referencia y compara con las calificaciones esperadas.

Uso, desde la raíz del proyecto:
    python -m scripts.evaluar_casos --modelo qwen3:4b --reps 3
    python -m scripts.evaluar_casos --modelo qwen3:8b --reps 3
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

from agents.evaluador import crear_nodo_evaluador
from config.settings import get_model
from graph.recoleccion import formatear_respuestas

RUTA_CASOS = Path("data/casos_prueba.json")
CARPETA_RESULTADOS = Path("data/resultados")
CLAVES = ["pregunta_1", "pregunta_2", "pregunta_3"]
_PATRON_PUNTOS = re.compile(
    r"Pregunta\s*(\d+)\s*:\s*(\d+(?:\.\d+)?)\s+de\s+(\d+(?:\.\d+)?)", re.IGNORECASE
)


def caso_correcto(tema: dict) -> dict:
    return next(c for c in tema["casos"] if c["tipo"] == "correcta")


def puntos_maximos(tema: dict) -> list[float]:
    """Los puntos máximos de cada pregunta son los que obtiene la respuesta correcta."""
    caso = caso_correcto(tema)
    return [float(caso["calificacion_esperada"][c]) for c in CLAVES]


def construir_rubrica(tema: dict, maximos: list[float]) -> str:
    """Rúbrica por tema: cada pregunta se compara con la respuesta de referencia del caso correcto."""
    referencias = caso_correcto(tema)["respuestas"]
    lineas = []
    for numero, (puntos, referencia) in enumerate(zip(maximos, referencias), start=1):
        lineas.append(
            f"Pregunta {numero} | Criterio: precisión conceptual y completitud frente a la "
            f"respuesta de referencia | Respuesta esperada: {referencia} | Puntos: {puntos:g}"
        )
    return "\n".join(lineas)


def extraer_puntos(evaluacion: str) -> list[float | None]:
    """Devuelve los puntos obtenidos por pregunta; None si el modelo no escribió esa línea."""
    encontrados = {}
    for numero, obtenido, _ in _PATRON_PUNTOS.findall(evaluacion):
        encontrados[int(numero)] = float(obtenido)
    return [encontrados.get(i) for i in (1, 2, 3)]


def evaluar_una_vez(nodo, tema: dict, respuestas: list[str], maximos: list[float]) -> tuple[list[float | None], str]:
    """Devuelve los puntos por pregunta y el texto completo de la evaluación."""
    estado = {
        "questions": "\n".join(f"{i}. {p}" for i, p in enumerate(tema["preguntas"], start=1)),
        "criteria": construir_rubrica(tema, maximos),
        "student_answers": formatear_respuestas(respuestas),
    }
    texto = nodo(estado)["evaluation"]
    return extraer_puntos(texto), texto


def formato(valor: float | None, decimales: int = 1) -> str:
    return "n/d" if valor is None else f"{valor:.{decimales}f}"


def nombre_seguro(modelo: str) -> str:
    """Convierte 'qwen3.5:9b-q4_K_M' en 'qwen3.5_9b-q4_K_M' para usarlo en un nombre de archivo."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", modelo)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", required=True, help="nombre del modelo en Ollama, p. ej. qwen3:8b")
    parser.add_argument("--reps", type=int, default=3, help="repeticiones por caso")
    args = parser.parse_args()

    try:
        temas = json.loads(RUTA_CASOS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"No se pudo leer {RUTA_CASOS}: {error}")
        return 1

    print(f"Modelo: {args.modelo}  |  repeticiones: {args.reps}")
    nodo = crear_nodo_evaluador(get_model(modelo=args.modelo))
    resultados = []

    for tema in temas:
        maximos = puntos_maximos(tema)
        print(f"\n=== {tema['tema']} ===")

        for caso in tema["casos"]:
            esperados = [float(caso["calificacion_esperada"][c]) for c in CLAVES]
            total_esperado = sum(esperados)
            ejecuciones = []
            evaluaciones = []

            try:
                for _ in range(args.reps):
                    puntos, texto = evaluar_una_vez(nodo, tema, caso["respuestas"], maximos)
                    ejecuciones.append(puntos)
                    evaluaciones.append(texto)
            except Exception as error:
                print(f"  [{caso['tipo']}] error al llamar a Ollama: {error}")
                print("  Comprueba que el servicio esté activo: systemctl status ollama")
                return 1

            validas = [f for f in ejecuciones if None not in f]
            sin_formato = len(ejecuciones) - len(validas)
            totales = [sum(f) for f in validas]

            if totales:
                media = statistics.mean(totales)
                desviacion = statistics.pstdev(totales) if len(totales) > 1 else 0.0
                error_absoluto = abs(media - total_esperado)
            else:
                media = desviacion = error_absoluto = None

            aviso = f"  sin formato: {sin_formato}/{len(ejecuciones)}" if sin_formato else ""
            print(
                f"  [{caso['tipo']:10}] esperado={total_esperado:g}  "
                f"modelo={formato(media)} (desv. {formato(desviacion)})  "
                f"ejecuciones={[sum(f) if None not in f else 'sin formato' for f in ejecuciones]}"
                f"{aviso}"
            )

            resultados.append({
                "tema": tema["tema"],
                "tipo": caso["tipo"],
                "esperados": esperados,
                "ejecuciones": ejecuciones,
                "ejecuciones_sin_formato": sin_formato,
                "total_esperado": total_esperado,
                "total_medio": media,
                "desviacion": desviacion,
                "error_absoluto": error_absoluto,
                "evaluaciones_completas": evaluaciones,
            })

    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_RESULTADOS / f"{nombre_seguro(args.modelo)}.json"
    ruta.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados guardados en {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
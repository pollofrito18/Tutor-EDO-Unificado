"""Cálculo aislado con transporte JSON UTF-8 explícito, también en Windows."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

RAIZ = Path(__file__).resolve().parent
TURNOS = threading.BoundedSemaphore(2)


def calcular(datos, timeout=18):
    if not TURNOS.acquire(timeout=1):
        return {"ok": False, "error": "El motor está ocupado con otros cálculos. Intenta de nuevo en unos segundos."}
    try:
        return _calcular(datos, timeout)
    finally:
        TURNOS.release()


def _calcular(datos, timeout):
    entorno = {k: v for k, v in os.environ.items() if k not in ('NVIDIA_API_KEY', 'DATABASE_URL')}
    # La codificación del padre no configura los pipes del Python hijo.
    # Windows puede usar CP1252 al redirigirlos: fijar ambos extremos evita
    # que letras como ó, ñ o símbolos matemáticos rompan la respuesta JSON.
    entorno.update(
        OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
        PYTHONUTF8='1', PYTHONIOENCODING='utf-8:strict',
    )
    try:
        resultado = subprocess.run(
            [sys.executable, '-X', 'utf8', str(RAIZ / "worker.py")],
            input=json.dumps(datos, ensure_ascii=False).encode('utf-8'),
            capture_output=True, text=False,
            cwd=RAIZ, timeout=timeout, check=False, env=entorno,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "El cálculo superó el límite de tiempo y fue detenido. Simplifica la expresión o prueba un intervalo más corto en el modo numérico."}
    except OSError:
        return {"ok": False, "error": "No se pudo iniciar el proceso de cálculo. Revisa el entorno Python y los permisos de la carpeta del proyecto."}
    if resultado.returncode != 0:
        return {"ok": False, "error": "No se pudo iniciar el motor. Comprueba que instalaste requirements.txt en el mismo entorno que ejecuta la aplicación."}
    try:
        # Leer bytes impide fallos de decodificación en _readerthread.
        # La validación se hace aquí, donde el error sí se puede controlar.
        if not isinstance(resultado.stdout, bytes) or not resultado.stdout:
            raise ValueError('Respuesta ausente.')
        informe = json.loads(resultado.stdout.decode('utf-8'))
        if not isinstance(informe, dict) or type(informe.get('ok')) is not bool:
            raise ValueError('Estructura de respuesta inválida.')
        if not informe['ok'] and not isinstance(informe.get('error'), str):
            raise ValueError('Falta el detalle del error.')
        return informe
    except (UnicodeDecodeError, ValueError, TypeError):
        return {"ok": False, "error": "El motor no devolvió un resultado válido. No se publica una solución sin comprobarla."}


def a_markdown(r):
    if not r.get("ok"):
        return "# Resultado\n\n"+r.get("error", "Cálculo no completado")
    lineas = ["# Desarrollo de la ecuación", "", "Entrada: `"+r["entrada"]+"`", "", "Método: "+r["metodo"], ""]
    for i, p in enumerate(r["pasos"], 1):
        lineas += [f"## {i}. {p['titulo']}", "", p["texto"], ""]
        for formula in p["formulas"]:
            lineas += ["$$", formula, "$$", ""]
    lineas += ["## Resultado", "", "$$", r["particular"] or r["general"], "$$", "",
               "Comprobación simbólica: "+("identidad verificada" if r["verificado"] else "no concluyente"), ""]
    if r["constantes"]:
        lineas += ["Soluciones constantes detectadas, sujetas al dominio original:", ""]
        for formula in r["constantes"]:
            lineas += ["$$", formula, "$$", ""]
    if r["restricciones"]:
        lineas += ["Restricciones de la rama calculada (los equilibrios se revisan aparte):", ""]
        for formula in r["restricciones"]:
            lineas += ["$$", formula, "$$", ""]
    lineas += ["\n".join(r["notas"])]
    return "\n".join(lineas)

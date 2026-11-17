"""Proceso de cálculo: entrada y salida JSON; sin interfaz gráfica."""
import json
import sys

from nucleo.entrada import EntradaError
from nucleo.motor import informe
from nucleo.numerico import aproximar


def main():
    try:
        datos = json.loads(sys.stdin.read())
        accion = datos.get("accion", "simbolico")
        if accion not in ("simbolico", "numerico", "practica", "integral"):
            raise EntradaError("Acción desconocida.")
        if accion == "numerico":
            resultado = aproximar(datos)
        elif accion == "practica":
            from modulos.practica import comprobar
            resultado = comprobar(datos)
        elif accion == "integral":
            from modulos.integrales import explicar_integral
            from nucleo.entrada import expresion, x, y
            import sympy as s
            expr, restricciones = expresion(datos.get("expresion", ""))
            if expr.has(y):
                raise EntradaError("Usa solo x en el laboratorio de integrales.")
            # El laboratorio declara x positivo para dar un dominio inequívoco a log(x).
            xp = s.Symbol("x", positive=True)
            resultado = explicar_integral(expr.subs(x, xp), xp)
            resultado.update(ok=True, restricciones=[r.latex() for r in restricciones]+["x>0"])
        else:
            resultado = informe(datos)
    except EntradaError as e:
        resultado = {"ok": False, "error": str(e)}
    except (NotImplementedError, ValueError, TypeError, ZeroDivisionError, OverflowError, RecursionError):
        resultado = {"ok": False, "error": "El motor no pudo completar este caso. Simplifica la entrada, prueba otro método o usa la aproximación numérica."}
    except Exception as e:
        print(f"Error interno de cálculo: {type(e).__name__}", file=sys.stderr)
        resultado = {"ok": False, "error": "Ocurrió un error interno de cálculo. La ecuación no se marca como resuelta; conserva la entrada para revisar el caso."}
    print(json.dumps(resultado, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

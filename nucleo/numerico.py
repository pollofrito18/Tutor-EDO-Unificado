"""RK4 con etapas visibles y contraste con una aproximación de SciPy."""
import math
import warnings

import numpy as np
import sympy as s
from scipy.integrate import solve_ivp

from .entrada import EntradaError, Restriccion, leer, numero, x, y


def aproximar(datos):
    p = leer(datos)
    x0, y0, xf = (float(numero(datos.get(k, v))) for k, v in (("x0", "0"), ("y0", "1"), ("xf", "2")))
    try:
        n = int(datos.get("n", 40))
    except (TypeError, ValueError):
        raise EntradaError("El número de subintervalos debe ser un entero.") from None
    if n < 4 or n > 1000 or x0 == xf or max(abs(x0), abs(xf)) > 10000:
        raise EntradaError("Usa entre 4 y 1000 subintervalos, extremos distintos y |x| menor o igual a 10000.")
    restricciones = p.restricciones + [Restriccion(p.N, "ne")]
    intervalo = s.Interval(min(x0, xf), max(x0, xf))
    for r in restricciones:
        if r.expresion.free_symbols.issubset({x}) and r.tipo == "ne":
            ceros = s.solveset(r.expresion, x, domain=intervalo)
            if ceros != s.S.EmptySet:
                raise EntradaError("El intervalo contiene un punto excluido, o no se pudo descartar ese cruce: "+r.latex()+". Reduce el intervalo.")
    f = s.lambdify((x, y), p.f, modules="numpy")
    controles = [(r, s.lambdify((x, y), r.expresion, modules="numpy")) for r in restricciones]

    def revisar(t, u):
        if not math.isfinite(t) or not math.isfinite(u) or abs(u) > 1e10:
            raise EntradaError("La trayectoria crece demasiado o deja de ser finita. Reduce el intervalo o el tamaño del paso.")
        valores = []
        with np.errstate(all="ignore"):
            for r, fun in controles:
                valor = float(fun(t, u))
                if not math.isfinite(valor) or (r.tipo == "ne" and valor == 0) or (r.tipo == "gt" and valor <= 0) or (r.tipo == "ge" and valor < 0):
                    raise EntradaError("La aproximación alcanza un punto fuera del dominio: "+r.latex()+". Reduce el intervalo.")
                valores.append(valor)
        return valores

    def evaluar(t, u):
        revisar(t, u)
        with np.errstate(all="ignore"):
            z = float(f(t, u))
        if not math.isfinite(z):
            raise EntradaError("La derivada deja de ser real y finita. Revisa el dato inicial y el intervalo.")
        return z

    revisar(x0, y0)
    xs = np.linspace(x0, xf, n+1)
    ys = np.empty(n+1)
    ys[0] = y0
    etapas = []
    h = float((xf-x0)/n)
    try:
        for i in range(n):
            t, u = float(xs[i]), float(ys[i])
            k1 = evaluar(t, u)
            k2 = evaluar(t+h/2, u+h*k1/2)
            k3 = evaluar(t+h/2, u+h*k2/2)
            k4 = evaluar(t+h, u+h*k3)
            siguiente = u+h*(k1+2*k2+2*k3+k4)/6
            va = revisar(t, u)
            vb = revisar(t+h, siguiente)
            if any(r.tipo == "ne" and a*b < 0 for (r, _), a, b in zip(controles, va, vb)):
                raise EntradaError("Un paso cruza un posible divisor cero. Reduce el intervalo; no es válido unir ambos lados de la singularidad.")
            ys[i+1] = siguiente
            etapas.append({"n": i, "x_n": t, "y_n": u, "k1": k1, "k2": k2, "k3": k3, "k4": k4, "y_siguiente": siguiente})
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            referencia = solve_ivp(lambda t, u: [evaluar(float(t), float(u[0]))], (x0, xf), [y0], t_eval=xs, rtol=1e-9, atol=1e-11, max_step=abs(h))
        if not referencia.success or len(referencia.t) != n+1 or not np.isfinite(referencia.y).all():
            raise EntradaError("El integrador de referencia no completó el intervalo. Reduce el intervalo y revisa posibles singularidades.")
    except EntradaError:
        raise
    except (ValueError, TypeError, OverflowError, FloatingPointError, RuntimeWarning, ZeroDivisionError):
        raise EntradaError("No se pudo integrar de forma real y finita en todo el intervalo. Revisa el dominio y reduce el paso o el intervalo.") from None
    euler = [y0]
    etapas_euler = []
    aviso_euler = None
    try:
        for i in range(n):
            t, u = float(xs[i]), euler[-1]
            pendiente = evaluar(t, u)
            siguiente = u+h*pendiente
            va, vb = revisar(t,u), revisar(float(xs[i+1]),siguiente)
            if any(r.tipo == "ne" and a*b < 0 for (r,_),a,b in zip(controles,va,vb)):
                raise EntradaError("Un paso de Euler cruza un posible divisor cero.")
            euler.append(siguiente)
            etapas_euler.append({"n":i,"x_n":t,"y_n":u,"pendiente":pendiente,"y_siguiente":siguiente})
    except (EntradaError, ValueError, OverflowError, TypeError):
        euler = None
        etapas_euler = []
        aviso_euler = "Euler salió del dominio o del rango finito. Reduce el paso para compararlo."
    diferencia = np.abs(ys-referencia.y[0])
    filas = [{"x": float(a), "RK4": float(b), "Referencia_SciPy": float(c), "Diferencia_absoluta": float(d)} for a, b, c, d in zip(xs, ys, referencia.y[0], diferencia)]
    if euler is not None:
        for fila, valor in zip(filas,euler):
            fila["Euler"] = float(valor)
    return {
        "etapas_euler": etapas_euler, "aviso_euler": aviso_euler,
        "ok": True, "entrada": p.entrada, "f_latex": s.latex(p.f), "h": h,
        "filas": filas, "etapas": etapas, "diferencia_maxima": float(diferencia.max()),
        "nota": "Ambas curvas son aproximaciones. Su diferencia no es una cota rigurosa del error. Los controles de dominio detectan varios casos comunes, pero no certifican el intervalo máximo de existencia.",
    }

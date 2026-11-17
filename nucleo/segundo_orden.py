"""Solución comprobada de EDO lineales de segundo orden con coeficientes constantes."""
import re

import sympy as s

from .entrada import EntradaError, cumple, expresion, numero, x, y, yp


ypp = s.Symbol("ypp", real=True)
FUNCION_Y = s.Function("y")(x)
DERIVADA_Y = s.diff(FUNCION_Y, x)
SEGUNDA_DERIVADA_Y = s.diff(FUNCION_Y, x, 2)


def _leer(datos):
    texto = datos.get("ecuacion", "")
    if not isinstance(texto, str) or not texto.strip():
        raise EntradaError("Escribe una EDO de segundo orden, por ejemplo y'' + y = 0.")
    normal = texto.replace("′", "'").replace("’", "'").replace("″", "''").replace("²", "^2")
    normal = re.sub(r"d\s*\^?\s*2\s*y\s*/\s*d\s*x\s*\^?\s*2", "ypp", normal)
    normal = re.sub(r"y\s*''\s*(?:\(\s*x\s*\))?", "ypp", normal)
    normal = re.sub(r"y\s*'\s*(?:\(\s*x\s*\))?", "yp", normal)
    normal = re.sub(r"y\s*\(\s*x\s*\)", "y", normal)
    if normal.count("=") != 1:
        raise EntradaError("Escribe una igualdad completa, por ejemplo y'' + 2*y' + y = sin(x).")
    izquierda, derecha = normal.split("=")
    a, restricciones_a = expresion(izquierda, derivada=True, segundo_orden=True)
    b, restricciones_b = expresion(derecha, derivada=True, segundo_orden=True)
    restricciones = restricciones_a + restricciones_b
    if any(r.expresion.has(yp, ypp) for r in restricciones):
        raise EntradaError("Las derivadas no pueden aparecer dentro de divisores o funciones.")
    residual = s.expand(a - b)
    try:
        polinomio = s.Poly(residual, ypp, yp, y)
    except s.PolynomialError:
        raise EntradaError("Escribe una EDO lineal en y, y' y y''.") from None
    if any(polinomio.degree(variable) > 1 for variable in (ypp, yp, y)):
        raise EntradaError("Solo se admiten EDO lineales: y, y' y y'' deben aparecer a la primera potencia.")
    c2 = s.simplify(residual.coeff(ypp))
    c1 = s.simplify(residual.coeff(yp))
    c0 = s.simplify(residual.coeff(y))
    for coeficiente in (c2, c1, c0):
        if coeficiente.free_symbols or coeficiente.is_real is not True or coeficiente.is_finite is not True:
            raise EntradaError("Esta ampliación admite coeficientes constantes; los coeficientes de y, y' y y'' no deben depender de x.")
    if c2 == 0:
        raise EntradaError("La ecuación no contiene una segunda derivada con coeficiente distinto de cero.")
    fuerza = s.simplify(residual.subs({ypp: 0, yp: 0, y: 0}))
    reconstruccion = c2*ypp + c1*yp + c0*y + fuerza
    if s.simplify(residual - reconstruccion) != 0:
        raise EntradaError("La ecuación no es lineal en y, y' y y''.")
    return texto, c1/c2, c0/c2, -fuerza/c2, restricciones


def informe(datos):
    if datos.get("formato", "ecuacion") != "ecuacion":
        raise EntradaError("Las EDO de segundo orden se escriben como una igualdad con y''.")
    if datos.get("metodo", "auto") != "auto":
        raise EntradaError("Para EDO de segundo orden usa el método Automático.")
    texto, coef_primera, coef_funcion, fuerza, restricciones = _leer(datos)
    ecuacion = s.Eq(
        SEGUNDA_DERIVADA_Y + coef_primera*DERIVADA_Y + coef_funcion*FUNCION_Y,
        fuerza,
    )
    try:
        resuelta = s.dsolve(ecuacion, FUNCION_Y)
    except (NotImplementedError, ValueError, TypeError, RecursionError):
        raise EntradaError("SymPy no encontró una forma simbólica para esta fuerza. No se publica una solución sin verificar.") from None
    if not isinstance(resuelta, s.Equality):
        raise EntradaError("El método simbólico no produjo una solución explícita verificable.")
    solucion = s.simplify(resuelta.rhs)
    constantes = sorted(solucion.free_symbols - {x}, key=str)
    if len(constantes) != 2:
        raise EntradaError("La solución no contiene exactamente dos constantes libres; no se publica como una solución general.")
    residuo = s.simplify(
        s.diff(solucion, x, 2)
        + coef_primera*s.diff(solucion, x)
        + coef_funcion*solucion
        - fuerza
    )
    if residuo != 0:
        raise EntradaError("No se pudo verificar simbólicamente la solución general; no se publica como resuelta.")

    particular = None
    if datos.get("usar_inicial"):
        x0 = numero(datos.get("x0", "0"))
        y0 = numero(datos.get("y0", "1"))
        yp0 = numero(datos.get("yp0", "0"))
        if not cumple(restricciones, {x: x0}):
            raise EntradaError("El dato inicial x0 está fuera del dominio de la ecuación.")
        condiciones = [
            s.Eq(solucion.subs(x, x0), y0),
            s.Eq(s.diff(solucion, x).subs(x, x0), yp0),
        ]
        soluciones_constantes = s.solve(condiciones, constantes, dict=True)
        if len(soluciones_constantes) != 1 or any(c not in soluciones_constantes[0] for c in constantes):
            raise EntradaError("No se pudo determinar una única solución con esos dos datos iniciales.")
        valores = soluciones_constantes[0]
        if any(v.free_symbols.intersection(constantes) or v.has(s.zoo, s.oo, -s.oo, s.nan, s.I) for v in valores.values()):
            raise EntradaError("Los datos iniciales no determinaron constantes reales finitas.")
        solucion_particular = s.simplify(solucion.subs(valores))
        if (
            s.simplify(solucion_particular.subs(x, x0) - y0) != 0
            or s.simplify(s.diff(solucion_particular, x).subs(x, x0) - yp0) != 0
        ):
            raise EntradaError("La solución calculada no reproduce ambos datos iniciales.")
        particular = r"y(x) = " + s.latex(solucion_particular)

    ecuacion_latex = r"\frac{d^2y}{dx^2} + " + s.latex(coef_primera) + r"\frac{dy}{dx} + " + s.latex(coef_funcion) + r"y = " + s.latex(fuerza)
    r = s.Symbol("r")
    caracteristica = r**2 + coef_primera*r + coef_funcion
    raices = s.solve(caracteristica, r)
    pasos = [
        {
            "titulo": "Identificar el tipo de ecuación",
            "texto": "La ecuación es lineal de segundo orden con coeficientes constantes. La fuerza puede incluir las funciones admitidas por el lector.",
            "formulas": [ecuacion_latex],
        },
        {
            "titulo": "Resolver la ecuación característica",
            "texto": "Para la parte homogénea, sustituimos y=e^(r·x) y resolvemos la ecuación cuadrática característica.",
            "formulas": [
                r"r^2 + " + s.latex(coef_primera) + r"r + " + s.latex(coef_funcion) + " = 0",
                r"r \in " + s.latex(s.FiniteSet(*raices)),
            ],
        },
        {
            "titulo": "Obtener la solución general",
            "texto": "Se calcula una solución simbólica y se sustituye en la ecuación original. Solo se muestra si el residuo se simplifica exactamente a cero.",
            "formulas": [r"y(x) = " + s.latex(solucion)],
        },
    ]
    if particular:
        pasos.append({
            "titulo": "Aplicar los datos iniciales",
            "texto": "Se determinan las dos constantes usando y(x₀) y y'(x₀), y se comprueba que ambos datos se reproduzcan.",
            "formulas": [
                r"y(" + s.latex(numero(datos.get("x0", "0"))) + r") = " + s.latex(numero(datos.get("y0", "1"))),
                r"y'\left(" + s.latex(numero(datos.get("x0", "0"))) + r"\right) = " + s.latex(numero(datos.get("yp0", "0"))),
                particular,
            ],
        })
    pasos.append({
        "titulo": "Comprobar por sustitución",
        "texto": "El residuo de sustituir la solución en la EDO original es cero.",
        "formulas": [r"y'' + " + s.latex(coef_primera) + r"y' + " + s.latex(coef_funcion) + r"y - " + s.latex(fuerza) + " = 0"],
    })
    return {
        "ok": True,
        "metodo": "EDO lineal de segundo orden con coeficientes constantes",
        "clave": "segundo_orden",
        "entrada": texto,
        "ecuacion_latex": ecuacion_latex,
        "metodos": ["EDO lineal de segundo orden con coeficientes constantes"],
        "general": r"y(x) = " + s.latex(solucion),
        "implicita": r"y(x) = " + s.latex(solucion),
        "particular": particular,
        "constantes": [],
        "pasos": pasos,
        "restricciones": list(dict.fromkeys(r.latex() for r in restricciones)),
        "notas": [
            "Esta ampliación cubre ecuaciones lineales de segundo orden con coeficientes constantes. No resuelve de forma universal ecuaciones no lineales, coeficientes variables, sistemas ni EDP."
        ],
        "verificado": True,
        "residuo": s.latex(residuo),
        "integrales_pendientes": solucion.has(s.Integral),
    }

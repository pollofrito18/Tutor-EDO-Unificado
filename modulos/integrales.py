"""Adaptación propia del patrón de árbol de reglas observado en SymPy Gamma.

Utiliza la API de SymPy 1.14.0, sin copiar su impresor HTML antiguo.
Recibe objetos SymPy construidos por código de confianza, nunca texto sin validar.
"""
import sympy as s
from sympy.integrals.manualintegrate import integral_steps

EXPLICACIONES = {
    "ConstantRule": "La integral de una constante es esa constante multiplicada por la variable.",
    "ConstantTimesRule": "Sacamos el factor constante fuera de la integral.",
    "PowerRule": "Aplicamos la regla de potencias: aumentamos el exponente en uno y dividimos por el nuevo exponente, cuando el exponente original no es -1.",
    "AddRule": "Integramos cada término de la suma por separado.",
    "URule": "Introducimos una sustitución, transformamos el diferencial e integramos respecto a la nueva variable.",
    "PartsRule": "Aplicamos integración por partes: integral(u dv) = u v - integral(v du).",
    "SinRule": "Una antiderivada del seno es el coseno con signo negativo.",
    "CosRule": "Una antiderivada del coseno es el seno.",
    "ExpRule": "Aplicamos la regla de integración de la exponencial.",
    "ReciprocalRule": "Aplicamos la regla logarítmica. En variable real, hay que considerar el valor absoluto y los intervalos que excluyen cero.",
    "RewriteRule": "Reescribimos la expresión y resolvemos la integral equivalente.",
    "DontKnowRule": "No se dispone de un desarrollo con las reglas de este módulo.",
}


def explicar_integral(expr, variable):
    if not isinstance(expr, s.Expr) or not isinstance(variable, s.Symbol):
        raise TypeError("Se requieren una expresión SymPy validada y un símbolo.")
    if s.count_ops(expr) > 60:
        raise ValueError("Expresión fuera del tamaño de este ejemplo.")
    contador = [0]

    def convertir(regla, nivel=0):
        contador[0] += 1
        if contador[0] > 80 or nivel > 12:
            raise ValueError("El desarrollo supera el límite de este adaptador.")
        nombre = type(regla).__name__
        if nombre == "AlternativeRule":
            return convertir(regla.alternatives[0], nivel+1)
        hijos = list(getattr(regla, "substeps", []))
        for atributo in ("substep", "v_step", "second_step"):
            hijo = getattr(regla, atributo, None)
            if hijo is not None:
                hijos.append(hijo)
        nodos = [convertir(h, nivel+1) for h in hijos]
        formulas = []
        if nombre == "URule":
            formulas.append(s.latex(regla.u_var)+"="+s.latex(regla.u_func))
            formulas.append(r"du="+s.latex(s.diff(regla.u_func, regla.variable))+r"\,d"+s.latex(regla.variable))
        if nombre == "PartsRule":
            formulas.extend(["u="+s.latex(regla.u), r"dv="+s.latex(regla.dv)+r"\,d"+s.latex(regla.variable)])
        resultado = regla.eval()
        formulas.append(s.latex(s.Integral(regla.integrand, regla.variable))+"="+s.latex(resultado))
        return {
            "regla": nombre,
            "explicacion": EXPLICACIONES.get(nombre, "SymPy calculó una regla cuya explicación todavía no está traducida en este adaptador."),
            "formulas_latex": formulas,
            "subpasos": nodos,
            "explicacion_completa": nombre in EXPLICACIONES and nombre != "DontKnowRule" and all(n["explicacion_completa"] for n in nodos),
        }

    regla = integral_steps(expr, variable)
    resultado = regla.eval()
    arbol = convertir(regla)
    residuo = s.simplify(s.diff(resultado, variable)-expr)
    return {
        "arbol": arbol,
        "primitiva_latex": s.latex(resultado),
        "resultado_latex": s.latex(resultado)+"+C",
        "verificado": residuo == 0 and not resultado.has(s.Integral),
        "explicacion_completa": arbol["explicacion_completa"],
        "nota": "La identidad es simbólica bajo los supuestos de las variables; no calcula automáticamente el dominio real completo. Ejecutar en un proceso con límite de tiempo al integrarlo a la aplicación.",
    }

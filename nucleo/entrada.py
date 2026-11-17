"""Lectura de expresiones matemáticas mediante una lista cerrada de sintaxis AST.

El texto del usuario nunca se pasa a eval, exec, sympify ni parse_expr.
Las restricciones se conservan antes de simplificar, incluso en y/y.
"""
import ast
import math
import re
from dataclasses import dataclass, field

import sympy as s

x, y, yp = s.symbols("x y yp", real=True)
C = s.Symbol("C", real=True)


class EntradaError(ValueError):
    pass


@dataclass
class Restriccion:
    expresion: s.Expr
    tipo: str  # ne: distinto de cero; gt: positivo; ge: no negativo

    def latex(self):
        signo = {"ne": r"\ne", "gt": ">", "ge": r"\ge"}[self.tipo]
        return f"{s.latex(self.expresion)} {signo} 0"


@dataclass
class Problema:
    M: s.Expr
    N: s.Expr
    restricciones: list = field(default_factory=list)
    entrada: str = ""
    formato: str = "ecuacion"

    @property
    def f(self):
        return s.cancel(-self.M / self.N)

    @property
    def latex(self):
        return s.latex(self.M) + r" + \left(" + s.latex(self.N) + r"\right)y'=0"


FUNCIONES = {
    "sin": s.sin, "sen": s.sin, "cos": s.cos, "tan": s.tan,
    "exp": s.exp, "log": s.log, "ln": s.log, "sqrt": s.sqrt,
    "abs": s.Abs, "asin": s.asin, "acos": s.acos, "atan": s.atan,
    "sinh": s.sinh, "cosh": s.cosh,
}


def expresion(texto, derivada=False, segundo_orden=False):
    if not isinstance(texto, str) or not texto.strip():
        raise EntradaError("Escribe una expresión; por ejemplo, 2*x*y.")
    if len(texto) > 350:
        raise EntradaError("Usa una expresión de hasta 350 caracteres.")
    texto = texto.strip().replace("^", "**").replace("−", "-").replace("×", "*")
    nombres = {"x": x, "y": y, "pi": s.pi, "e": s.E, "E": s.E}
    if derivada:
        nombres["yp"] = yp
        if segundo_orden:
            nombres["ypp"] = s.Symbol("ypp", real=True)
    restricciones = []
    try:
        arbol = ast.parse(texto, mode="eval")
    except (SyntaxError, ValueError, RecursionError):
        raise EntradaError("Sintaxis inválida. Usa * para multiplicar: 2*x, y exp(x) para e^x.") from None
    if sum(1 for _ in ast.walk(arbol)) > 140:
        raise EntradaError("La expresión es demasiado compleja para esta versión educativa.")

    def visitar(nodo, profundidad=0):
        if profundidad > 18:
            raise EntradaError("Hay demasiados paréntesis u operaciones anidadas.")
        v = lambda n: visitar(n, profundidad + 1)
        if isinstance(nodo, ast.Expression):
            return v(nodo.body)
        if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
            if not math.isfinite(nodo.value) or abs(nodo.value) > 10**6:
                raise EntradaError("Usa números finitos con valor absoluto menor o igual a 1000000.")
            return s.Rational(str(nodo.value))
        if isinstance(nodo, ast.Name) and nodo.id in nombres:
            return nombres[nodo.id]
        if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.UAdd, ast.USub)):
            a = v(nodo.operand)
            return a if isinstance(nodo.op, ast.UAdd) else -a
        if isinstance(nodo, ast.BinOp):
            a, b = v(nodo.left), v(nodo.right)
            if isinstance(nodo.op, ast.Add):
                return a + b
            if isinstance(nodo.op, ast.Sub):
                return a - b
            if isinstance(nodo.op, ast.Mult):
                return a * b
            if isinstance(nodo.op, ast.Div):
                if b == 0:
                    raise EntradaError("La expresión contiene una división por cero.")
                restricciones.append(Restriccion(b, "ne"))
                return a / b
            if isinstance(nodo.op, ast.Pow):
                if b.is_number and (b.is_real is not True or abs(b) > 20):
                    raise EntradaError("Los exponentes numéricos deben estar entre -20 y 20.")
                if b.is_negative:
                    restricciones.append(Restriccion(a, "ne"))
                if b.is_Rational and b.q % 2 == 0:
                    restricciones.append(Restriccion(a, "ge"))
                elif b.is_integer is not True:
                    restricciones.append(Restriccion(a, "gt"))
                # Limita la evaluación de potencias numéricas encadenadas.
                if a.is_number and b.is_number:
                    try:
                        if abs(complex(a)) > 1 and float(b) > 0 and float(b) * math.log10(abs(complex(a))) > 100:
                            raise EntradaError("La potencia numérica es demasiado grande.")
                    except (TypeError, OverflowError):
                        raise EntradaError("Potencia numérica no admitida.") from None
                return a**b
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            nombre = nodo.func.id
            if nombre in FUNCIONES and len(nodo.args) == 1 and not nodo.keywords:
                a = v(nodo.args[0])
                if nombre in ("log", "ln"):
                    restricciones.append(Restriccion(a, "gt"))
                if nombre == "sqrt":
                    restricciones.append(Restriccion(a, "ge"))
                if nombre == "tan":
                    restricciones.append(Restriccion(s.cos(a), "ne"))
                if nombre in ("asin", "acos"):
                    restricciones.append(Restriccion(1 - a*a, "ge"))
                return FUNCIONES[nombre](a)
        raise EntradaError("Solo se admiten x, y, números, + - * / ^, paréntesis y las funciones de la guía.")

    try:
        resultado = visitar(arbol)
    except RecursionError:
        raise EntradaError("La expresión es demasiado profunda.") from None
    if resultado.has(s.zoo, s.oo, -s.oo, s.nan, s.I):
        raise EntradaError("La expresión no representa un valor real finito.")
    return resultado, restricciones


def numero(texto):
    valor, _ = expresion(str(texto))
    if valor.free_symbols or valor.is_real is not True or valor.is_finite is not True:
        raise EntradaError("La condición inicial debe contener números reales finitos; por ejemplo 0, -1 o 1/2.")
    return valor


def leer(datos):
    formato = datos.get("formato", "ecuacion")
    if formato == "mn":
        M, rm = expresion(datos.get("M", ""))
        N, rn = expresion(datos.get("N", ""))
        texto = f"M={datos['M']}; N={datos['N']}"
    elif formato == "ecuacion":
        texto = datos.get("ecuacion", "")
        normal = texto.replace("′", "'").replace("’", "'")
        if "''" in normal or "″" in normal or "d2y" in normal:
            raise EntradaError("Esta versión explica ecuaciones ordinarias de primer orden. Las de segundo orden requieren otro módulo.")
        normal = re.sub(r"y\s*\(\s*x\s*\)", "y", normal)
        normal = normal.replace("dy/dx", "yp").replace("y'", "yp")
        if normal.count("=") != 1:
            raise EntradaError("Escribe una igualdad completa; por ejemplo y' = 2*x*y.")
        izquierda, derecha = normal.split("=")
        a, rm = expresion(izquierda, True)
        b, rn = expresion(derecha, True)
        if any(r.expresion.has(yp) for r in rm + rn):
            raise EntradaError("La derivada debe aparecer sin divisores ni funciones que la contengan.")
        residual = s.expand(a-b)
        try:
            polinomio = s.Poly(residual, yp)
        except s.PolynomialError:
            raise EntradaError("Usa una ecuación lineal en y': M(x,y) + N(x,y)*y' = 0.") from None
        if polinomio.degree() != 1:
            raise EntradaError("La ecuación debe contener y' en primer grado. No se admiten ecuaciones algebraicas ni (y')^2.")
        N, M = s.simplify(polinomio.coeff_monomial(yp)), s.simplify(residual.subs(yp, 0))
    else:
        raise EntradaError("Formato de entrada desconocido.")
    if N == 0:
        raise EntradaError("N es cero: no queda una ecuación diferencial para y(x).")
    return Problema(s.simplify(M), s.simplify(N), rm + rn, texto, formato)


def cumple(restricciones, valores):
    for r in restricciones:
        v = s.simplify(r.expresion.subs(valores))
        if v.has(s.zoo, s.oo, -s.oo, s.nan) or v.is_real is False:
            return False
        propiedad = {"ne": v.is_zero is False, "gt": v.is_positive is True, "ge": v.is_nonnegative is True}[r.tipo]
        if not propiedad:
            return False
    return True

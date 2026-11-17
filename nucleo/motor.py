"""Métodos explicados con transformaciones calculadas para la entrada recibida.

No usa dsolve como generador de explicaciones. La comprobación simbólica es
una identidad local, no una certificación del dominio máximo ni de unicidad.
"""
from dataclasses import dataclass, field
import re

import sympy as s

from .entrada import C, x, y, EntradaError, Restriccion, cumple, leer, numero


class LogAbs(s.Function):
    """Primitiva real log|u|; su derivada u'/u exige u != 0."""
    nargs = 1

    @classmethod
    def eval(cls, a):
        if a.is_number or a.is_positive:
            return s.log(s.Abs(a))

    def fdiff(self, argindex=1):
        return 1 / self.args[0]

    def _latex(self, printer):
        return r"\log\left|" + printer._print(self.args[0]) + r"\right|"


def primitiva(expresion, variable, restricciones):
    p = s.integrate(expresion, variable)
    for log in list(p.atoms(s.log)):
        a = log.args[0]
        if a.is_real is True and a.is_positive is not True:
            restricciones.append(Restriccion(a, "ne"))
            p = p.xreplace({log: LogAbs(a)})
    return p


def paso(titulo, texto, *formulas):
    return {"titulo": titulo, "texto": texto, "formulas": list(formulas)}


def igualdad(a, b):
    return s.latex(a) + " = " + s.latex(b)


def regla_integracion(f, v):
    if not f.has(v):
        return "La integral de una constante k es k multiplicado por la variable."
    if f.is_polynomial(v):
        return "Integramos término a término: la integral de a·u^n es a·u^(n+1)/(n+1), con n distinto de -1."
    if s.simplify(f*v).has(v) is False:
        return "Usamos la regla de 1/u: su integral real es log|u|, sobre intervalos que no contienen cero."
    return "Calculamos una antiderivada. Si no se puede evaluar, conservamos la integral de forma explícita."


@dataclass
class Desarrollo:
    clave: str
    nombre: str
    potencial: s.Expr
    pasos: list
    restricciones: list = field(default_factory=list)
    explicita: s.Expr | None = None
    constantes: list = field(default_factory=list)
    notas: list = field(default_factory=list)


METODOS = {
    "auto": "Automático", "separables": "Variables separables",
    "lineal": "Lineal de primer orden", "exacta": "Exacta",
    "factor_x": "No exacta con factor integrante de x",
    "factor_y": "No exacta con factor integrante de y",
}


def clasificar(p):
    f = p.f
    hallados = {}
    if f == 0:
        hallados["separables"] = (s.S.Zero, s.S.One)
    else:
        separado = s.separatevars(f, symbols=(x, y), dict=True)
        if separado and set(separado).issubset({"coeff", x, y}):
            a = s.simplify(separado.get("coeff", 1)*separado.get(x, 1))
            b = separado.get(y, s.S.One)
            if not a.has(y) and not b.has(x) and s.simplify(f-a*b) == 0:
                hallados["separables"] = (a, b)
    if s.simplify(s.diff(f, y, 2)) == 0:
        P = -s.diff(f, y)
        Q = s.simplify(f+P*y)
        if not P.has(y) and not Q.has(y):
            hallados["lineal"] = (P, Q)
    My, Nx = s.diff(p.M, y), s.diff(p.N, x)
    delta = s.simplify(My-Nx)
    if delta == 0:
        hallados["exacta"] = None
    else:
        rx = s.simplify(delta/p.N)
        if not rx.has(y):
            hallados["factor_x"] = rx
        if p.M != 0:
            ry = s.simplify(-delta/p.M)
            if not ry.has(x):
                hallados["factor_y"] = ry
    return hallados


def constantes_validas(p, expresion):
    try:
        raices = s.solveset(expresion, y, domain=s.S.Reals)
    except (NotImplementedError, ValueError):
        return []
    validas = []
    if isinstance(raices, s.FiniteSet):
        for c in raices:
            if c.has(x) or s.simplify(p.M.subs(y, c)) != 0:
                continue
            # Rechaza violaciones idénticas; restricciones dependientes de x
            # siguen visibles para que la solución sea solamente local.
            mal = False
            for r in p.restricciones:
                a = s.simplify(r.expresion.subs(y, c))
                if a.has(s.zoo, s.oo, s.nan) or a.is_real is False:
                    mal = True
                if r.tipo == "ne" and a == 0:
                    mal = True
                if r.tipo == "gt" and a.is_nonpositive is True:
                    mal = True
                if r.tipo == "ge" and a.is_negative is True:
                    mal = True
            if not mal:
                validas.append(c)
    return validas


def separables(p, factores):
    a, b = factores
    r = list(p.restricciones) + [Restriccion(p.N, "ne")]
    constantes = constantes_validas(p, b) + constantes_validas(p, p.N)
    r.append(Restriccion(b, "ne"))
    A, B = primitiva(a, x, r), primitiva(1/b, y, r)
    F = B-A
    pasos = [
        paso("Despejar la derivada", "Dividimos por N donde N no sea cero.", r"y'="+s.latex(p.f)),
        paso("Identificar los factores", "El primer factor depende solo de x y el segundo solo de y.", "f(x)="+s.latex(a), "g(y)="+s.latex(b)),
        paso("Revisar soluciones constantes", "Antes de dividir por g(y), buscamos sus ceros y los comprobamos en la ecuación original.", igualdad(b, 0)),
        paso("Separar las variables", "Dividimos por g(y) únicamente en las ramas donde no es cero.", s.latex(1/b)+r"\,dy="+s.latex(a)+r"\,dx"),
        paso("Integrar respecto a y", regla_integracion(1/b, y), igualdad(s.Integral(1/b, y), B)),
        paso("Integrar respecto a x", regla_integracion(a, x), igualdad(s.Integral(a, x), A)),
        paso("Incluir la constante de integración", "Las dos constantes de integración se reúnen en una sola constante real C.", igualdad(F, C)),
    ]
    explicita = None
    if s.diff(b, y) == 0:
        explicita = s.simplify(b*(A+C))
    elif s.diff(b, y, 2) == 0:
        alfa, beta = s.diff(b, y), s.simplify(b-s.diff(b, y)*y)
        explicita = s.simplify((C*s.exp(alfa*A)-beta)/alfa)
        pasos.append(paso("Despejar y", "Exponenciamos y absorbemos el signo y los factores constantes en una nueva C. C=0 recupera el equilibrio cuando la entrada original lo permite.", igualdad(y, explicita)))
    elif F.is_rational_function(y) and s.count_ops(F) < 45:
        ramas = s.solve(F-C, y)
        if len(ramas) == 1:
            explicita = s.simplify(ramas[0])
            pasos.append(paso("Despejar y", "Resolvemos algebraicamente la relación obtenida.", igualdad(y, explicita)))
    return Desarrollo("separables", METODOS["separables"], F, pasos, r, explicita, list(dict.fromkeys(constantes)))


def lineal(p, coeficientes):
    P, Q = coeficientes
    r = list(p.restricciones) + [Restriccion(p.N, "ne")]
    integral_P = s.integrate(P, x)
    mu = s.simplify(s.exp(integral_P))
    r.append(Restriccion(mu, "ne"))
    I = primitiva(s.simplify(mu*Q), x, r)
    F = mu*y-I
    solucion = s.simplify((I+C)/mu)
    pasos = [
        paso("Normalizar", "Dividimos por el coeficiente de y' en un intervalo donde no sea cero.", r"y'+\left("+s.latex(P)+r"\right)y="+s.latex(Q)),
        paso("Identificar P y Q", "Una ecuación lineal no contiene potencias no lineales ni funciones de y.", "P(x)="+s.latex(P), "Q(x)="+s.latex(Q)),
        paso("Calcular el factor integrante", "Integramos P y exponenciamos. Cualquier múltiplo constante no nulo del factor también sirve.", r"\int P(x)\,dx="+s.latex(integral_P), r"\mu(x)=e^{\int P(x)\,dx}="+s.latex(mu)),
        paso("Aplicar la regla del producto", "Como la derivada de mu es P por mu, el lado izquierdo se convierte en la derivada de mu por y.", r"\frac{d}{dx}\left[\left("+s.latex(mu)+r"\right)y\right]="+s.latex(s.simplify(mu*Q))),
        paso("Integrar", regla_integracion(s.simplify(mu*Q), x), igualdad(mu*y, I+C)),
        paso("Despejar y", "Dividimos por el factor integrante en su dominio de validez.", igualdad(y, solucion)),
    ]
    return Desarrollo("lineal", METODOS["lineal"], F, pasos, r, solucion, constantes_validas(p, p.N))


def exacta(p, clave, razon):
    r = list(p.restricciones)
    M, N = p.M, p.N
    pasos = [paso("Identificar M y N", "Escribimos M dx + N dy = 0.", "M="+s.latex(M), "N="+s.latex(N)),
             paso("Comparar derivadas parciales", "La condición de exactitud es que la derivada de M respecto a y coincida con la de N respecto a x.", "M_y="+s.latex(s.diff(M, y)), "N_x="+s.latex(s.diff(N, x)))]
    if clave != "exacta":
        v = x if clave == "factor_x" else y
        formula = r"\frac{M_y-N_x}{N}" if v == x else r"\frac{N_x-M_y}{M}"
        mu = s.simplify(s.exp(s.integrate(razon, v)))
        r.extend([Restriccion(mu, "ne"), Restriccion(p.N if v == x else p.M, "ne")])
        pasos.append(paso("Buscar un factor de una sola variable", "La razón calculada depende únicamente de "+str(v)+"; por eso este método es aplicable.", formula+"="+s.latex(razon)))
        pasos.append(paso("Multiplicar por el factor integrante", "La ecuación transformada conserva las soluciones donde el factor es finito y no nulo.", r"\mu="+s.latex(mu)))
        M, N = s.simplify(mu*M), s.simplify(mu*N)
        if s.simplify(s.diff(M, y)-s.diff(N, x)) != 0:
            raise EntradaError("No se pudo comprobar que el factor obtenido haga exacta la ecuación.")
        pasos.append(paso("Comprobar la nueva exactitud", "Recalculamos ambas derivadas después de multiplicar.", r"\widetilde M="+s.latex(M), r"\widetilde N="+s.latex(N), igualdad(s.diff(M, y), s.diff(N, x))))
    A = primitiva(M, x, r)
    gprima = s.simplify(N-s.diff(A, y))
    if gprima.has(x):
        raise EntradaError("No se logró reducir la función auxiliar a una sola variable.")
    g = primitiva(gprima, y, r)
    F = s.simplify(A+g)
    pasos.extend([
        paso("Integrar M respecto a x", "Tratamos y como constante y añadimos una función g(y), porque su derivada respecto a x es cero.", r"F(x,y)="+s.latex(A)+"+g(y)"),
        paso("Determinar g'(y)", "Derivamos respecto a y e igualamos a N.", "g'(y)="+s.latex(gprima)),
        paso("Integrar g'(y)", regla_integracion(gprima, y), "g(y)="+s.latex(g)),
        paso("Escribir la solución implícita", "La función F permanece constante a lo largo de cada curva solución, en el dominio indicado.", igualdad(F, C)),
    ])
    explicita = None
    if s.diff(F, y, 2) == 0 and s.diff(F, y) != 0:
        explicita = s.simplify((C-F.subs(y, 0))/s.diff(F, y))
    return Desarrollo(clave, METODOS[clave], F, pasos, r, explicita, constantes_validas(p, p.N))


def desarrollar(p, metodo="auto"):
    opciones = clasificar(p)
    if metodo == "auto":
        if p.formato == "mn" and "exacta" in opciones:
            metodo = "exacta"
        else:
            metodo = next(iter(opciones), None)
    if metodo not in opciones:
        nombres = ", ".join(METODOS[k] for k in opciones)
        if nombres:
            raise EntradaError("El método elegido no aplica. Métodos detectados: "+nombres+".")
        raise EntradaError("No se detectó un método simbólico de los implementados. Puedes intentar una aproximación numérica con condición inicial. Esto no significa que la ecuación no tenga solución.")
    if metodo == "separables":
        d = separables(p, opciones[metodo])
    elif metodo == "lineal":
        d = lineal(p, opciones[metodo])
    else:
        d = exacta(p, metodo, opciones[metodo])
    d.constantes = list(dict.fromkeys(d.constantes + constantes_validas(p, p.M)))
    d.notas.append("La comprobación es local: todas las expresiones deben ser reales y finitas. No determina automáticamente el intervalo máximo ni demuestra unicidad.")
    return d, opciones


def informe(datos):
    if datos.get("formato", "ecuacion") == "ecuacion":
        texto = datos.get("ecuacion", "")
        if isinstance(texto, str) and re.search(
            r"(?:y\s*''|y\s*″|d\s*(?:\^?\s*2|²)\s*y\s*/\s*d\s*x\s*(?:\^?\s*2|²)|d2y\s*/\s*dx2)",
            texto,
        ):
            from .segundo_orden import informe as informe_segundo_orden
            return informe_segundo_orden(datos)
    p = leer(datos)
    d, opciones = desarrollar(p, datos.get("metodo", "auto"))
    F, solucion = d.potencial, d.explicita
    solucion_comprobar = solucion
    residual = s.simplify(s.diff(F, x)*p.N-s.diff(F, y)*p.M)
    verificado = residual == 0
    if solucion is not None:
        prueba = s.simplify(p.N.subs(y, solucion)*s.diff(solucion, x)+p.M.subs(y, solucion))
        if prueba != 0:
            # Una forma implícita válida es preferible a publicar un despeje
            # que no se pudo verificar.
            solucion = None
            solucion_comprobar = None
            d.pasos = [p for p in d.pasos if p["titulo"] != "Despejar y"]
            d.notas.append("Se conserva la forma implícita porque no se pudo verificar un despeje explícito.")
    general = igualdad(y, solucion) if solucion is not None else igualdad(F, C)
    particular = None
    if datos.get("usar_inicial"):
        x0, y0 = numero(datos.get("x0", "0")), numero(datos.get("y0", "1"))
        if not cumple(p.restricciones, {x:x0, y:y0}):
            raise EntradaError("La condición inicial viola el dominio de la ecuación escrita.")
        if s.simplify(p.N.subs({x:x0, y:y0})) == 0 and y0 not in d.constantes:
            raise EntradaError("N se anula en el punto inicial. Esta versión no determina una rama regular y(x) en ese punto singular; elige otro punto o estudia las ramas por separado.")
        d.pasos.append(paso("Aplicar la condición inicial", "Sustituimos el punto indicado para determinar la constante.", igualdad(y.subs(y, s.Function('y')(x0)), y0)))
        if y0 in d.constantes and s.simplify(p.M.subs(y, y0)) == 0:
            particular = igualdad(y, y0)
            solucion_comprobar = y0
            d.pasos.append(paso("Conservar el equilibrio", "El valor inicial coincide con una solución constante comprobada. No se debe dividir por el factor que se anula.", particular))
            d.notas.append("Se muestra una solución constante que cumple el dato inicial; no se afirma que sea la única.")
        elif solucion is not None:
            ecuacion_C = solucion.subs(x, x0)-y0
            constantes = s.solve(ecuacion_C, C)
            if len(constantes) != 1 or constantes[0].has(s.zoo, s.oo, s.nan, s.I):
                raise EntradaError("Esta representación de la solución no permite aplicar ese dato inicial. Revisa las restricciones o utiliza la aproximación numérica.")
            cp = s.simplify(constantes[0])
            solp = s.simplify(solucion.subs(C, cp))
            solucion_comprobar = solp
            if not cumple(d.restricciones, {x:x0, y:y0}):
                raise EntradaError("El punto inicial está fuera del dominio de la rama calculada. Revisa otra rama o método.")
            particular = igualdad(y, solp)
            d.pasos.append(paso("Obtener la solución particular", "Reemplazamos la constante y comprobamos el valor inicial.", igualdad(C, cp), particular, igualdad(solp.subs(x, x0), y0)))
        else:
            if not cumple(d.restricciones, {x:x0, y:y0}):
                raise EntradaError("El dato inicial está en un punto excluido por esta rama del método.")
            cp = s.simplify(F.subs({x:x0, y:y0}))
            if cp.has(s.zoo, s.oo, s.nan, s.I):
                raise EntradaError("No se pudo evaluar la constante en ese punto inicial.")
            particular = igualdad(F, cp)
            d.pasos.append(paso("Obtener la relación particular", "La condición inicial determina el nivel de F. Una curva implícita puede tener varias ramas; aquí no se afirma unicidad.", igualdad(C, cp), particular))
    d.pasos.append(paso("Comprobar por diferenciación", "Para F(x,y)=C verificamos F_x·N - F_y·M. Un residuo cero comprueba la identidad diferencial donde la transformación es válida.", r"F_xN-F_yM="+s.latex(residual)))
    if solucion_comprobar is not None:
        derivada = s.diff(solucion_comprobar, x)
        residuo_explicito = s.simplify(p.M.subs(y, solucion_comprobar)+p.N.subs(y, solucion_comprobar)*derivada)
        d.pasos.append(paso("Sustituir en la ecuación original", "Derivamos la solución mostrada y la sustituimos junto con su derivada en M + N·y'.", r"y'="+s.latex(derivada), r"M(x,y(x))+N(x,y(x))y'(x)="+s.latex(residuo_explicito)))
        verificado = verificado and residuo_explicito == 0
    restricciones = list(dict.fromkeys(r.latex() for r in d.restricciones if not (r.expresion.is_number and cumple([r], {}))))
    return {
        "ok": True, "metodo": d.nombre, "clave": d.clave, "entrada": p.entrada,
        "ecuacion_latex": p.latex, "metodos": [METODOS[k] for k in opciones],
        "general": general, "implicita": igualdad(F, C), "particular": particular,
        "constantes": [igualdad(y, c) for c in d.constantes], "pasos": d.pasos,
        "restricciones": restricciones, "notas": d.notas, "verificado": verificado,
        "residuo": s.latex(residual), "integrales_pendientes": bool(F.has(s.Integral)),
    }

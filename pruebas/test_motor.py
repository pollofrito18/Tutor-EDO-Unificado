import math
import unittest

import numpy as np
import sympy as s

from ejemplos import EJEMPLOS
from nucleo.entrada import EntradaError, C, leer, x, y
from nucleo.motor import desarrollar, informe
from nucleo.numerico import aproximar
from servicio import calcular


class PruebasSimbolicas(unittest.TestCase):
    def test_ejemplos_del_curso(self):
        for nombre, datos in EJEMPLOS.items():
            if nombre.startswith("Aproximación"):
                continue
            with self.subTest(nombre=nombre):
                r = informe(dict(datos, usar_inicial=True))
                self.assertTrue(r["verificado"])
                self.assertIsNotNone(r["particular"])

    def test_separable_solucion_conocida(self):
        p = leer({"ecuacion": "y' = 2*x*y"})
        d, _ = desarrollar(p)
        self.assertEqual(s.simplify(d.explicita-C*s.exp(x*x)), 0)
        self.assertIn(s.S.Zero, d.constantes)

    def test_condiciones_iniciales_de_ambos_signos(self):
        for valor in ("1", "-1", "0", "1/2"):
            with self.subTest(valor=valor):
                r = informe({"ecuacion": "y' = 2*x*y", "usar_inicial": True, "x0": "0", "y0": valor})
                self.assertTrue(r["verificado"])
                self.assertIsNotNone(r["particular"])

    def test_logaritmos_reales(self):
        r = informe({"ecuacion": "y' = -x/y", "usar_inicial": True, "x0": "0", "y0": "-1"})
        self.assertTrue(r["verificado"])
        r = informe({"ecuacion": "y' = y*(1-y)", "usar_inicial": True, "x0": "0", "y0": "2"})
        self.assertTrue(r["verificado"])
        self.assertNotIn("i", r["particular"].replace("right", "").replace("left", ""))

    def test_lineal_contra_solucion_independiente(self):
        p = leer({"ecuacion": "y' + 2*y = x"})
        d, _ = desarrollar(p, "lineal")
        esperada = C*s.exp(-2*x)+x/2-s.Rational(1, 4)
        self.assertEqual(s.simplify(d.explicita-esperada), 0)

    def test_exactas_generadas_desde_potenciales(self):
        for a, b, c in ((1,2,3), (-2,3,1), (4,-1,2)):
            with self.subTest(a=a,b=b,c=c):
                F = a*x*x*y+b*x+c*y*y
                p = leer({"formato":"mn", "M":str(s.diff(F,x)), "N":str(s.diff(F,y))})
                d, _ = desarrollar(p, "exacta")
                self.assertEqual(s.simplify(s.diff(d.potencial-F,x)), 0)
                self.assertEqual(s.simplify(s.diff(d.potencial-F,y)), 0)

    def test_factores_integrantes_con_resultado_conocido(self):
        for M,N,metodo,F in (("2*y","x","factor_x",x*x*y), ("y","2*x","factor_y",x*y*y)):
            with self.subTest(metodo=metodo):
                p = leer({"formato":"mn","M":M,"N":N})
                d, _ = desarrollar(p, metodo)
                self.assertEqual(s.simplify(d.potencial-F), 0)

    def test_equilibrio_en_factor_integrante_de_y(self):
        r = informe({"formato":"mn","M":"y","N":"2*x","metodo":"factor_y", "usar_inicial":True,"x0":"1","y0":"0"})
        self.assertEqual(r["particular"], "y = 0")

    def test_equilibrios_logisticos(self):
        r = informe({"ecuacion":"y' = y*(1-y)"})
        self.assertEqual(set(r["constantes"]), {"y = 0", "y = 1"})

    def test_coeficiente_singular_con_solucion_constante(self):
        r = informe({"ecuacion":"y*y' = 0", "usar_inicial":True,"x0":"0","y0":"0"})
        self.assertEqual(r["particular"], "y = 0")

    def test_entrada_con_cancelacion_conserva_restriccion(self):
        with self.assertRaises(EntradaError):
            informe({"ecuacion":"y' = y/y", "usar_inicial":True,"x0":"0","y0":"0"})

    def test_dato_inicial_fuera_de_dominio(self):
        with self.assertRaises(EntradaError):
            informe({"ecuacion":"y' = y/x", "usar_inicial":True,"x0":"0","y0":"1"})

    def test_punto_aislado_de_nivel_no_se_afirma_como_trayectoria(self):
        with self.assertRaisesRegex(EntradaError, "punto singular"):
            informe({"formato":"mn","M":"x","N":"y","metodo":"exacta", "usar_inicial":True,"x0":"0","y0":"0"})

    def test_metodo_incompatible(self):
        with self.assertRaises(EntradaError):
            informe({"ecuacion":"y' = x*y^2", "metodo":"lineal"})

    def test_metodo_no_implementado_no_se_inventa(self):
        with self.assertRaisesRegex(EntradaError, "No se detectó"):
            informe({"ecuacion":"y' = sin(x*y) + x^2"})


class PruebasSegundoOrden(unittest.TestCase):
    def test_homogenea_con_raices_imaginarias_y_dos_datos(self):
        r = informe({"ecuacion":"y'' + y = 0", "usar_inicial":True, "x0":"0", "y0":"1", "yp0":"0"})
        self.assertTrue(r["verificado"])
        self.assertEqual(r["residuo"], "0")
        self.assertEqual(r["particular"], r"y(x) = \cos{\left(x \right)}")

    def test_raiz_repetida_y_forzamiento_resonante(self):
        casos = (
            ("y'' - 2*y' + y = 0", "1", "0", r"y(x) = \left(1 - x\right) e^{x}"),
            ("y'' + y = sin(x)", "0", "0", r"y(x) = - \frac{x \cos{\left(x \right)}}{2} + \frac{\sin{\left(x \right)}}{2}"),
            ("y'' + 2*y' + y = exp(-x)", "0", "0", r"y(x) = \frac{x^{2} e^{- x}}{2}"),
        )
        for ecuacion, y0, yp0, esperada in casos:
            with self.subTest(ecuacion=ecuacion):
                r = informe({"ecuacion":ecuacion, "usar_inicial":True, "x0":"0", "y0":y0, "yp0":yp0})
                self.assertTrue(r["verificado"])
                self.assertEqual(r["particular"], esperada)

    def test_notacion_d2y_y_rechazo_de_coeficientes_variables(self):
        for texto in ("d2y/dx2 + y = 0", "d²y/dx² + y = 0"):
            with self.subTest(texto=texto):
                r = informe({"ecuacion":texto})
                self.assertTrue(r["verificado"])
        with self.assertRaisesRegex(EntradaError, "coeficientes constantes"):
            informe({"ecuacion":"x*y'' + y = 0"})
        with self.assertRaises(EntradaError):
            informe({"ecuacion":"y*y'' + y = 0"})


class PruebasEntrada(unittest.TestCase):
    def test_aliases_equivalentes(self):
        for texto in ("y' = x^2", "dy/dx = x**2", "y′ = x*x"):
            with self.subTest(texto=texto):
                self.assertEqual(leer({"ecuacion":texto}).f,x*x)

    def test_ordenes_y_derivadas_no_admitidas(self):
        for texto in ("y'' + y = 0", "y^2 = x", "(y')^2 = x", "1/y' = x", "sin(y') = x"):
            with self.subTest(texto=texto), self.assertRaises(EntradaError):
                leer({"ecuacion":texto})

    def test_expresiones_fuera_de_lista_cerrada(self):
        for texto in ("y' = __import__('os')", "y' = x.__class__", "y' = [x for x in y]", "y'=open('dato')", "y'=2**1000000", "y'=log(-1)", "y'=1/0"):
            with self.subTest(texto=texto), self.assertRaises(EntradaError):
                leer({"ecuacion":texto})


class PruebasNumericas(unittest.TestCase):
    def test_rk4_contra_exponencial(self):
        r = aproximar({"ecuacion":"y'=y", "x0":"0","y0":"1","xf":"1","n":40})
        xs = np.array([f["x"] for f in r["filas"]])
        ys = np.array([f["RK4"] for f in r["filas"]])
        self.assertLess(float(np.max(np.abs(ys-np.exp(xs)))), 1e-7)
        self.assertEqual(len(r["etapas"]), 40)

    def test_rk4_refinamiento_reduccion_del_error(self):
        errores=[]
        for n in (10,20):
            r=aproximar({"ecuacion":"y'=y", "x0":"0","y0":"1","xf":"1","n":n})
            errores.append(abs(r["filas"][-1]["RK4"]-math.e))
        self.assertGreater(errores[0]/errores[1], 14)

    def test_integracion_hacia_atras(self):
        r=aproximar({"ecuacion":"y'=2*x", "x0":"1","y0":"1","xf":"0","n":10})
        self.assertAlmostEqual(r["filas"][-1]["RK4"],0,places=10)

    def test_fallback_para_caso_no_clasificado(self):
        r=aproximar({"ecuacion":"y'=sin(x*y)+x^2", "x0":"0","y0":"1","xf":"1","n":40})
        self.assertTrue(r["ok"])
        self.assertGreater(r["filas"][-1]["RK4"], 1)

    def test_rechaza_intervalo_que_cruza_polo(self):
        for ec in ("y'=1/x", "y'=tan(x)"):
            with self.subTest(ec=ec), self.assertRaises(EntradaError):
                aproximar({"ecuacion":ec, "x0":"-2","y0":"1","xf":"2","n":40})

    def test_rechaza_dominio_invalido_y_explosion(self):
        for ec,y0,xf in (("y'=sqrt(y)","-1","1"), ("y'=y^2","1","2"), ("y'=-1/y","1","1")):
            with self.subTest(ec=ec), self.assertRaises(EntradaError):
                aproximar({"ecuacion":ec, "x0":"0","y0":y0,"xf":xf,"n":100})

    def test_modelo_temperatura_contra_formula(self):
        r=aproximar({"ecuacion":"y'=-0.15*(y-25)", "x0":"0","y0":"80","xf":"20","n":100})
        esperada=25+55*math.exp(-0.15*20)
        self.assertAlmostEqual(r["filas"][-1]["RK4"],esperada,places=5)


class PruebasServicio(unittest.TestCase):
    def test_proceso_real(self):
        r=calcular({"ecuacion":"y'=y", "usar_inicial":True,"x0":"0","y0":"1"})
        self.assertTrue(r["ok"],r)
        self.assertTrue(r["verificado"])

    def test_proceso_rechaza_entrada_sin_detener_interfaz(self):
        r=calcular({"ecuacion":"y'=__import__('os')"})
        self.assertFalse(r["ok"])
        self.assertIn("Solo se admiten",r["error"])

    def test_proceso_resuelve_segundo_orden(self):
        r=calcular({"ecuacion":"y'' + y = 0", "usar_inicial":True, "x0":"0", "y0":"1", "yp0":"0"})
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["verificado"])
        self.assertEqual(r["residuo"], "0")


if __name__ == "__main__":
    unittest.main()

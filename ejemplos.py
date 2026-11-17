EJEMPLOS = {
    "Separable: crecimiento": {"formato": "ecuacion", "ecuacion": "y' = 2*x*y", "metodo": "separables", "x0": "0", "y0": "1"},
    "Separable: equilibrio": {"formato": "ecuacion", "ecuacion": "y' = y*(1-y)", "metodo": "separables", "x0": "0", "y0": "0"},
    "Separable: potencia": {"formato": "ecuacion", "ecuacion": "y' = x*y^2", "metodo": "separables", "x0": "0", "y0": "1"},
    "Lineal: factor integrante": {"formato": "ecuacion", "ecuacion": "y' + 2*y = x", "metodo": "lineal", "x0": "0", "y0": "1"},
    "Exacta: función potencial": {"formato": "mn", "M": "2*x*y + 1", "N": "x^2 + 2*y", "metodo": "exacta", "x0": "0", "y0": "1"},
    "No exacta: factor de x": {"formato": "mn", "M": "2*y", "N": "x", "metodo": "factor_x", "x0": "1", "y0": "1"},
    "No exacta: factor de y": {"formato": "mn", "M": "y", "N": "2*x", "metodo": "factor_y", "x0": "1", "y0": "1"},
    "Aproximación: caso fuera de los métodos": {"formato": "ecuacion", "ecuacion": "y' = sin(x*y) + x^2", "metodo": "auto", "x0": "0", "y0": "1"},
}

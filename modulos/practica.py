"""Validación simbólica aislada en el worker; respuestas libres, sin ejecutar código."""
import sympy as s
from nucleo.entrada import expresion, EntradaError, x, y
from .contenido import EJERCICIOS


def comprobar(datos):
    clave=datos.get('ejercicio')
    if clave not in EJERCICIOS:
        raise EntradaError('Ejercicio desconocido.')
    ejercicio=EJERCICIOS[clave]
    respuesta, restricciones=expresion(datos.get('respuesta',''))
    if respuesta.has(y):
        raise EntradaError('Escribe la respuesta en función de x, sin la variable y.')
    objetivo,_=expresion(ejercicio['respuesta'])
    equivalente=s.simplify(respuesta-objetivo)==0
    # Los ejercicios de esta colección tienen soluciones válidas para todo x real.
    # No aceptar cancelaciones que pierdan puntos de ese dominio.
    dominio=True
    for r in restricciones:
        if r.tipo=='ne':
            valido=r.expresion.is_zero is False or s.solveset(r.expresion,x,domain=s.S.Reals)==s.S.EmptySet
        elif r.tipo=='gt':
            valido=r.expresion.is_positive is True
        else:
            valido=r.expresion.is_nonnegative is True
        dominio=dominio and bool(valido)
    correcto=equivalente and dominio
    return {'ok':True,'correcto':correcto,'mensaje':'Respuesta comprobada.' if correcto else ('La expresión coincide, pero introduce restricciones de dominio. Escribe una forma válida en todo x real.' if equivalente else 'Todavía no coincide. Revisa la pista y vuelve a intentar.'),'respuesta_latex':s.latex(respuesta),'pasos':ejercicio['desarrollo']}

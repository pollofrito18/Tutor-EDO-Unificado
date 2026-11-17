"""Cinco modelos: familias analíticas, fórmulas y supuestos de uso."""
import math
import numpy as np
import sympy as s

MODELOS = {
 'enfriamiento': {'nombre':'Enfriamiento de Newton','simbolo':'T','unidad':'Temperatura (°C)','tiempo':'minutos','referencia':'Temperatura ambiente (°C)','tasa':'k (por minuto)','inicial':80.,'ref':25.,'k':.1,'final':20.,
  'formula':r'T(t)=T_a+(T_0-T_a)e^{-kt}',
  'importancia':'Estimar cómo una bebida o un objeto se aproxima a la temperatura del ambiente.',
  'supuestos':'Ambiente constante, temperatura uniforme del objeto y coeficiente k constante. No se usa como criterio de seguridad alimentaria.',
  'ejemplo':'Con T0=80 °C, Ta=25 °C y k=0.1 por minuto: T(10)=45.23 °C.'},
 'exponencial': {'nombre':'Crecimiento exponencial','simbolo':'P','unidad':'Cantidad','tiempo':'unidades de tiempo','referencia':'Referencia no utilizada','tasa':'r (por unidad de tiempo)','inicial':10.,'ref':100.,'k':.1,'final':10.,
  'formula':r'P(t)=P_0e^{rt}',
  'importancia':'Comparar etapas de crecimiento proporcional cuando la limitación de recursos todavía es pequeña.',
  'supuestos':'Tasa proporcional constante y ausencia de límites de recursos. No describe un crecimiento ilimitado real a largo plazo.',
  'ejemplo':'Con P0=10 y r=0.1: P(10)=27.18 unidades aproximadamente.'},
 'logistica': {'nombre':'Crecimiento logístico','simbolo':'P','unidad':'Población','tiempo':'unidades de tiempo','referencia':'Capacidad K','tasa':'r (por unidad de tiempo)','inicial':10.,'ref':100.,'k':.1,'final':30.,
  'formula':r'P(t)=\frac{KP_0}{P_0+(K-P_0)e^{-rt}}',
  'importancia':'Estudiar cómo una población se aproxima a una capacidad bajo recursos limitados.',
  'supuestos':'Capacidad y tasa constantes; población continua y no negativa. Es una idealización y no obliga a que cada valor sea entero.',
  'ejemplo':'Con P0=10, K=100 y r=0.1: P(10)=23.20 aproximadamente.'},
 'velocidad': {'nombre':'Velocidad con resistencia lineal','simbolo':'v','unidad':'Velocidad (m/s)','tiempo':'segundos','referencia':'Velocidad límite (m/s)','tasa':'k (por segundo)','inicial':0.,'ref':30.,'k':.2,'final':15.,
  'formula':r'v(t)=v_\infty+(v_0-v_\infty)e^{-kt}',
  'importancia':'Explorar cómo una resistencia proporcional a la velocidad produce una velocidad límite.',
  'supuestos':'Movimiento en una dimensión, fuerza motriz constante y resistencia lineal. La aceleración motriz del modelo es k por la velocidad límite.',
  'ejemplo':'Con v0=0, velocidad límite 30 m/s y k=0.2 por segundo: v(10)=25.94 m/s.'},
 'mezcla': {'nombre':'Mezcla en un tanque','simbolo':'A','unidad':'Soluto (g)','tiempo':'minutos','referencia':'Cantidad de equilibrio (g)','tasa':'q/V (por minuto)','inicial':0.,'ref':100.,'k':.02,'final':40.,
  'formula':r'A(t)=A_\infty+(A_0-A_\infty)e^{-(q/V)t}',
  'importancia':'Calcular cómo cambia la cantidad de soluto al entrar y salir líquido de un tanque.',
  'supuestos':'Tanque de 100 L, mezcla uniforme y caudales de entrada y salida iguales. q=100k L/min y concentración de entrada=A∞/100 g/L.',
  'ejemplo':'Con A0=0 g, A∞=100 g y q/V=0.02 por minuto: A(20)=32.97 g.'},
}


def validar(clave,k,ref,final,inicial_min,inicial_max,puntos):
    if clave not in MODELOS or not all(math.isfinite(float(v)) for v in [k,ref,final,inicial_min,inicial_max]):
        raise ValueError('Modelo o parámetros no válidos.')
    if not .001<=k<=1 or not 1<=ref<=1000 or not 0<final<=100:
        raise ValueError('Usa una tasa entre 0.001 y 1, referencia de 1 a 1000 y tiempo de 0 a 100.')
    if not 0<=inicial_min<inicial_max<=1000 or type(puntos) is not int or not 10<=puntos<=120:
        raise ValueError('Usa iniciales crecientes entre 0 y 1000 y de 10 a 120 puntos.')
    if clave=='exponencial' and k*final>15:
        raise ValueError('Reduce el tiempo o la tasa para mantener el crecimiento dentro del rango de esta simulación.')


def ecuacion(clave,k,ref):
    if clave=='exponencial': return f"y'=({k})*y"
    if clave=='logistica': return f"y'=({k})*y*(1-y/({ref}))"
    return f"y'=-({k})*(y-({ref}))"


def evaluar(clave,k,ref,t,inicial):
    if clave=='exponencial': return inicial*np.exp(k*t)
    if clave=='logistica': return ref*inicial/(inicial+(ref-inicial)*np.exp(-k*t))
    return ref+(inicial-ref)*np.exp(-k*t)


def comprobar_formula(clave,k,ref):
    t=s.Symbol('t',nonnegative=True)
    u=s.Symbol('u',nonnegative=True)
    K,R=s.Rational(str(k)),s.Rational(str(ref))
    if clave=='exponencial':
        f=u*s.exp(K*t); rhs=K*f
    elif clave=='logistica':
        f=R*u/(u+(R-u)*s.exp(-K*t)); rhs=K*f*(1-f/R)
    else:
        f=R+(u-R)*s.exp(-K*t); rhs=-K*(f-R)
    return s.simplify(s.diff(f,t)-rhs)==0 and s.simplify(f.subs(t,0)-u)==0


def familia(clave,k,ref,final,inicial_min,inicial_max,puntos=60):
    validar(clave,k,ref,final,inicial_min,inicial_max,puntos)
    tiempos=np.linspace(0,final,puntos)
    iniciales=np.linspace(inicial_min,inicial_max,puntos)
    t,i=np.meshgrid(tiempos,iniciales)
    z=evaluar(clave,k,ref,t,i)
    if not np.isfinite(z).all(): raise ValueError('El modelo deja de ser finito.')
    return {'ok':True,'t':tiempos.tolist(),'iniciales':iniciales.tolist(),'z':z.tolist(),
            'formula':MODELOS[clave]['formula'],'verificado':bool(comprobar_formula(clave,k,ref))}

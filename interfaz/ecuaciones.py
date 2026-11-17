"""Recorrido completo: entrada, cálculo aislado, resultado y persistencia."""
import streamlit as st
from ejemplos import EJEMPLOS
from nucleo.motor import METODOS
from servicio import calcular
from .componentes import encabezado, mostrar_solucion, mostrar_numerico, avisar


def ejecutar(db,token,datos,tipo,titulo):
    db.cuota(token,'calculo')
    with st.spinner('Calculando y comprobando…'):
        r=calcular(datos)
    rid=None
    if r.get('ok'):
        rid=db.guardar(token,tipo,titulo,datos,r)
        avisar('Resultado guardado en tu historial.')
    else:
        avisar(r.get('error','No se pudo calcular.'),'error',True)
    return r,rid


def panel(db,token):
    encabezado('Resolver ecuaciones','Clasifica, sigue cada operación y comprueba la solución.')
    if 'restaurar_ecuacion' in st.session_state:
        datos=st.session_state.pop('restaurar_ecuacion')
        for k in ['ecuacion','M','N','metodo','x0','y0','yp0','usar_inicial']:
            if k in datos:st.session_state['ec_'+k]=datos[k]
        st.session_state['ec_formato']=datos.get('formato','ecuacion')
        st.session_state.pop('solucion',None);st.session_state.pop('numerico',None)
    for k,v in {'ecuacion':"y'=2*x*y",'M':'2*x*y+1','N':'x^2+2*y','x0':'0','y0':'1','yp0':'0','metodo':'auto','usar_inicial':True,'formato':'ecuacion'}.items():
        st.session_state.setdefault('ec_'+k,v)
    with st.expander('Cargar un ejemplo del curso'):
        ejemplo=st.selectbox('Ejemplo',list(EJEMPLOS))
        if st.button('Cargar ejemplo'):
            st.session_state.restaurar_ecuacion={**EJEMPLOS[ejemplo],'usar_inicial':True}
            st.rerun()
    formato=st.radio('Forma de entrada',['ecuacion','mn'],format_func=lambda x:"Ecuación con y'" if x=='ecuacion' else 'M dx + N dy = 0',horizontal=True,key='ec_formato')
    with st.form('resolver'):
        if formato=='ecuacion':
            entrada={'formato':formato,'ecuacion':st.text_input('Ecuación',key='ec_ecuacion',max_chars=350,help="Ejemplos: y' + 2*y = x; y'' + 2*y' + y = exp(-x). Usa * para multiplicar.")}
        else:
            entrada={'formato':formato,'M':st.text_input('M(x,y)',key='ec_M',max_chars=350),'N':st.text_input('N(x,y)',key='ec_N',max_chars=350)}
        entrada['metodo']=st.selectbox('Clase o método de ecuación',list(METODOS),format_func=METODOS.get,key='ec_metodo')
        entrada['usar_inicial']=st.checkbox('Aplicar condición inicial',key='ec_usar_inicial')
        a,b,c=st.columns(3)
        entrada['x0']=a.text_input('x inicial',key='ec_x0',max_chars=100)
        entrada['y0']=b.text_input('y inicial',key='ec_y0',max_chars=100)
        entrada['yp0']=c.text_input("y' inicial (segundo orden)",key='ec_yp0',max_chars=100)
        enviar=st.form_submit_button('Resolver paso a paso',type='primary')
    if enviar:
        st.session_state.ultima_entrada=dict(entrada)
        st.session_state.pop('numerico',None)
        r,rid=ejecutar(db,token,entrada,'ecuacion',entrada.get('ecuacion','Ecuación diferencial en M y N'))
        st.session_state.solucion=r
        st.session_state.resultado_actual=rid
    if 'solucion' in st.session_state:
        r=st.session_state.solucion
        st.caption('Los resultados corresponden a la última entrada enviada. Editar los campos requiere volver a resolver.')
        mostrar_solucion(r)
        if r.get('ok'):
            if r.get('clave') != 'segundo_orden':
                with st.expander('Comparar con otra clase aplicable'):
                    aplicables=[k for k,v in METODOS.items() if v in r['metodos']]
                    if aplicables:
                        otro=st.selectbox('Método alternativo',aplicables,format_func=METODOS.get)
                        if st.button('Resolver con este método'):
                            nueva=dict(st.session_state.ultima_entrada,metodo=otro)
                            r,rid=ejecutar(db,token,nueva,'ecuacion','Comparación: '+METODOS[otro])
                            st.session_state.solucion=r;st.session_state.resultado_actual=rid
                            st.session_state.ultima_entrada=nueva;st.rerun()
            if st.button('Consultar este resultado con el tutor'):
                st.session_state.contexto_tutor=st.session_state.resultado_actual
                st.session_state.ir='Tutor NVIDIA';st.rerun()
        if r.get('clave') == 'segundo_orden':
            st.info('La gráfica y la aproximación numérica actualmente están disponibles para EDO de primer orden.')
        else:
            st.divider()
            st.subheader('Gráfica y comparación numérica')
            st.write('Puedes aproximar también ecuaciones para las que el motor no encontró un procedimiento simbólico.')
            with st.form('form_numerico'):
                c1,c2,c3=st.columns(3)
                nx=c1.text_input('x inicial numérico',st.session_state.ultima_entrada.get('x0','0'))
                ny=c2.text_input('y inicial numérico',st.session_state.ultima_entrada.get('y0','1'))
                xf=c3.text_input('x final','1')
                n=st.slider('Subintervalos',4,1000,80)
                comparar=st.form_submit_button('Calcular gráfica y tabla')
            if comparar:
                datos=dict(st.session_state.ultima_entrada,accion='numerico',x0=nx,y0=ny,xf=xf,n=n)
                r,_=ejecutar(db,token,datos,'numerico','Comparación Euler, RK4 y SciPy')
                st.session_state.numerico=r
            if 'numerico' in st.session_state:mostrar_numerico(st.session_state.numerico)
    with st.expander('Sintaxis y alcance'):
        st.table([{'Operación':'Multiplicación','Escritura':'2*x*y'}, {'Operación':'Potencias','Escritura':'x^2 o x**2'}, {'Operación':'Derivadas','Escritura':"y', dy/dx, y'' o d2y/dx2"}, {'Operación':'Funciones','Escritura':'exp(x), log(x), sqrt(x), sin(x), cos(x), tan(x), abs(x)'}, {'Operación':'Constantes','Escritura':'pi, e, E, 1/2'}])
        st.write("El motor explica EDO de primer orden: separables, lineales, exactas y algunos factores integrantes. También resuelve EDO lineales de segundo orden con coeficientes constantes y dos datos iniciales. La aproximación numérica disponible es para primer orden. No cubre cualquier ecuación, coeficientes variables, sistemas ni derivadas parciales. Las restricciones de dominio se conservan antes de simplificar.")

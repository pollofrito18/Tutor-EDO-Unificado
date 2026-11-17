import streamlit as st
from modulos.contenido import LECCIONES,EJERCICIOS
from servicio import calcular
from .componentes import encabezado,avisar,mostrar_integral,json_descarga


def panel(db,token):
    encabezado('Aprender y practicar','Entiende el cambio, aprende el método y comprueba lo aprendido.','libro')
    p=db.progreso(token)
    st.progress(len(p['lecciones'])/len(LECCIONES),text=f"{len(p['lecciones'])} de {len(LECCIONES)} lecciones completadas")
    ruta=st.radio('Área de aprendizaje',['Lecciones','Práctica','Laboratorio de integrales'],horizontal=True)
    if ruta=='Lecciones':
        clave=st.selectbox('Lección',list(LECCIONES),format_func=lambda k:LECCIONES[k]['titulo'])
        l=LECCIONES[clave]
        st.caption(l['nivel'])
        st.write('**Por qué importa**')
        st.write(l['importancia'])
        for i,(titulo,texto,formula) in enumerate(l['pasos'],1):
            with st.container(border=True):
                st.subheader(f'{i}. {titulo}')
                st.write(texto);st.latex(formula)
        st.info('Consejo: '+l['tip'])
        st.warning('Error frecuente: '+l['error'])
        if clave in p['lecciones']: st.success('Ya completaste esta lección. Puedes repasarla cuando quieras.')
        elif st.button('Marcar lección como completada',type='primary'):
            db.completar(token,clave);st.session_state.aviso_pendiente=('Progreso guardado.','aprendizaje')
            st.rerun()
    elif ruta=='Práctica':
        st.caption(f"Intentos guardados: {p['intentos']} · Respuestas correctas: {p['correctos']}")
        clave=st.selectbox('Ejercicio',list(EJERCICIOS),format_func=lambda k:EJERCICIOS[k]['enunciado'])
        e=EJERCICIOS[clave]
        st.write(e['enunciado'])
        with st.form('form_practica'):
            respuesta=st.text_input('Tu respuesta',max_chars=350,help='Usa * para multiplicar y exp(x) para la exponencial.')
            enviar=st.form_submit_button('Comprobar respuesta',type='primary')
        if enviar:
            db.cuota(token,'calculo')
            r=calcular({'accion':'practica','ejercicio':clave,'respuesta':respuesta})
            st.session_state.practica=(clave,r)
            if r.get('ok'):
                db.intento(token,clave,respuesta,r['correcto'])
                if r['correcto']:avisar(r['mensaje'],'aprendizaje')
        if 'practica' in st.session_state and st.session_state.practica[0]==clave:
            r=st.session_state.practica[1]
            if not r.get('ok'):st.warning(r['error'])
            elif r['correcto']:st.success(r['mensaje']);st.latex(r['respuesta_latex'])
            else:st.info(r['mensaje'])
        with st.expander('Ver pista'): st.write(e['pista'])
        with st.expander('Estudiar la solución explicada'):
            for f,texto in e['desarrollo']:st.write(texto);st.latex(f)
    else:
        st.write('Explora reglas de integración con un árbol de pasos. Este laboratorio trabaja en x>0, además de las restricciones propias de la expresión.')
        with st.form('form_integral'):
            expr=st.text_input('Función a integrar respecto a x','2*x*exp(x^2)',max_chars=350)
            enviar=st.form_submit_button('Explicar integral',type='primary')
        if enviar:
            db.cuota(token,'calculo')
            with st.spinner('Desarrollando las reglas…'):
                r=calcular({'accion':'integral','expresion':expr})
            st.session_state.integral=r
            if r.get('ok'):
                db.guardar(token,'integral','Integral: '+expr,{'expresion':expr},r)
                avisar('Integral guardada en tu historial.')
        if 'integral' in st.session_state:
            mostrar_integral(st.session_state.integral)
            if st.session_state.integral.get('ok'):json_descarga('Descargar desarrollo JSON',st.session_state.integral,'integral.json','int_json')

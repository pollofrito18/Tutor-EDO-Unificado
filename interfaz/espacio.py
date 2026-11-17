import json
import streamlit as st
from configuracion import nvidia_disponible
from modulos.nvidia import explicar
from .componentes import encabezado,mostrar_solucion,mostrar_numerico,mostrar_integral,json_descarga,avisar,fecha,tono


def historial(db,token):
    encabezado('Mi historial','Recupera entradas y conserva los resultados tal como se calcularon.')
    tipos={'Todos':None,'Ecuaciones':'ecuacion','Comparación numérica':'numerico','Modelos':'modelo','Escenarios 3D':'grafica3d','Integrales':'integral'}
    filtro=st.selectbox('Clase de resultado',list(tipos))
    registros=db.resultados(token,tipos[filtro])
    if not registros:st.info('Los resultados aparecerán aquí al resolver o guardar un escenario.');return
    buscar=st.text_input('Buscar en los últimos 200 resultados',max_chars=100)
    registros=[r for r in registros if buscar.casefold() in r['titulo'].casefold()]
    if not registros:st.info('No hay coincidencias con esa búsqueda.');return
    etiquetas={r['id']:r for r in registros}
    seleccionado=st.selectbox('Resultado guardado',list(etiquetas),format_func=lambda k:fecha(etiquetas[k]['creado'])+' · '+etiquetas[k]['titulo'])
    reg=db.resultado(token,seleccionado);r=reg['resultado']
    st.caption('Tipo: '+reg['tipo']+' · Fecha: '+fecha(reg['creado']))
    json_descarga('Descargar registro completo JSON',reg,'resultado.json','hist_json')
    if reg['tipo']=='ecuacion':
        mostrar_solucion(r,'hist_sol')
        if st.button('Recuperar entrada para resolver'):
            st.session_state.restaurar_ecuacion=reg['entrada'];st.session_state.ir='Resolver';st.rerun()
    elif reg['tipo']=='numerico':
        mostrar_numerico(r,'hist_num')
    elif reg['tipo']=='grafica3d':
        from .graficas import mostrar_snapshot
        mostrar_snapshot(r,'hist_g')
        if st.button('Recuperar parámetros para editar'):
            st.session_state.restaurar_grafica=reg['entrada'];st.session_state.grafica_restaurada=True
            st.session_state.ir='Modelos y 3D';st.rerun()
    elif reg['tipo']=='modelo':
        mostrar_solucion(r['simbolico'],'hist_modelo');mostrar_numerico(r['numerico'],'hist_modelonum')
    elif reg['tipo']=='integral':mostrar_integral(r,'hist_int')
    if reg['tipo'] in ('ecuacion','modelo') and st.button('Abrir este resultado con el tutor'):
        st.session_state.contexto_tutor=reg['id'];st.session_state.ir='Tutor NVIDIA';st.rerun()


def contexto_de(registro):
    if not registro:return {}
    r=registro['resultado']
    if registro['tipo']=='modelo':r=r.get('simbolico',{})
    if not r.get('ok'):return {'nota':'El motor no obtuvo un resultado simbólico.'}
    return {'ecuacion':r.get('ecuacion_latex'),'metodo':r.get('metodo'),
            'resultado_latex':r.get('particular') or r.get('general'), 'pasos':r.get('pasos',[]), 'verificado':r.get('verificado',False)}


def tutor(db,token):
    encabezado('Tutor NVIDIA','Pregunta por un paso, una fórmula o la interpretación de un resultado.','libro')
    st.info('Al enviar, NVIDIA recibirá tu pregunta, el procedimiento asociado y hasta seis mensajes anteriores. La cuenta y la contraseña no se incluyen.')
    if not nvidia_disponible():
        st.warning('Tutor pendiente de configurar: añade NVIDIA_API_KEY y NVIDIA_MODEL al archivo .env del servidor y reinicia la aplicación. El motor y las gráficas están disponibles.')
    if 'contexto_tutor' in st.session_state:
        rid=st.session_state.pop('contexto_tutor')
        reg=db.resultado(token,rid)
        cid=db.nueva_conversacion(token,reg['titulo'],rid)
        st.session_state.conversacion=cid
    conversaciones=db.conversaciones(token)
    if st.button('Crear conversación general'):
        cid=db.nueva_conversacion(token,'Consulta general')
        st.session_state.conversacion=cid;st.rerun()
    if not conversaciones:st.write('Crea una conversación o abre un resultado desde Resolver o Mi historial.');return
    mapa={c['id']:c for c in conversaciones}
    if st.session_state.get('conversacion') not in mapa:st.session_state.conversacion=conversaciones[0]['id']
    cid=st.selectbox('Conversación',list(mapa),format_func=lambda k:mapa[k]['titulo'],key='conversacion')
    reg=db.resultado(token,mapa[cid]['resultado_id']) if mapa[cid]['resultado_id'] else None
    if reg:st.caption('Contexto fijo de esta conversación: '+reg['titulo'])
    mensajes=db.mensajes(token,cid)
    for m in mensajes:
        with st.container(border=True):
            st.write('**Tu pregunta**' if m['role']=='user' else '**Tutor NVIDIA · explicación de IA**')
            st.markdown(m['content'],unsafe_allow_html=False)
    if mensajes:json_descarga('Descargar conversación',mensajes,'conversacion.json','chat_json')
    st.caption('Las explicaciones de IA no se marcan como cálculos verificados. Contrasta fórmulas nuevas con el motor.')
    with st.form('tutor_form',clear_on_submit=True):
        pregunta=st.text_area('Pregunta',max_chars=1500,placeholder='¿Por qué hay que revisar y=0 antes de dividir?')
        enviar=st.form_submit_button('Enviar pregunta a NVIDIA',disabled=not nvidia_disponible(),type='primary')
    if enviar:
        if not pregunta.strip():st.warning('Escribe una pregunta.');return
        db.cuota(token,'tutor')
        try:
            with st.spinner('Esperando la explicación de NVIDIA…'):
                r=explicar(pregunta,contexto_de(reg),mensajes)
            db.guardar_dialogo(token,cid,pregunta,r['texto'])
            st.session_state.aviso_pendiente=('Respuesta guardada.','tutor')
            st.rerun()
        except (ValueError,RuntimeError) as e:avisar(str(e),'error',True)


def notificaciones(db,token):
    encabezado('Notificaciones','Resultados, respuestas del tutor y avances de aprendizaje.','campana')
    registros=db.notificaciones(token)
    solo=st.checkbox('Mostrar solo no leídas',value=True)
    if st.button('Marcar todas como leídas'):
        db.leer_notificaciones(token);st.rerun()
    visibles=[r for r in registros if not solo or not r['leida']]
    if not visibles:st.info('No hay notificaciones pendientes.')
    for n in visibles:
        with st.container(border=True):
            st.write(n['texto']);st.caption(fecha(n['creado'])+' · '+('Leída' if n['leida'] else 'No leída'))
            if not n['leida'] and st.button('Marcar como leída',key='n_'+n['id']):
                db.leer_notificaciones(token,n['id']);st.rerun()


def ajustes(db,token):
    encabezado('Perfil y preferencias','Ajusta la lectura, los colores y los avisos.')
    perfil=db.perfil(token);p=perfil['preferencias']
    st.caption('Usuario: '+perfil['usuario'])
    with st.form('preferencias'):
        nombre=st.text_input('Nombre visible',perfil['nombre'],max_chars=80)
        fuente=st.selectbox('Tamaño del texto',[16,18,20,22],index=[16,18,20,22].index(p['fuente']))
        color=st.selectbox('Color preferido para las gráficas',['Azul','Rojo','Amarillo'],index=['Azul','Rojo','Amarillo'].index(p['color']))
        sonidos=st.checkbox('Activar sonidos',p['sonidos'])
        volumen=st.slider('Volumen',0,100,p['volumen'])
        eventos=st.multiselect('Eventos con sonido',['resultado','aprendizaje','tutor','error'],p['eventos'])
        enviar=st.form_submit_button('Guardar preferencias',type='primary')
    if enviar:
        db.preferencias(token,nombre,dict(fuente=fuente,color=color,sonidos=sonidos,volumen=volumen,eventos=eventos))
        st.session_state.aviso_pendiente=('Preferencias guardadas.','resultado');st.rerun()
    st.caption('Los sonidos están desactivados inicialmente. El navegador puede bloquear la reproducción automática; cada aviso tiene también un mensaje visible.')
    if st.button('Probar sonido con el volumen guardado'):
        st.audio(tono('resultado',p['volumen']),format='audio/wav',autoplay=True)
    with st.expander('Cambiar contraseña'):
        with st.form('clave'):
            actual=st.text_input('Contraseña actual',type='password',max_chars=128)
            nueva=st.text_input('Nueva contraseña',type='password',max_chars=128)
            repetir=st.text_input('Repetir contraseña nueva',type='password',max_chars=128)
            cambiar=st.form_submit_button('Cambiar contraseña y cerrar sesiones')
        if cambiar:
            if nueva!=repetir:st.warning('Las contraseñas nuevas no coinciden.')
            else:
                db.cambiar_clave(token,actual,nueva)
                st.session_state.clear();st.rerun()
    with st.expander('Exportar mi información'):
        datos={'perfil':perfil,'resultados':db.resultados(token),'progreso':db.progreso(token),
               'conversaciones':[dict(c,mensajes=db.mensajes(token,c['id'])) for c in db.conversaciones(token)],'notificaciones':db.notificaciones(token)}
        st.caption('Incluye los últimos 200 resultados, 100 conversaciones y 100 mensajes por conversación, además del progreso y las preferencias.')
        json_descarga('Descargar mis datos JSON',datos,'mis_datos_tutor.json','perfil_json')

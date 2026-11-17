"""Modelos, superficies 3D y curvas ligadas al motor y al historial."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modulos.modelos import MODELOS,familia,evaluar,ecuacion
from servicio import calcular
from .componentes import COLORES,encabezado,mostrar_solucion,mostrar_numerico,avisar

VISTAS={'Perspectiva':dict(x=1.6,y=1.6,z=1.2),'Frontal':dict(x=0,y=-2.5,z=.3),'Superior':dict(x=.01,y=.01,z=2.5)}


def figura(snapshot):
    d=snapshot['familia'];p=snapshot['parametros'];m=MODELOS[p['modelo']]
    color=COLORES.get(p['color'],COLORES['Azul'])
    fig=go.Figure(go.Surface(x=d['t'],y=d['iniciales'],z=d['z'],colorscale=[[0,'#EFF4FF'],[1,color]],opacity=.8,
        name='Familia de soluciones',colorbar=dict(title=m['simbolo']),
        hovertemplate='Tiempo: %{x:.3f}<br>Dato inicial: %{y:.3f}<br>Resultado: %{z:.5g}<extra></extra>'))
    curva=snapshot['curva']
    fig.add_trace(go.Scatter3d(x=d['t'],y=[p['inicial']]*len(d['t']),z=curva,mode='lines',
        line=dict(color='#B91C1C' if p['color']!='Rojo' else '#1746B6',width=7),name='Curva seleccionada'))
    fig.update_layout(template='plotly_white',height=550,margin=dict(l=0,r=0,t=20,b=0),
       scene=dict(xaxis_title='Tiempo ('+m['tiempo']+')',yaxis_title='Dato inicial',zaxis_title=m['unidad'],camera=dict(eye=VISTAS[p['vista']])),
       legend=dict(orientation='h'),uirevision=p['vista']+p['modelo'])
    return fig


def mostrar_snapshot(snapshot,key='g3'):
    d=snapshot['familia'];p=snapshot['parametros'];m=MODELOS[p['modelo']]
    st.latex(d['formula'])
    f=figura(snapshot)
    st.plotly_chart(f,width='stretch',key=key+'_3d',config={'displaylogo':False,'scrollZoom':True,'toImageButtonOptions':{'format':'png','filename':'modelo_3d'}})
    st.caption('Arrastra para rotar y usa la rueda para acercar. La barra permite restaurar la cámara y guardar una imagen. Las vistas predefinidas se pueden seleccionar con teclado.')
    a,b=st.columns(2)
    a.metric('Dato inicial',f"{p['inicial']:.4g}")
    b.metric('Resultado al tiempo final',f"{snapshot['curva'][-1]:.6g}")
    df=pd.DataFrame({'Tiempo':d['t'],m['unidad']:snapshot['curva']})
    grafica=go.Figure(go.Scatter(x=d['t'],y=snapshot['curva'],mode='lines',name='Solución analítica',line=dict(color=COLORES[p['color']],width=3)))
    grafica.update_layout(template='plotly_white',height=320,xaxis_title='Tiempo ('+m['tiempo']+')',yaxis_title=m['unidad'])
    st.plotly_chart(grafica,width='stretch',key=key+'_2d',config={'displaylogo':False})
    with st.expander('Tabla accesible de la curva seleccionada'):
        st.dataframe(df,hide_index=True)
    st.download_button('Descargar curva CSV',df.to_csv(index=False),'curva_modelo.csv','text/csv',key=key+'_csv')
    st.download_button('Descargar gráfica 3D interactiva',f.to_html(include_plotlyjs=True),'modelo_3d.html','text/html',key=key+'_html')
    st.caption('El HTML incluye el visor y abre sin conexión en un navegador con WebGL. Los ejes representan tiempo, dato inicial y resultado: cada corte es una solución de la misma ecuación.')


def panel(db,token):
    encabezado('Modelos y laboratorio 3D','Explora cómo cambian las soluciones al modificar sus parámetros.','cubo')
    restaurado = 'restaurar_grafica' in st.session_state
    st.session_state.pop('grafica_restaurada',None)
    if restaurado:
        restaurar=st.session_state.pop('restaurar_grafica')
        for k,v in restaurar.items():st.session_state['g_'+k]=v
    clave=st.selectbox('Modelo',list(MODELOS),format_func=lambda k:MODELOS[k]['nombre'],key='g_modelo')
    m=MODELOS[clave]
    if st.session_state.get('modelo_previo')!=clave:
        st.session_state.modelo_previo=clave
        # Restaurar el historial tiene prioridad; al cambiar de modelo se usan sus unidades y valores iniciales.
        if not restaurado:
            for k,v in {'k':m['k'],'ref':m['ref'],'final':m['final'],'minimo':0.,'maximo':100.,'inicial':m['inicial']}.items():st.session_state['g_'+k]=v
    st.write('**Para qué sirve:** '+m['importancia'])
    with st.expander('Supuestos y ejemplo con resultado',expanded=True):st.write(m['supuestos']);st.write(m['ejemplo'])
    c1,c2=st.columns(2)
    k=c1.slider(m['tasa'],min_value=.001,max_value=1.,step=.001,key='g_k')
    ref=c2.number_input(m['referencia'],1.,1000.,key='g_ref',disabled=clave=='exponencial')
    final=st.slider('Tiempo final ('+m['tiempo']+')',1.,100.,key='g_final')
    a,b=st.columns(2)
    minimo=a.number_input('Dato inicial mínimo',0.,999.,key='g_minimo')
    maximo=b.number_input('Dato inicial máximo',1.,1000.,key='g_maximo')
    if minimo>=maximo:st.warning('El dato inicial máximo debe ser mayor que el mínimo.');return
    if not minimo<=st.session_state.get('g_inicial',m['inicial'])<=maximo:st.session_state.g_inicial=(minimo+maximo)/2
    inicial=st.slider('Dato inicial de la curva seleccionada',float(minimo),float(maximo),key='g_inicial')
    with st.expander('Apariencia y precisión de la malla'):
        st.session_state.setdefault('g_puntos',60)
        puntos=st.slider('Puntos por eje',10,120,key='g_puntos')
        pred=st.session_state.perfil['preferencias']['color']
        st.session_state.setdefault('g_color',pred)
        color=st.selectbox('Color principal',list(COLORES),key='g_color')
        vista=st.radio('Vista de cámara',list(VISTAS),horizontal=True,key='g_vista')
    parametros=dict(modelo=clave,k=k,ref=ref,final=final,minimo=minimo,maximo=maximo,inicial=inicial,puntos=puntos,color=color,vista=vista)
    try:
        d=familia(clave,k,ref,final,minimo,maximo,puntos)
        curva=evaluar(clave,k,ref,np.array(d['t']),inicial).tolist()
    except ValueError as e:st.warning(str(e));return
    snap={'parametros':parametros,'familia':d,'curva':curva}
    if d['verificado']:st.caption('La fórmula de la familia cumple simbólicamente la ecuación y el dato inicial.')
    mostrar_snapshot(snap)
    if st.button('Guardar escenario 3D en mi historial',type='primary'):
        db.guardar(token,'grafica3d',m['nombre']+' · escenario 3D',parametros,snap)
        avisar('Escenario guardado con parámetros y valores.')
    solicitud={'ecuacion':ecuacion(clave,k,ref),'metodo':'auto','usar_inicial':True,'x0':'0','y0':str(inicial)}
    firma=str(parametros)
    if st.button('Resolver y comparar la curva seleccionada'):
        db.cuota(token,'calculo')
        with st.spinner('Resolviendo y comparando el modelo…'):
            simb=calcular(solicitud)
            num=calcular(dict(solicitud,accion='numerico',xf=str(final),n=200))
        paquete={'simbolico':simb,'numerico':num,'parametros':parametros}
        if simb.get('ok') or num.get('ok'):
            rid=db.guardar(token,'modelo',m['nombre']+' · procedimiento',solicitud,paquete)
            st.session_state.resultado_actual=rid
            avisar('Procedimiento del modelo guardado.')
        st.session_state.modelo_resuelto=(firma,paquete)
    if 'modelo_resuelto' in st.session_state and st.session_state.modelo_resuelto[0]==firma:
        paq=st.session_state.modelo_resuelto[1]
        mostrar_solucion(paq['simbolico'],'modelo_sol')
        mostrar_numerico(paq['numerico'],'modelo_num')
        if paq['numerico'].get('ok'):
            filas=paq['numerico']['filas'];t=np.array([f['x'] for f in filas]);val=np.array([f['RK4'] for f in filas])
            error=float(np.max(np.abs(val-evaluar(clave,k,ref,t,inicial))))
            st.metric('Error máximo RK4 frente a la fórmula en los puntos de la tabla',f'{error:.4g}')
        if st.button('Preguntar al tutor sobre este modelo'):
            st.session_state.contexto_tutor=st.session_state.resultado_actual;st.session_state.ir='Tutor NVIDIA';st.rerun()

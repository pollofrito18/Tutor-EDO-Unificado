"""Componentes de interfaz compartidos, iconos SVG y avisos opcionales."""
import io
import json
import math
import wave
import struct
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
from servicio import a_markdown

COLORES={'Azul':'#1746B6','Rojo':'#B91C1C','Amarillo':'#946B00'}
ICONOS={
 'libro':'M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4V4m9 3a3 3 0 0 1 3-3h5v15h-4a4 4 0 0 0-4 2',
 'curva':'M3 3v18h18M6 16c3 0 3-9 6-9s3 7 8-2',
 'cubo':'m12 2 9 5v10l-9 5-9-5V7l9-5m0 10 9-5M12 12 3 7m9 5v10',
 'campana':'M5 17h14l-2-4V9a5 5 0 0 0-10 0v4l-2 4m5 3h4',
}


def estilo(fuente=18):
    fuente=fuente if fuente in (16,18,20,22) else 18
    css=Path(__file__).with_name('estilo.css').read_text()
    st.markdown('<style>'+css+f'html {{font-size:{fuente}px;}}'+ '</style>',unsafe_allow_html=True)


def encabezado(titulo,descripcion,icono='curva'):
    svg=f'<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="{ICONOS[icono]}"/></svg>'
    st.markdown(f'<div class="titulo-app">{svg}<div><h1>{escape(titulo)}</h1><p>{escape(descripcion)}</p></div></div>',unsafe_allow_html=True)


def fecha(segundos):
    return datetime.fromtimestamp(segundos,timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def tono(evento='resultado',volumen=30):
    frecuencia={'resultado':660,'aprendizaje':880,'tutor':550,'error':330}.get(evento,660)
    volumen=max(0,min(100,int(volumen)))/100
    frecuencia_muestreo=22050
    salida=io.BytesIO()
    with wave.open(salida,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(frecuencia_muestreo)
        datos=[]
        duracion=.22
        for n in range(int(frecuencia_muestreo*duracion)):
            t=n/frecuencia_muestreo
            envolvente=min(t/.02,1,(duracion-t)/.04)
            datos.append(struct.pack('<h',int(10000*volumen*envolvente*math.sin(2*math.pi*frecuencia*t))))
        w.writeframes(b''.join(datos))
    return salida.getvalue()


def avisar(texto,evento='resultado',error=False):
    (st.error if error else st.success)(texto)
    p=st.session_state.get('perfil',{}).get('preferencias',{})
    if p.get('sonidos') and evento in p.get('eventos',[]) and p.get('volumen',0)>0:
        st.audio(tono(evento,p['volumen']),format='audio/wav',autoplay=True)


def json_descarga(etiqueta,datos,archivo,key):
    st.download_button(etiqueta,json.dumps(datos,ensure_ascii=False,indent=2,allow_nan=False),archivo,'application/json',key=key)


def mostrar_solucion(r,key='sol'):
    if not r.get('ok'):
        st.warning(r.get('error','No se completó el cálculo.'));return
    st.subheader('Resultado y procedimiento')
    st.latex(r['ecuacion_latex'])
    st.caption('Método: '+r['metodo'])
    if r['verificado']: st.success('Identidad diferencial comprobada en el dominio indicado.')
    else: st.warning('Comprobación simbólica no concluyente. Revisa el procedimiento.')
    if r['integrales_pendientes']: st.info('La solución conserva integrales pendientes; no se presenta como una fórmula elemental completa.')
    st.latex(r.get('particular') or r['general'])
    abiertos=st.checkbox('Mostrar todos los pasos',True,key=key+'_abiertos')
    for i,p in enumerate(r['pasos'],1):
        with st.expander(f"{i}. {p['titulo']}",expanded=abiertos):
            st.write(p['texto'])
            for formula in p['formulas']: st.latex(formula)
    if r['constantes']:
        with st.expander('Soluciones constantes detectadas'):
            st.caption('Se revisan en la ecuación original; las restricciones añadidas al dividir se analizan aparte. La lista puede no cubrir todos los casos singulares.')
            for f in r['constantes']: st.latex(f)
    with st.expander('Dominio y observaciones',expanded=bool(r['restricciones'])):
        for f in r['restricciones']: st.latex(f)
        for nota in r['notas']: st.write(nota)
    st.download_button('Descargar procedimiento Markdown',a_markdown(r),'procedimiento.md','text/markdown',key=key+'_md')


def mostrar_numerico(r,key='num'):
    import pandas as pd
    if not r.get('ok'): st.warning(r.get('error'));return
    df=pd.DataFrame(r['filas'])
    st.latex(r'y\prime=f(x,y)='+r['f_latex'])
    st.write(f"Tamaño de paso h = {r['h']:.6g}")
    colores=['#1746B6','#B91C1C','#946B00']
    f=go.Figure()
    for col,color,dash in zip(['RK4','Referencia_SciPy','Euler'],colores,['solid','dash','dot']):
        if col in df:
            f.add_trace(go.Scatter(x=df['x'],y=df[col],name=col.replace('_',' '),line=dict(color=color,dash=dash,width=2.5)))
    f.update_layout(template='plotly_white',xaxis_title='x',yaxis_title='y(x)',height=400,legend=dict(orientation='h'))
    st.plotly_chart(f,width='stretch',key=key+'_grafica',config={'displaylogo':False})
    st.metric('Diferencia máxima RK4 frente a SciPy',f"{r['diferencia_maxima']:.4g}")
    st.caption(r['nota'])
    if r.get('aviso_euler'): st.warning(r['aviso_euler'])
    with st.expander('Fórmulas y etapas numéricas'):
        st.latex(r'y_{n+1}^{Euler}=y_n+h f(x_n,y_n)')
        st.latex(r'k_1=f(x_n,y_n),\quad k_2=f(x_n+h/2,y_n+hk_1/2)')
        st.latex(r'k_3=f(x_n+h/2,y_n+hk_2/2),\quad k_4=f(x_n+h,y_n+hk_3)')
        st.latex(r'y_{n+1}^{RK4}=y_n+\frac h6(k_1+2k_2+2k_3+k_4)')
        st.dataframe(r['etapas'],hide_index=True)
        if r.get('etapas_euler'): st.dataframe(r['etapas_euler'],hide_index=True)
    with st.expander('Tabla accesible de valores'):
        st.dataframe(df,hide_index=True)
    st.download_button('Descargar valores CSV',df.to_csv(index=False),'valores.csv','text/csv',key=key+'_csv')
    st.download_button('Descargar gráfica interactiva',f.to_html(include_plotlyjs=True),'grafica_2d.html','text/html',key=key+'_html')


def mostrar_integral(r,key='int'):
    if not r.get('ok'): st.warning(r.get('error'));return
    st.latex(r['resultado_latex'])
    if r['verificado']: st.success('La derivada de la antiderivada coincide con la entrada bajo los supuestos indicados.')
    else: st.warning('La comprobación no concluyó; puede haber integrales pendientes.')
    def nodo(n,nivel=1):
        st.write(n['explicacion'])
        for f in n['formulas_latex']:st.latex(f)
        for i,hijo in enumerate(n['subpasos'],1):
            with st.expander(f'Subpaso {nivel}.{i}'): nodo(hijo,nivel+1)
    nodo(r['arbol'])
    if not r['explicacion_completa']: st.info('La explicación detallada de algunas reglas todavía no está disponible; el resultado y la comprobación se muestran por separado.')
    st.caption(r['nota'])
    for f in r.get('restricciones',[]):st.latex(f)

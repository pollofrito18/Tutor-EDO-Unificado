"""Entrada única de Tutor EDO. Todos los módulos usan la misma cuenta y base de datos."""
import logging
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from configuracion import database_url,nvidia_disponible
from datos_app.almacen import Almacen,AccesoError
from interfaz.componentes import estilo,encabezado,avisar

st.set_page_config(page_title='Tutor EDO · aprender, resolver y explorar',layout='wide',initial_sidebar_state='expanded')


@st.cache_resource
def abrir_almacen(url):
    return Almacen(url)


def acceso(db):
    estilo()
    encabezado('Tutor EDO','Aprende el porqué, resuelve paso a paso y explora en 3D.','libro')
    st.write('Un espacio personal para tus ecuaciones, escenarios y avances. Crea una cuenta en esta instalación para empezar.')
    a,b=st.tabs(['Iniciar sesión','Crear cuenta'])
    with a:
        with st.form('login'):
            usuario=st.text_input('Usuario',max_chars=32)
            clave=st.text_input('Contraseña',type='password',max_chars=128)
            enviar=st.form_submit_button('Entrar',type='primary')
        if enviar:
            try:
                token=db.entrar(usuario,clave)
                st.session_state.clear()
                st.session_state.token=token
                st.rerun()
            except ValueError as e:st.error(str(e))
    with b:
        with st.form('registro'):
            usuario=st.text_input('Nombre de usuario',max_chars=32,help='Letras sin acentos, números y guion bajo.')
            nombre=st.text_input('Nombre visible',max_chars=80)
            clave=st.text_input('Crear contraseña',type='password',max_chars=128,help='De 12 a 128 caracteres. Una frase larga es fácil de recordar.')
            repetir=st.text_input('Repetir contraseña',type='password',max_chars=128)
            enviar=st.form_submit_button('Crear mi cuenta')
        if enviar:
            if clave!=repetir:st.error('Las contraseñas no coinciden.')
            else:
                try:
                    db.registrar(usuario,nombre,clave)
                    st.success('Cuenta creada. Ahora puedes iniciar sesión.')
                except ValueError as e:st.error(str(e))
    st.caption('Las credenciales se usan en esta instalación. El tutor externo recibe únicamente las consultas que decidas enviar y su contexto matemático.')


try:
    db=abrir_almacen(database_url())
except Exception as e:
    logging.error('No se pudo inicializar la base: %s',type(e).__name__)
    st.error('No se pudo abrir o migrar la base de datos. Revisa DATABASE_URL, sus permisos y las instrucciones de instalación.')
    st.stop()

if 'token' not in st.session_state:
    acceso(db)
    st.stop()

token=st.session_state.token
try:
    perfil=db.perfil(token)
except AccesoError:
    st.session_state.clear();st.rerun()
st.session_state.perfil=perfil
estilo(perfil['preferencias']['fuente'])
if 'ir' in st.session_state:
    st.session_state.pagina=st.session_state.pop('ir')
with st.sidebar:
    st.title('Tutor EDO')
    st.write(perfil['nombre'])
    nuevas=sum(not n['leida'] for n in db.notificaciones(token))
    st.caption(f'{nuevas} notificaciones sin leer')
    pagina=st.radio('Navegación',['Inicio','Resolver','Modelos y 3D','Aprender','Mi historial','Tutor NVIDIA','Notificaciones','Ajustes'],key='pagina')
    st.divider()
    st.caption('Tutor NVIDIA: '+('configurado' if nvidia_disponible() else 'pendiente de configurar'))
    if st.button('Cerrar sesión'):
        db.salir(token);st.session_state.clear();st.rerun()
if 'aviso_pendiente' in st.session_state:
    texto,evento=st.session_state.pop('aviso_pendiente');avisar(texto,evento)
try:
    if pagina=='Inicio':
        from modulos.contenido import LECCIONES
        encabezado('Entender. Resolver. Explorar.','Tu laboratorio de ecuaciones diferenciales.','libro')
        progreso=db.progreso(token)
        a,b,c=st.columns(3)
        a.metric('Lecciones completadas',f"{len(progreso['lecciones'])}/{len(LECCIONES)}")
        b.metric('Intentos de práctica',progreso['intentos'])
        c.metric('Respuestas correctas',progreso['correctos'])
        st.write('Empieza con una idea concreta: una ecuación diferencial relaciona una cantidad con la rapidez a la que cambia. El motor muestra cómo resolverla y comprueba la identidad matemática cuando puede hacerlo.')
        st.latex(r"T(t)=25+55e^{-0.1t},\quad T(10)\approx45.23\;{}^\circ C")
        st.caption('Una bebida a 80 °C en ambiente de 25 °C, bajo el modelo de Newton con k=0.1 por minuto.')
        for titulo,descripcion,destino in [('Resolver una ecuación','Métodos del curso, dominio, condiciones iniciales y comparación numérica.','Resolver'),('Explorar modelos y 3D','Cinco modelos cotidianos, superficies, parámetros editables y curvas explicadas.','Modelos y 3D'),('Aprender desde lo básico','Diez lecciones, ejercicios con corrección y laboratorio de integrales.','Aprender')]:
            with st.container(border=True):
                st.subheader(titulo);st.write(descripcion)
                if st.button('Abrir '+destino,key='inicio_'+destino):
                    st.session_state.ir=destino;st.rerun()
        st.caption('Python · SymPy · NumPy · SciPy · Plotly · Streamlit. Las ecuaciones admitidas son EDO de primer orden; consulta el alcance en Resolver.')
    elif pagina=='Resolver':
        from interfaz.ecuaciones import panel
        panel(db,token)
    elif pagina=='Modelos y 3D':
        from interfaz.graficas import panel
        panel(db,token)
    elif pagina=='Aprender':
        from interfaz.aprendizaje import panel
        panel(db,token)
    else:
        from interfaz.espacio import historial,tutor,notificaciones,ajustes
        {'Mi historial':historial,'Tutor NVIDIA':tutor,'Notificaciones':notificaciones,'Ajustes':ajustes}[pagina](db,token)
except (ValueError,RuntimeError) as e:
    avisar(str(e),'error',True)
except SQLAlchemyError as e:
    logging.error('Error de persistencia: %s',type(e).__name__)
    st.error('No se pudo completar la operación en la base de datos. No se confirma el guardado. Revisa la conexión y vuelve a intentar.')


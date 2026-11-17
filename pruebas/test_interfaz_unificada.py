import gc
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import streamlit as st
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.pool import NullPool


class Recorridos(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'DATABASE_URL':'sqlite:///'+str(Path(self.tmp.name)/'ui.sqlite3'),'NVIDIA_API_KEY':'','NVIDIA_MODEL':''})
        self.env.start()
        self.engine_factory=patch(
            'datos_app.almacen.create_engine',
            side_effect=lambda *args,**kwargs: sqlalchemy_create_engine(*args,poolclass=NullPool,**kwargs),
        )
        self.engine_factory.start()
        self.app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
    def tearDown(self):
        self.env.stop()
        self.engine_factory.stop()
        st.cache_resource.clear()
        gc.collect()
        self.tmp.cleanup()
    def elem(self,tipo,label):
        return next(e for e in getattr(self.app,tipo) if e.label==label)
    def boton(self,label):
        self.elem('button',label).click().run(timeout=30)
        self.assertFalse(self.app.exception)
    def entrada(self,label,value):self.elem('text_input',label).set_value(value)
    def pagina(self,nombre):
        self.elem('radio','Navegación').set_value(nombre).run(timeout=30)
        self.assertFalse(self.app.exception)
    def cuenta(self,usuario='estudiante'):
        self.entrada('Nombre de usuario',usuario);self.entrada('Nombre visible','Estudiante de prueba')
        self.entrada('Crear contraseña','Frase larga segura 123');self.entrada('Repetir contraseña','Frase larga segura 123')
        self.boton('Crear mi cuenta')
        self.assertFalse(self.app.error)
        self.login(usuario)
    def login(self,usuario):
        self.entrada('Usuario',usuario);self.entrada('Contraseña','Frase larga segura 123');self.boton('Entrar')
        self.assertTrue(self.app.sidebar)
        self.assertFalse(self.app.error)
    def test_recorrido_aprender_resolver_historial(self):
        self.cuenta()
        self.pagina('Aprender');self.boton('Marcar lección como completada')
        self.assertTrue(any('completaste' in s.value for s in self.app.success))
        self.elem('radio','Área de aprendizaje').set_value('Práctica').run()
        self.elem('selectbox','Ejercicio').select('euler').run()
        self.entrada('Tu respuesta','11/10');self.boton('Comprobar respuesta')
        self.assertTrue(any('comprobada' in s.value for s in self.app.success))
        self.pagina('Resolver')
        self.boton('Resolver paso a paso');self.assertFalse(self.app.error)
        self.boton('Calcular gráfica y tabla');self.assertFalse(self.app.error)
        self.pagina('Mi historial')
        self.assertGreaterEqual(len(self.elem('selectbox','Resultado guardado').options),2)
        self.elem('selectbox','Clase de resultado').select('Ecuaciones').run()
        self.boton('Recuperar entrada para resolver')
        self.assertEqual(self.elem('text_input','Ecuación').value,"y'=2*x*y")
        self.pagina('Ajustes')
        self.entrada('Nombre visible','Perfil editado')
        self.elem('checkbox','Activar sonidos').check()
        self.elem('selectbox','Tamaño del texto').select(20)
        self.boton('Guardar preferencias');self.assertFalse(self.app.error)
        self.boton('Cerrar sesión');self.login('estudiante')
        self.pagina('Ajustes')
        self.assertTrue(self.elem('checkbox','Activar sonidos').value)
        self.assertEqual(self.elem('text_input','Nombre visible').value,'Perfil editado')
        self.pagina('Notificaciones');self.boton('Marcar todas como leídas')
        self.assertTrue(any('pendientes' in s.value for s in self.app.info))
    def test_modelos_3d_y_restauracion(self):
        self.cuenta();self.pagina('Modelos y 3D')
        self.assertFalse(self.app.error)
        self.elem('slider','k (por minuto)').set_value(.2).run()
        self.boton('Guardar escenario 3D en mi historial')
        self.boton('Resolver y comparar la curva seleccionada')
        self.assertFalse(self.app.error)
        self.assertTrue(any('Error máximo RK4' in m.label for m in self.app.metric))
        self.pagina('Mi historial')
        self.elem('selectbox','Clase de resultado').select('Escenarios 3D').run()
        self.boton('Recuperar parámetros para editar')
        self.assertAlmostEqual(self.elem('slider','k (por minuto)').value,.2)
        self.elem('selectbox','Modelo').select('logistica').run()
        self.assertFalse(self.app.error)
        self.assertAlmostEqual(self.elem('slider','r (por unidad de tiempo)').value,.1)
    def test_aislamiento_en_interfaz_y_tutor_sin_clave(self):
        self.cuenta();self.pagina('Resolver');self.boton('Resolver paso a paso')
        self.boton('Consultar este resultado con el tutor')
        self.assertTrue(any('pendiente de configurar' in w.value for w in self.app.warning))
        self.assertTrue(self.elem('button','Enviar pregunta a NVIDIA').disabled)
        self.boton('Cerrar sesión');self.cuenta('otra_cuenta')
        self.pagina('Mi historial')
        self.assertTrue(any('aparecerán' in i.value for i in self.app.info))
        self.pagina('Tutor NVIDIA')
        self.assertFalse(any(e.label=='Conversación' for e in self.app.selectbox))
    def test_integral_y_metodo_alternativo(self):
        self.cuenta();self.pagina('Aprender')
        self.elem('radio','Área de aprendizaje').set_value('Laboratorio de integrales').run()
        self.boton('Explicar integral');self.assertFalse(self.app.error)
        self.assertTrue(any('antiderivada' in e.value for e in self.app.success))
        self.pagina('Resolver');self.boton('Resolver paso a paso')
        self.elem('selectbox','Método alternativo').select('lineal').run()
        self.boton('Resolver con este método');self.assertFalse(self.app.error)
        self.assertEqual(self.app.session_state['solucion']['clave'],'lineal')
    def test_tutor_con_respuesta_simulada_persistida(self):
        self.cuenta()
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'credencial-prueba','NVIDIA_MODEL':'modelo-prueba'}):
            self.pagina('Tutor NVIDIA');self.boton('Crear conversación general')
            self.elem('text_area','Pregunta').set_value('¿Qué es una derivada?')
            with patch('interfaz.espacio.explicar',return_value={'texto':'La derivada describe una tasa de cambio.','verificado_por_motor':False}):
                self.boton('Enviar pregunta a NVIDIA')
            self.assertTrue(any('La derivada describe' in m.value for m in self.app.markdown))
            self.pagina('Inicio');self.pagina('Tutor NVIDIA')
            self.assertTrue(any('La derivada describe' in m.value for m in self.app.markdown))

    def test_resolver_segundo_orden_desde_la_interfaz(self):
        self.cuenta();self.pagina('Resolver')
        self.entrada('Ecuación',"y'' + y = 0")
        self.entrada("y' inicial (segundo orden)",'0')
        self.boton('Resolver paso a paso')
        self.assertFalse(self.app.error)
        self.assertTrue(any('Identidad diferencial comprobada' in s.value for s in self.app.success))
        self.assertTrue(any('gráfica y la aproximación numérica' in i.value for i in self.app.info))

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
import requests
from sqlalchemy import select,update,inspect
from sqlalchemy.orm import Session
from datos_app.almacen import Almacen,AccesoError,PREFERENCIAS
from datos_app.modelos import Usuario,Sesion,Mensaje
from modulos.modelos import MODELOS,familia,evaluar,comprobar_formula
from modulos.contenido import EJERCICIOS
from modulos.practica import comprobar
from modulos.nvidia import explicar
from servicio import calcular


class Persistencia(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.url='sqlite:///'+str(Path(self.tmp.name)/'tutor.sqlite3')
        self.db=Almacen(self.url)
        self.db.registrar('alfa','Alfa','Una clave de prueba 123')
        self.db.registrar('beta','Beta','Otra clave de prueba 456')
        self.a=self.db.entrar('alfa','Una clave de prueba 123')
        self.b=self.db.entrar('beta','Otra clave de prueba 456')
    def tearDown(self):
        self.db.engine.dispose();self.tmp.cleanup()
    def test_hash_y_cierre(self):
        with Session(self.db.engine) as s:
            u=s.scalar(select(Usuario).where(Usuario.usuario=='alfa'))
            self.assertTrue(u.clave_hash.startswith('$argon2id$'))
            self.assertNotIn('Una clave',u.clave_hash)
            token=s.scalar(select(Sesion.token_hash))
            self.assertNotEqual(token,self.a)
        self.db.salir(self.a)
        with self.assertRaises(AccesoError):self.db.perfil(self.a)
    def test_aislamiento_resultados_y_chat(self):
        rid=self.db.guardar(self.a,'ecuacion','Solución',{'ecuacion':"y'=y"},{'ok':True})
        self.assertEqual(self.db.resultados(self.b),[])
        with self.assertRaises(AccesoError):self.db.resultado(self.b,rid)
        with self.assertRaises(AccesoError):self.db.nueva_conversacion(self.b,'Ajena',rid)
        cid=self.db.nueva_conversacion(self.a,'Propia',rid)
        self.db.guardar_dialogo(self.a,cid,'Pregunta','Respuesta')
        with self.assertRaises(AccesoError):self.db.mensajes(self.b,cid)
        with self.assertRaises(AccesoError):self.db.guardar_dialogo(self.b,cid,'Cambio','Cambio')
        self.assertEqual(len(self.db.mensajes(self.a,cid)),2)
    def test_notificaciones_pertenencia(self):
        nid=self.db.notificaciones(self.a)[0]['id']
        self.db.leer_notificaciones(self.b,nid)
        self.assertFalse(self.db.notificaciones(self.a)[0]['leida'])
        self.db.leer_notificaciones(self.a,nid)
        self.assertTrue(self.db.notificaciones(self.a)[0]['leida'])
    def test_progreso_preferencias_reinicio(self):
        self.db.completar(self.a,'variables');self.db.completar(self.a,'variables')
        self.db.intento(self.a,'euler','1.1',True)
        self.db.preferencias(self.a,'Alfa Nueva',dict(PREFERENCIAS,sonidos=True,volumen=50))
        otra=Almacen(self.url)
        self.assertEqual(otra.progreso(self.a)['lecciones'],['variables'])
        self.assertEqual(otra.progreso(self.a)['correctos'],1)
        self.assertEqual(otra.perfil(self.a)['preferencias']['volumen'],50)
        self.assertEqual(otra.progreso(self.b)['lecciones'],[])
        otra.engine.dispose()
    def test_cambio_clave_revoca_todas(self):
        segunda=self.db.entrar('alfa','Una clave de prueba 123')
        self.db.cambiar_clave(self.a,'Una clave de prueba 123','Nueva frase segura 456')
        for t in [self.a,segunda]:
            with self.assertRaises(AccesoError):self.db.perfil(t)
        nueva=self.db.entrar('alfa','Nueva frase segura 456')
        self.assertEqual(self.db.perfil(nueva)['usuario'],'alfa')
    def test_caducidad(self):
        with Session(self.db.engine) as s,s.begin():s.execute(update(Sesion).values(vence=time.time()-1))
        with self.assertRaises(AccesoError):self.db.resultados(self.a)
    def test_login_limitado_y_mensaje_generico(self):
        for _ in range(8):
            with self.assertRaisesRegex(AccesoError,'incorrectos'):self.db.entrar('desconocido','contraseña incorrecta')
        with self.assertRaisesRegex(AccesoError,'límite'):self.db.entrar('desconocido','contraseña incorrecta')
    def test_respaldo_recuperable(self):
        from mantenimiento import respaldo_sqlite
        from sqlalchemy.engine import make_url
        destino=Path(self.tmp.name)/'copia.sqlite3'
        self.db.guardar(self.a,'ecuacion','Persistente',{}, {'ok':True})
        respaldo_sqlite(make_url(self.url).database,destino)
        copia=Almacen('sqlite:///'+str(destino))
        self.assertEqual(copia.resultados(self.a)[0]['titulo'],'Persistente')
        copia.engine.dispose()
        with self.assertRaises(ValueError):respaldo_sqlite(make_url(self.url).database,destino)
    def test_migraciones(self):
        self.assertTrue({'usuarios','sesiones','resultados','conversaciones','mensajes','progreso','intentos','notificaciones','alembic_version'}<=set(inspect(self.db.engine).get_table_names()))
        with self.assertRaises(ValueError):self.db.guardar(self.a,'incorrecto','x',{}, {})
        with self.assertRaises(ValueError):self.db.guardar(self.a,'ecuacion','x',{}, {'dato':float('nan')})


class ModelosYAprendizaje(unittest.TestCase):
    def test_familias_cumplen_dato_inicial_y_edo(self):
        for clave in MODELOS:
            with self.subTest(modelo=clave):
                d=familia(clave,.1,100,10,0,100,50)
                np.testing.assert_allclose(np.array(d['z'])[:,0],d['iniciales'],atol=1e-12)
                self.assertTrue(d['verificado'])
                self.assertTrue(comprobar_formula(clave,.2,25))
    def test_valores_independientes(self):
        self.assertAlmostEqual(float(evaluar('enfriamiento',.1,25,10,80)),45.2333692644,places=8)
        self.assertAlmostEqual(float(evaluar('exponencial',.1,100,10,10)),27.1828182846,places=8)
        self.assertAlmostEqual(float(evaluar('logistica',.1,100,10,10)),23.1969316684,places=8)
        self.assertAlmostEqual(float(evaluar('velocidad',.2,30,10,0)),25.9399415029,places=8)
        self.assertAlmostEqual(float(evaluar('mezcla',.02,100,20,0)),32.9679953964,places=8)
    def test_equilibrios_y_limites(self):
        d=familia('logistica',.1,100,10,0,100,50)
        np.testing.assert_allclose(d['z'][0],0);np.testing.assert_allclose(d['z'][-1],100)
        with self.assertRaises(ValueError):familia('exponencial',1,100,100,0,100)
        with self.assertRaises(ValueError):familia('logistica',.1,100,10,100,0)
    def test_practica_equivalencia(self):
        for k,e in EJERCICIOS.items():
            self.assertTrue(comprobar({'ejercicio':k,'respuesta':e['respuesta']})['correcto'])
        self.assertTrue(comprobar({'ejercicio':'euler','respuesta':'11/10'})['correcto'])
        self.assertFalse(comprobar({'ejercicio':'derivada_potencia','respuesta':'3*x^3/x'})['correcto'])
        self.assertFalse(comprobar({'ejercicio':'euler','respuesta':'1.2'})['correcto'])
    def test_integral_y_euler_worker(self):
        r=calcular({'accion':'integral','expresion':'2*x*exp(x^2)'})
        self.assertTrue(r['ok'],r);self.assertTrue(r['verificado'])
        r=calcular({'accion':'numerico','ecuacion':"y'=y",'x0':'0','y0':'1','xf':'1','n':10})
        self.assertAlmostEqual(r['filas'][1]['Euler'],1.1)
        self.assertAlmostEqual(r['filas'][-1]['Euler'],1.1**10)


class NVIDIA(unittest.TestCase):
    def test_sin_clave_no_hay_llamada(self):
        c=Mock()
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'','NVIDIA_MODEL':''}):
            with self.assertRaises(ValueError):explicar('Pregunta',{},cliente=c)
        c.post.assert_not_called()
    def test_formato_seguro_y_contexto(self):
        c=Mock();c.post.return_value.status_code=200;c.post.return_value.json.return_value={'choices':[{'message':{'content':'Respuesta con $x^2$'}}]}
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'test-no-real','NVIDIA_MODEL':'modelo-prueba'}):
            r=explicar('Pregunta',{'verificado':True,'password':'no enviar'},[{'role':'system','content':'no enviar'}],cliente=c)
        args=c.post.call_args.kwargs
        self.assertFalse(args['allow_redirects']);self.assertFalse(r['verificado_por_motor'])
        self.assertNotIn('password',str(args['json']))
        self.assertEqual(len(args['json']['messages']),3)
        self.assertEqual(args['headers']['Authorization'],'Bearer test-no-real')
    def test_errores(self):
        for status in [401,403,429,500]:
            c=Mock();c.post.return_value.status_code=status
            with patch.dict(os.environ,{'NVIDIA_API_KEY':'test','NVIDIA_MODEL':'test'}):
                with self.assertRaises(RuntimeError):explicar('Pregunta',{},cliente=c)
        c=Mock();c.post.side_effect=requests.Timeout()
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'test','NVIDIA_MODEL':'test'}):
            with self.assertRaisesRegex(RuntimeError,'tiempo'):explicar('Pregunta',{},cliente=c)
    def test_respuesta_invalida(self):
        c=Mock();c.post.return_value.status_code=200;c.post.return_value.json.return_value={'choices':[]}
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'test','NVIDIA_MODEL':'test'}):
            with self.assertRaises(RuntimeError):explicar('Pregunta',{},cliente=c)

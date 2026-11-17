"""Casos de uso de persistencia y autenticación; ningún método confía en un id de usuario del cliente."""
import hashlib
import json
import re
import secrets
import threading
import time
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from sqlalchemy import create_engine, select, delete, update, event, func
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from configuracion import RAIZ
from .modelos import Usuario, Sesion, Limite, Resultado, Progreso, Intento, Conversacion, Mensaje, Notificacion

PREFERENCIAS = {'sonidos': False, 'volumen': 30, 'eventos': ['resultado', 'aprendizaje', 'tutor'],
                'fuente': 18, 'color': 'Azul'}
HASHER = PasswordHasher()
HASH_FICTICIO = HASHER.hash(secrets.token_urlsafe(32))


class AccesoError(ValueError):
    pass


def resumen_hash(texto):
    return hashlib.sha256(texto.encode()).hexdigest()


def validar_clave(clave):
    if not isinstance(clave, str) or not 12 <= len(clave) <= 128:
        raise ValueError('Usa una contraseña de 12 a 128 caracteres. Puedes usar una frase larga.')


def preferencias_validas(p):
    if not isinstance(p, dict):
        raise ValueError('Preferencias inválidas.')
    if type(p.get('sonidos')) is not bool or type(p.get('volumen')) is not int or not 0 <= p['volumen'] <= 100:
        raise ValueError('Configuración de sonido inválida.')
    if p.get('fuente') not in (16, 18, 20, 22) or p.get('color') not in ('Azul', 'Rojo', 'Amarillo'):
        raise ValueError('Configuración visual inválida.')
    if not isinstance(p.get('eventos'), list) or not set(p['eventos']) <= {'resultado', 'aprendizaje', 'tutor', 'error'}:
        raise ValueError('Eventos no reconocidos.')
    return {k: p[k] for k in PREFERENCIAS}


class Almacen:
    def __init__(self, url):
        self.lock = threading.RLock()
        self.url = url
        opciones = {'pool_pre_ping': True}
        if url.startswith('sqlite'):
            opciones['connect_args'] = {'check_same_thread': False, 'timeout': 20}
        self.engine = create_engine(url, **opciones)
        if self.engine.dialect.name == 'sqlite':
            @event.listens_for(self.engine, 'connect')
            def configurar(dbapi, _):
                dbapi.execute('PRAGMA foreign_keys=ON')
                dbapi.execute('PRAGMA journal_mode=WAL')
        from alembic.config import Config
        from alembic import command
        config = Config()
        config.set_main_option('script_location', str(RAIZ / 'migraciones'))
        with self.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
        if self.engine.dialect.name == 'sqlite':
            archivo = make_url(url).database
            if archivo and archivo != ':memory:':
                Path(archivo).chmod(0o600)

    def _consumir(self, clave, maximo, segundos):
        """Contador persistente; la actualización condicional impide rebasar la cuota."""
        ahora = time.time()
        with self.lock, Session(self.engine) as db, db.begin():
            db.execute(delete(Limite).where(Limite.vence <= ahora))
            fila = db.get(Limite, clave)
            if fila is None:
                try:
                    with db.begin_nested():
                        db.add(Limite(clave=clave, cuenta=0, vence=ahora+segundos))
                        db.flush()
                except IntegrityError:
                    pass
            r = db.execute(update(Limite).where(Limite.clave == clave, Limite.cuenta < maximo)
                           .values(cuenta=Limite.cuenta+1))
            if r.rowcount != 1:
                raise AccesoError('Se alcanzó el límite de intentos. Espera unos minutos antes de volver a intentar.')

    def registrar(self, usuario, nombre, clave):
        usuario = usuario.strip().lower()
        nombre = nombre.strip()
        if not re.fullmatch(r'[a-z0-9_]{3,32}', usuario):
            raise ValueError('Usuario: 3 a 32 letras sin acentos, números o guion bajo.')
        if not 2 <= len(nombre) <= 80:
            raise ValueError('El nombre debe tener de 2 a 80 caracteres.')
        validar_clave(clave)
        self._consumir('registro-global', 30, 3600)
        try:
            with Session(self.engine) as db, db.begin():
                u = Usuario(usuario=usuario, nombre=nombre, clave_hash=HASHER.hash(clave), preferencias=dict(PREFERENCIAS))
                db.add(u)
                db.flush()
                db.add(Notificacion(usuario_id=u.id, evento='aprendizaje', texto='Tu espacio está listo. Comienza con la lección de variables y cambios.'))
        except IntegrityError:
            raise ValueError('Ese nombre de usuario no está disponible.') from None

    def entrar(self, usuario, clave):
        usuario = str(usuario).strip().lower()[:64]
        if not isinstance(clave, str) or len(clave) > 128:
            raise AccesoError('Usuario o contraseña incorrectos.')
        llave = 'login-' + resumen_hash(usuario)
        self._consumir(llave, 8, 900)
        with Session(self.engine) as db, db.begin():
            u = db.scalar(select(Usuario).where(Usuario.usuario == usuario))
            try:
                valido = HASHER.verify(u.clave_hash if u else HASH_FICTICIO, clave)
            except (VerificationError, InvalidHashError):
                valido = False
            if not u or not valido:
                raise AccesoError('Usuario o contraseña incorrectos.')
            if HASHER.check_needs_rehash(u.clave_hash):
                u.clave_hash = HASHER.hash(clave)
            db.execute(delete(Limite).where(Limite.clave == llave))
            db.execute(delete(Sesion).where(Sesion.vence <= time.time()))
            token = secrets.token_urlsafe(32)
            db.add(Sesion(token_hash=resumen_hash(token), usuario_id=u.id, vence=time.time()+12*3600))
            return token

    def _usuario(self, db, token):
        if not isinstance(token, str) or not 20 <= len(token) <= 100:
            raise AccesoError('Inicia sesión para continuar.')
        u = db.scalar(select(Usuario).join(Sesion).where(Sesion.token_hash == resumen_hash(token), Sesion.vence > time.time()))
        if u is None:
            raise AccesoError('La sesión venció o se cerró. Vuelve a iniciar sesión.')
        return u

    def perfil(self, token):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            return {'usuario': u.usuario, 'nombre': u.nombre, 'preferencias': {**PREFERENCIAS, **u.preferencias}}

    def salir(self, token):
        with Session(self.engine) as db, db.begin():
            db.execute(delete(Sesion).where(Sesion.token_hash == resumen_hash(token)))

    def cambiar_clave(self, token, actual, nueva):
        validar_clave(nueva)
        with Session(self.engine) as db:
            uid = self._usuario(db, token).id
        self._consumir('clave-'+uid, 5, 900)
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            try:
                HASHER.verify(u.clave_hash, actual)
            except (VerificationError, InvalidHashError):
                raise AccesoError('La contraseña actual no es correcta.') from None
            u.clave_hash = HASHER.hash(nueva)
            db.execute(delete(Sesion).where(Sesion.usuario_id == u.id))

    def preferencias(self, token, nombre, datos):
        p = preferencias_validas(datos)
        if not 2 <= len(nombre.strip()) <= 80:
            raise ValueError('El nombre debe tener de 2 a 80 caracteres.')
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            u.nombre, u.preferencias = nombre.strip(), p

    def cuota(self, token, accion):
        limites = {'calculo': (60, 600), 'tutor': (20, 3600)}
        if accion not in limites:
            raise ValueError('Acción no válida.')
        with Session(self.engine) as db:
            uid = self._usuario(db, token).id
        self._consumir(accion+'-'+uid, *limites[accion])

    def guardar(self, token, tipo, titulo, entrada, resultado):
        if tipo not in {'ecuacion', 'numerico', 'modelo', 'grafica3d', 'integral'}:
            raise ValueError('Tipo de resultado no reconocido.')
        if not isinstance(entrada, dict) or not isinstance(resultado, dict):
            raise ValueError('El resultado debe tener una estructura válida.')
        if len(json.dumps([entrada, resultado], allow_nan=False)) > 2_000_000:
            raise ValueError('El resultado supera el tamaño permitido.')
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            r = Resultado(usuario_id=u.id, tipo=tipo, titulo=titulo[:160], entrada=entrada, resultado=resultado)
            db.add(r)
            db.flush()
            db.add(Notificacion(usuario_id=u.id, evento='resultado', texto='Guardado: '+titulo[:160]))
            return r.id

    @staticmethod
    def _registro(r):
        return {'id': r.id, 'tipo': r.tipo, 'titulo': r.titulo, 'creado': r.creado, 'entrada': r.entrada, 'resultado': r.resultado}

    def resultados(self, token, tipo=None):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            consulta = select(Resultado).where(Resultado.usuario_id == u.id)
            if tipo:
                consulta = consulta.where(Resultado.tipo == tipo)
            return [self._registro(r) for r in db.scalars(consulta.order_by(Resultado.creado.desc()).limit(200))]

    def resultado(self, token, identificador):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            r = db.scalar(select(Resultado).where(Resultado.id == identificador, Resultado.usuario_id == u.id))
            if r is None:
                raise AccesoError('Resultado no disponible para esta cuenta.')
            return self._registro(r)

    def completar(self, token, leccion):
        from modulos.contenido import LECCIONES
        if leccion not in LECCIONES:
            raise ValueError('Lección no válida.')
        with self.lock, Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            p = db.scalar(select(Progreso).where(Progreso.usuario_id == u.id, Progreso.leccion == leccion))
            if not p:
                db.add(Progreso(usuario_id=u.id, leccion=leccion))
                db.add(Notificacion(usuario_id=u.id, evento='aprendizaje', texto='Lección completada: '+LECCIONES[leccion]['titulo']))

    def intento(self, token, ejercicio, respuesta, correcto):
        from modulos.contenido import EJERCICIOS
        if ejercicio not in EJERCICIOS or len(respuesta) > 350 or type(correcto) is not bool:
            raise ValueError('Intento inválido.')
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            db.add(Intento(usuario_id=u.id, ejercicio=ejercicio, respuesta=respuesta, correcto=correcto))

    def progreso(self, token):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            lecciones = list(db.scalars(select(Progreso.leccion).where(Progreso.usuario_id == u.id, Progreso.completada.is_(True))))
            intentos = db.scalar(select(func.count()).select_from(Intento).where(Intento.usuario_id == u.id))
            correctos = db.scalar(select(func.count()).select_from(Intento).where(Intento.usuario_id == u.id, Intento.correcto.is_(True)))
            return {'lecciones': lecciones, 'intentos': intentos, 'correctos': correctos}

    def nueva_conversacion(self, token, titulo, resultado_id=None):
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            if resultado_id and not db.scalar(select(Resultado.id).where(Resultado.id == resultado_id, Resultado.usuario_id == u.id)):
                raise AccesoError('Resultado no disponible para esta cuenta.')
            c = Conversacion(usuario_id=u.id, titulo=titulo[:100], resultado_id=resultado_id)
            db.add(c)
            db.flush()
            return c.id

    def conversaciones(self, token):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            return [{'id': c.id, 'titulo': c.titulo, 'resultado_id': c.resultado_id} for c in db.scalars(
                select(Conversacion).where(Conversacion.usuario_id == u.id).order_by(Conversacion.creado.desc()).limit(100))]

    def _conversacion(self, db, token, identificador):
        u = self._usuario(db, token)
        c = db.scalar(select(Conversacion).where(Conversacion.id == identificador, Conversacion.usuario_id == u.id))
        if c is None:
            raise AccesoError('Conversación no disponible para esta cuenta.')
        return c

    def mensajes(self, token, identificador):
        with Session(self.engine) as db:
            self._conversacion(db, token, identificador)
            filas = list(db.scalars(select(Mensaje).where(Mensaje.conversacion_id == identificador).order_by(Mensaje.creado.desc()).limit(100)))
            return [{'role': m.rol, 'content': m.texto} for m in reversed(filas)]

    def guardar_dialogo(self, token, identificador, pregunta, respuesta):
        if not 1 <= len(pregunta) <= 1500 or not 1 <= len(respuesta) <= 20000:
            raise ValueError('El diálogo supera la longitud permitida.')
        with Session(self.engine) as db, db.begin():
            c = self._conversacion(db, token, identificador)
            ahora = time.time()
            db.add(Mensaje(conversacion_id=c.id, rol='user', texto=pregunta, creado=ahora))
            db.add(Mensaje(conversacion_id=c.id, rol='assistant', texto=respuesta, creado=ahora+0.0001))
            db.add(Notificacion(usuario_id=c.usuario_id, evento='tutor', texto='El tutor respondió en: '+c.titulo))

    def notificaciones(self, token):
        with Session(self.engine) as db:
            u = self._usuario(db, token)
            return [{'id': n.id, 'texto': n.texto, 'evento': n.evento, 'leida': n.leida, 'creado': n.creado} for n in db.scalars(
                select(Notificacion).where(Notificacion.usuario_id == u.id).order_by(Notificacion.creado.desc()).limit(100))]

    def leer_notificaciones(self, token, identificador=None):
        with Session(self.engine) as db, db.begin():
            u = self._usuario(db, token)
            q = update(Notificacion).where(Notificacion.usuario_id == u.id)
            if identificador:
                q = q.where(Notificacion.id == identificador)
            db.execute(q.values(leida=True))

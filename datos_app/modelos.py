"""Esquema relacional. Las consultas de la aplicación exigen sesión autenticada."""
import time
import uuid
from sqlalchemy import String, Text, Float, Integer, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def identificador():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = 'usuarios'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80))
    clave_hash: Mapped[str] = mapped_column(Text)
    creado: Mapped[float] = mapped_column(Float, default=time.time)
    preferencias: Mapped[dict] = mapped_column(JSON, default=dict)


class Sesion(Base):
    __tablename__ = 'sesiones'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    vence: Mapped[float] = mapped_column(Float, index=True)


class Limite(Base):
    __tablename__ = 'limites'
    clave: Mapped[str] = mapped_column(String(100), primary_key=True)
    cuenta: Mapped[int] = mapped_column(Integer, default=0)
    vence: Mapped[float] = mapped_column(Float)


class Resultado(Base):
    __tablename__ = 'resultados'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(160))
    creado: Mapped[float] = mapped_column(Float, default=time.time, index=True)
    entrada: Mapped[dict] = mapped_column(JSON)
    resultado: Mapped[dict] = mapped_column(JSON)


class Progreso(Base):
    __tablename__ = 'progreso'
    __table_args__ = (UniqueConstraint('usuario_id', 'leccion', name='uq_progreso_usuario_leccion'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    leccion: Mapped[str] = mapped_column(String(50))
    completada: Mapped[bool] = mapped_column(Boolean, default=True)
    actualizado: Mapped[float] = mapped_column(Float, default=time.time)


class Intento(Base):
    __tablename__ = 'intentos'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    ejercicio: Mapped[str] = mapped_column(String(50))
    respuesta: Mapped[str] = mapped_column(String(350))
    correcto: Mapped[bool] = mapped_column(Boolean)
    creado: Mapped[float] = mapped_column(Float, default=time.time)


class Conversacion(Base):
    __tablename__ = 'conversaciones'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    titulo: Mapped[str] = mapped_column(String(100))
    resultado_id: Mapped[str | None] = mapped_column(ForeignKey('resultados.id'), nullable=True)
    creado: Mapped[float] = mapped_column(Float, default=time.time)


class Mensaje(Base):
    __tablename__ = 'mensajes'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    conversacion_id: Mapped[str] = mapped_column(ForeignKey('conversaciones.id', ondelete='CASCADE'), index=True)
    rol: Mapped[str] = mapped_column(String(12))
    texto: Mapped[str] = mapped_column(Text)
    creado: Mapped[float] = mapped_column(Float, default=time.time)


class Notificacion(Base):
    __tablename__ = 'notificaciones'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    usuario_id: Mapped[str] = mapped_column(ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    texto: Mapped[str] = mapped_column(String(300))
    evento: Mapped[str] = mapped_column(String(20))
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    creado: Mapped[float] = mapped_column(Float, default=time.time)

"""Esquema inicial congelado: cuentas, resultados y aprendizaje."""
from alembic import op
import sqlalchemy as sa
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('limites',
        sa.Column('clave', sa.String(length=100), nullable=False, primary_key=True),
        sa.Column('cuenta', sa.Integer(), nullable=False),
        sa.Column('vence', sa.Float(), nullable=False),
    )
    op.create_table('usuarios',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario', sa.String(length=32), nullable=False),
        sa.Column('nombre', sa.String(length=80), nullable=False),
        sa.Column('clave_hash', sa.Text(), nullable=False),
        sa.Column('creado', sa.Float(), nullable=False),
        sa.Column('preferencias', sa.JSON(), nullable=False),
    )
    op.create_index('ix_usuarios_usuario', 'usuarios', ['usuario'], unique=True)
    op.create_table('intentos',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ejercicio', sa.String(length=50), nullable=False),
        sa.Column('respuesta', sa.String(length=350), nullable=False),
        sa.Column('correcto', sa.Boolean(), nullable=False),
        sa.Column('creado', sa.Float(), nullable=False),
    )
    op.create_index('ix_intentos_usuario_id', 'intentos', ['usuario_id'], unique=False)
    op.create_table('notificaciones',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('texto', sa.String(length=300), nullable=False),
        sa.Column('evento', sa.String(length=20), nullable=False),
        sa.Column('leida', sa.Boolean(), nullable=False),
        sa.Column('creado', sa.Float(), nullable=False),
    )
    op.create_index('ix_notificaciones_usuario_id', 'notificaciones', ['usuario_id'], unique=False)
    op.create_table('progreso',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leccion', sa.String(length=50), nullable=False),
        sa.Column('completada', sa.Boolean(), nullable=False),
        sa.Column('actualizado', sa.Float(), nullable=False),
        sa.UniqueConstraint('usuario_id', 'leccion', name='uq_progreso_usuario_leccion'),
    )
    op.create_index('ix_progreso_usuario_id', 'progreso', ['usuario_id'], unique=False)
    op.create_table('resultados',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('titulo', sa.String(length=160), nullable=False),
        sa.Column('creado', sa.Float(), nullable=False),
        sa.Column('entrada', sa.JSON(), nullable=False),
        sa.Column('resultado', sa.JSON(), nullable=False),
    )
    op.create_index('ix_resultados_creado', 'resultados', ['creado'], unique=False)
    op.create_index('ix_resultados_usuario_id', 'resultados', ['usuario_id'], unique=False)
    op.create_table('sesiones',
        sa.Column('token_hash', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vence', sa.Float(), nullable=False),
    )
    op.create_index('ix_sesiones_vence', 'sesiones', ['vence'], unique=False)
    op.create_index('ix_sesiones_usuario_id', 'sesiones', ['usuario_id'], unique=False)
    op.create_table('conversaciones',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('usuario_id', sa.String(length=36), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('titulo', sa.String(length=100), nullable=False),
        sa.Column('resultado_id', sa.String(length=36), sa.ForeignKey('resultados.id', ondelete=None), nullable=True),
        sa.Column('creado', sa.Float(), nullable=False),
    )
    op.create_index('ix_conversaciones_usuario_id', 'conversaciones', ['usuario_id'], unique=False)
    op.create_table('mensajes',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('conversacion_id', sa.String(length=36), sa.ForeignKey('conversaciones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rol', sa.String(length=12), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('creado', sa.Float(), nullable=False),
    )
    op.create_index('ix_mensajes_conversacion_id', 'mensajes', ['conversacion_id'], unique=False)

def downgrade():
    op.drop_table('mensajes')
    op.drop_table('conversaciones')
    op.drop_table('sesiones')
    op.drop_table('resultados')
    op.drop_table('progreso')
    op.drop_table('notificaciones')
    op.drop_table('intentos')
    op.drop_table('usuarios')
    op.drop_table('limites')

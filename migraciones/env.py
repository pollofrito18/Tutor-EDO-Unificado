"""Migraciones ejecutadas con la conexión privada que proporciona el servidor."""
from alembic import context
from datos_app.modelos import Base
from configuracion import database_url
from sqlalchemy import create_engine


def ejecutar(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url(), target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = context.config.attributes.get('connection')
    if connection is not None:
        ejecutar(connection)
    else:
        with create_engine(database_url()).connect() as connection:
            ejecutar(connection)

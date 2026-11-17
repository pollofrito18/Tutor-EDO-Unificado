"""Operaciones locales del administrador: migrar y respaldar SQLite sin copiar archivos activos."""
import argparse
import sqlite3
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy.engine import make_url
from configuracion import RAIZ,database_url
from datos_app.almacen import Almacen


def respaldo_sqlite(origen,destino):
    destino=Path(destino)
    if destino.exists():raise ValueError('El destino ya existe. Elige un nombre nuevo.')
    if not Path(origen).is_file():raise ValueError('La base de origen no existe.')
    destino.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:
        with sqlite3.connect(Path(origen).resolve().as_uri()+'?mode=ro',uri=True) as entrada:
            with sqlite3.connect(destino) as salida:
                entrada.backup(salida)
                if salida.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise ValueError('El respaldo no superó la comprobación de integridad.')
        destino.chmod(0o600)
    except Exception:
        if destino.exists():destino.unlink()
        raise
    return destino


def main():
    p=argparse.ArgumentParser(description='Mantenimiento de Tutor EDO')
    p.add_argument('accion',choices=['migrar','respaldo'])
    p.add_argument('--destino')
    args=p.parse_args()
    url=database_url()
    if args.accion=='migrar':
        db=Almacen(url);db.engine.dispose();print('Migraciones aplicadas.');return
    if make_url(url).get_backend_name()!='sqlite':
        p.error('Para PostgreSQL usa pg_dump. Consulta documentacion/OPERACION_Y_SEGURIDAD.md.')
    destino=args.destino or str(RAIZ/'backups'/('tutor_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')+'.sqlite3'))
    print('Respaldo verificado: '+str(respaldo_sqlite(make_url(url).database,destino)))


if __name__=='__main__':main()

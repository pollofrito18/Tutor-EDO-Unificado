"""Configuración privada del servidor; nunca se muestra la clave en la interfaz."""
import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / '.env', override=False)


def database_url():
    url = os.environ.get('DATABASE_URL', '').strip()
    if url:
        if url.startswith('postgresql://'):
            url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return url
    directorio = Path(os.environ.get('TUTOR_DATA_DIR', str(RAIZ / 'datos'))).resolve()
    directorio.mkdir(parents=True, exist_ok=True, mode=0o700)
    return 'sqlite:///' + (directorio / 'tutor.sqlite3').as_posix()


def nvidia_disponible():
    return bool(os.environ.get('NVIDIA_API_KEY', '').strip() and os.environ.get('NVIDIA_MODEL', '').strip())

"""Construye una carpeta Windows autocontenida para ejecutar Tutor EDO sin internet."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


VERSION_PYTHON = "3.12.10"
URL_PYTHON = (
    "https://www.python.org/ftp/python/"
    f"{VERSION_PYTHON}/python-{VERSION_PYTHON}-embed-amd64.zip"
)
IMPORTS_PRUEBA = (
    "import streamlit, sympy, numpy, scipy, plotly, pandas, sqlalchemy, "
    "alembic, argon2, requests, nucleo, interfaz"
)
EXCLUIR = {
    ".env", ".git", ".venv", "__pycache__", ".pytest_cache",
    ".agents", "Tutor_EDO_Portable", "Tutor_EDO_Portable.zip", "backups",
    "crear_portable.py", "crear_portable_windows.bat",
    "iniciar_windows.bat", "instalar_windows.bat", "probar_windows.bat",
    "iniciar_linux.sh", "lanzador_portable.cs",
}


def ignorar(directorio, nombres):
    excluidos = {nombre for nombre in nombres if nombre in EXCLUIR or nombre.endswith(".pyc")}
    if Path(directorio).name == "datos":
        excluidos.update({"tutor.sqlite3", "tutor.sqlite3-shm", "tutor.sqlite3-wal"})
    return excluidos


def descargar_python(destino):
    print(f"Descargando Python {VERSION_PYTHON} embebible para Windows x64...")
    with urllib.request.urlopen(URL_PYTHON, timeout=60) as respuesta, destino.open("wb") as archivo:
        shutil.copyfileobj(respuesta, archivo)


def compilar_lanzador(raiz, paquete):
    fuente = str(raiz / "lanzador_portable.cs").replace("'", "''")
    archivo_salida = paquete / "TutorEDO.exe"
    if archivo_salida.exists():
        archivo_salida.unlink()
    salida = str(archivo_salida).replace("'", "''")
    comando = (
        f"$codigo = Get-Content -LiteralPath '{fuente}' -Raw; "
        f"Add-Type -TypeDefinition $codigo -Language CSharp "
        f"-OutputAssembly '{salida}' -OutputType ConsoleApplication"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", comando],
        cwd=paquete,
        check=True,
    )


def crear():
    raiz = Path(__file__).resolve().parent
    destino = raiz / "Tutor_EDO_Portable"
    nombre_marcador = ".paquete-portable-generado"
    if destino.exists() and not (destino / nombre_marcador).is_file():
        raise RuntimeError(
            f"No se reemplaza {destino}: la carpeta existe y no fue creada por este generador."
        )

    with tempfile.TemporaryDirectory(prefix="tutor_edo_portable_") as temporal:
        temporal = Path(temporal)
        paquete = temporal / "Tutor_EDO_Portable"
        shutil.copytree(raiz, paquete, ignore=ignorar)

        archivo_zip = temporal / "python-embebible.zip"
        descargar_python(archivo_zip)
        directorio_python = paquete / "python"
        directorio_python.mkdir()
        with zipfile.ZipFile(archivo_zip) as archivo:
            archivo.extractall(directorio_python)

        mayor, menor = VERSION_PYTHON.split(".")[:2]
        prefijo = f"python{mayor}{menor}"
        archivo_rutas = directorio_python / f"{prefijo}._pth"
        archivo_rutas.write_text(
            f"{prefijo}.zip\n"
            ".\n"
            "..\n"
            "Lib\\site-packages\n"
            "import site\n",
            encoding="ascii",
        )
        sitio_paquetes = directorio_python / "Lib" / "site-packages"
        sitio_paquetes.mkdir(parents=True)

        print("Instalando las dependencias dentro del paquete portable...")
        subprocess.run(
            [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check", "--no-warn-script-location",
                "--target", str(sitio_paquetes),
                "-r", str(raiz / "requirements.txt"),
            ],
            cwd=raiz,
            check=True,
        )

        interprete = directorio_python / "python.exe"
        print("Verificando imports y versión de Streamlit con el Python incluido...")
        subprocess.run([str(interprete), "-c", IMPORTS_PRUEBA], cwd=paquete, check=True)
        subprocess.run(
            [str(interprete), "-m", "streamlit", "--version"],
            cwd=paquete,
            check=True,
        )
        print("Compilando TutorEDO.exe...")
        compilar_lanzador(raiz, paquete)
        (paquete / nombre_marcador).write_text(
            "Paquete generado. No contiene .env ni la base de datos local.\n",
            encoding="utf-8",
        )

        if destino.exists():
            shutil.rmtree(destino)
        shutil.move(str(paquete), str(destino))

    print(f"\nPaquete portable listo: {destino}")
    print("Copia esa carpeta completa a la memoria USB y ejecuta TutorEDO.exe.")
    print("La PC de destino debe ser Windows x64; no necesita instalar Python ni conectarse a internet.")


if __name__ == "__main__":
    crear()

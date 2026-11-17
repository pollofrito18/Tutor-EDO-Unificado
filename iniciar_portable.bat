@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "python\python.exe" (
  echo Falta la carpeta python del paquete portable.
  echo Ejecuta crear_portable_windows.bat en la PC donde se preparo el proyecto.
  pause
  exit /b 1
)

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"python\python.exe" -m streamlit run app.py --server.headless true --server.port 8501
if errorlevel 1 pause

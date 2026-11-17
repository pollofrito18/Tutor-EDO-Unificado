@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Instala Python 3.12 con el lanzador py y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo No se completo la instalacion. Revisa la conexion y el mensaje anterior.
  pause
  exit /b 1
)
echo Instalacion lista. Ejecuta iniciar_windows.bat.
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Primero ejecuta instalar_windows.bat y espera a que termine.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" crear_portable.py
if errorlevel 1 (
  echo No se pudo crear el paquete. Revisa el error anterior y la conexion a internet.
  pause
  exit /b 1
)

echo.
echo Copia la carpeta Tutor_EDO_Portable completa a la memoria USB.
pause

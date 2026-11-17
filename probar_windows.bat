@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m unittest discover -s pruebas -v
pause

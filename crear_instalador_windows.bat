@echo off
setlocal
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo No se encontro Inno Setup 6.
    echo Instala Inno Setup 6 en esta PC y vuelve a ejecutar este archivo.
    pause
    exit /b 1
)
if not exist "%~dp0Tutor_EDO_Portable\TutorEDO.exe" (
    echo No se encontro Tutor_EDO_Portable\TutorEDO.exe.
    echo Primero ejecuta crear_portable_windows.bat.
    pause
    exit /b 1
)
pushd "%~dp0"
"%ISCC%" /Q "%~dp0TutorEDO_Instalador.iss"
set "BUILD_RESULT=%ERRORLEVEL%"
popd
if not "%BUILD_RESULT%"=="0" (
    echo Fallo la creacion del instalador. Codigo: %BUILD_RESULT%
    pause
    exit /b %BUILD_RESULT%
)
echo.
echo Instalador listo: %~dp0Instalador_TutorEDO_Windows_x64.exe
pause

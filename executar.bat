@echo off
setlocal
chcp 65001 > nul

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    goto :missing_venv
)

"%PYTHON_EXE%" --version > nul 2>&1
if errorlevel 1 goto :invalid_venv

"%PYTHON_EXE%" "%PROJECT_DIR%app.py"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo O aplicativo foi encerrado com erro. Codigo: %EXIT_CODE%
    pause
)

endlocal & exit /b %EXIT_CODE%

:missing_venv
echo.
echo Ambiente virtual nao encontrado.
echo Execute primeiro os comandos de instalacao do README.md.
echo.
pause
exit /b 1

:invalid_venv
echo.
echo O ambiente virtual esta invalido ou o Python original foi removido.
echo Recrie a pasta .venv seguindo as instrucoes do README.md.
echo.
pause
exit /b 1

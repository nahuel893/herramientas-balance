@echo off
title Silver Column Selector
cd /d "%~dp0"

:: Activar entorno virtual
call venv\Scripts\activate.bat

:: Actualizar desde repositorio
echo Buscando actualizaciones...
git pull origin main
pip install -r requirements.txt --quiet

:: Abrir navegador despues de 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Iniciar servidor
echo Iniciando servidor en http://localhost:8000 ...
echo Presiona Ctrl+C para detener.
python run.py

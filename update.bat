@echo off
echo ========================================
echo   Actualizando Silver Column Selector
echo ========================================
echo.
cd /d "%~dp0"

:: Pull cambios
echo Descargando actualizaciones...
git pull origin main

:: Actualizar dependencias
echo Actualizando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo ========================================
echo   Actualizacion completada!
echo ========================================
pause

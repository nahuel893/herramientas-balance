@echo off
echo ========================================
echo   Instalando Silver Column Selector
echo ========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo Descargalo de https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Crear entorno virtual
echo Creando entorno virtual...
python -m venv venv

:: Activar e instalar dependencias
echo Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: Crear carpeta exports si no existe
if not exist exports mkdir exports

echo.
echo ========================================
echo   Instalacion completada!
echo   Configura el archivo .env con los
echo   datos de conexion a la base de datos.
echo ========================================
echo.
pause

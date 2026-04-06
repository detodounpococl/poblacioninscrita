@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Actualizar Poblacion Inscrita

echo ==============================
echo ACTUALIZANDO POBLACION INSCRITA
echo ==============================

REM ===== RUTA ORIGEN =====
set "ORIGEN=C:\Users\14538348-k\Desktop\DASHBOARD (html)\Nuevos\Pobl. Inscrita"

REM ===== RUTA REPO =====
set "REPO=C:\Users\14538348-k\Desktop\DASHBOARD (html)\Nuevos\Pobl. Inscrita\poblacioninscrita"

REM ===== ARCHIVOS =====
set "ARCH1=datos.json"
set "ARCH2=index.html"

echo.
echo [1] Verificando carpeta ORIGEN...
if not exist "%ORIGEN%\" (
    echo ERROR: No existe ORIGEN
    echo %ORIGEN%
    pause
    exit /b 1
)

echo [2] Verificando carpeta REPO...
if not exist "%REPO%\" (
    echo ERROR: No existe REPO
    echo %REPO%
    pause
    exit /b 1
)

echo [3] Verificando que REPO sea git...
if not exist "%REPO%\.git\" (
    echo ERROR: La carpeta REPO no contiene .git
    echo %REPO%
    pause
    exit /b 1
)

echo [4] Verificando git en Windows...
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no esta instalado o no esta en PATH
    pause
    exit /b 1
)

echo [5] Verificando archivos origen...
if not exist "%ORIGEN%\%ARCH1%" (
    echo ERROR: Falta %ORIGEN%\%ARCH1%
    pause
    exit /b 1
)
if not exist "%ORIGEN%\%ARCH2%" (
    echo ERROR: Falta %ORIGEN%\%ARCH2%
    pause
    exit /b 1
)

echo.
echo [6] Copiando archivos...
copy /Y "%ORIGEN%\%ARCH1%" "%REPO%\%ARCH1%" >nul
if errorlevel 1 (
    echo ERROR al copiar %ARCH1%
    pause
    exit /b 1
)

copy /Y "%ORIGEN%\%ARCH2%" "%REPO%\%ARCH2%" >nul
if errorlevel 1 (
    echo ERROR al copiar %ARCH2%
    pause
    exit /b 1
)

echo [7] Entrando al repo...
cd /d "%REPO%"
if errorlevel 1 (
    echo ERROR: No se pudo entrar a %REPO%
    pause
    exit /b 1
)

echo.
echo [8] Estado actual:
git status
if errorlevel 1 (
    echo ERROR: git status fallo
    pause
    exit /b 1
)

echo.
echo [9] Agregando cambios...
git add "%ARCH1%" "%ARCH2%"
if errorlevel 1 (
    echo ERROR: git add fallo
    pause
    exit /b 1
)

echo.
echo [10] Revisando si hay cambios listos...
git diff --cached --quiet
if not errorlevel 1 (
    echo No hay cambios para subir.
    pause
    exit /b 0
)

echo Hay cambios. Continuando...

echo.
echo [11] Commit...
git commit -m "update poblacion inscrita (index + json)"
if errorlevel 1 (
    echo ERROR: git commit fallo
    pause
    exit /b 1
)

echo.
echo [12] Push...
git push origin main
if errorlevel 1 (
    echo ERROR: git push fallo
    pause
    exit /b 1
)

echo.
echo ==============================
echo ACTUALIZACION COMPLETADA
echo ==============================
pause
exit /b 0
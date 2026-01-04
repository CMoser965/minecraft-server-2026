@echo off
title Updating Mods directly to .minecraft

:: 1. Get the location of this script and the jar file
set "SCRIPT_DIR=%~dp0"
set "BOOTSTRAP_JAR=%SCRIPT_DIR%packwiz-installer-bootstrap.jar"

:: 2. Set the target directory to your default Minecraft folder
set "TARGET_DIR=%APPDATA%\.minecraft"

echo ---------------------------------------------------
echo  SOURCE: %BOOTSTRAP_JAR%
echo  TARGET: %TARGET_DIR%
echo ---------------------------------------------------

:: 3. Switch "Context" to the target folder
:: This tricks the installer into thinking it is running inside .minecraft
if exist "%TARGET_DIR%" (
    cd /d "%TARGET_DIR%"
) else (
    echo [ERROR] Could not find Minecraft folder at:
    echo %TARGET_DIR%
    pause
    exit /b
)

:: 4. Run the update
:: It will verify mods in %APPDATA%\.minecraft\mods
java -jar "%BOOTSTRAP_JAR%" -g -s client http://localhost:8080/pack.toml

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Update failed!
    pause
) else (
    echo.
    echo [SUCCESS] Mods installed to AppData.
    timeout /t 3
)
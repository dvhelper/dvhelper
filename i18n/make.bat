@echo off
setlocal enabledelayedexpansion

set "DOMAIN=dvhelper"
set "I18N_DIR=%~dp0"
set "PROJECT_ROOT=%I18N_DIR%..\"
set "LANG=en_US"
set "PO_FILE=%I18N_DIR%%LANG%\LC_MESSAGES\%DOMAIN%.po"

if not "%~1" == "" (
    set "choice=%~1"
    if "!choice!" == "1" goto EXTRACT_UPDATE
    if "!choice!" == "2" goto EXTRACT_INIT
    if "!choice!" == "3" goto COMPILE

    goto MENU
)

:MENU
cls
echo ======================================================
echo           DV-Helper Translation Management
echo ======================================================
echo. 
echo 1. Extract and Update English Translation
echo 2. Extract and Initialize English Translation
echo 3. Compile Translation Files
echo. 
echo ======================================================
REM Set default choice to 1 if user presses Enter without input
set choice=1
set /p choice="Please enter your choice [1-3] (default: 1): "

echo.

if "!choice!" == "1" goto EXTRACT_UPDATE
if "!choice!" == "2" goto EXTRACT_INIT
if "!choice!" == "3" goto COMPILE

goto MENU

:EXTRACT_UPDATE
REM Extract translation strings
call :EXTRACT_STRINGS

REM Update existing translation
if exist "%PO_FILE%" (
    echo Updating existing English translation...
    poetry run pybabel update -D %DOMAIN% -i %I18N_DIR%%DOMAIN%.pot -d %I18N_DIR% -l %LANG%
) else (
    echo No existing English translation found. Please use option 2 to initialize.
)
exit /b

:EXTRACT_INIT
REM Extract translation strings
call :EXTRACT_STRINGS

REM Initialize new translation
if not exist "%PO_FILE%" (
    echo Initializing new English translation...
    poetry run pybabel init -D %DOMAIN% -i %I18N_DIR%%DOMAIN%.pot -d %I18N_DIR% -l %LANG%
) else (
    echo English translation already exists. Please use option 1 to update.
)
exit /b

:COMPILE
REM Compile translation files
if exist "%PO_FILE%" (
    echo Compiling translation files...
    poetry run pybabel compile -D %DOMAIN% -d %I18N_DIR% -l %LANG% --statistics
) else (
    echo No PO file found at %PO_FILE%. Please initialize translation first.
)
exit /b

REM Helper function to extract strings
:EXTRACT_STRINGS
echo Extracting translation strings...
poetry run pybabel extract -F %I18N_DIR%babel.config -o %I18N_DIR%%DOMAIN%.pot %PROJECT_ROOT% --project=%DOMAIN% --no-location
exit /b

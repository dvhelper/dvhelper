@echo off
setlocal enabledelayedexpansion

set "DOMAIN=dvhelper"
set "I18N_DIR=%~dp0"
set "ROOT_DIR=%I18N_DIR%..\"

if not "%~1" == "" (
    set "choice=%~1"
    if "!choice!" == "1" goto UPDATE
    if "!choice!" == "2" (
        if not "%~2" == "" (
            set "LANG=%~2"
        )
        goto CREATE
    )
    if "!choice!" == "3" goto COMPILE

    goto MENU
)

:MENU
cls
echo ======================================================
echo           DV-Helper Translation Management
echo ======================================================
echo. 
echo 1. Update All Translations
echo 2. Initialize a New Translation
echo 3. Compile Translation Files
echo. 
echo ======================================================
set choice=1
set /p choice="Please enter your choice [1-3] (default: 1): "

echo.

if "!choice!" == "1" goto UPDATE
if "!choice!" == "2" goto CREATE
if "!choice!" == "3" goto COMPILE

goto MENU



REM Update existing translation
:UPDATE

REM Search for message catalogs
set "found_po_file=false"
for /r "%I18N_DIR%" %%f in (*.po) do (
    if "%%~xf" == ".po" (
        set "found_po_file=true"
        goto :FOUND_PO
    )
)

:FOUND_PO
if "%found_po_file%" == "true" (
    REM Extract messages
    call :EXTRACT

    echo Updating translations...
    poetry run pybabel update -D %DOMAIN% -i %I18N_DIR%%DOMAIN%.pot -d %I18N_DIR% --omit-header
) else (
    echo No existing message catalogs found.
    echo Please use option 2 to initialize a new translation.
)
exit /b



REM Initialize a new translation
:CREATE

REM If language code is not provided as a parameter, prompt user
if not defined LANG (
    set "LANG="
    set /p "LANG=Enter language code (format: zh_CN): "
)

REM Check if language code is provided
if "%LANG%" == "" (
    echo Error: Language code cannot be empty.
    exit /b 1
)

REM Check if message catalogs exists
set "PO_FILE=%I18N_DIR%%LANG%\LC_MESSAGES\%DOMAIN%.po"
set "PO_FILE_REL=.\%LANG%\LC_MESSAGES\%DOMAIN%.po"

if exist "%PO_FILE%" (
    echo Error: Message catalogs %PO_FILE_REL% already exists.
    echo Please use option 1 to update.
    exit /b 1
)

REM Extract messages
call :EXTRACT

REM Initialize new translation
echo Initializing %LANG% translation...
poetry run pybabel init -D %DOMAIN% -i %I18N_DIR%%DOMAIN%.pot -d %I18N_DIR% -l %LANG%
exit /b



REM Extract messages
:EXTRACT
echo Extracting translation messages...
poetry run pybabel extract %ROOT_DIR% -F %I18N_DIR%babel.config -o %I18N_DIR%%DOMAIN%.pot --no-location --omit-header
exit /b



REM Compile translation files
:COMPILE
echo Compiling translation files...
poetry run pybabel compile -D %DOMAIN% -d %I18N_DIR% --statistics --use-fuzzy
exit /b

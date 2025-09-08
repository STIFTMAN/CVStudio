@echo off
REM Pfad zum Zielordner
set "target=.\src\assets\projects"

REM Überprüfen, ob der Ordner existiert
if not exist "%target%" (
    echo Ordner "%target%" wurde nicht gefunden.
    pause
    exit /b
)

REM Löscht alle Dateien im Zielordner (rekursiv)
del /q "%target%\*.*"

REM Falls Unterordner auch geleert werden sollen
for /d %%p in ("%target%\*") do del /q "%%p\*.*"

echo Alle Dateien in "%target%" wurden gelöscht.
start clear_additional_filter.bat
pause
@echo off
REM Sucht und löscht alle __pycache__ Ordner rekursiv
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo Lösche "%%d"
        rd /s /q "%%d"
    )
)
pause

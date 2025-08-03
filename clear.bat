for /d /r . %%d in (__pycache__) do (
    rd /s /q "%%d"
)
PAUSE
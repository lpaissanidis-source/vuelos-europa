' ============================================================
' EJECUTAR_SILENCIOSO.VBS
' Corre main.py sin mostrar ninguna ventana negra.
' Guarda todo lo que imprime Python en "log.txt"
' para que puedas revisar si hubo errores.
' Task Scheduler apunta a ESTE archivo, no a main.py directo.
' ============================================================

Set WshShell = CreateObject("WScript.Shell")

Dim comando
comando = "cmd /c cd /d ""C:\Users\HP\Documents\Vuelos Europa"" && " & _
            "set PYTHONIOENCODING=utf-8 && " & _
            "C:\Python314\python.exe main.py >> log.txt 2>&1"

WshShell.Run comando, 0, False

Set WshShell = Nothing

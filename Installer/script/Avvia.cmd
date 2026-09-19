@echo off
rem --------------------------------------------------------------------
rem  Avvio del Cruscotto Degenze.
rem
rem  E' il file a cui puntano il collegamento sul Desktop e la voce nel
rem  menu Start. Fa una cosa sola: chiamare Avvia.ps1, che e' scritto in
rem  PowerShell perche' lassu' si ragiona meglio che qui.
rem
rem  "-ExecutionPolicy Bypass" serve perche' Windows, appena installato,
rem  rifiuta di eseguire script PowerShell. Vale solo per questa chiamata:
rem  non cambia le impostazioni del PC.
rem --------------------------------------------------------------------
title Cruscotto Degenze
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installazione\Avvia.ps1"
if errorlevel 1 (
    echo.
    pause
)

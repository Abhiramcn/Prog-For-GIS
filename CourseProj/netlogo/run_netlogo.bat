@echo off
echo ======================================================================
echo Launching NetLogo 7.0.4 with Nedumangad Epidemic GIS-ABM Model...
echo ======================================================================

set "MODEL_PATH=%~dp0Nedumangad_Epidemic_GIS.nlogox"
set "NETLOGO_EXE=C:\Program Files\NetLogo 7.0.4\NetLogo.exe"

if exist "%NETLOGO_EXE%" (
    echo Opening model in NetLogo GUI...
    start "" "%NETLOGO_EXE%" "%MODEL_PATH%"
) else (
    echo NetLogo.exe not found at %NETLOGO_EXE%.
    echo Please open NetLogo manually and load %MODEL_PATH%.
)

pause

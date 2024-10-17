@ECHO on

:: Check for Anaconda installation paths
if exist "C:\ProgramData\anaconda3\condabin\conda.bat" (
    set "conda_path=C:\ProgramData\anaconda3\condabin\conda.bat"
) else if exist "C:\Users\%USERNAME%\Anaconda3\condabin\conda.bat" (
    set "conda_path=C:\Users\%USERNAME%\Anaconda3\condabin\conda.bat"
) else if exist "C:\Users\%USERNAME%\Miniconda3\condabin\conda.bat" (
    set "conda_path=C:\Users\%USERNAME%\Miniconda3\condabin\conda.bat"
) else if exist "C:\Anaconda3\condabin\conda.bat" (
    set "conda_path=C:\Anaconda3\condabin\conda.bat"
) else if exist "C:\Miniconda3\condabin\conda.bat" (
    set "conda_path=C:\Miniconda3\condabin\conda.bat"
) else (
    echo Anaconda installation not found.
    PAUSE
    exit /b
)

:: Check for helao repository paths
if exist "C:\Users\%USERNAME%\helao-dev\testing\helao_interface.py" (
    set "helao_repo=C:\Users\%USERNAME%\helao-dev"
) else if exist "C:\Users\%USERNAME%\Documents\helao-dev\testing\helao_interface.py" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao-dev"
) else if exist "C:\Users\%USERNAME%\helao-pub\testing\helao_interface.py" (
    set "helao_repo=C:\Users\%USERNAME%\helao-pub"
) else if exist "C:\Users\%USERNAME%\Documents\helao-pub\testing\helao_interface.py" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao-pub"

else (
    echo helao repository not found.
    PAUSE
    exit /b
)

:: Activate Conda environment
call "%conda_path%" activate helao
:: Change directory to the helao repository
cd /d "%helao_repo%\testing"
title HELAO
:: Run the ipython script
ipython helao_interface.py sdc_cyan
PAUSE

@ECHO on

:: Check for Anaconda and Miniconda installation paths
if exist "C:\ProgramData\anaconda3\condabin\conda.bat" (
    set "conda_path=C:\ProgramData\anaconda3\condabin\conda.bat"
) else if exist "C:\Users\%USERNAME%\Anaconda3\condabin\conda.bat" (
    set "conda_path=C:\Users\%USERNAME%\Anaconda3\condabin\conda.bat"
) else if exist "C:\Anaconda3\condabin\conda.bat" (
    set "conda_path=C:\Anaconda3\condabin\conda.bat"
) else if exist "C:\Users\%USERNAME%\Miniconda3\condabin\conda.bat" (
    set "conda_path=C:\Users\%USERNAME%\Miniconda3\condabin\conda.bat"
) else if exist "C:\Miniconda3\condabin\conda.bat" (
    set "conda_path=C:\Miniconda3\condabin\conda.bat"
) else if exist "C:\ProgramData\Miniconda3\condabin\conda.bat" (
    set "conda_path=C:\ProgramData\Miniconda3\condabin\conda.bat"
) else (
    echo No Anaconda or Miniconda installation found.
    PAUSE
    exit /b
)

:: Check for helao repository paths
if exist "C:\Users\%USERNAME%\helao-pub" (
    set "helao_repo=C:\Users\%USERNAME%\helao-pub"
) else if exist "C:\Users\%USERNAME%\Documents\helao-pub" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao-pub"
)

else (
    echo helao repository not found.
    PAUSE
    exit /b
)

:: Activate Conda environment
call "%conda_path%" activate helao
:: Change directory to the helao repository
title HELAO
:: Run the ipython script
ipython helao.py sdc_tum
PAUSE

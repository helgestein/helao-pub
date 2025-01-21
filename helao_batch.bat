@ECHO off

setlocal EnableDelayedExpansion

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

echo Found Conda at: !conda_path!
call "!conda_path!" activate helao

:: Check for Helao repository paths
if exist "C:\Users\%USERNAME%\helao-dev" (
    set "helao_repo=C:\Users\%USERNAME%\helao-dev"
) else if exist "C:\Users\%USERNAME%\Documents\helao-dev" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao-dev"
) else if exist "C:\Users\%USERNAME%\Documents\helao-dev" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao-dev"
) else if exist "C:\Users\%USERNAME%\Documents\helao" (
    set "helao_repo=C:\Users\%USERNAME%\Documents\helao"
) else (
    echo Helao repository not found.
    PAUSE
    exit /b
)

echo Found HELAO repository at: !helao_repo!

:: Activate Conda environment
call "!conda_path!" activate helao

:: Change directory to the Helao repository
cd /d "!helao_repo!"

:: Set window title
title HELAO

:: Run the ipython script
ipython helao.py sdc_tum

PAUSE
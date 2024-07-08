@ECHO on
call C:\ProgramData\anaconda3\condabin\conda.bat activate helao
cd C:\Users\juliu\helao-dev

title orchestrator
ipython testing_orchestrator_script.py
ipython -i

PAUSE
@ECHO on
call C:\ProgramData\anaconda3\condabin\conda.bat activate helao
cd C:\Users\juliu\helao-dev

title testing_force
ipython testing_force_script.py
ipython -i

PAUSE
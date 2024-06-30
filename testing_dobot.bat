@ECHO on
call C:\ProgramData\anaconda3\condabin\conda.bat activate helao
cd C:\Users\juliu\helao-dev

title testing_dobot
ipython testing_dobot_script.py
ipython -i

PAUSE
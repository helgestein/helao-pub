@ECHO on
call C:\ProgramData\anaconda3\condabin\conda.bat activate helao
cd C:\Users\juliu\helao-dev\testing
title HELAO
ipython helao_interface.py sdc_cyan
PAUSE
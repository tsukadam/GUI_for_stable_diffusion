chcp 932
rem %~1 = �R�}���h
rem %~2 = stable-diffusion�̃��[�g�̃p�X
rem %~3 = ���[�g�̃h���C�u
rem %~4 = anaconda��activate.bat�̃p�X
rem %~5 = optimized_xxx2img.py�̃p�X
setlocal
set arg1=%~1
cd /d %~3
cd %~2
call %~4
call conda activate ldm
set optionTxt=%arg1:'="%
python %~5 %optionTxt%
endlocal
echo Completed
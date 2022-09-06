chcp 932
rem %~1 = コマンド
rem %~2 = stable-diffusionのルートのパス
rem %~3 = ルートのドライブ
rem %~4 = anacondaのactivate.batのパス
rem %~5 = optimized_xxx2img.pyのパス
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
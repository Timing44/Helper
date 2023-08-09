@echo off
setlocal

REM 设置pyinstaller命令
set pyinstaller_command=pyinstaller -F --i .\logo.ico .\helper.py -n helper.exe --hidden-import plyer.platforms.win.notification --noconsole

REM 执行pyinstaller命令，并将输出回显到命令行窗口
echo Running: %pyinstaller_command%
%pyinstaller_command%

endlocal
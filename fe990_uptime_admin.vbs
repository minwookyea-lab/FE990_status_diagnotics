Set objShell = CreateObject("Shell.Application")
strPath = CreateObject("WScript.Shell").CurrentDirectory
objShell.ShellExecute "cmd.exe", "/c cd /d """ & strPath & """ && python natural.py ""FE990 업타임 알려줘""", "", "runas", 1

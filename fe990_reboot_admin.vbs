Set objShell = CreateObject("Shell.Application")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.ShellExecute "cmd.exe", "/c cd /d """ & strScriptPath & """ && python natural.py ""FE990 재부팅""", "", "runas", 1

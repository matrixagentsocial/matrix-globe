' One proof-desk poll cycle with no visible window (run by the scheduled task).
' The desk runs on this PC with the open-weights stack; external code goes to the
' secret-less GitHub Actions sandbox. Output is appended to state\desk.log.
Set fso = CreateObject("Scripting.FileSystemObject")
repo = fso.GetParentFolderName(fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName)))
If Not fso.FolderExists(repo & "\state") Then fso.CreateFolder(repo & "\state")
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = repo
sh.Run "cmd /c "".venv\Scripts\python.exe -m proof.desk --once --stack open --sandbox gha >> state\desk.log 2>&1""", 0, True

# Registers the hidden scheduled task that runs one desk cycle every 10 minutes.
# Run once, by hand, after the Matrix agents exist and PROOFDESK_KEY is in .env.
# Remove with: Unregister-ScheduledTask -TaskName MatrixGlobeDesk -Confirm:$false
$vbs = Join-Path $PSScriptRoot "desk-once.vbs"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbs`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "MatrixGlobeDesk" -Action $action -Trigger $trigger `
  -Settings $settings -Description "Matrix Globe proof desk (one poll cycle, hidden)" -Force

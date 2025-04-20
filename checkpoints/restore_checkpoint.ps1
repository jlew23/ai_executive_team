# Restore Checkpoint Script
param (
    [Parameter(Mandatory=$true)]
    [string]$CheckpointName
)

$checkpointPath = ".\$CheckpointName"

# Check if checkpoint exists
if (-not (Test-Path $checkpointPath)) {
    Write-Error "Checkpoint '$CheckpointName' not found!"
    exit 1
}

# Stop any running Flask processes
Write-Host "Stopping any running Flask processes..." -ForegroundColor Yellow
Get-Process -Name python | Where-Object { $_.CommandLine -like "*run_dashboard.py*" } | Stop-Process -Force

# Backup current files before restoring
$backupFolder = "..\backup_before_restore_$(Get-Date -Format 'yyyy-MM-dd_HHmm')"
Write-Host "Creating backup of current files to $backupFolder..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
Copy-Item "..\run_dashboard.py" -Destination $backupFolder -Force
Copy-Item "..\web_dashboard" -Destination "$backupFolder\web_dashboard" -Recurse -Force

# Restore files from checkpoint
Write-Host "Restoring files from checkpoint '$CheckpointName'..." -ForegroundColor Green
Copy-Item "$checkpointPath\run_dashboard.py" -Destination "..\" -Force
Copy-Item "$checkpointPath\web_dashboard" -Destination "..\" -Recurse -Force

Write-Host "Checkpoint restored successfully!" -ForegroundColor Green
Write-Host "You can now run 'python run_dashboard.py' to start the application." -ForegroundColor Cyan

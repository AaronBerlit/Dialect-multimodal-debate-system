# Setup Ollama Models Path
$modelPath = "d:\PROJECTS\ollama\models"

Write-Host "[+] Setting OLLAMA_MODELS to $modelPath" -ForegroundColor Cyan

# Set for current user persistently
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $modelPath, "User")

# Set for current session
$env:OLLAMA_MODELS = $modelPath

Write-Host "[+] Restarting Ollama..." -ForegroundColor Yellow

# Kill existing Ollama processes
Write-Host "[+] Stopping all Ollama processes..." -ForegroundColor Yellow
Get-Process *ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Start Ollama in the background
# Note: On Windows, starting 'ollama app' or 'ollama serve'
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

Start-Sleep -Seconds 5

Write-Host "[+] Verifying models..." -ForegroundColor Green
ollama list

param (
    [string]$host,
    [string]$port,
    [string]$cmd
)

while (-not (Test-Connection -ComputerName $host -Port $port -Quiet)) {
    Write-Host "Waiting for $host:$port to be available..."
    Start-Sleep -Seconds 1
}

Write-Host "$host:$port is available - executing command"
Invoke-Expression $cmd

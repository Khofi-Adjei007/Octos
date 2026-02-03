Write-Host "=== RESETTING DJANGO MIGRATIONS ===" -ForegroundColor Yellow

$apps = @(
    "Human_Resources",
    "branches",
    "employees",
    "hr_workflows"
)

foreach ($app in $apps) {
    $path = "$app\migrations"

    if (Test-Path $path) {
        Get-ChildItem $path -Recurse -Include *.py |
            Where-Object { $_.Name -ne "__init__.py" } |
            Remove-Item -Force

        Get-ChildItem $path -Recurse -Include *.pyc |
            Remove-Item -Force -ErrorAction SilentlyContinue

        Write-Host "✔ Cleared migrations for $app"
    }
}

Write-Host "`n=== REMOVING __pycache__ ===" -ForegroundColor Yellow
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "`n=== DONE ===" -ForegroundColor Green

# Stop any existing Flask server on port 5000
try {
    $conn = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped existing process on port 5000"
    }
} catch {
    # Ignore errors
}

# Start the Flask server
Write-Host "Starting Flask server..."
python app.py
$env:APP_BASE_URL = if ($env:APP_BASE_URL) { $env:APP_BASE_URL } else { "http://127.0.0.1:5000" }
$env:ARDUINO_SERIAL_PORT = if ($env:ARDUINO_SERIAL_PORT) { $env:ARDUINO_SERIAL_PORT } else { "COM10" }
$env:ARDUINO_BAUD_RATE = if ($env:ARDUINO_BAUD_RATE) { $env:ARDUINO_BAUD_RATE } else { "9600" }
$env:RFID_DEFAULT_LOCATION = if ($env:RFID_DEFAULT_LOCATION) { $env:RFID_DEFAULT_LOCATION } else { "Main Gate" }
$env:ARDUINO_ENABLED = "true"

Write-Host "Starting Arduino bridge for $env:APP_BASE_URL on port $env:ARDUINO_SERIAL_PORT..."
py arduino_connection.py

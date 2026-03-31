import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class ArduinoRFIDBridge:
    def __init__(self, app_base_url, serial_port, baud_rate, default_location, enabled=True):
        self.app_base_url = app_base_url.rstrip("/")
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.default_location = default_location
        self.enabled = enabled
        self.connected = False
        self.last_tag = ""
        self.last_location = default_location
        self.last_message = ""
        self.last_scan_time = ""
        self.last_error = ""
        self._thread = None
        self._stop_event = threading.Event()
        self.status_update_url = f"{self.app_base_url}/arduino_status/update"

    def start(self):
        if not self.enabled or serial is None or self._thread:
            if serial is None:
                self.last_error = "pyserial is not installed. Run: pip install pyserial"
            self._publish_status()
            return

        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        self._publish_status()

    def stop(self):
        self._stop_event.set()
        self.connected = False
        self._publish_status()

    def get_status(self):
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "port": self.serial_port,
            "baud_rate": self.baud_rate,
            "default_location": self.default_location,
            "last_tag": self.last_tag,
            "last_location": self.last_location,
            "last_message": self.last_message,
            "last_scan_time": self.last_scan_time,
            "last_error": self.last_error,
            "pyserial_installed": serial is not None
        }

    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as connection:
                    self.connected = True
                    self.last_error = ""
                    self._publish_status()

                    while not self._stop_event.is_set():
                        raw_line = connection.readline().decode("utf-8", errors="ignore").strip()

                        if not raw_line:
                            continue

                        tag, location = self._parse_serial_message(raw_line)

                        if not tag:
                            self.last_error = f"Unrecognized serial data: {raw_line}"
                            continue

                        self.last_tag = tag
                        self.last_location = location
                        self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self._send_scan(tag, location)
                        self._publish_status()
            except PermissionError:  # pragma: no cover
                self.connected = False
                self.last_error = (
                    f"COM port {self.serial_port} is busy. Close Arduino Serial Monitor, "
                    "stop any old Flask/Python process, then restart the app."
                )
                self._publish_status()
                time.sleep(3)
            except Exception as exc:  # pragma: no cover
                self.connected = False
                self.last_error = str(exc)
                self._publish_status()
                time.sleep(3)

    def _parse_serial_message(self, raw_line):
        cleaned_line = raw_line.strip()

        for prefix in ("UID:", "RFID:", "TAG:"):
            if cleaned_line.upper().startswith(prefix):
                cleaned_line = cleaned_line[len(prefix):].strip()
                break

        location = self.default_location

        for separator in ("|", ","):
            if separator in cleaned_line:
                tag_part, location_part = cleaned_line.split(separator, 1)
                cleaned_line = tag_part.strip()
                location = location_part.strip() or self.default_location
                break

        tag = "".join(cleaned_line.split()).upper()
        return tag, location

    def _send_scan(self, tag, location):
        payload = json.dumps({
            "rfid_tag": tag,
            "location": location
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self.app_base_url}/rfid_scan",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                self.last_message = response_data.get("message", "Scan received")
                self.last_error = ""
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            self.last_message = ""
            self.last_error = f"HTTP {exc.code}: {error_body}"
            self._publish_status()
        except Exception as exc:  # pragma: no cover
            self.last_message = ""
            self.last_error = str(exc)
            self._publish_status()

    def _publish_status(self):
        payload = json.dumps(self.get_status()).encode("utf-8")

        request = urllib.request.Request(
            self.status_update_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=5):
                return
        except Exception:
            return


def create_arduino_bridge(app_base_url, serial_port, baud_rate, default_location, enabled=True):
    return ArduinoRFIDBridge(
        app_base_url=app_base_url,
        serial_port=serial_port,
        baud_rate=baud_rate,
        default_location=default_location,
        enabled=enabled
    )


if __name__ == "__main__":
    bridge = create_arduino_bridge(
        app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:5000"),
        serial_port=os.getenv("ARDUINO_SERIAL_PORT", "COM10"),
        baud_rate=int(os.getenv("ARDUINO_BAUD_RATE", "9600")),
        default_location=os.getenv("RFID_DEFAULT_LOCATION", "Main Gate"),
        enabled=os.getenv("ARDUINO_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    )

    bridge.start()

    try:
        while True:
            bridge._publish_status()
            time.sleep(5)
    except KeyboardInterrupt:
        bridge.stop()

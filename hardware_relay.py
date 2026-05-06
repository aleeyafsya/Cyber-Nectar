import serial
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

# configuration
SERIAL_PORT = 'COM3'  # the ESP32's COM port
BAUD_RATE = 115200
HTTP_PORT = 5000

print("="*50)
print("  CYBER NECTAR - HARDWARE RELAY BRIDGE")
print("="*50)

# intialise serial Connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # wait for ESP32 to reset
    print(f"Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"ERROR: Could not connect to {SERIAL_PORT}")
    print(f"Details: {e}")
    print("\nTip: Make sure the ESP32 is plugged in and check the COM port in 'Device Manager'.")
    sys.exit(1)

class RelayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        
        if self.path.startswith('/alert'):
            level = query_components.get("level", ["NORMAL"])[0]
            print(f"🕭 [DOCKER SIGNAL] Triggering level: {level}")
            
            try:
                # send the command over serial to the ESP32
                ser.write(f"{level}\n".encode())
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Relay Success")
            except Exception as e:
                print(f"Failed to relay signal: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    # silence logs to save console space
    def log_message(self, format, *args):
        return

def run():
    print(f"Relay Server active at http://localhost:{HTTP_PORT}")
    # print("Keep this window open during demo.")
    print("-" * 50)
    
    server_address = ('', HTTP_PORT)
    httpd = HTTPServer(server_address, RelayHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Relay...")
        ser.close()
        httpd.server_close()

if __name__ == '__main__':
    run()

import serial
import time
import sys
from hardware_bridge import HardwareBridge

def manual_test():
    # attempt to detect the COM port or use default
    port = 'COM3'
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    print(f"--- ESP32 Hardware Relay Test ---")
    print(f"Target: Host Relay (hardware_relay.py)")
    print(f"Instructions: Enter 1, 2, or 3 to trigger alerts. Enter 0 to reset. Ctrl+C to exit.")
    
    bridge = HardwareBridge(enabled=True)
    
    if not bridge.enabled:
        print("Test failed: Hardware bridge could not be initialised.")
        return

    try:
        while True:
            print("\nSelect Action:")
            print("1: Trigger CRITICAL (Red LED + Buzz)")
            print("2: Trigger MEDIUM (Yellow LED + Beep)")
            print("3: Trigger NORMAL (Reset Status)")
            print("0: Exit")
            
            choice = input("Choice: ")
            
            if choice == '1':
                bridge.send_alert("CRITICAL")
            elif choice == '2':
                bridge.send_alert("MEDIUM")
            elif choice == '3':
                bridge.send_alert("NORMAL")
            elif choice == '0':
                bridge.send_alert("NORMAL")
                break
            else:
                print("Invalid choice.")
                
    except KeyboardInterrupt:
        print("\nExiting test...")
    finally:
        bridge.close()

if __name__ == "__main__":
    manual_test()

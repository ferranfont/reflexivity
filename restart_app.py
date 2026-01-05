import os
import sys
import subprocess
import time

def kill_port_8000():
    print("Checking for process on port 8000...")
    # netstat -ano returns lines like:
    #   TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       1234
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode(errors='ignore')
        lines = output.split('\r\n')
        target_pid = None
        for line in lines:
            if ":8000 " in line and "LISTENING" in line:
                parts = line.strip().split()
                # The PID is usually the last element
                target_pid = parts[-1]
                break
        
        if target_pid:
            print(f"Found server PID: {target_pid}. Killing...")
            subprocess.run(f"taskkill /F /PID {target_pid}", shell=True)
            time.sleep(2)
            print("Process killed.")
        else:
            print("No internal server found on port 8000.")
            
    except Exception as e:
        print(f"Error killing process: {e}")

if __name__ == "__main__":
    kill_port_8000()
    # Now run show_main.py which will start the new server
    print("Launching application with fresh server...")
    subprocess.run([sys.executable, "show_main.py"])

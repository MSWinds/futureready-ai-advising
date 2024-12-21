import subprocess
import platform
import signal
import os
import time

def start_process(command, cwd):
    try:
        return subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=(platform.system() == "Windows")
        )
    except Exception as e:
        print(f"Failed to start process: {e}")
        return None

def stream_output(process, prefix):
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            print(f"{prefix}: {line.decode('utf-8').strip()}")

def main():
    print("Starting backend server...")
    backend = start_process(
        ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        "backend"
    )
    if not backend:
        return

    time.sleep(2)  # Brief pause to let backend initialize

    print("Starting frontend server...")
    frontend = start_process(
        ["npm", "run", "dev"],
        "frontend"
    )
    if not frontend:
        backend.terminate()
        return

    print("\nServers running at:")
    print("Frontend: http://localhost:3000")
    print("Backend: http://localhost:8000")
    print("Press Ctrl+C to stop both servers\n")

    try:
        while True:
            stream_output(backend, "[Backend]")
            stream_output(frontend, "[Frontend]")
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend.terminate()
        frontend.terminate()
        print("Servers terminated")

if __name__ == "__main__":
    main()
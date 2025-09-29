#!/usr/bin/env python3
"""
Clear all ports used by the movie recommender application
"""

import subprocess
import sys
import signal
import os
from port_config import ALL_PORTS

def kill_process_on_port(port):
    """Kill any process running on the specified port"""
    try:
        # Find processes using the port
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"🔫 Killing process {pid} on port {port}")
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ Process {pid} terminated")
                    except ProcessLookupError:
                        print(f"⚠️  Process {pid} already terminated")
                    except PermissionError:
                        print(f"❌ Permission denied to kill process {pid}")
                        # Try with sudo if available
                        try:
                            subprocess.run(['sudo', 'kill', pid], check=True)
                            print(f"✅ Process {pid} terminated with sudo")
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            print(f"❌ Could not kill process {pid} even with sudo")
            return True
        else:
            print(f"✅ No processes found on port {port}")
            return False
    except FileNotFoundError:
        print("❌ 'lsof' command not found. Please install it or use a different method.")
        return False

def main():
    print("🧹 Clearing Movie Recommender Ports")
    print("=" * 40)
    
    ports_to_clear = ALL_PORTS
    cleared_any = False
    
    for port in ports_to_clear:
        print(f"\n🔍 Checking port {port}...")
        if kill_process_on_port(port):
            cleared_any = True
    
    if cleared_any:
        print("\n✅ Port clearing completed!")
        print("💡 You can now start your servers with: python start_servers.py")
    else:
        print("\n✅ All ports are already clear!")
        print("💡 You can start your servers with: python start_servers.py")

if __name__ == "__main__":
    main()

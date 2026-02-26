#!/usr/bin/env python3
"""
FE990 CPU 사용량 빠른 조회
"""

from controller import ATController

# FE990 USB 연결 시 일반적인 IP 주소들
configs = [
    {"host": "192.168.1.1", "user": "root", "pass": "telit"},
    {"host": "192.168.225.1", "user": "root", "pass": "telit"},
    {"host": "192.168.0.1", "user": "root", "pass": "telit"},
    {"host": "192.168.100.1", "user": "root", "pass": "telit"},
    {"host": "169.254.6.1", "user": "root", "pass": "telit"},  # Cellular 인터페이스 기반
]

print("=" * 60)
print("FE990 CPU Usage Quick Test")
print("=" * 60)

for config in configs:
    print(f"\n[INFO] Trying {config['host']}...")
    
    controller = ATController(
        ssh_host=config["host"],
        ssh_user=config["user"],
        ssh_pass=config["pass"]
    )
    
    try:
        if controller.ssh_connect():
            print(f"[OK] Connected to {config['host']}")
            
            print("[INFO] Getting CPU usage...")
            cpu_usage = controller.get_remote_cpu_usage()
            
            if cpu_usage is not None:
                print(f"\n{'='*60}")
                print(f"✓ FE990 CPU Usage: {cpu_usage}%")
                print(f"{'='*60}")
                controller.ssh_disconnect()
                break
            else:
                print("[WARN] Failed to get CPU usage")
        else:
            print(f"[SKIP] Cannot connect to {config['host']}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        controller.ssh_disconnect()
else:
    print("\n[ERROR] Could not connect to FE990 with any configuration")
    print("\nPlease manually specify the connection:")
    print("  from controller import ATController")
    print("  controller = ATController(ssh_host='YOUR_IP', ssh_user='USER', ssh_pass='PASS')")
    print("  controller.ssh_connect()")
    print("  cpu = controller.get_remote_cpu_usage()")
    print(f"  print(f'CPU: {{cpu}}%')")

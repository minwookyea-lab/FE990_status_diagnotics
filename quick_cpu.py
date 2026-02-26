#!/usr/bin/env python3
"""
FE990 CPU 사용률 즉시 조회 (여러 IP 시도)
"""

from controller import ATController
import sys


def try_connect(ip: str, user: str = "root", password: str = "telit") -> tuple:
    """지정된 IP로 SSH 연결 시도"""
    controller = ATController(
        ssh_host=ip,
        ssh_user=user,
        ssh_pass=password
    )
    
    print(f"[INFO] Trying {ip}...", end=" ")
    if controller.ssh_connect():
        print("✓ Connected")
        return controller, True
    else:
        print("✗ Failed")
        return controller, False


def main():
    """FE990 CPU 사용량 조회 (여러 IP 시도)"""
    print("=" * 60)
    print("FE990 CPU Usage Query")
    print("=" * 60)
    
    # 시도할 IP 주소 목록
    ip_candidates = [
        "192.168.1.1",
        "192.168.0.1",
        "10.0.0.1",
        "172.16.0.1",
    ]
    
    controller = None
    connected = False
    
    try:
        # 여러 IP로 연결 시도
        print("\n[INFO] Attempting SSH connection...")
        for ip in ip_candidates:
            controller, connected = try_connect(ip)
            if connected:
                break
        
        if not connected:
            print("\n[ERROR] Could not connect to any IP address")
            print("[INFO] Please check FE990 IP address or network connection")
            sys.exit(1)
        
        # CPU 사용량 조회
        print("\n[INFO] Measuring CPU usage...")
        cpu_usage = controller.get_remote_cpu_usage()
        
        if cpu_usage is not None:
            print(f"\n{'='*60}")
            print(f"  FE990 CPU Usage: {cpu_usage}%")
            print(f"{'='*60}")
        else:
            print("[ERROR] Failed to get CPU usage")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # SSH 연결 해제
        if controller:
            controller.ssh_disconnect()
            print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

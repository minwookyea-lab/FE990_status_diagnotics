#!/usr/bin/env python3
"""
FE990 CPU 사용률 간단 조회
SSH IP 주소를 직접 입력받아 측정
"""

from controller import ATController
import sys


def main():
    """FE990 CPU 사용률 조회"""
    print("=" * 60)
    print("FE990 CPU Usage Query")
    print("=" * 60)
    
    # SSH 정보 입력
    print("\nEnter FE990 SSH connection info:")
    ip = input("  IP address [192.168.1.1]: ").strip() or "192.168.1.1"
    user = input("  Username [root]: ").strip() or "root"
    password = input("  Password [telit]: ").strip() or "telit"
    
    controller = ATController(
        ssh_host=ip,
        ssh_user=user,
        ssh_pass=password
    )
    
    try:
        # SSH 연결
        print(f"\n[INFO] Connecting to {ip}...")
        if not controller.ssh_connect():
            print(f"[ERROR] Failed to connect to {ip}")
            print("[INFO] Please check:")
            print("  - IP address is correct")
            print("  - FE990 is on the network")
            print("  - SSH is enabled")
            sys.exit(1)
        
        print("[OK] SSH Connected")
        
        # CPU 사용률 측정
        print("\n[INFO] Measuring CPU usage...")
        cpu_usage = controller.get_remote_cpu_usage()
        
        if cpu_usage is not None:
            print(f"\n{'='*60}")
            print(f"  FE990 CPU Usage: {cpu_usage}%")
            print(f"{'='*60}")
        else:
            print("[ERROR] Failed to measure CPU usage")
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
        controller.ssh_disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

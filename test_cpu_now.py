#!/usr/bin/env python3
"""
FE990 CPU 사용량 즉시 조회
"""

from controller import ATController
import sys


def main():
    """FE990 CPU 사용량 조회 (기본값 사용)"""
    print("=" * 60)
    print("FE990 CPU Usage Query")
    print("=" * 60)
    
    # 기본 SSH 정보로 컨트롤러 초기화
    controller = ATController(
        ssh_host="192.168.1.1",
        ssh_user="root",
        ssh_pass="telit"
    )
    
    try:
        # SSH 연결
        print(f"\n[INFO] Connecting to 192.168.1.1...")
        if not controller.ssh_connect():
            print(f"[ERROR] Failed to connect to 192.168.1.1")
            sys.exit(1)
        
        print("[OK] SSH Connected")
        
        # CPU 사용량 조회
        print("\n[INFO] Querying CPU usage...")
        cpu_usage = controller.get_remote_cpu_usage()
        
        if cpu_usage is not None:
            print(f"\n{'='*60}")
            print(f"CPU Usage: {cpu_usage}%")
            print(f"{'='*60}")
        else:
            print("[ERROR] Failed to get CPU usage")
            sys.exit(1)
    
    finally:
        # SSH 연결 해제
        controller.ssh_disconnect()
        print("\n[OK] SSH Disconnected")


if __name__ == "__main__":
    main()

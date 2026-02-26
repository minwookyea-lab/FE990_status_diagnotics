#!/usr/bin/env python3
"""
FE990 CPU 사용량 조회 (SSH 방식)
SSH로 FE990에 접속하여 /proc/stat을 읽어 CPU 사용률 계산
"""

from controller import ATController
import sys


def main():
    """FE990 CPU 사용량 SSH 조회"""
    print("=" * 60)
    print("FE990 CPU Usage Query via SSH")
    print("=" * 60)
    
    # SSH 정보 입력 (기본값 사용 가능)
    ssh_host = input(f"SSH Host [192.168.1.1]: ").strip() or "192.168.1.1"
    ssh_user = input(f"SSH User [root]: ").strip() or "root"
    ssh_pass = input(f"SSH Password [telit]: ").strip() or "telit"
    
    # 컨트롤러 초기화
    controller = ATController(
        ssh_host=ssh_host,
        ssh_user=ssh_user,
        ssh_pass=ssh_pass
    )
    
    try:
        # SSH 연결
        print(f"\n[INFO] Connecting to {ssh_host}...")
        if not controller.ssh_connect():
            print(f"[ERROR] Failed to connect to {ssh_host}")
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


def quick_test(host: str = "192.168.1.1", user: str = "root", password: str = "telit"):
    """빠른 테스트용 함수"""
    controller = ATController(ssh_host=host, ssh_user=user, ssh_pass=password)
    
    try:
        print(f"[INFO] Connecting to {host}...")
        if not controller.ssh_connect():
            print(f"[ERROR] Failed to connect")
            return None
        
        print("[OK] Connected")
        print("[INFO] Getting CPU usage...")
        
        cpu_usage = controller.get_remote_cpu_usage()
        controller.ssh_disconnect()
        
        return cpu_usage
    except Exception as e:
        print(f"[ERROR] {e}")
        controller.ssh_disconnect()
        return None


if __name__ == "__main__":
    # 대화형 모드로 실행
    main()
    
    # 빠른 테스트를 원하면 아래 주석 해제
    # cpu = quick_test()
    # if cpu is not None:
    #     print(f"CPU Usage: {cpu}%")

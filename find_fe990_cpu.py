#!/usr/bin/env python3
"""
FE990 자동 검색 및 CPU 사용률 조회
일반적인 USB 모뎀 IP 주소들을 스캔
"""

from controller import ATController
import socket


def check_host(host, port=22, timeout=2):
    """호스트 포트가 열려있는지 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def find_and_get_cpu():
    """FE990 찾아서 CPU 사용률 조회"""
    
    # 일반적인 USB 모뎀 IP 주소들
    candidates = [
        ("192.168.225.1", "root", "telit"),    # Telit 모듈 기본값
        ("192.168.1.1", "root", "telit"),
        ("192.168.0.1", "root", "telit"),
        ("10.0.0.1", "root", "telit"),
        ("192.168.1.1", "admin", "admin"),
        ("192.168.225.1", "root", "root"),
    ]
    
    print("=" * 60)
    print("FE990 Auto-Discovery & CPU Usage")
    print("=" * 60)
    
    for host, user, password in candidates:
        print(f"\n[SCAN] Checking {host}...", end=" ")
        
        # SSH 포트 확인
        if not check_host(host, port=22, timeout=2):
            print("✗ No SSH service")
            continue
        
        print("✓ SSH open")
        print(f"[INFO] Trying login ({user}@{host})...", end=" ")
        
        # SSH 연결 시도
        controller = ATController(
            ssh_host=host,
            ssh_user=user,
            ssh_pass=password
        )
        
        try:
            if controller.ssh_connect():
                print("✓ Connected!")
                
                # CPU 사용률 조회
                print("[INFO] Getting CPU usage...", end=" ")
                cpu_usage = controller.get_remote_cpu_usage()
                
                if cpu_usage is not None:
                    print(f"✓ Done")
                    print("\n" + "=" * 60)
                    print(f"✓ Found FE990 at {host}")
                    print(f"  User: {user}")
                    print(f"  CPU Usage: {cpu_usage}%")
                    print("=" * 60)
                    controller.ssh_disconnect()
                    return True
                else:
                    print("✗ Failed")
                    controller.ssh_disconnect()
            else:
                print("✗ Auth failed")
        except Exception as e:
            print(f"✗ Error: {e}")
            controller.ssh_disconnect()
    
    print("\n" + "=" * 60)
    print("✗ FE990 not found")
    print("=" * 60)
    print("\nPlease check:")
    print("  1. FE990 is connected via USB")
    print("  2. Network interface is up (ipconfig)")
    print("  3. SSH service is enabled on FE990")
    print("\nOr manually specify:")
    print("  controller = ATController(ssh_host='IP', ssh_user='USER', ssh_pass='PASS')")
    print("  controller.ssh_connect()")
    print("  cpu = controller.get_remote_cpu_usage()")
    
    return False


if __name__ == "__main__":
    find_and_get_cpu()

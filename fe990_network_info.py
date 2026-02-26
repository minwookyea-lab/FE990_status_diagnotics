#!/usr/bin/env python3
"""
FE990 네트워크 정보 조회 - IP 주소 찾기
"""

from controller import ATController
import sys

def main():
    print("=" * 60)
    print("FE990 Network Info Query")
    print("=" * 60)
    
    # COM9 포트로 연결
    controller = ATController(port="COM9")
    
    try:
        print(f"[INFO] Connecting to {controller.port}...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to {controller.port}")
            sys.exit(1)
        
        print("[OK] Connected")
        
        # 네트워크 관련 명령어 테스트
        commands = [
            "AT+CGPADDR",       # PDP 주소 조회
            "AT#IPADDR",        # IP 주소 조회
            "AT#NETCONFIG",     # 네트워크 설정 조회
            "AT#NWCONFIG",      # 네트워크 설정
            "AT#IPCONFIG",      # IP 설정 조회
            "AT+CGCONTRDP",     # 동적 파라미터
            "AT#WANIP",         # WAN IP
            "AT#LANIP",         # LAN IP
        ]
        
        print("\n[INFO] Testing network commands...")
        for cmd in commands:
            print(f"\n[TEST] Sending: {cmd}")
            response = controller.send_cmd(cmd, wait_s=1.0)
            decoded = response.decode('ascii', errors='ignore')
            
            # ERROR가 아닌 응답만 출력
            if "ERROR" not in decoded:
                print(f"[Response] {decoded}")
            else:
                print("[SKIP] Command not supported")
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

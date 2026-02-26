#!/usr/bin/env python3
"""
FE990 간단한 CPU 사용량 - AT 명령으로 직접 실행
FE990에서 shell 명령 실행이 가능한지 테스트
"""

from controller import ATController
import sys

def main():
    print("=" * 60)
    print("FE990 Shell Command Test")
    print("=" * 60)
    
    controller = ATController(port="COM9")
    
    try:
        print(f"[INFO] Connecting to {controller.port}...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect")
            sys.exit(1)
        
        print("[OK] Connected\n")
        
        # Shell 명령 실행 시도
        test_commands = [
            ("AT#SHCMD=\"cat /proc/stat | head -1\"", "Shell 명령 직접 실행"),
            ("AT#SHCMD=\"uptime\"", "uptime 명령"),
            ("AT#SHCMD=\"top -bn1 | head -5\"", "top 명령"),
            ("AT#SHELL=\"cat /proc/stat\"", "SHELL 명령 시도"),
            ("AT#CMD=\"cat /proc/stat\"", "CMD 명령 시도"),
        ]
        
        for cmd, desc in test_commands:
            print(f"[TEST] {desc}: {cmd}")
            response = controller.send_cmd(cmd, wait_s=2.0)
            decoded = response.decode('ascii', errors='ignore')
            
            if "ERROR" not in decoded:
                print(f"[OK] Response:\n{decoded}")
                print("-" * 60)
            else:
                print("[SKIP] Not supported\n")
    
    finally:
        controller.disconnect()
        print("[OK] Disconnected")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FE990 CPU 사용률 - AT 명령으로 셸 실행
"""

from controller import ATController
import time
import re


def execute_shell_command(controller, cmd):
    """AT#SHCMD로 셸 명령 실행"""
    at_cmd = f'AT#SHCMD="{cmd}"'
    response = controller.send_cmd(at_cmd, wait_s=1.0)
    decoded = response.decode('ascii', errors='ignore')
    return decoded


def get_cpu_line(controller):
    """CPU 정보 라인 가져오기"""
    response = execute_shell_command(controller, "cat /proc/stat | head -1")
    
    # 응답에서 'cpu' 라인 찾기
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('cpu '):
            return line
    
    return None


def calculate_cpu_usage(line1, line2):
    """두 CPU 라인으로 사용률 계산"""
    try:
        values1 = [int(v) for v in line1.split()[1:]]
        values2 = [int(v) for v in line2.split()[1:]]
        
        total1 = sum(values1)
        total2 = sum(values2)
        idle1 = values1[3] + (values1[4] if len(values1) > 4 else 0)
        idle2 = values2[3] + (values2[4] if len(values2) > 4 else 0)
        
        total_delta = total2 - total1
        idle_delta = idle2 - idle1
        
        if total_delta == 0:
            return 0.0
        
        cpu_usage = (1.0 - idle_delta / total_delta) * 100.0
        return cpu_usage
    except Exception as e:
        print(f"[ERROR] Calculation failed: {e}")
        return None


def main():
    """FE990 CPU 사용률 측정 - AT#SHCMD 사용"""
    print("=" * 60)
    print("FE990 CPU Usage via AT#SHCMD")
    print("=" * 60)
    
    # COM9로 연결 (사용 가능한 포트)
    controller = ATController(port="COM9")
    
    try:
        print(f"\n[INFO] Connecting to COM9...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to COM9")
            return
        
        print("[OK] Connected")
        
        # AT#SHCMD 지원 여부 테스트
        print("\n[TEST] Testing AT#SHCMD command...")
        test_response = execute_shell_command(controller, "echo test")
        print(f"Response: {test_response.strip()}")
        
        if "ERROR" in test_response:
            print("\n[ERROR] AT#SHCMD not supported")
            print("\n[HELP] Trying alternative shell commands...")
            
            # 다른 명령어 시도
            alt_commands = [
                ('AT#SHELLCMD="cat /proc/stat | head -1"', "SHELLCMD"),
                ('AT$SHELL="cat /proc/stat | head -1"', "$SHELL"),
                ('AT+SYSCMD="cat /proc/stat | head -1"', "+SYSCMD"),
            ]
            
            for cmd, name in alt_commands:
                print(f"\n[TEST] {name}")
                response = controller.send_cmd(cmd, wait_s=1.0)
                decoded = response.decode('ascii', errors='ignore')
                print(f"Response: {decoded.strip()[:200]}")
                
                if "ERROR" not in decoded and "cpu" in decoded.lower():
                    print(f"[OK] {name} works!")
                    break
            
            print("\n[ERROR] No working shell command found")
            print("[INFO] CPU usage requires SSH access")
            return
        
        # CPU 정보 수집
        print("\n[INFO] Measuring CPU usage...")
        
        line1 = get_cpu_line(controller)
        if not line1:
            print("[ERROR] Failed to get first CPU measurement")
            return
        
        print(f"[DEBUG] CPU line 1: {line1}")
        
        # 1초 대기
        time.sleep(1.0)
        
        line2 = get_cpu_line(controller)
        if not line2:
            print("[ERROR] Failed to get second CPU measurement")
            return
        
        print(f"[DEBUG] CPU line 2: {line2}")
        
        # CPU 사용률 계산
        cpu_usage = calculate_cpu_usage(line1, line2)
        
        if cpu_usage is not None:
            print(f"\n{'='*60}")
            print(f"  FE990 CPU Usage: {cpu_usage:.2f}%")
            print(f"{'='*60}")
        else:
            print("\n[ERROR] Failed to calculate CPU usage")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

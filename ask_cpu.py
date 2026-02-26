#!/usr/bin/env python3
"""
FE990 CPU 사용량 조회 스크립트
"""

from controller import ATController
import sys
import time


def read_proc_stat(controller):
    """
    /proc/stat 파일을 읽어서 CPU 시간 정보를 반환
    
    Args:
        controller: ATController 인스턴스
        
    Returns:
        dict: CPU 시간 정보 {'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq'}
              실패 시 None
    """
    try:
        # AT 명령어로 /proc/stat 읽기 시도
        cmd = 'AT#SHCMD="cat /proc/stat | head -1"'
        response = controller.send_cmd(cmd, wait_s=1.0)
        
        if not response:
            print("[DEBUG] No response from AT command")
            return None
            
        # 응답을 문자열로 변환
        stat_data = response.decode('ascii', errors='ignore')
        print(f"[DEBUG] Response: {stat_data}")
        
        # 첫 번째 줄(cpu 전체 정보) 파싱
        for line in stat_data.split('\n'):
            if line.startswith('cpu '):
                parts = line.split()
                if len(parts) >= 8:
                    return {
                        'user': int(parts[1]),
                        'nice': int(parts[2]),
                        'system': int(parts[3]),
                        'idle': int(parts[4]),
                        'iowait': int(parts[5]),
                        'irq': int(parts[6]),
                        'softirq': int(parts[7])
                    }
        
        print("[DEBUG] No 'cpu ' line found in response")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read /proc/stat: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_cpu_usage(stat1, stat2):
    """
    두 시점의 /proc/stat 데이터로부터 CPU 사용률을 계산
    
    Args:
        stat1: 첫 번째 시점의 CPU 시간 정보
        stat2: 두 번째 시점의 CPU 시간 정보
        
    Returns:
        float: CPU 사용률 (0-100%), 계산 실패 시 None
    """
    if not stat1 or not stat2:
        return None
    
    try:
        # 각 시점의 총 CPU 시간 계산
        total1 = sum(stat1.values())
        total2 = sum(stat2.values())
        
        # 변화량 계산
        total_delta = total2 - total1
        idle_delta = stat2['idle'] - stat1['idle']
        
        if total_delta == 0:
            return None
        
        # CPU 사용률 계산 (idle이 아닌 시간의 비율)
        cpu_usage = (1.0 - idle_delta / total_delta) * 100.0
        
        return cpu_usage
    except Exception as e:
        print(f"[ERROR] Failed to calculate CPU usage: {e}")
        return None


def get_cpu_usage(controller, interval=1.0):
    """
    /proc/stat을 읽어서 CPU 사용률을 계산
    
    Args:
        controller: ATController 인스턴스
        interval: 측정 간격 (초)
        
    Returns:
        float: CPU 사용률 (0-100%), 실패 시 None
    """
    # 첫 번째 측정
    stat1 = read_proc_stat(controller)
    if not stat1:
        return None
    
    # 대기
    time.sleep(interval)
    
    # 두 번째 측정
    stat2 = read_proc_stat(controller)
    if not stat2:
        return None
    
    # CPU 사용률 계산
    return calculate_cpu_usage(stat1, stat2)


def main():
    """FE990 CPU 사용량 조회"""
    print("=" * 60)
    print("FE990 CPU Usage Query")
    print("=" * 60)
    
    # 컨트롤러 초기화 (포트: COM9)
    controller = ATController(port="COM9")
    
    try:
        # 연결
        print(f"[INFO] Connecting to {controller.port}...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to {controller.port}")
            sys.exit(1)
        
        print("[OK] Connected")
        
        # /proc/stat을 이용한 CPU 사용률 측정
        print("\n[INFO] Measuring CPU usage from /proc/stat...")
        cpu_usage = get_cpu_usage(controller, interval=1.0)
        
        if cpu_usage is not None:
            print(f"[OK] CPU Usage: {cpu_usage:.2f}%")
        else:
            print("[ERROR] Failed to measure CPU usage")
        
        # CPU 사용량 조회 시도 (여러 명령어 테스트)
        commands = [
            "AT#cpu",           # CPU 사용량 조회 시도
            "AT#cpuusage",      # CPU usage 조회 시도
            "AT#stat",          # 통계 정보 조회 시도
            "AT#sysinfo",       # 시스템 정보 조회 시도
            "AT#top",           # top 정보 조회 시도
        ]
        
        print("\n[INFO] Testing CPU usage commands...")
        for cmd in commands:
            print(f"\n[TEST] Sending: {cmd}")
            response = controller.send_cmd(cmd, wait_s=1.0)
            print(f"[Response] {response.decode('ascii', errors='ignore')}")
        
        # 추가: 일반적인 시스템 정보 명령어 테스트
        print("\n[INFO] Testing general system commands...")
        general_commands = [
            "AT#help",          # 도움말
            "AT#?",             # 명령어 목록
            "ATI",              # 정보 조회
        ]
        
        for cmd in general_commands:
            print(f"\n[TEST] Sending: {cmd}")
            response = controller.send_cmd(cmd, wait_s=1.0)
            print(f"[Response] {response.decode('ascii', errors='ignore')}")
    
    finally:
        # 연결 해제
        controller.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

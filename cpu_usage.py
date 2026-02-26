#!/usr/bin/env python3
"""
/proc/stat을 읽어서 CPU 사용률을 계산하는 유틸리티 함수
"""

import time
from typing import Optional, Dict


def parse_proc_stat(stat_content: str) -> Optional[Dict[str, int]]:
    """
    /proc/stat 내용을 파싱하여 CPU 시간 정보를 반환
    
    Args:
        stat_content: /proc/stat 파일의 내용 (첫 번째 줄만 있어도 됨)
        
    Returns:
        dict: CPU 시간 정보 {'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq'}
              파싱 실패 시 None
              
    Example:
        >>> stat = "cpu  1234 567 890 12345 678 90 12 0 0 0"
        >>> result = parse_proc_stat(stat)
        >>> print(result)
        {'user': 1234, 'nice': 567, 'system': 890, 'idle': 12345, 'iowait': 678, 'irq': 90, 'softirq': 12}
    """
    try:
        # 첫 번째 줄(cpu 전체 정보) 찾기
        for line in stat_content.split('\n'):
            line = line.strip()
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
        return None
    except (ValueError, IndexError) as e:
        print(f"[ERROR] Failed to parse /proc/stat: {e}")
        return None


def calculate_cpu_usage(stat1: Dict[str, int], stat2: Dict[str, int]) -> Optional[float]:
    """
    두 시점의 /proc/stat 데이터로부터 CPU 사용률을 계산
    
    Args:
        stat1: 첫 번째 시점의 CPU 시간 정보
        stat2: 두 번째 시점의 CPU 시간 정보
        
    Returns:
        float: CPU 사용률 (0.0-100.0%), 계산 실패 시 None
        
    Example:
        >>> stat1 = {'user': 1000, 'nice': 100, 'system': 200, 'idle': 5000, 'iowait': 50, 'irq': 10, 'softirq': 5}
        >>> stat2 = {'user': 1100, 'nice': 110, 'system': 220, 'idle': 5200, 'iowait': 55, 'irq': 12, 'softirq': 6}
        >>> usage = calculate_cpu_usage(stat1, stat2)
        >>> print(f"{usage:.2f}%")
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
    except (KeyError, ZeroDivisionError) as e:
        print(f"[ERROR] Failed to calculate CPU usage: {e}")
        return None


def get_cpu_usage_local(interval: float = 1.0) -> Optional[float]:
    """
    로컬 시스템의 /proc/stat을 읽어서 CPU 사용률을 계산
    (Linux 시스템에서만 동작)
    
    Args:
        interval: 측정 간격 (초)
        
    Returns:
        float: CPU 사용률 (0.0-100.0%), 실패 시 None
        
    Example:
        >>> usage = get_cpu_usage_local(interval=1.0)
        >>> if usage is not None:
        ...     print(f"CPU Usage: {usage:.2f}%")
    """
    try:
        # 첫 번째 측정
        with open('/proc/stat', 'r') as f:
            stat_content1 = f.read()
        stat1 = parse_proc_stat(stat_content1)
        if not stat1:
            return None
        
        # 대기
        time.sleep(interval)
        
        # 두 번째 측정
        with open('/proc/stat', 'r') as f:
            stat_content2 = f.read()
        stat2 = parse_proc_stat(stat_content2)
        if not stat2:
            return None
        
        # CPU 사용률 계산
        return calculate_cpu_usage(stat1, stat2)
        
    except FileNotFoundError:
        print("[ERROR] /proc/stat not found. This function only works on Linux systems.")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read /proc/stat: {e}")
        return None


def get_cpu_usage_remote(read_func, interval: float = 1.0) -> Optional[float]:
    """
    원격 시스템의 /proc/stat을 읽어서 CPU 사용률을 계산
    
    Args:
        read_func: /proc/stat을 읽어서 문자열로 반환하는 함수
                   예: lambda: ssh_client.exec_command("cat /proc/stat")[1].read().decode()
        interval: 측정 간격 (초)
        
    Returns:
        float: CPU 사용률 (0.0-100.0%), 실패 시 None
        
    Example:
        >>> def read_remote_stat():
        ...     # SSH나 다른 방법으로 원격의 /proc/stat 읽기
        ...     return remote_execute("cat /proc/stat")
        >>> usage = get_cpu_usage_remote(read_remote_stat, interval=1.0)
        >>> if usage is not None:
        ...     print(f"CPU Usage: {usage:.2f}%")
    """
    try:
        # 첫 번째 측정
        stat_content1 = read_func()
        stat1 = parse_proc_stat(stat_content1)
        if not stat1:
            return None
        
        # 대기
        time.sleep(interval)
        
        # 두 번째 측정
        stat_content2 = read_func()
        stat2 = parse_proc_stat(stat_content2)
        if not stat2:
            return None
        
        # CPU 사용률 계산
        return calculate_cpu_usage(stat1, stat2)
        
    except Exception as e:
        print(f"[ERROR] Failed to get remote CPU usage: {e}")
        return None


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("CPU Usage Calculator - Test")
    print("=" * 60)
    
    # 로컬 시스템 테스트
    print("\n[TEST] Local CPU usage measurement...")
    usage = get_cpu_usage_local(interval=1.0)
    
    if usage is not None:
        print(f"[OK] CPU Usage: {usage:.2f}%")
    else:
        print("[FAIL] Could not measure CPU usage")
        print("      This is normal on non-Linux systems (Windows, macOS)")
    
    # 파싱 테스트
    print("\n[TEST] Parsing test...")
    test_stat = "cpu  1234567 5678 890123 45678901 12345 678 90 0 0 0"
    result = parse_proc_stat(test_stat)
    if result:
        print(f"[OK] Parsed: {result}")
    else:
        print("[FAIL] Failed to parse")
    
    print("\n" + "=" * 60)

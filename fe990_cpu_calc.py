#!/usr/bin/env python3
"""
FE990 CPU 사용률 측정 스크립트
/proc/stat을 읽어서 CPU 사용률 계산
"""

import time


def get_cpu_usage(interval=0.5):
    """
    /proc/stat을 두 번 읽어서 CPU 사용률(%) 계산
    
    Args:
        interval: 측정 간격 (초, 기본값: 0.5)
    
    Returns:
        int: CPU 사용률 (0-100%)
    """
    def read_cpu_times():
        """CPU 시간 값 읽기"""
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        
        if not line.startswith('cpu '):
            raise ValueError("Invalid /proc/stat format")
        
        # cpu  user nice system idle iowait irq softirq...
        values = [int(v) for v in line.split()[1:]]
        
        total = sum(values)
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        
        return total, idle
    
    # 첫 번째 측정
    total1, idle1 = read_cpu_times()
    
    # 대기
    time.sleep(interval)
    
    # 두 번째 측정
    total2, idle2 = read_cpu_times()
    
    # CPU 사용률 계산
    total_delta = total2 - total1
    idle_delta = idle2 - idle1
    
    if total_delta == 0:
        return 0
    
    usage = ((total_delta - idle_delta) / total_delta) * 100
    return int(usage)


def main():
    """메인 실행"""
    try:
        print("Measuring CPU usage...")
        cpu = get_cpu_usage()
        print(f"CPU: {cpu}%")
        return cpu
    except FileNotFoundError:
        print("Error: /proc/stat not found (Not a Linux system?)")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FE990 CPU 사용률 - USB 시리얼 직접 연결
"""

import serial
import time
import re


def test_shell_access(port, baudrate=115200):
    """시리얼 포트로 직접 셸 명령 실행 시도"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        print(f"[INFO] Connected to {port}")
        
        # 기존 버퍼 비우기
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Enter 몇 번 보내서 프롬프트 확인
        ser.write(b'\r\n')
        time.sleep(0.3)
        response = ser.read(ser.in_waiting or 1000)
        print(f"[DEBUG] Initial response: {response[:200]}")
        
        # cat /proc/stat 명령 시도
        cmd = "cat /proc/stat | head -1\r\n"
        ser.write(cmd.encode())
        time.sleep(0.5)
        
        response = b""
        deadline = time.time() + 2
        while time.time() < deadline:
            if ser.in_waiting:
                response += ser.read(ser.in_waiting)
            time.sleep(0.1)
        
        decoded = response.decode('ascii', errors='ignore')
        print(f"\n[RESPONSE]\n{decoded}\n")
        
        # CPU 라인 찾기
        for line in decoded.split('\n'):
            if line.strip().startswith('cpu '):
                print(f"[OK] Found CPU line: {line.strip()}")
                ser.close()
                return True, line.strip()
        
        ser.close()
        return False, decoded
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False, str(e)


def parse_cpu_stats(line1, line2):
    """두 CPU 라인에서 사용률 계산"""
    try:
        values1 = [int(v) for v in line1.split()[1:]]
        values2 = [int(v) for v in line2.split()[1:]]
        
        total1 = sum(values1)
        total2 = sum(values2)
        idle1 = values1[3]
        idle2 = values2[3]
        
        total_delta = total2 - total1
        idle_delta = idle2 - idle1
        
        if total_delta == 0:
            return 0.0
        
        cpu_usage = (1.0 - idle_delta / total_delta) * 100.0
        return cpu_usage
    except:
        return None


def measure_cpu_direct(port, baudrate=115200):
    """직접 셸 명령으로 CPU 측정"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        # 첫 번째 측정
        ser.reset_input_buffer()
        ser.write(b"cat /proc/stat | head -1\r\n")
        time.sleep(0.5)
        response1 = ser.read(ser.in_waiting or 1000).decode('ascii', errors='ignore')
        
        line1 = None
        for line in response1.split('\n'):
            if line.strip().startswith('cpu '):
                line1 = line.strip()
                break
        
        if not line1:
            ser.close()
            return None
        
        # 1초 대기
        time.sleep(1.0)
        
        # 두 번째 측정
        ser.reset_input_buffer()
        ser.write(b"cat /proc/stat | head -1\r\n")
        time.sleep(0.5)
        response2 = ser.read(ser.in_waiting or 1000).decode('ascii', errors='ignore')
        
        line2 = None
        for line in response2.split('\n'):
            if line.strip().startswith('cpu '):
                line2 = line.strip()
                break
        
        ser.close()
        
        if not line2:
            return None
        
        # CPU 사용률 계산
        return parse_cpu_stats(line1, line2)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def main():
    """FE990 CPU 사용률 측정 (USB 직접 연결)"""
    print("=" * 60)
    print("FE990 CPU Usage - Direct USB Access")
    print("=" * 60)
    
    # 테스트할 포트들
    test_ports = [
        ("COM7", 115200, "Diagnostics Interface"),
        ("COM9", 115200, "Auxiliary Interface"),
        ("COM8", 115200, "USB Modem"),
        ("COM33", 115200, "USB Modem 2"),
    ]
    
    print("\n[STEP 1] Testing shell access on each port...")
    
    shell_port = None
    for port, baud, desc in test_ports:
        print(f"\n[TEST] {port} ({desc})")
        success, result = test_shell_access(port, baud)
        
        if success:
            shell_port = port
            print(f"[OK] {port} has shell access!")
            break
    
    if not shell_port:
        print("\n[ERROR] No port with shell access found")
        print("[HELP] FE990 may need special configuration for shell access")
        return
    
    # CPU 측정
    print(f"\n[STEP 2] Measuring CPU usage via {shell_port}...")
    cpu_usage = measure_cpu_direct(shell_port)
    
    if cpu_usage is not None:
        print(f"\n{'='*60}")
        print(f"  FE990 CPU Usage: {cpu_usage:.2f}%")
        print(f"  Port: {shell_port}")
        print(f"{'='*60}")
    else:
        print("\n[ERROR] Failed to measure CPU usage")


if __name__ == "__main__":
    main()

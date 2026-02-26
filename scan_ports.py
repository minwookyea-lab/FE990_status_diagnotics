#!/usr/bin/env python3
"""
사용 가능한 COM 포트 스캔 및 FE990 찾기
"""

import serial.tools.list_ports
from controller import ATController
import re


def scan_available_ports():
    """사용 가능한 COM 포트 스캔"""
    print("=" * 60)
    print("Scanning Available COM Ports")
    print("=" * 60)
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("\n[WARNING] No COM ports found")
        return []
    
    print(f"\nFound {len(ports)} COM port(s):")
    available_ports = []
    
    for port in ports:
        print(f"\n  Port: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        available_ports.append(port.device)
    
    return available_ports


def try_connect_port(port):
    """지정된 포트로 연결 시도"""
    try:
        controller = ATController(port=port)
        if controller.connect():
            # ATI 명령으로 장치 정보 확인
            response = controller.send_cmd("ATI", wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            
            # IP 주소 찾기
            ip_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
            ips = ip_pattern.findall(decoded)
            valid_ips = [ip for ip in ips if ip != "0.0.0.0" and not ip.startswith("127.")]
            
            controller.disconnect()
            return True, decoded, valid_ips
        return False, "", []
    except Exception as e:
        return False, str(e), []


def main():
    """COM 포트 스캔 및 FE990 찾기"""
    print("=" * 60)
    print("FE990 Port Scanner")
    print("=" * 60)
    
    # 사용 가능한 포트 스캔
    available_ports = scan_available_ports()
    
    if not available_ports:
        print("\n[ERROR] No COM ports available")
        return
    
    # 각 포트에 연결 시도
    print("\n" + "=" * 60)
    print("Testing Each Port")
    print("=" * 60)
    
    found_devices = []
    
    for port in available_ports:
        print(f"\n[TEST] {port}...", end=" ")
        success, info, ips = try_connect_port(port)
        
        if success:
            print("✓ Connected")
            print(f"  Info: {info.strip()[:100]}")
            if ips:
                print(f"  Found IPs: {', '.join(ips)}")
            found_devices.append((port, info, ips))
        else:
            print("✗ Failed or in use")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if found_devices:
        print(f"\n✓ Found {len(found_devices)} accessible device(s):")
        for port, info, ips in found_devices:
            print(f"\n  {port}:")
            if ips:
                print(f"    IP: {ips[0]}")
                print(f"\n    [NEXT] To measure CPU, run:")
                print(f"      python simple_cpu.py")
                print(f"      Enter IP: {ips[0]}")
            else:
                print(f"    No IP found - device may not be networked")
    else:
        print("\n✗ No accessible devices found")
        print("\n[HELP] All ports may be in use. Please:")
        print("  1. Close Tera Term, PuTTY, or other serial programs")
        print("  2. Close other Python scripts using COM ports")
        print("  3. Try again")


if __name__ == "__main__":
    main()

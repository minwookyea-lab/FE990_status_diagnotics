#!/usr/bin/env python3
"""
FE990 CPU 사용률 자동 측정 (포트 자동 선택)
"""

import serial.tools.list_ports
from controller import ATController
import re
import sys
import time


def find_working_port():
    """사용 가능한 첫 번째 포트 찾기"""
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        try:
            controller = ATController(port=port.device)
            if controller.connect():
                # ATI로 테스트
                response = controller.send_cmd("ATI", wait_s=0.3)
                decoded = response.decode('ascii', errors='ignore')
                
                if "OK" in decoded or "332" in decoded:
                    print(f"[OK] Found working port: {port.device}")
                    return controller, port.device
                
                controller.disconnect()
        except:
            pass
    
    return None, None


def find_ip_via_at(controller):
    """AT 명령으로 IP 주소 찾기"""
    print("\n[INFO] Searching for IP address...")
    
    commands = [
        "AT+CGPADDR",
        "AT#IPADDR",
        "AT+CGCONTRDP",
        "ATI",
    ]
    
    ip_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
    
    for cmd in commands:
        try:
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            
            if "ERROR" not in decoded:
                matches = ip_pattern.findall(decoded)
                for ip in matches:
                    if ip != "0.0.0.0" and not ip.startswith("127."):
                        print(f"[OK] Found IP: {ip}")
                        return ip
        except:
            pass
    
    return None


def measure_cpu_via_ssh(ip):
    """SSH로 CPU 측정"""
    print(f"\n[INFO] Connecting to {ip} via SSH...")
    
    ssh_controller = ATController(
        ssh_host=ip,
        ssh_user="root",
        ssh_pass="telit"
    )
    
    try:
        if not ssh_controller.ssh_connect():
            print(f"[ERROR] SSH connection failed")
            return None
        
        print("[OK] SSH Connected")
        print("[INFO] Measuring CPU usage...")
        
        cpu_usage = ssh_controller.get_remote_cpu_usage()
        ssh_controller.ssh_disconnect()
        
        return cpu_usage
    except Exception as e:
        print(f"[ERROR] {e}")
        if ssh_controller:
            ssh_controller.ssh_disconnect()
        return None


def main():
    """FE990 CPU 사용률 자동 측정"""
    print("=" * 60)
    print("FE990 CPU Usage - Automatic Detection")
    print("=" * 60)
    
    # 1단계: 사용 가능한 포트 찾기
    print("\n[STEP 1] Finding available COM port...")
    controller, port = find_working_port()
    
    if not controller:
        print("\n[ERROR] No available COM port found")
        print("[HELP] Please close programs using COM ports")
        sys.exit(1)
    
    try:
        # 2단계: IP 주소 찾기
        print(f"\n[STEP 2] Finding IP address via {port}...")
        ip = find_ip_via_at(controller)
        
        controller.disconnect()
        print(f"[OK] Disconnected from {port}")
        
        if not ip:
            print("\n[WARNING] Could not find IP via AT commands")
            print("[INFO] Trying default IPs...")
            default_ips = ["192.168.1.1", "192.168.0.1", "10.0.0.1"]
        else:
            default_ips = [ip]
        
        # 3단계: SSH로 CPU 측정
        print(f"\n[STEP 3] Measuring CPU usage...")
        
        cpu_usage = None
        for test_ip in default_ips:
            cpu_usage = measure_cpu_via_ssh(test_ip)
            if cpu_usage is not None:
                print(f"\n{'='*60}")
                print(f"  FE990 CPU Usage: {cpu_usage}%")
                print(f"  IP Address: {test_ip}")
                print(f"{'='*60}")
                break
        
        if cpu_usage is None:
            print("\n[ERROR] Could not measure CPU usage")
            print("\n[HELP] Possible reasons:")
            print("  1. FE990 not connected to network")
            print("  2. SSH not enabled on FE990")
            print("  3. Incorrect credentials (default: root/telit)")
            print("  4. IP address changed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if controller and controller.ser and controller.ser.is_open:
            controller.disconnect()


if __name__ == "__main__":
    main()

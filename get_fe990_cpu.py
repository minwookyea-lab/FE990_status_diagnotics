#!/usr/bin/env python3
"""
FE990 CPU 사용률 조회 (COM37)
AT 명령으로 IP 확인 후 SSH로 CPU 측정
"""

from controller import ATController
import sys
import re


def get_ip_from_at_commands(controller):
    """AT 명령으로 IP 주소 찾기 시도"""
    print("[INFO] Trying to find IP address via AT commands...")
    
    # 시도할 AT 명령어들
    commands = [
        "AT+CGPADDR",
        "AT#IPADDR",  
        "AT+CGCONTRDP",
        "ATI",
        "AT#NETINFO",
        "AT#IFCONFIG",
    ]
    
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    
    for cmd in commands:
        try:
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            
            # IP 주소 패턴 찾기
            matches = ip_pattern.findall(decoded)
            for ip in matches:
                # 유효한 IP인지 확인 (0.0.0.0이나 127.x.x.x 제외)
                if ip != "0.0.0.0" and not ip.startswith("127."):
                    print(f"[OK] Found IP: {ip} (from {cmd})")
                    return ip
        except:
            continue
    
    return None


def main():
    """FE990 CPU 사용률 조회"""
    print("=" * 60)
    print("FE990 CPU Usage Query (COM37)")
    print("=" * 60)
    
    # COM37로 연결
    controller = ATController(port="COM37")
    
    try:
        # AT 연결
        print(f"\n[INFO] Connecting to COM37...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to COM37")
            sys.exit(1)
        
        print("[OK] Connected to COM37")
        
        # IP 주소 찾기
        ip_address = get_ip_from_at_commands(controller)
        
        if not ip_address:
            print("\n[WARNING] Could not find IP via AT commands")
            print("[INFO] Will try default IP addresses...")
            ip_candidates = ["192.168.1.1", "192.168.0.1", "10.0.0.1"]
        else:
            ip_candidates = [ip_address]
        
        # AT 연결 해제
        controller.disconnect()
        print("[OK] Disconnected from COM37\n")
        
        # SSH로 CPU 측정 시도
        print("=" * 60)
        print("Measuring CPU Usage via SSH")
        print("=" * 60)
        
        cpu_usage = None
        for ip in ip_candidates:
            print(f"\n[INFO] Trying SSH to {ip}...")
            
            ssh_controller = ATController(
                ssh_host=ip,
                ssh_user="root",
                ssh_pass="telit"
            )
            
            if ssh_controller.ssh_connect():
                print(f"[OK] SSH Connected to {ip}")
                print("[INFO] Measuring CPU usage...")
                
                cpu_usage = ssh_controller.get_remote_cpu_usage()
                ssh_controller.ssh_disconnect()
                
                if cpu_usage is not None:
                    print(f"\n{'='*60}")
                    print(f"  FE990 CPU Usage: {cpu_usage}%")
                    print(f"  IP Address: {ip}")
                    print(f"{'='*60}")
                    break
                else:
                    print("[WARNING] Failed to measure CPU")
            else:
                print(f"[FAIL] Could not connect to {ip}")
        
        if cpu_usage is None:
            print("\n[ERROR] Could not measure CPU usage")
            print("[INFO] Please verify:")
            print("  1. FE990 is connected to network")
            print("  2. SSH is enabled on FE990")
            print("  3. Correct IP address and credentials")
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
        if controller.ser and controller.ser.is_open:
            controller.disconnect()


if __name__ == "__main__":
    main()

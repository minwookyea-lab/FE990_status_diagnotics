#!/usr/bin/env python3
"""
COM 포트에서 FE990 정보 수집 (IP 주소 찾기)
"""

from controller import ATController
import sys
import re


def find_ip_address(controller):
    """AT 명령으로 IP 주소 찾기"""
    print("\n" + "=" * 60)
    print("Searching for IP Address")
    print("=" * 60)
    
    # 시도할 AT 명령어들 (IP 주소가 포함될 가능성이 있는 명령)
    commands = [
        ("ATI", "Device Information"),
        ("AT+CGPADDR", "PDP Address"),
        ("AT+CGCONTRDP", "Context Parameters"),
        ("AT#IPADDR", "IP Address"),
        ("AT#NETINFO", "Network Info"),
        ("AT#IFCONFIG", "Interface Config"),
        ("AT+CSQ", "Signal Quality"),
        ("AT+COPS?", "Operator Selection"),
    ]
    
    ip_pattern = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b')
    found_ips = []
    
    for cmd, description in commands:
        try:
            print(f"\n[TEST] {cmd} ({description})")
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            
            # ERROR가 아니면 출력
            if "ERROR" not in decoded:
                print(f"Response: {decoded.strip()}")
                
                # IP 주소 패턴 찾기
                matches = ip_pattern.findall(decoded)
                for ip in matches:
                    # 유효한 IP인지 확인 (0.0.0.0이나 127.x.x.x 제외)
                    if ip not in found_ips and ip != "0.0.0.0" and not ip.startswith("127."):
                        found_ips.append(ip)
                        print(f"  → Found IP: {ip}")
            else:
                print("  (Not supported)")
        except Exception as e:
            print(f"  Error: {e}")
    
    return found_ips


def main():
    """FE990 정보 수집"""
    print("=" * 60)
    print("FE990 Information Collector")
    print("=" * 60)
    
    # COM 포트 입력
    port = input("\nEnter COM port [COM37]: ").strip() or "COM37"
    
    controller = ATController(port=port)
    
    try:
        # 연결
        print(f"\n[INFO] Connecting to {port}...")
        if not controller.connect():
            print(f"\n[ERROR] Failed to connect to {port}")
            print("\n[HELP] Port may be in use. Please:")
            print("  1. Close any program using the COM port")
            print("  2. Check Device Manager to verify the port number")
            print("  3. Try unplugging and replugging the device")
            sys.exit(1)
        
        print(f"[OK] Connected to {port}")
        
        # IP 주소 찾기
        found_ips = find_ip_address(controller)
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        if found_ips:
            print(f"\n✓ Found {len(found_ips)} IP address(es):")
            for i, ip in enumerate(found_ips, 1):
                print(f"  {i}. {ip}")
            
            print("\n[NEXT] To measure CPU usage, run:")
            print(f"  python simple_cpu.py")
            print(f"  Then enter IP: {found_ips[0]}")
        else:
            print("\n✗ No IP address found via AT commands")
            print("\n[HELP] Try these options:")
            print("  1. Check if FE990 has network connection")
            print("  2. Use router/network scanner to find device IP")
            print("  3. Check FE990 documentation for default IP")
            print("  4. Common default IPs: 192.168.1.1, 192.168.0.1")
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()

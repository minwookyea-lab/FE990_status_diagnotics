#!/usr/bin/env python3
"""
FE990 RF 상태 조회
신호 강도, 네트워크 등록, 셀 정보 등 RF 관련 모든 정보 수집
"""

from controller import ATController
import sys
from datetime import datetime


def print_header(title):
    """헤더 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_info(label, value):
    """정보 출력"""
    print(f"  {label:30s}: {value}")


def send_and_parse(controller, cmd, label, wait_s=0.5):
    """AT 명령 전송 및 결과 출력"""
    try:
        response = controller.send_cmd(cmd, wait_s=wait_s)
        decoded = response.decode('ascii', errors='ignore').strip()
        
        if "ERROR" in decoded:
            print_info(label, "Not supported")
            return None
        
        # AT 명령 에코 제거하고 실제 응답만 추출
        lines = [line.strip() for line in decoded.split('\n') 
                 if line.strip() and not line.strip().startswith('AT') and line.strip() != 'OK']
        
        if lines:
            result = '\n' + '\n  '.join([''] + lines)
            print_info(label, result)
            return lines
        else:
            print_info(label, "No data")
            return None
            
    except Exception as e:
        print_info(label, f"Error: {e}")
        return None


def main():
    """FE990 RF 상태 조회"""
    print("\n" + "="*60)
    print("  FE990 RF Status Report")
    print("="*60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # COM9 포트로 연결
    controller = ATController(port="COM9")
    
    try:
        # 연결
        if not controller.connect():
            print("[ERROR] Failed to connect to COM9")
            sys.exit(1)
        
        print_header("Signal Strength")
        
        # 1. 신호 강도 (AT+CSQ)
        send_and_parse(controller, "AT+CSQ", "Signal Quality (CSQ)")
        
        # 2. 확장 신호 강도 (AT+CESQ)
        send_and_parse(controller, "AT+CESQ", "Extended Signal Quality")
        
        print_header("Network Registration")
        
        # 3. CS 네트워크 등록 (AT+CREG?)
        send_and_parse(controller, "AT+CREG?", "CS Registration (CREG)")
        
        # 4. GPRS 네트워크 등록 (AT+CGREG?)
        send_and_parse(controller, "AT+CGREG?", "GPRS Registration (CGREG)")
        
        # 5. LTE 네트워크 등록 (AT+CEREG?)
        send_and_parse(controller, "AT+CEREG?", "LTE Registration (CEREG)")
        
        print_header("Network Operator")
        
        # 6. 현재 네트워크 오퍼레이터 (AT+COPS?)
        send_and_parse(controller, "AT+COPS?", "Current Operator (COPS)")
        
        print_header("Radio Technology")
        
        # 7. 현재 무선 기술 (AT+WS46?)
        send_and_parse(controller, "AT+WS46?", "Wireless Standard (WS46)")
        
        # 8. 네트워크 시스템 모드 (AT#WS46?)
        send_and_parse(controller, "AT#WS46?", "System Mode (WS46)")
        
        print_header("Cell Information")
        
        # 9. 서빙 셀 정보 (AT#SERVINFO)
        send_and_parse(controller, "AT#SERVINFO", "Serving Cell Info", wait_s=1.0)
        
        # 10. RF 상태 (AT#RFSTS)
        send_and_parse(controller, "AT#RFSTS", "RF Status", wait_s=0.5)
        
        # 11. 모니터 정보 (AT#MONI)
        send_and_parse(controller, "AT#MONI", "Monitor Info", wait_s=1.0)
        
        print_header("Additional RF Information")
        
        # 12. 밴드 정보 (AT#BND?)
        send_and_parse(controller, "AT#BND?", "Band Configuration")
        
        # 13. 무선 파워 설정 (AT+CPWROFF?)
        send_and_parse(controller, "AT+CPWROFF?", "Power Off Status")
        
        # 14. 기능 레벨 (AT+CFUN?)
        send_and_parse(controller, "AT+CFUN?", "Functionality Level")
        
        # 15. 무선 모드 (AT#SELRAT?)
        send_and_parse(controller, "AT#SELRAT?", "RAT Selection")
        
        print("\n" + "="*60)
        print("  End of RF Status Report")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    
    finally:
        controller.disconnect()


if __name__ == "__main__":
    main()

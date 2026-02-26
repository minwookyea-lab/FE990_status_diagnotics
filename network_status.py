#!/usr/bin/env python3
"""
FE990 네트워크 상태 조회
"""

from controller import ATController
from typing import Dict, Optional, Any
import re


def get_network_registration_status(controller) -> Optional[Dict[str, Any]]:
    """
    네트워크 등록 상태 상세 조회 (AT+CREG?, AT+CGREG?, AT+CEREG?)
    
    Returns:
        dict: 네트워크 등록 정보
    """
    result = {}
    
    # CS 도메인 등록 상태 (AT+CREG?)
    try:
        response = controller.send_cmd("AT+CREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CREG:\s*(\d+),(\d+)', decoded)
        if match:
            stat = int(match.group(2))
            status_map = {
                0: "Not registered, not searching",
                1: "Registered, home network",
                2: "Not registered, searching",
                3: "Registration denied",
                4: "Unknown",
                5: "Registered, roaming"
            }
            result['cs_registration'] = {
                'mode': int(match.group(1)),
                'stat': stat,
                'status': status_map.get(stat, "Unknown")
            }
    except:
        pass
    
    # PS 도메인 등록 상태 (AT+CGREG?)
    try:
        response = controller.send_cmd("AT+CGREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CGREG:\s*(\d+),(\d+)', decoded)
        if match:
            stat = int(match.group(2))
            result['ps_registration'] = {
                'mode': int(match.group(1)),
                'stat': stat,
                'status': status_map.get(stat, "Unknown")
            }
    except:
        pass
    
    # EPS 등록 상태 (AT+CEREG?)
    try:
        response = controller.send_cmd("AT+CEREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CEREG:\s*(\d+),(\d+)', decoded)
        if match:
            stat = int(match.group(2))
            result['eps_registration'] = {
                'mode': int(match.group(1)),
                'stat': stat,
                'status': status_map.get(stat, "Unknown")
            }
    except:
        pass
    
    return result if result else None


def get_operator_info(controller) -> Optional[Dict[str, Any]]:
    """
    오퍼레이터 상세 정보 조회 (AT+COPS?)
    
    Returns:
        dict: 오퍼레이터 정보
    """
    try:
        response = controller.send_cmd("AT+COPS?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        # +COPS: mode,format,"operator",act
        match = re.search(r'\+COPS:\s*(\d+)(?:,(\d+)(?:,"([^"]*)"(?:,(\d+))?)?)?', decoded)
        if match:
            mode = int(match.group(1))
            mode_map = {
                0: "Automatic",
                1: "Manual",
                2: "Deregister",
                3: "Set format only",
                4: "Manual/Automatic"
            }
            
            result = {
                'mode': mode,
                'mode_text': mode_map.get(mode, "Unknown")
            }
            
            if match.group(2):
                result['format'] = int(match.group(2))
            if match.group(3):
                result['operator'] = match.group(3)
            if match.group(4):
                act = int(match.group(4))
                act_map = {
                    0: "GSM",
                    1: "GSM Compact",
                    2: "UTRAN",
                    3: "GSM w/EGPRS",
                    4: "UTRAN w/HSDPA",
                    5: "UTRAN w/HSUPA",
                    6: "UTRAN w/HSDPA and HSUPA",
                    7: "E-UTRAN",
                    8: "EC-GSM-IoT",
                    9: "E-UTRAN (NB-S1 mode)"
                }
                result['access_technology'] = act
                result['access_technology_text'] = act_map.get(act, "Unknown")
            
            return result
    except:
        pass
    return None


def get_signal_strength(controller) -> Optional[Dict[str, Any]]:
    """
    신호 강도 상세 조회 (AT+CSQ)
    
    Returns:
        dict: 신호 강도 정보
    """
    try:
        response = controller.send_cmd("AT+CSQ", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        match = re.search(r'\+CSQ:\s*(\d+),(\d+)', decoded)
        if match:
            rssi = int(match.group(1))
            ber = int(match.group(2))
            
            # RSSI를 dBm으로 변환
            if rssi == 99:
                dbm = None
                quality = "Unknown"
            elif rssi == 0:
                dbm = -113
                quality = "Very weak"
            elif rssi == 31:
                dbm = -51
                quality = "Excellent"
            else:
                dbm = -113 + (rssi * 2)
                if dbm >= -70:
                    quality = "Excellent"
                elif dbm >= -85:
                    quality = "Good"
                elif dbm >= -100:
                    quality = "Fair"
                else:
                    quality = "Poor"
            
            # BER 해석
            ber_map = {
                0: "< 0.2%",
                1: "0.2% - 0.4%",
                2: "0.4% - 0.8%",
                3: "0.8% - 1.6%",
                4: "1.6% - 3.2%",
                5: "3.2% - 6.4%",
                6: "6.4% - 12.8%",
                7: "> 12.8%",
                99: "Unknown"
            }
            
            return {
                'rssi': rssi,
                'rssi_dbm': dbm,
                'quality': quality,
                'ber': ber,
                'ber_text': ber_map.get(ber, "Unknown")
            }
    except:
        pass
    return None


def get_pdp_context(controller) -> Optional[list]:
    """
    PDP 컨텍스트 정보 조회 (AT+CGDCONT?)
    
    Returns:
        list: PDP 컨텍스트 리스트
    """
    try:
        response = controller.send_cmd("AT+CGDCONT?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        contexts = []
        for line in decoded.split('\n'):
            # +CGDCONT: cid,pdp_type,apn,pdp_addr
            match = re.search(r'\+CGDCONT:\s*(\d+),"([^"]*)"(?:,"([^"]*)")?(?:,"([^"]*)")?', line)
            if match:
                contexts.append({
                    'cid': int(match.group(1)),
                    'pdp_type': match.group(2),
                    'apn': match.group(3) if match.group(3) else "",
                    'pdp_addr': match.group(4) if match.group(4) else ""
                })
        
        return contexts if contexts else None
    except:
        pass
    return None


def get_pdp_activation(controller) -> Optional[list]:
    """
    PDP 활성화 상태 조회 (AT+CGACT?)
    
    Returns:
        list: PDP 활성화 상태
    """
    try:
        response = controller.send_cmd("AT+CGACT?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        activations = []
        for line in decoded.split('\n'):
            match = re.search(r'\+CGACT:\s*(\d+),(\d+)', line)
            if match:
                activations.append({
                    'cid': int(match.group(1)),
                    'state': int(match.group(2)),
                    'state_text': "Activated" if int(match.group(2)) == 1 else "Deactivated"
                })
        
        return activations if activations else None
    except:
        pass
    return None


def get_network_status(controller) -> Dict[str, Any]:
    """
    FE990 네트워크 전체 상태 조회
    
    Args:
        controller: ATController 인스턴스 (연결된 상태)
        
    Returns:
        dict: 네트워크 상태 정보
    """
    print("[INFO] Collecting network status information...")
    
    status = {}
    
    # 네트워크 등록 상태
    print("  - Checking network registration...", end=" ")
    registration = get_network_registration_status(controller)
    if registration:
        status['registration'] = registration
        cs_stat = registration.get('cs_registration', {}).get('stat', 0)
        print(f"✓ CS:{cs_stat}")
    else:
        print("✗")
    
    # 오퍼레이터
    print("  - Checking operator...", end=" ")
    operator = get_operator_info(controller)
    if operator:
        status['operator'] = operator
        op_name = operator.get('operator', 'N/A')
        print(f"✓ {op_name}")
    else:
        print("✗")
    
    # 신호 강도
    print("  - Checking signal strength...", end=" ")
    signal = get_signal_strength(controller)
    if signal:
        status['signal'] = signal
        if signal['rssi_dbm']:
            print(f"✓ {signal['rssi_dbm']}dBm ({signal['quality']})")
        else:
            print("✓ Unknown")
    else:
        print("✗")
    
    # PDP 컨텍스트
    print("  - Checking PDP context...", end=" ")
    pdp_context = get_pdp_context(controller)
    if pdp_context:
        status['pdp_context'] = pdp_context
        print(f"✓ {len(pdp_context)} context(s)")
    else:
        print("✗")
    
    # PDP 활성화
    print("  - Checking PDP activation...", end=" ")
    pdp_activation = get_pdp_activation(controller)
    if pdp_activation:
        status['pdp_activation'] = pdp_activation
        active_count = sum(1 for p in pdp_activation if p['state'] == 1)
        print(f"✓ {active_count}/{len(pdp_activation)} active")
    else:
        print("✗")
    
    return status


def print_network_status(status: Dict[str, Any]):
    """네트워크 상태를 보기 좋게 출력"""
    print("\n" + "=" * 60)
    print("FE990 Network Status")
    print("=" * 60)
    
    # 네트워크 등록
    if 'registration' in status:
        print(f"\n[Network Registration]")
        if 'cs_registration' in status['registration']:
            cs = status['registration']['cs_registration']
            print(f"  CS Domain: {cs['status']} (stat={cs['stat']})")
        if 'ps_registration' in status['registration']:
            ps = status['registration']['ps_registration']
            print(f"  PS Domain: {ps['status']} (stat={ps['stat']})")
        if 'eps_registration' in status['registration']:
            eps = status['registration']['eps_registration']
            print(f"  EPS:       {eps['status']} (stat={eps['stat']})")
    
    # 오퍼레이터
    if 'operator' in status:
        print(f"\n[Operator]")
        print(f"  Mode:     {status['operator'].get('mode_text', 'N/A')}")
        if 'operator' in status['operator']:
            print(f"  Operator: {status['operator']['operator']}")
        if 'access_technology_text' in status['operator']:
            print(f"  Technology: {status['operator']['access_technology_text']}")
    
    # 신호 강도
    if 'signal' in status:
        print(f"\n[Signal Strength]")
        if status['signal']['rssi_dbm']:
            print(f"  RSSI:    {status['signal']['rssi_dbm']} dBm")
            print(f"  Quality: {status['signal']['quality']}")
        else:
            print(f"  RSSI:    Unknown")
        print(f"  BER:     {status['signal']['ber_text']}")
    
    # PDP 컨텍스트
    if 'pdp_context' in status:
        print(f"\n[PDP Context]")
        for ctx in status['pdp_context']:
            print(f"  CID {ctx['cid']}: {ctx['pdp_type']}")
            if ctx['apn']:
                print(f"    APN: {ctx['apn']}")
            if ctx['pdp_addr']:
                print(f"    Address: {ctx['pdp_addr']}")
    
    # PDP 활성화
    if 'pdp_activation' in status:
        print(f"\n[PDP Activation]")
        for act in status['pdp_activation']:
            print(f"  CID {act['cid']}: {act['state_text']}")
    
    print("\n" + "=" * 60)


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("FE990 Network Status Checker")
    print("=" * 60)
    
    # COM9로 연결
    controller = ATController(port="COM9")
    
    try:
        print(f"\n[INFO] Connecting to COM9...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to COM9")
            exit(1)
        
        print("[OK] Connected\n")
        
        # 네트워크 상태 조회
        status = get_network_status(controller)
        
        # 결과 출력
        print_network_status(status)
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")

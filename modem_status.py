#!/usr/bin/env python3
"""
FE990 모뎀 상태 조회 함수
AT 명령으로 조회 가능한 모든 상태 정보 수집
"""

from controller import ATController
from typing import Dict, Optional, Any
import re


def get_signal_quality(controller) -> Optional[Dict[str, int]]:
    """
    신호 품질 조회 (AT+CSQ)
    
    Returns:
        dict: {'rssi': int, 'ber': int} 또는 None
        rssi: 0-31 (0=<-113dBm, 31=>-51dBm, 99=unknown)
        ber: Bit Error Rate (0-7, 99=unknown)
    """
    try:
        response = controller.send_cmd("AT+CSQ", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        # +CSQ: 23,99 형식
        match = re.search(r'\+CSQ:\s*(\d+),(\d+)', decoded)
        if match:
            rssi = int(match.group(1))
            ber = int(match.group(2))
            
            # RSSI를 dBm으로 변환
            if rssi == 99:
                dbm = None
            elif rssi == 0:
                dbm = -113
            elif rssi == 31:
                dbm = -51
            else:
                dbm = -113 + (rssi * 2)
            
            return {
                'rssi': rssi,
                'rssi_dbm': dbm,
                'ber': ber
            }
    except:
        pass
    return None


def get_temperature(controller) -> Optional[float]:
    """
    모뎀 온도 조회
    
    Returns:
        float: 온도(°C) 또는 None
    """
    commands = ["AT#TEMPMON?", "AT#TEMP?", "AT+CMTE?"]
    
    for cmd in commands:
        try:
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            
            if "ERROR" not in decoded:
                # 숫자 추출
                match = re.search(r'[-+]?\d+\.?\d*', decoded)
                if match:
                    return float(match.group())
        except:
            pass
    return None


def get_voltage(controller) -> Optional[Dict[str, Any]]:
    """
    배터리/전압 정보 조회 (AT+CBC)
    
    Returns:
        dict: {'status': int, 'charge': int, 'voltage': int} 또는 None
    """
    try:
        response = controller.send_cmd("AT+CBC", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        # +CBC: 0,100,4200 형식 (status, charge%, voltage mV)
        match = re.search(r'\+CBC:\s*(\d+),(\d+),(\d+)', decoded)
        if match:
            return {
                'status': int(match.group(1)),  # 0=not charging, 1=charging, 2=charging done
                'charge_percent': int(match.group(2)),
                'voltage_mv': int(match.group(3))
            }
    except:
        pass
    return None


def get_network_registration(controller) -> Optional[Dict[str, Any]]:
    """
    네트워크 등록 상태 조회 (AT+CREG?)
    
    Returns:
        dict: {'mode': int, 'stat': int} 또는 None
        stat: 0=not registered, 1=registered home, 2=searching, 3=denied, 5=registered roaming
    """
    try:
        response = controller.send_cmd("AT+CREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        # +CREG: 0,1 형식
        match = re.search(r'\+CREG:\s*(\d+),(\d+)', decoded)
        if match:
            stat = int(match.group(2))
            status_map = {
                0: "Not registered",
                1: "Registered (Home)",
                2: "Searching",
                3: "Registration denied",
                5: "Registered (Roaming)"
            }
            return {
                'mode': int(match.group(1)),
                'stat': stat,
                'status': status_map.get(stat, "Unknown")
            }
    except:
        pass
    return None


def get_operator(controller) -> Optional[str]:
    """
    현재 오퍼레이터 조회 (AT+COPS?)
    
    Returns:
        str: 오퍼레이터 이름 또는 None
    """
    try:
        response = controller.send_cmd("AT+COPS?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        # +COPS: 0,0,"SKT",7 형식
        match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]+)"', decoded)
        if match:
            return match.group(1)
    except:
        pass
    return None


def get_device_info(controller) -> Optional[Dict[str, str]]:
    """
    장치 정보 조회 (ATI, AT+CGMI, AT+CGMM, AT+CGMR 등)
    
    Returns:
        dict: 장치 상세 정보 또는 None
    """
    info = {}
    
    # 제조사 (AT+CGMI)
    try:
        response = controller.send_cmd("AT+CGMI", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            info['manufacturer'] = lines[0]
    except:
        pass
    
    # 모델 (AT+CGMM)
    try:
        response = controller.send_cmd("AT+CGMM", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            info['model'] = lines[0]
    except:
        pass
    
    # 펌웨어 버전 (AT+CGMR)
    try:
        response = controller.send_cmd("AT+CGMR", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            info['firmware'] = lines[0]
    except:
        pass
    
    # IMEI (ATI3)
    try:
        response = controller.send_cmd("ATI3", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'ATI' not in l]
        if lines:
            info['imei_info'] = lines[0]
    except:
        pass
    
    # 모델 정보 (ATI4)
    try:
        response = controller.send_cmd("ATI4", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'ATI' not in l]
        if lines:
            info['model_detail'] = lines[0]
    except:
        pass
    
    return info if info else None


def get_adc_values(controller) -> Optional[Dict[str, Any]]:
    """
    ADC 값 조회 (AT#ADC?)
    
    Returns:
        dict: ADC 값들 또는 None
    """
    try:
        response = controller.send_cmd("AT#ADC?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        adc_values = []
        for line in decoded.split('\n'):
            match = re.search(r'#ADC:\s*(\d+)', line)
            if match:
                adc_values.append(int(match.group(1)))
        
        if adc_values:
            return {'values': adc_values}
    except:
        pass
    return None


def get_gpio_status(controller) -> Optional[Dict[str, Any]]:
    """
    GPIO 상태 조회 (AT#GPIO?)
    
    Returns:
        dict: GPIO 상태들 또는 None
    """
    try:
        response = controller.send_cmd("AT#GPIO?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        
        gpio_pins = []
        for line in decoded.split('\n'):
            match = re.search(r'#GPIO:\s*(\d+),(\d+),(\d+)', line)
            if match:
                gpio_pins.append({
                    'pin': int(match.group(1)),
                    'mode': int(match.group(2)),
                    'value': int(match.group(3))
                })
        
        if gpio_pins:
            return {'pins': gpio_pins}
    except:
        pass
    return None


def get_system_info(controller) -> Optional[Dict[str, Any]]:
    """
    시스템 정보 조회 (AT+CFUN?, AT#FWSWITCH?, AT#USBCFG?)
    
    Returns:
        dict: 시스템 정보 또는 None
    """
    info = {}
    
    # 기능 레벨
    try:
        response = controller.send_cmd("AT+CFUN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CFUN:\s*(\d+)', decoded)
        if match:
            info['function_level'] = int(match.group(1))
    except:
        pass
    
    # 펌웨어 스위치
    try:
        response = controller.send_cmd("AT#FWSWITCH?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'#FWSWITCH:\s*(\d+)', decoded)
        if match:
            info['firmware_switch'] = int(match.group(1))
    except:
        pass
    
    # USB 설정
    try:
        response = controller.send_cmd("AT#USBCFG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'#USBCFG:\s*(\d+)', decoded)
        if match:
            info['usb_config'] = int(match.group(1))
    except:
        pass
    
    return info if info else None


def get_clock(controller) -> Optional[str]:
    """
    시스템 시계 조회 (AT+CCLK?)
    
    Returns:
        str: 시계 정보 또는 None
    """
    try:
        response = controller.send_cmd("AT+CCLK?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CCLK:\s*"([^"]+)"', decoded)
        if match:
            return match.group(1)
    except:
        pass
    return None


def get_indicators(controller) -> Optional[Dict[str, Any]]:
    """
    인디케이터 상태 조회 (AT+CIND?)
    
    Returns:
        dict: 인디케이터 값들 또는 None
    """
    try:
        response = controller.send_cmd("AT+CIND?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CIND:\s*([\d,]+)', decoded)
        if match:
            values = [int(v) for v in match.group(1).split(',')]
            return {'values': values}
    except:
        pass
    return None


def get_modem_status(controller) -> Dict[str, Any]:
    """
    FE990 모뎀의 전체 상태 정보 조회
    
    Args:
        controller: ATController 인스턴스 (연결된 상태)
        
    Returns:
        dict: 모뎀 상태 정보
        {
            'signal': {'rssi': int, 'rssi_dbm': int, 'ber': int},
            'temperature': float,
            'voltage': {'status': int, 'charge_percent': int, 'voltage_mv': int},
            'network': {'mode': int, 'stat': int, 'status': str},
            'operator': str,
            'device': {'model': str, 'imei': str}
        }
    """
    print("[INFO] Collecting modem status information...")
    
    status = {}
    
    # 신호 품질
    print("  - Checking signal quality...", end=" ")
    signal = get_signal_quality(controller)
    if signal:
        status['signal'] = signal
        print(f"✓ RSSI: {signal['rssi_dbm']}dBm" if signal['rssi_dbm'] else "✓")
    else:
        print("✗")
    
    # 온도
    print("  - Checking temperature...", end=" ")
    temp = get_temperature(controller)
    if temp is not None:
        status['temperature'] = temp
        print(f"✓ {temp}°C")
    else:
        print("✗")
    
    # 전압
    print("  - Checking voltage...", end=" ")
    voltage = get_voltage(controller)
    if voltage:
        status['voltage'] = voltage
        print(f"✓ {voltage['voltage_mv']}mV")
    else:
        print("✗")
    
    # 네트워크 등록
    print("  - Checking network registration...", end=" ")
    network = get_network_registration(controller)
    if network:
        status['network'] = network
        print(f"✓ {network['status']}")
    else:
        print("✗")
    
    # 오퍼레이터
    print("  - Checking operator...", end=" ")
    operator = get_operator(controller)
    if operator:
        status['operator'] = operator
        print(f"✓ {operator}")
    else:
        print("✗")
    
    # 장치 정보
    print("  - Checking device info...", end=" ")
    device = get_device_info(controller)
    if device:
        status['device'] = device
        print(f"✓ {device.get('model', 'N/A')}")
    else:
        print("✗")
    
    # ADC 값
    print("  - Checking ADC values...", end=" ")
    adc = get_adc_values(controller)
    if adc:
        status['adc'] = adc
        print(f"✓ {len(adc['values'])} values")
    else:
        print("✗")
    
    # GPIO 상태
    print("  - Checking GPIO status...", end=" ")
    gpio = get_gpio_status(controller)
    if gpio:
        status['gpio'] = gpio
        print(f"✓ {len(gpio['pins'])} pins")
    else:
        print("✗")
    
    # 시스템 정보
    print("  - Checking system info...", end=" ")
    system = get_system_info(controller)
    if system:
        status['system'] = system
        print("✓")
    else:
        print("✗")
    
    # 시계
    print("  - Checking clock...", end=" ")
    clock = get_clock(controller)
    if clock:
        status['clock'] = clock
        print(f"✓ {clock}")
    else:
        print("✗")
    
    # 인디케이터
    print("  - Checking indicators...", end=" ")
    indicators = get_indicators(controller)
    if indicators:
        status['indicators'] = indicators
        print("✓")
    else:
        print("✗")
    
    return status


def print_modem_status(status: Dict[str, Any]):
    """모뎀 상태를 보기 좋게 출력"""
    print("\n" + "=" * 60)
    print("FE990 Modem Status")
    print("=" * 60)
    
    # 장치 정보
    if 'device' in status:
        print(f"\n[Device Information]")
        print(f"  Manufacturer: {status['device'].get('manufacturer', 'N/A')}")
        print(f"  Model:        {status['device'].get('model', 'N/A')}")
        print(f"  Model Detail: {status['device'].get('model_detail', 'N/A')}")
        print(f"  Firmware:     {status['device'].get('firmware', 'N/A')}")
        print(f"  IMEI Info:    {status['device'].get('imei_info', 'N/A')}")
    
    # 신호 품질
    if 'signal' in status:
        print(f"\n[Signal Quality]")
        rssi_dbm = status['signal'].get('rssi_dbm')
        if rssi_dbm:
            print(f"  RSSI:  {rssi_dbm} dBm")
        print(f"  RSSI Value: {status['signal']['rssi']}/31")
        print(f"  BER:   {status['signal']['ber']}")
    
    # 네트워크
    if 'network' in status:
        print(f"\n[Network]")
        print(f"  Status: {status['network']['status']}")
        if 'operator' in status:
            print(f"  Operator: {status['operator']}")
    
    # 전압
    if 'voltage' in status:
        print(f"\n[Power]")
        print(f"  Voltage: {status['voltage']['voltage_mv']} mV")
        print(f"  Charge:  {status['voltage']['charge_percent']}%")
    
    # 온도
    if 'temperature' in status:
        print(f"\n[Temperature]")
        print(f"  Temperature: {status['temperature']:.1f}°C")
    
    # 시스템 정보
    if 'system' in status:
        print(f"\n[System]")
        if 'function_level' in status['system']:
            print(f"  Function Level:  {status['system']['function_level']}")
        if 'firmware_switch' in status['system']:
            print(f"  Firmware Switch: {status['system']['firmware_switch']}")
        if 'usb_config' in status['system']:
            print(f"  USB Config:      {status['system']['usb_config']}")
    
    # 시계
    if 'clock' in status:
        print(f"\n[Clock]")
        print(f"  System Time: {status['clock']}")
    
    # ADC
    if 'adc' in status:
        print(f"\n[ADC Values]")
        for i, val in enumerate(status['adc']['values']):
            print(f"  ADC {i}: {val}")
    
    # GPIO
    if 'gpio' in status:
        print(f"\n[GPIO Status]")
        for pin in status['gpio']['pins']:
            print(f"  GPIO {pin['pin']:2d}: Mode={pin['mode']}, Value={pin['value']}")
    
    # 인디케이터
    if 'indicators' in status:
        print(f"\n[Indicators]")
        print(f"  Values: {status['indicators']['values']}")
    
    print("\n" + "=" * 60)


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("FE990 Modem Status Checker")
    print("=" * 60)
    
    # COM9로 연결 (사용 가능한 포트)
    controller = ATController(port="COM9")
    
    try:
        print(f"\n[INFO] Connecting to COM9...")
        if not controller.connect():
            print(f"[ERROR] Failed to connect to COM9")
            exit(1)
        
        print("[OK] Connected\n")
        
        # 모뎀 상태 조회
        status = get_modem_status(controller)
        
        # 결과 출력
        print_modem_status(status)
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")

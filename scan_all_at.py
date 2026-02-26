#!/usr/bin/env python3
"""
FE990 모든 가능한 AT 명령 테스트
"""

from controller import ATController


def test_all_at_commands():
    """모든 AT 명령 시도"""
    
    # 테스트할 AT 명령들
    commands = [
        # 기본 정보
        ("ATI", "제조사/모델 정보"),
        ("ATI0", "제조사 정보"),
        ("ATI1", "모델 정보"),
        ("ATI2", "버전 정보"),
        ("ATI3", "IMEI"),
        ("ATI4", "IMEI SV"),
        ("ATI9", "확장 정보"),
        ("AT+CGMI", "제조사"),
        ("AT+CGMM", "모델"),
        ("AT+CGMR", "리비전"),
        ("AT+CGSN", "IMEI"),
        ("AT+GSN", "시리얼 번호"),
        
        # 네트워크
        ("AT+CSQ", "신호 품질"),
        ("AT+CREG?", "네트워크 등록"),
        ("AT+COPS?", "오퍼레이터"),
        ("AT+CIMI", "IMSI"),
        ("AT+CCID", "ICCID (SIM)"),
        
        # 전원/배터리
        ("AT+CBC", "배터리"),
        ("AT#ADC?", "ADC 읽기"),
        ("AT+CIND?", "인디케이터"),
        
        # 온도
        ("AT#TEMPSENS=2", "온도 센서 전체"),
        ("AT#TEMPMON?", "온도 모니터"),
        ("AT+CMTE?", "온도"),
        
        # 시스템 정보
        ("AT#SNUM", "시리얼 번호"),
        ("AT#HWVERSION", "하드웨어 버전"),
        ("AT#SWVERSION", "소프트웨어 버전"),
        ("AT#FWSWITCH?", "펌웨어 스위치"),
        ("AT#CFUN?", "기능 모드"),
        ("AT+CFUN?", "기능 레벨"),
        
        # 메모리/저장소
        ("AT#LSCRIPT", "스크립트 목록"),
        ("AT#CPUMODE?", "CPU 모드"),
        
        # SIM 카드
        ("AT+CPIN?", "PIN 상태"),
        ("AT+ICCID", "SIM ICCID"),
        
        # 네트워크 설정
        ("AT+CGDCONT?", "PDP 컨텍스트"),
        ("AT+CGACT?", "PDP 활성화"),
        ("AT+CGPADDR", "PDP 주소"),
        
        # USB/시리얼
        ("AT#USBCFG?", "USB 설정"),
        ("AT#PORTCFG?", "포트 설정"),
        
        # GPIO
        ("AT#GPIO?", "GPIO 상태"),
        
        # RF/신호 상태
        ("AT+CESQ", "확장 신호 품질"),
        ("AT+CGREG?", "GPRS 등록"),
        ("AT+CEREG?", "LTE 등록"),
        ("AT+WS46?", "무선 표준"),
        ("AT#WS46?", "시스템 모드"),
        ("AT#SERVINFO", "서빙 셀 정보"),
        ("AT#RFSTS", "RF 상태"),
        ("AT#MONI", "모니터 정보"),
        ("AT#BND?", "밴드 설정"),
        ("AT#SELRAT?", "RAT 선택"),
        
        # 기타
        ("AT#CCLK?", "시계"),
        ("AT+CCLK?", "시계2"),
        ("AT#E2SLRI", "마지막 재시작 정보"),
    ]
    
    print("=" * 70)
    print("FE990 전체 AT 명령 테스트")
    print("=" * 70)
    
    controller = ATController(port="COM10")
    
    try:
        print("\n[연결 중...]")
        if not controller.connect():
            print("[ERROR] 연결 실패")
            return
        
        print("[OK] 연결 성공\n")
        
        success_count = 0
        results = []
        
        for cmd, desc in commands:
            try:
                response = controller.send_cmd(cmd, wait_s=0.5)
                decoded = response.decode('ascii', errors='ignore').strip()
                
                # ERROR가 아닌 응답만 저장
                if "ERROR" not in decoded and decoded and len(decoded) > len(cmd) + 10:
                    success_count += 1
                    results.append((cmd, desc, decoded))
                    print(f"[OK] {cmd:20s} - {desc}")
                else:
                    print(f"[X]  {cmd:20s} - {desc}")
            except Exception as e:
                print(f"[X]  {cmd:20s} - {desc} (오류: {e})")
        
        # 결과 상세 출력
        print("\n" + "=" * 70)
        print(f"성공: {success_count}/{len(commands)}")
        print("=" * 70)
        
        if results:
            print("\n상세 응답:\n")
            for cmd, desc, response in results:
                print(f"[{cmd}] {desc}")
                print("-" * 70)
                # 응답을 정리해서 출력
                lines = [l.strip() for l in response.split('\n') if l.strip() and cmd not in l and 'OK' not in l]
                for line in lines:
                    print(f"  {line}")
                print()
        
    except Exception as e:
        print(f"\n[ERROR] 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[연결 해제]")


if __name__ == "__main__":
    test_all_at_commands()

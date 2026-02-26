#!/usr/bin/env python3
"""
AT#RFSTS 테스트 - RSRP/RSRQ/SINR 조회
"""

from controller import ATController

controller = ATController(port="COM9")

try:
    if controller.connect():
        print("AT#RFSTS 테스트\n")
        
        # AT#RFSTS 실행
        response = controller.send_cmd("AT#RFSTS", wait_s=1.0, total_read_s=5.0)
        decoded = response.decode('ascii', errors='ignore')
        
        print("원본 응답:")
        print("=" * 60)
        print(decoded)
        print("=" * 60)
        
        # 파싱
        if "ERROR" in decoded:
            print("\n✗ 명령 실패 또는 지원 안 함")
        elif "#RFSTS" in decoded or "RSRP" in decoded or "RSRQ" in decoded:
            print("\n✓ RF 상태 수신:")
            for line in decoded.split('\n'):
                line = line.strip()
                if line and not line.startswith('AT') and line != 'OK':
                    print(f"  {line}")
        else:
            print("\n⚠ 응답 있으나 RF 데이터 없음 (네트워크 미등록)")
            
    else:
        print("연결 실패")
        
finally:
    controller.disconnect()

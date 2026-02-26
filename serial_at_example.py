#!/usr/bin/env python3
"""
AT 명령 시리얼 포트 예제
간단한 AT 커맨드를 시리얼 포트로 전송하고 응답을 받는 예제
"""

import serial
import time


def send_at_command(port: str, baud: int, command: str, timeout: float = 2.0) -> str:
    """
    시리얼 포트를 통해 AT 명령을 전송하고 응답을 받음
    
    Args:
        port: 시리얼 포트 (예: 'COM3', 'COM33')
        baud: 보드 레이트 (예: 115200)
        command: AT 명령어 (예: 'AT', 'AT#uptime=0')
        timeout: 응답 대기 타임아웃 (초)
    
    Returns:
        응답 문자열
    """
    try:
        # 1. 시리얼 포트 열기
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=timeout,
            write_timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"✓ 포트 열음: {port} @ {baud} baud")
        
        # 2. 버퍼 초기화
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # 3. AT 명령 전송
        cmd_with_crlf = command + "\r\n"
        ser.write(cmd_with_crlf.encode("ascii"))
        ser.flush()
        print(f"→ 명령 전송: {repr(command)}")
        
        # 4. 응답 수집
        time.sleep(0.5)  # 초기 대기
        
        response = b""
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting)
                response += chunk
                
                # OK 또는 ERROR 수신 시 종료
                if b"OK" in response or b"ERROR" in response:
                    break
            else:
                time.sleep(0.05)
        
        # 5. 응답 디코딩
        response_str = response.decode(errors="ignore").strip()
        
        # 6. 포트 닫기
        ser.close()
        print(f"✓ 포트 닫음")
        
        return response_str
    
    except serial.SerialException as e:
        print(f"✗ 시리얼 오류: {e}")
        return ""
    except Exception as e:
        print(f"✗ 오류: {e}")
        return ""


def main():
    """메인 함수 - 여러 AT 명령 예제"""
    
    PORT = "COM33"  # 사용자 환경에 맞게 수정
    BAUD = 115200
    
    print("=" * 50)
    print("AT 명령 시리얼 포트 예제")
    print("=" * 50)
    
    # 예제 1: 기본 AT 핑 테스트
    print("\n[예제 1] 기본 AT 핑 테스트")
    response = send_at_command(PORT, BAUD, "AT")
    print(f"← 응답: {repr(response)}\n")
    
    # 예제 2: 업타임 조회
    print("[예제 2] 업타임 조회 (AT#uptime=0)")
    response = send_at_command(PORT, BAUD, "AT#uptime=0", timeout=5.0)
    print(f"← 응답: {repr(response)}\n")
    
    # 예제 3: 재부팅 (주의: 실제 재부팅됨)
    print("[예제 3] 재부팅 명령 (AT#reboot)")
    response = send_at_command(PORT, BAUD, "AT#reboot", timeout=5.0)
    print(f"← 응답: {repr(response)}\n")
    
    print("=" * 50)


if __name__ == "__main__":
    main()

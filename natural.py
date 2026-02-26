#!/usr/bin/env python3
"""
Natural Language Interface for FE990 Device Control
자연어로 FE990 장비를 제어하는 인터페이스

사용 예:
    python natural.py FE990 업타임 알려줘
    python natural.py FE990 제품정보 알려줘
    python natural.py FE990 온도 알려줘
    python natural.py FE990 재부팅 시켜줘
    python natural.py FE990 꺼줘
"""

import sys      # 명령줄 인자 처리 및 종료 코드
import re       # 정규식 패턴 매칭 (응답 파싱용)
import time     # 시리얼 통신 대기 시간

# 디버그 메시지 출력
print("[DBG] natural.py started")
print("[DBG] __name__ =", __name__)

def parse_seconds_from_hms(text: str):
    """
    '#UPTIME: hh:mm:ss' 형식을 초로 변환
    
    Args:
        text: AT 명령 응답 문자열
    
    Returns:
        초 단위 정수 또는 None (파싱 실패 시)
    
    예시:
        "#UPTIME: 1:23:45" → 1*3600 + 23*60 + 45 = 5025초
        "#UPTIME: 0:05:30" → 330초
    """
    # 정규식 패턴: 시:분:초 또는 시:분 형식
    # (?:^|\r?\n) - 줄 시작 또는 개행
    # \s*#?UPTIME\s*: - UPTIME 키워드 (# 선택적)
    # (\d{1,2}):(\d{2})(?::(\d{2}))? - hh:mm 또는 hh:mm:ss
    m = re.search(r"(?:^|\r?\n)\s*#?UPTIME\s*:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:\r?\n|$)", text, re.IGNORECASE)
    if not m:
        return None
    
    # 그룹 추출 및 변환
    hh = int(m.group(1))           # 시간
    mm = int(m.group(2))           # 분
    ss = int(m.group(3) or 0)      # 초 (없으면 0)
    
    # 초 단위로 통합
    return hh*3600 + mm*60 + ss

def parse_seconds_from_decimal(text: str):
    """
    '#UPTIME: 9164' 형식을 초로 변환
    
    Args:
        text: AT 명령 응답 문자열
    
    Returns:
        초 단위 정수 또는 None (파싱 실패 시)
    
    예시:
        "#UPTIME: 2654" → 2654초
        "#uptime: 86400" → 86400초 (1일)
    """
    # 라인별로 검사
    for line in text.splitlines():
        line = line.strip()
        # 정규식 패턴: #UPTIME: 숫자
        # \b - 단어 경계 (숫자 끝 확인)
        m = re.match(r"#?UPTIME\s*:\s*(\d+)\b", line, re.IGNORECASE)
        if m:
            return int(m.group(1))  # 첫 번째 매칭 값 반환
    return None

def humanize(seconds: int):
    """
    초 단위를 인간이 읽을 수 있는 형식으로 변환
    
    Args:
        seconds: 초 단위 정수
    
    Returns:
        "X일 Y시간 Z분 W초" 형식의 문자열
    
    예시:
        2654초 → "44분 14초"
        86400초 → "1일"
        3661초 → "1시간 1분 1초"
    """
    # divmod로 일/시간/분/초 계산
    d, r = divmod(seconds, 86400)  # 일 (86400초 = 1일)
    h, r = divmod(r, 3600)          # 시간 (3600초 = 1시간)
    m, s = divmod(r, 60)            # 분, 초
    
    # 0이 아닌 값만 리스트에 추가
    parts = []
    if d: parts.append(f"{d}일")
    if h: parts.append(f"{h}시간")
    if m: parts.append(f"{m}분")
    if s or not parts: parts.append(f"{s}초")  # 0초도 표시 (parts가 비어있을 때)
    
    # 공백으로 연결하여 반환
    return " ".join(parts)

def get_fe990_uptime():
    """
    FE990 업타임 조회 (직접 시리얼 통신)
    
    동작 순서:
        1. AT 명령으로 연결 확인 (ping)
        2. AT#uptime=1 시도 (시:분:초 형식)
        3. 실패 시 AT#uptime=0 시도 (초 단위)
    
    Returns:
        업타임 초 단위 정수 또는 None (실패 시)
    """
    try:
        import serial
        # FE990 시리얼 포트 연결 (COM9, 115200 bps, 타임아웃 1초)
        ser = serial.Serial("COM9", 115200, timeout=1)
        try:
            # 수신/송신 버퍼 초기화 (이전 데이터 제거)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # DTR/RTS 신호 설정 (일부 장비에서 필요)
            try:
                ser.dtr = True   # Data Terminal Ready
                ser.rts = False  # Request To Send
            except Exception:
                pass  # 실패해도 무시

            # 1단계: AT 명령으로 연결 확인 (ping)
            ser.write(b"AT\r")         # AT 명령 전송
            time.sleep(0.2)            # 200ms 대기
            _ = ser.read(256)          # 응답 읽기 (무시)

            # 2단계: AT#uptime=1 시도 (시:분:초 형식 반환)
            ser.write(b"AT#uptime=1\r") # uptime=1 명령 전송
            time.sleep(0.6)             # 600ms 대기
            buf = ser.read(4096).decode(errors="ignore")  # 응답 읽기
            time.sleep(0.4)             # 추가 대기
            buf += ser.read(8192).decode(errors="ignore") # 남은 데이터 읽기
            
            # 시:분:초 형식 파싱 시도
            seconds = parse_seconds_from_hms(buf)
            
            # 3단계: 실패 시 AT#uptime=0 시도 (초 단위 반환)
            if seconds is None:
                ser.write(b"AT#uptime=0\r")  # uptime=0 명령 전송
                time.sleep(0.6)
                buf2 = ser.read(4096).decode(errors="ignore")
                time.sleep(0.4)
                buf2 += ser.read(8192).decode(errors="ignore")
                # 초 단위 파싱
                seconds = parse_seconds_from_decimal(buf2)
            
            return seconds
        finally:
            # 포트 닫기 (항상 실행)
            ser.close()
    except Exception as e:
        print(f"[ERROR] FE990 업타임 조회 실패: {e}", file=sys.stderr)
        return None

def interpret(text: str):
    """
    자연어 명령을 액션 코드로 변환
    
    Args:
        text: 사용자 입력 문자열 (예: "FE990 업타임 알려줘")
    
    Returns:
        액션 코드 문자열 또는 None
        - "fe990_uptime": FE990 업타임 조회
        - "fe990_off": FE990 전원 끄기
        - "fe990_reboot": FE990 재부팅
        - "fe990_gmm": FE990 제품 정보 조회
        - "fe990_tempsens": FE990 온도 조회
        - "power_on": 장치 전원 켜기
        - "off": 장치 전원 끄기
        - "reboot": 장치 재부팅
        - "uptime": 장치 업타임 조회
    
    예시:
        "FE990 업타임 알려줘" → "fe990_uptime"
        "FE990 제품정보" → "fe990_gmm"
        "FE990 온도" → "fe990_tempsens"
    """
    t = text.lower()  # 소문자로 변환 (대소문자 무시)
    
    # FE990 관련 명령 우선 체크 (키워드 조합으로 판단)
    # "fe990" 또는 "f990" + 특정 키워드
    
    if ("fe990" in t or "f990" in t) and ("업타임" in t or "uptime" in t or "시간" in t):
        return "fe990_uptime"
    
    if ("fe990" in t or "f990" in t) and ("꺼" in t or "off" in t or "종료" in t or "셧다운" in t):
        return "fe990_off"
    
    if ("fe990" in t or "f990" in t) and ("재부팅" in t or "re부트" in t or "reboot" in t):
        return "fe990_reboot"
    
    if ("fe990" in t or "f990" in t) and ("제품" in t or "모델" in t or "gmm" in t or "정보" in t):
        return "fe990_gmm"
    
    if ("fe990" in t or "f990" in t) and ("온도" in t or "temp" in t or "센서" in t):
        return "fe990_tempsens"
    
    # 기존 AT 명령 (FE990이 아닌 일반 장치용, COM33 포트)
    if "켜" in t or "on" in t:
        return "power_on"
    
    if "꺼" in t or "off" in t or "종료" in t or "셧다운" in t:
        return "off"
    
    if "재부팅" in t or "re부트" in t or "reboot" in t:
        return "reboot"
    
    if "업타임" in t or "uptime" in t or "시간" in t:
        return "uptime"
    
    # 해석 불가
    return None

if __name__ == "__main__":
    # 명령줄 인자를 하나의 문자열로 결합
    # 예: ["FE990", "업타임", "알려줘"] → "FE990 업타임 알려줘"
    text = " ".join(sys.argv[1:])
    
    # 자연어를 액션 코드로 해석
    action = interpret(text)

    # ===== FE990 관련 명령 처리 (COM9 포트) =====
    
    if action == "fe990_uptime":
        # FE990 업타임 조회
        print("[FE990] 업타임 조회 중...")
        seconds = get_fe990_uptime()  # 직접 시리얼 통신
        if seconds is not None:
            # 성공: 사람이 읽기 쉬운 형식으로 출력
            print(f"[FE990] 업타임: {humanize(seconds)} (총 {seconds}초)")
        else:
            # 실패
            print("[FE990] 업타임 조회 실패")
            sys.exit(1)
        sys.exit(0)
    
    elif action == "fe990_off":
        # FE990 전원 끄기 (AT#shdn 명령)
        print("[FE990] Off 명령 송신 중...")
        import serial
        try:
            # COM9 포트로 시리얼 연결
            ser = serial.Serial("COM9", 115200, timeout=2)
            ser.reset_input_buffer()   # 버퍼 초기화
            ser.reset_output_buffer()
            
            # AT#shdn 명령 전송 (CR+LF로 종료)
            ser.write(b"AT#shdn\r\n")
            ser.flush()  # 즉시 전송
            time.sleep(1)  # 1초 대기
            
            # 응답 읽기
            response = ser.read(256).decode(errors="ignore")
            ser.close()
            print(f"[FE990] Off 명령 송신 완료: {response.strip()}")
        except Exception as e:
            print(f"[ERROR] FE990 Off 실패: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif action == "fe990_reboot":
        # FE990 재부팅 (AT#reboot 명령)
        print("[FE990] Reboot 명령 송신 중...")
        import serial
        try:
            ser = serial.Serial("COM9", 115200, timeout=2)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # AT#reboot 명령 전송
            ser.write(b"AT#reboot\r\n")
            ser.flush()
            time.sleep(1)
            
            response = ser.read(256).decode(errors="ignore")
            ser.close()
            print(f"[FE990] Reboot 명령 송신 완료: {response.strip()}")
        except Exception as e:
            print(f"[ERROR] FE990 Reboot 실패: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif action == "fe990_gmm":
        # FE990 제품 정보 조회 (AT+GMM 명령)
        print("[FE990] 제품 정보 조회 중...")
        import serial
        try:
            ser = serial.Serial("COM9", 115200, timeout=2)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # AT+GMM 명령 전송 (CR로 종료)
            ser.write(b"AT+GMM\r")
            ser.flush()
            time.sleep(0.5)
            
            # 응답 읽기 (최대 512바이트)
            response = ser.read(512).decode(errors="ignore")
            ser.close()
            
            # 모델명 파싱: "OK", "ERROR", "AT" 라인 제외
            lines = [ln.strip() for ln in response.split("\n") if ln.strip()]
            model_lines = [ln for ln in lines if ln not in ["OK", "ERROR"] and not ln.startswith("AT")]
            
            if model_lines:
                # 첫 번째 라인이 모델명 (예: "FE990B40-NA")
                print(f"[FE990] 제품 정보: {model_lines[0]}")
            else:
                print(f"[FE990] 제품 정보를 찾을 수 없습니다. 응답: {response.strip()}")
        except Exception as e:
            print(f"[ERROR] FE990 GMM 실패: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif action == "fe990_tempsens":
        # FE990 온도 정보 조회 (AT#TEMPSENS=2 명령)
        print("[FE990] 온도 정보 조회 중...")
        import serial
        try:
            ser = serial.Serial("COM9", 115200, timeout=2)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # AT#TEMPSENS=2 명령 전송 (모든 센서 조회)
            ser.write(b"AT#TEMPSENS=2\r")
            ser.flush()
            time.sleep(0.5)
            
            # 응답 읽기 (최대 1024바이트)
            response = ser.read(1024).decode(errors="ignore")
            ser.close()
            
            # 정규식으로 온도 정보 파싱
            # 패턴: "#TEMPSENS: 센서명,온도값"
            # 예: "#TEMPSENS: TSENS,26" → sensor="TSENS", temp=26.0
            pattern = re.compile(r"#TEMPSENS\s*:\s*([A-Z_\d]+)\s*,\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
            temperatures = {}
            
            for line in response.split("\n"):
                m = pattern.search(line)
                if m:
                    try:
                        sensor_name = m.group(1)        # 센서명
                        temp_value = float(m.group(2))  # 온도값
                        temperatures[sensor_name] = temp_value
                    except ValueError:
                        continue  # 변환 실패 시 무시
            
            # 결과 출력
            if temperatures:
                print("[FE990] 온도 정보:")
                for sensor, temp in temperatures.items():
                    print(f"  {sensor}: {temp}°C")
            else:
                print(f"[FE990] 온도 정보를 찾을 수 없습니다. 응답: {response.strip()}")
        except Exception as e:
            print(f"[ERROR] FE990 TEMPSENS 실패: {e}")
            sys.exit(1)
        sys.exit(0)

    # ===== AT Controller 명령 처리 (COM33 포트, 일반 장치용) =====
    # FE990이 아닌 명령은 controller.py의 ATController 사용
    
    if action not in ["fe990_uptime", "fe990_off", "fe990_reboot", "fe990_gmm", "fe990_tempsens"]:
        from controller import ATController
        
        # COM33 포트로 컨트롤러 생성
        ctl = ATController(port="COM33")

        # 연결 시도
        if not ctl.connect():
            print("[FAIL] Cannot connect to device")
            sys.exit(1)

        try:
            # 액션별 실행
            if action == "power_on":
                # 전원 켜기 (GPIO 제어, 현재 미구현)
                success, msg = ctl.power_on()
                print(f"[power_on] {'SUCCESS' if success else 'FAILED'}: {msg}")
            
            elif action == "off":
                # 전원 끄기 (AT#shdn)
                success, msg = ctl.off()
                print(f"[off] {'SUCCESS' if success else 'FAILED'}: {msg}")
            
            elif action == "reboot":
                # 재부팅 (AT#reboot)
                success, msg = ctl.reboot()
                print(f"[reboot] {'SUCCESS' if success else 'FAILED'}: {msg}")
            
            elif action == "uptime":
                # 업타임 조회 (AT#uptime=0)
                success, uptime_val, msg = ctl.get_uptime()
                print(f"[uptime] {'SUCCESS' if success else 'FAILED'}: {msg}")
                if uptime_val is not None:
                    # 시간:분 형식으로 출력
                    print(f"  Uptime: {uptime_val} seconds ({uptime_val // 3600}h {(uptime_val % 3600) // 60}m)")
            
            else:
                # 해석할 수 없는 명령
                print("해석할 수 없는 명령입니다.")
        finally:
            # 연결 해제 (항상 실행)
            ctl.disconnect()

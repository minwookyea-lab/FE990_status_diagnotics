
# test_uptime.py  ← 임시로 교체
import time
import re
import serial

PORT = "COM9"
BAUD = 115200

CANDIDATE_CMDS = [
    "AT#UPTIME",     # 우리가 시도했던 것
    "AT#UPTIME?",    # 일부 모뎀은 조회형에 ? 필요
    "AT+UPTIME",     # +계열
    "AT+UPTIME?",    # +계열 조회형
    "AT$UPTIME?",    # $ 프리픽스 계열
    "AT!UPTIME?",    # ! 프리픽스(벤더 특화)
    "AT+SYSTIME?",   # 시스템 시간/업타임 계열(벤더에 따라 다름)
    "AT+TIME?",      # 시간 관련
    "AT!GSTATUS?",   # Sierra 계열 상태 정보(여기에 up time 들어가는 경우 있음)
]

def send(ser, cmd, wait=1.5):
    ser.reset_input_buffer()
    ser.write((cmd + "\r\n").encode())
    time.sleep(wait)
    data = ser.read(8192)
    text = data.decode(errors="ignore")
    print(f"\n=== {cmd} ===")
    print(text if text.strip() else "(no text)")
    return text

if __name__ == "__main__":
    print(f"[INFO] Open {PORT} @ {BAUD}")
    try:
        with serial.Serial(PORT, BAUD, timeout=0.2) as ser:
            # 기본 설정
            send(ser, "ATE0", 0.5)
            send(ser, "ATV1", 0.5)
            send(ser, "ATQ0", 0.5)
            send(ser, "AT",   0.8)

            # 후보 명령들 시퀀스 테스트
            for cmd in CANDIDATE_CMDS:
                txt = send(ser, cmd, 2.5)

                # 즉석에서 초/시간 형태 패턴이 보이는지 대충 체크
                if re.search(r"\b\d{4,}\b", txt):  # 4자리 이상 숫자(초)처럼 보이는 값
                    print(f"[HINT] 큰 숫자 감지됨 → {cmd} 후보 유력")
                if re.search(r"\b\d+\s*days?\b|\b\d{1,2}:\d{2}:\d{2}\b", txt, re.I):
                    print(f"[HINT] 일/시:분:초 패턴 감지됨 → {cmd} 후보 유력")

    except Exception as e:
        print(f"[ERR] 포트 열기/통신 실패: {e}")

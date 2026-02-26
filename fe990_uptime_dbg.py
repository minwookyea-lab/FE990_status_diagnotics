
# file: fe990_uptime_dbg.py
import time, sys, re

PORT = "COM9"   # 민욱님 환경
BAUD = 115200

CAND = [
    b"AT\r",
    b"ATI\r",
    b"AT#uptime=0\r",
    b"AT#uptime=1\r",
    b"AT#uptime=2\r",
    b"AT#uptime=3\r",
]

def main():
    try:
        import serial
    except Exception:
        print("pyserial이 필요합니다: pip install pyserial", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Open {PORT} @ {BAUD}")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"[ERROR] 포트 열기 실패: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        ser.reset_input_buffer(); ser.reset_output_buffer()
        try:
            # 일부 장비는 DTR/RTS 설정이 필요할 수 있음
            ser.dtr = True
            ser.rts = False
        except Exception:
            pass

        for cmd in CAND:
            print("="*70)
            print(f"[SEND] {cmd!r}")
            ser.write(cmd)

            # 응답 수집: 첫 번째 덩어리 + 추가 지연 후 추가 덩어리
            time.sleep(0.6)
            buf = ser.read(8192).decode(errors="ignore")
            time.sleep(0.4)
            buf += ser.read(16384).decode(errors="ignore")

            print("[RECV RAW]")
            print(buf.strip() or "(no data)")

            # 간단히 숫자/시:분:초/일-시간 포맷도 미리 스캔
            candidates = []
            # 1) 정수(10진/16진) 추출
            for m in re.finditer(r"\b(0x[0-9A-Fa-f]+|\d+)\b", buf):
                candidates.append(("number", m.group(0)))
            # 2) d일 h시간 m분 s초 스타일
            for m in re.finditer(r"(\d+)\s*d|\b(\d+)\s*h|\b(\d+)\s*m(?!s)|\b(\d+)\s*s", buf):
                pass
            # 3) hh:mm(:ss) / d,hh:mm(:ss)
            for m in re.finditer(r"\b(?:(\d+),)?(\d{1,2}):(\d{2})(?::(\d{2}))?\b", buf):
                candidates.append(("clock", m.group(0)))

            if candidates:
                print("[PARSE HINT] candidates:", candidates)
            else:
                print("[PARSE HINT] candidates: (none)")

            time.sleep(0.2)

    finally:
        try:
            ser.close()
        except Exception:
            pass
        print("[INFO] Closed")

if __name__ == "__main__":
    main()

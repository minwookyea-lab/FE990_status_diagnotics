
# fe990_uptime.py — FE990 업타임 조회 (COM9, 안전 파서)
import sys
import re
import time

PORT = "COM9"          # 민욱님 환경
BAUD = 115200
# 우선 hh:mm:ss 포맷이 안정적이므로 =1을 기본으로 사용
CMD_PRIMARY   = "AT#uptime=1\r"
# 보조: 초 단위가 필요한 경우를 대비해 =0도 파싱 가능(단, '#uptime=0' 라인은 무시)
CMD_FALLBACK  = "AT#uptime=0\r"

def parse_seconds_from_hms(text: str):
    """
    '#UPTIME: hh:mm:ss' 또는 'UPTIME: hh:mm:ss'를 초로 변환
    """
    m = re.search(r"(?:^|\r?\n)\s*#?UPTIME\s*:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:\r?\n|$)", text, re.IGNORECASE)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2)); ss = int(m.group(3) or 0)
    return hh*3600 + mm*60 + ss

def parse_seconds_from_decimal(text: str):
    """
    '#UPTIME: 9164' 또는 'UPTIME: 9164' 형태만 인식하도록 제한.
    (주의) '#uptime=0' 같은 라인의 '0'은 절대 매칭하지 않도록 ':'가 있는 라인만 허용.
    """
    # 줄 단위로 스캔하여 '...UPTIME: <number>' 형태만 채택
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"#?UPTIME\s*:\s*(\d+)\b", line, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None

def humanize(seconds: int):
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}일")
    if h: parts.append(f"{h}시간")
    if m: parts.append(f"{m}분")
    if s or not parts: parts.append(f"{s}초")
    return " ".join(parts)

def query(cmd: str):
    try:
        import serial
    except Exception:
        print("[ERROR] pyserial 모듈이 필요합니다. 설치: pip install pyserial", file=sys.stderr)
        sys.exit(1)

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"[ERROR] 포트 열기 실패: {PORT} ({e})", file=sys.stderr)
        sys.exit(2)

    try:
        ser.reset_input_buffer(); ser.reset_output_buffer()

        # 일부 장치에서 안정화를 위해 DTR/RTS 조정
        try:
            ser.dtr = True
            ser.rts = False
        except Exception:
            pass

        # keepalive
        ser.write(b"AT\r")
        time.sleep(0.2)
        _ = ser.read(256)

        # 실제 명령
        ser.write(cmd.encode("ascii"))
        time.sleep(0.6)
        buf = ser.read(4096).decode(errors="ignore")
        time.sleep(0.4)
        buf += ser.read(8192).decode(errors="ignore")
        return buf
    finally:
        try:
            ser.close()
        except Exception:
            pass

def run():
    # 1) hh:mm:ss 포맷(=1) 시도
    buf = query(CMD_PRIMARY)
    seconds = parse_seconds_from_hms(buf)

    # 2) 실패 시 =0(순수 초) 포맷 시도
    if seconds is None:
        buf2 = query(CMD_FALLBACK)
        seconds = parse_seconds_from_decimal(buf2)
        if seconds is None:
            print("[RAW RESPONSE]")
            print((buf + "\n---\n" + buf2).strip())
            print("\n[PARSE] 업타임을 인식하지 못했습니다. RAW를 복사해 주세요.")
            sys.exit(3)

    print(f"FE990 업타임: {humanize(seconds)} (총 {seconds}초)")
    sys.exit(0)

if __name__ == "__main__":
    run()

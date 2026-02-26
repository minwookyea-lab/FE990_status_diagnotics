
# filename: at_uptime_0.py
import time
import serial

PORT = "COM33"      # ← 사용자 환경 기준
BAUD = 115200
TIMEOUT = 2         # 너무 길면 응답 대기 중 UI가 멈춰있는 느낌이 큼, 루프로 보완
CMD = "AT#reboot"

def send_cmd(
    ser: serial.Serial,
    cmd: str,
    use_crlf: bool = True,
    wait_s: float = 0.5,       # write 후 초기 대기
    total_read_s: float = 5.0  # 전체 읽기 시간 한도
):
    """
    AT 커맨드 송신 후 응답 수집.
    - use_crlf=True: '\r\n', 모듈에 따라 '\r'만 필요하면 False로.
    - wait_s: 쓰기 직후 약간의 대기
    - total_read_s: 최대 수집 시간
    """
    line = cmd + ("\r\n" if use_crlf else "\r")
    ser.write(line.encode("ascii"))
    ser.flush()

    # 초기 대기 후 현재 버퍼를 쭉 훑어 읽는다.
    time.sleep(wait_s)

    buf = bytearray()
    deadline = time.time() + total_read_s
    while time.time() < deadline:
        n = ser.in_waiting
        if n:
            chunk = ser.read(n)
            if chunk:
                buf.extend(chunk)
                # 'OK' or 'ERROR' 등 종결 키워드를 빠르게 감지하면 조기 종료
                text = buf.decode(errors="ignore")
                if ("OK" in text) or ("ERROR" in text):
                    break
        else:
            # 잠깐 쉬었다가 다시 in_waiting 체크
            time.sleep(0.05)

    return bytes(buf)

if __name__ == "__main__":
    # 포트 열기
    ser = serial.Serial(
        PORT, BAUD,
        timeout=TIMEOUT, write_timeout=TIMEOUT,
        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        rtscts=False, dsrdtr=False  # 필요하면 아래에서 켬
    )

    # 필요 시 제어선 ON (장비/모듈에 따라 필수)
    # ser.setDTR(True)
    # ser.setRTS(True)

    # 버퍼 정리
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    # 또는: time.sleep(0.2); _ = ser.read(ser.in_waiting or 1)

    print(f"[OPEN] {PORT} @ {BAUD}")
    print(f">> {CMD}")

    raw = send_cmd(ser, CMD, use_crlf=True, wait_s=0.5, total_read_s=10.0)

    # 로우 바이트와 디코딩 텍스트 모두 보여주기
    if raw:
        try:
            txt = raw.decode("ascii", errors="ignore").strip()
        except Exception:
            txt = raw.decode(errors="ignore").strip()

        print("[RAW]", raw)  # 바이트 그대로 (디버깅용)
        print("[TXT]")
        print(txt if txt else "(no data text)")
    else:
        print("(no data)")

    ser.close()
    print("[CLOSE] Port closed.")

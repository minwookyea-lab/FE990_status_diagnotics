
# test_at_guard.py — 가드 타임 + '+++'로 AT 커맨드 모드 전환 시도
import serial, time

PORT = 'COM37'
BAUD = 115200

print(f"open {PORT} @ {BAUD}")
with serial.Serial(PORT, BAUD, timeout=2, write_timeout=2) as s:
    # 0) 버퍼 비우고 잠깐 대기 (가드 타임)
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(1.2)  # 가드 타임

    # 1) '+++' 전송 (개행 없이)
    s.write(b'+++')
    time.sleep(1.5)
    resp0 = s.read(4096)
    print("AFTER +++:", resp0)

    # 2) AT 핑
    s.write(b'AT\r')
    time.sleep(1.0)
    resp1 = s.read(4096)
    print("AT:", resp1)

    # 3) CRLF도 시도
    if b'OK' not in resp1:
        s.write(b'AT\r\n')
        time.sleep(1.0)
        resp2 = s.read(4096)
        print("AT (CRLF):", resp2)

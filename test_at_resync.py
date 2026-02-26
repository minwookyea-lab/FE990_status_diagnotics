
# test_at_resync.py — 콘솔 프롬프트가 먼저 나타나는 포트에서 AT 모드로 재동기화 시도
import serial, time

PORT = 'COM37'     # TeraTerm에서 AT OK가 나오는 포트
BAUD = 115200

def drain(s, label, t=0.3):
    time.sleep(t)
    data = s.read(4096)
    if data:
        print(f"{label}:", data)

print(f"open {PORT} @ {BAUD}")
with serial.Serial(
    PORT, BAUD,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1.2,
    write_timeout=1.2,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False
) as s:
    # 신호 설정: TeraTerm 기본에 가깝게
    s.dtr = True
    s.rts = False
    time.sleep(0.3)

    # 버퍼 비우기
    s.reset_input_buffer()
    s.reset_output_buffer()
    drain(s, "JUNK0", 0.2)

    # 1) 콘솔 프롬프트를 날려버리기 (ESC, Ctrl-C, CR 반복)
    for i in range(3):
        s.write(b'\x1b')   # ESC
        s.write(b'\x03')   # Ctrl-C
        s.write(b'\r')     # CR
        drain(s, f"JUNK{i+1}", 0.3)

    # 2) 에코 끄기 시도
    s.write(b'ATE0\r')
    drain(s, "ATE0", 0.6)

    # 3) AT 핑 (CR)
    s.write(b'AT\r')
    drain(s, "AT1", 0.8)

    # 4) 안 되면 CRLF로 재시도
    s.write(b'AT\r\n')
    drain(s, "AT2", 0.8)

    # 5) 그래도 안 되면 DTR 토글 + 재시도
    s.dtr = False
    time.sleep(0.3)
    s.dtr = True
    s.reset_input_buffer()
    s.reset_output_buffer()
    s.write(b'\r')
    drain(s, "AFTER_DTR", 0.5)

    s.write(b'AT\r')
    drain(s, "AT3", 0.8)

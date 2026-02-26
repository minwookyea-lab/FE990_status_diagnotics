
import serial, time

PORT = 'COM9'   # ← AT 포트로 확인된 값 (COM36/COM8/COM33도 가능)
BAUD = 115200

print(f"Open {PORT} @ {BAUD}")
with serial.Serial(PORT, BAUD, timeout=2, write_timeout=2) as s:
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(0.5)

    s.write(b'AT\r')
    time.sleep(0.5)
    resp = s.read(200)
    print("AT:", resp)

    s.write(b'ATE0\r')
    time.sleep(0.5)
    resp = s.read(200)
    print("ATE0:", resp)

    s.write(b'ATI\r')
    time.sleep(0.5)
    resp = s.read(400)
    print("ATI:", resp)

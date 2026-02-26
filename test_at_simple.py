
import serial, time

PORT = 'COM37'
BAUD = 115200

print(f"open {PORT} @ {BAUD}")
with serial.Serial(PORT, BAUD, timeout=3) as s:
    # 버퍼 비우기
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(0.5)

    # AT 명령 보내기
    s.write(b'AT\r')
    print("Sent: AT")

    # 충분히 기다린 뒤 응답 읽기
    time.sleep(1.5)
    resp = s.read(4096)
    print("Response:", resp)

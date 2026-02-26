
# test_at.py — COM37 기본 AT 테스트
import serial, time

PORT = 'COM37'   # 장치 관리자에서 확인한 AT 포트
BAUD = 115200    # 테라텀에서 쓰던 속도

print(f"open {PORT} @ {BAUD}")
with serial.Serial(PORT, BAUD, timeout=2) as s:
    # 버퍼 초기화
    s.reset_input_buffer()
    s.reset_output_buffer()

    # 가장 기본 핑: AT (CR)
    s.write(b'AT\r')
    time.sleep(0.5)
    resp = s.read(1024)
    print("RAW:", resp)

    # 대안으로 ATI도 한번
    if b'OK' not in resp:
        s.write(b'ATI\r')
        time.sleep(0.5)
        resp2 = s.read(2048)
        print("RAW2:", resp2)

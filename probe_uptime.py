
# probe_uptime.py
import time
import serial

PORT = "COM9"         # 민욱님 환경
BAUD = 115200

def read_for(ser, seconds=2.0):
    end = time.time() + seconds
    chunks = []
    while time.time() < end:
        data = ser.read(512)
        if data:
            chunks.append(data)
        else:
            time.sleep(0.02)
    return b"".join(chunks)

if __name__ == "__main__":
    print(f"[INFO] Open {PORT} @ {BAUD}")
    try:
        with serial.Serial(PORT, BAUD, timeout=0.2) as ser:
            # 1) 버퍼 비우기
            ser.reset_input_buffer()

            # 2) 모뎀 깨우기
            ser.write(b"AT\r")
            time.sleep(0.1)
            data = read_for(ser, 0.8)
            print("\n[AT] RAW bytes:\n", repr(data))
            print("\n[AT] As text:\n", data.decode(errors="ignore"))

            # 3) 업타임 요청
            ser.reset_input_buffer()
            ser.write(b"AT#UPTIME\r")  # \r\n이 필요한 장비도 있으므로, 안 나오면 \r\n로 바꿔보자
            print("\n[AT#UPTIME] waiting 3.0s...")
            data = read_for(ser, 3.0)  # 필요 시 5초까지 늘릴 수 있음
            print("\n[AT#UPTIME] RAW bytes:\n", repr(data))
            print("\n[AT#UPTIME] As text:\n", data.decode(errors="ignore"))

    except Exception as e:
        print(f"[ERR] 포트 열기/통신 실패: {e}")


# filename: at_test.py
import time
import serial

PORT = "COM33"          # 민욱님 포트 번호
BAUD = 115200           # 테라텀과 동일한 속도
TIMEOUT = 2             # 응답 대기 시간 (초)

def send_at(cmd: str, ser: serial.Serial):
    # CRLF로 전송
    ser.write((cmd + "\r\n").encode("ascii"))
    ser.flush()

    # 200ms 대기 후 응답 수집
    time.sleep(0.2)

    resp = b""
    for _ in range(10):                 # 최대 10번에 걸쳐 조금씩 읽기
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            resp += chunk
        time.sleep(0.05)                # 매번 50ms 대기

    reply = resp.decode(errors="ignore")
    return reply

if __name__ == "__main__":
    # 시리얼 포트 열기
    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=TIMEOUT,
        write_timeout=TIMEOUT,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        rtscts=False,
        dsrdtr=False
    )

    # 필요 시 제어선 활성화 (응답 없으면 주석 해제해서 테스트)
    # ser.setDTR(True)
    # ser.setRTS(True)

    print(">> AT")
    reply = send_at("AT", ser)
    print(reply)

    ser.close()

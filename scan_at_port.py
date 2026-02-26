
# scan_at_ports.py
import time
import serial
import serial.tools.list_ports

def try_port(port, baud=115200):
    try:
        with serial.Serial(port, baud, timeout=1, write_timeout=1) as s:
            # 잔여 버퍼 비우기
            s.reset_input_buffer()
            s.reset_output_buffer()
            time.sleep(0.2)
            # 간단 테스트: AT 후 500ms 대기
            s.write(b'AT\r')
            time.sleep(0.5)
            resp = s.read(200)
            # 보기 좋게 디코드
            txt = resp.decode(errors='replace')
            return True, txt
    except Exception as e:
        return False, str(e)

def main():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("[INFO] 사용 가능한 COM 포트가 없습니다.")
        return
    print("[INFO] 후보 COM 포트:", ports)

    for p in ports:
        ok, msg = try_port(p)
        print(f"\n=== {p} ===")
        if ok:
            print("[RX]", msg.replace("\r", "\\r").replace("\n", "\\n"))
            if "OK" in msg:
                print(f"[HINT] {p} 에서 'OK' 발견 → 이 포트가 AT 포트일 가능성 높음")
        else:
            print("[ERR]", msg)

if __name__ == "__main__":
    main()

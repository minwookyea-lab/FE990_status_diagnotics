
# test_at_init.py — 콘솔 로그인 프롬프트가 먼저 뜨는 포트에서 AT 모드 안정화 시도
import serial, time

PORT = 'COM37'   # TeraTerm에서 AT OK가 나왔던 포트
BAUD = 115200    # TeraTerm에서 사용한 속도

print(f"open {PORT} @ {BAUD}")
with serial.Serial(
    PORT, BAUD,
    timeout=1.5,           # 약간 늘림
    write_timeout=1.5
) as s:
    # 1) 모뎀 초기화 신호 (TeraTerm과 맞추기 위해 DTR/RTS 조정)
    s.dtr = True
    s.rts = False
    time.sleep(0.3)

    # 2) 버퍼 완전 비우기
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(0.2)

    # 3) 오픈 직후 콘솔 프롬프트가 떠 있어도, CR만 여러 번 던져서 넘기기
    for _ in range(3):
        s.write(b'\r')         # CR만 (TeraTerm 기본과 동일)
        time.sleep(0.2)
        junk = s.read(512)     # 남는 것들은 버림 (로그인 문구 등)
        # print("JUNK:", junk)  # 필요시 주석 해제해 원문 확인

    # 4) AT 핑 (CR → 0.5s 대기 → 읽기)
    s.write(b'AT\r')
    time.sleep(0.6)
    resp = s.read(2048)
    print("AT RAW:", resp)

    # 5) 만약 OK가 없다면: 한번 더 (CRLF로도 시도)
    if b'OK' not in resp:
        s.write(b'AT\r\n')
        time.sleep(0.6)
        resp2 = s.read(2048)
        print("AT RAW2:", resp2)

    # 6) 그래도 OK가 없다면, DTR 토글 + 재시도 (장비에 따라 유효)
    if b'OK' not in resp and ('resp2' not in locals() or b'OK' not in resp2):
        s.dtr = False
        time.sleep(0.3)
        s.dtr = True
        time.sleep(0.3)
        s.reset_input_buffer()
        s.reset_output_buffer()
        s.write(b'AT\r')
        time.sleep(0.8)
        resp3 = s.read(2048)
        print("AT RAW3:", resp3)


# uptime_service.py
import re
import serial
from typing import Optional, Tuple

DEFAULT_BAUD = 115200
DEFAULT_AT_CMD = "AT#UPTIME=0"   # 민욱님 장비 기준
DEFAULT_PORT   = "COM9"          # Windows 예시: COM9 / Linux 예시: /dev/ttyUSB0

READ_TIMEOUT_SEC = 2.5           # 읽기 타임아웃 약간 증가
OPEN_TIMEOUT_SEC = 2.0           # 포트 오픈 시도 제한
MAX_READ_BYTES   = 8192          # 최대 읽기 바이트 상향
RETRY_COUNT      = 1             # 1회 재시도 (총 2번 시도)

def _read_all(ser: serial.Serial, max_bytes=MAX_READ_BYTES) -> bytes:
    """
    가벼운 '대기→수집' 방식:
      - 버퍼가 잠시 비어 있어도 약간 더 기다렸다가 모아 읽음
      - 장비에 따라 OK/ERROR가 늦게 붙는 경우 방지
    """
    chunks = []
    total = 0
    # 기본 타임아웃 내에서 in_waiting 확인하며 조금 더 모읍니다.
    while True:
        data = ser.read(ser.in_waiting or 1)
        if not data:
            # timeout 경과로 read가 빈 바이트를 반환하면 종료
            break
        chunks.append(data)
        total += len(data)
        if total >= max_bytes:
            break
    return b"".join(chunks)

def _send_at(port: str, cmd: str, timeout=READ_TIMEOUT_SEC) -> str:
    """
    - 포트 오픈 실패와 읽기 타임아웃을 별도 메시지로 노출
    - CR은 유지(\r), LF는 장비에 따라 자동 처리
    """
    try:
        with serial.Serial(port, DEFAULT_BAUD, timeout=timeout) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write((cmd + "\r").encode("ascii", errors="ignore"))

            # 1차 수신
            raw = _read_all(ser)

            # 일부 장비는 약간 늦게 'OK'가 붙으므로 한 번 더 짧게 시도
            if b"OK" not in raw and b"ERROR" not in raw:
                ser.timeout = 0.7
                raw += _read_all(ser, max_bytes=(MAX_READ_BYTES // 2))

    except serial.SerialException as e:
        raise RuntimeError(f"포트 열기/설정 실패: {port} ({e})") from e

    except Exception as e:
        # 기타 알 수 없는 예외
        raise RuntimeError(f"AT 전송/수신 중 예외: {e}") from e

    return raw.decode(errors="ignore")

def _normalize_resp(resp: str) -> str:
    """
    응답 정규화:
    - CR 제거, 다중 공백 정리
    - 좌우 공백 제거
    """
    # \r 제거, 줄 단위 정리
    resp = resp.replace("\r", "")
    # 라인 단위로 정리하고 다시 합치기
    lines = [ln.strip() for ln in resp.split("\n") if ln.strip()]
    return "\n".join(lines)

def parse_seconds(resp: str) -> Optional[int]:
    """
    예:
      "#UPTIME=0: 123456"
      "#UPTIME : 123456"
      "+UPTIME: 123456"
      "UPTIME: 123456"
    """
    # 먼저 정규화
    norm = _normalize_resp(resp)

    # 일부 응답은 여러 라인 가운데 데이터가 있을 수 있으니 라인별 검사
    pattern = re.compile(r"(?:\+|#)?UPTIME(?:=\d+)?\s*:\s*(\d+)", flags=re.IGNORECASE)
    for line in norm.split("\n"):
        m = pattern.search(line)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None

def humanize(total: int) -> Tuple[int, int, int, int]:
    d = total // 86400
    rem = total % 86400
    h = rem // 3600
    rem %= 3600
    m = rem // 60
    s = rem % 60
    return d, h, m, s

def get_fe990_uptime(port: Optional[str] = None, at_cmd: Optional[str] = None) -> dict:
    p = port or DEFAULT_PORT
    cmd = at_cmd or DEFAULT_AT_CMD

    last_error = None
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = _send_at(p, cmd)
            secs = parse_seconds(resp)
            if secs is None:
                # 재시도 가치가 있을만한 경우: 응답에 'OK'는 있는데 데이터가 없는 등
                last_error = {"ok": False, "error": f"응답 파싱 실패: {resp.strip()}", "port": p, "raw": resp}
                continue

            d, h, m, s = humanize(secs)
            return {
                "ok": True,
                "seconds": secs,
                "human": f"{d}일 {h}시간 {m}분 {s}초",
                "port": p,
                "raw": resp
            }

        except RuntimeError as e:
            # 포트 오픈 실패/수신 예외 등
            last_error = {"ok": False, "error": str(e), "port": p}

    # 모든 시도 실패 시 마지막 에러 반환
    return last_error or {"ok": False, "error": "알 수 없는 실패", "port": p}

def parse_model_info(resp: str) -> Optional[str]:
    """
    AT+GMM 응답에서 모델 정보 추출
    예:
      "AT+GMM\r\nFE990\r\nOK"
      "FE990 5G Module"
    """
    # 정규화
    norm = _normalize_resp(resp)
    
    # OK/ERROR 라인 제거하고 명령어 라인 제거
    lines = [ln for ln in norm.split("\n") if ln and ln not in ["OK", "ERROR"] and not ln.startswith("AT")]
    
    if lines:
        return lines[0].strip()
    return None

def get_fe990_gmm(port: Optional[str] = None, at_cmd: Optional[str] = None) -> dict:
    """
    AT+GMM 명령으로 제품 정보 조회
    """
    p = port or DEFAULT_PORT
    cmd = at_cmd or "AT+GMM"

    last_error = None
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = _send_at(p, cmd)
            model = parse_model_info(resp)
            if model is None:
                last_error = {"ok": False, "error": f"응답 파싱 실패: {resp.strip()}", "port": p, "raw": resp}
                continue

            return {
                "ok": True,
                "model": model,
                "port": p,
                "raw": resp
            }

        except RuntimeError as e:
            last_error = {"ok": False, "error": str(e), "port": p}

    return last_error or {"ok": False, "error": "알 수 없는 실패", "port": p}

def parse_temperature(resp: str) -> Optional[dict]:
    """
    AT#TEMPSENS=2 응답에서 온도 정보 추출
    예:
      "#TEMPSENS: TSENS,26"
      "#TEMPSENS: PA_THERM1,24"
    """
    # 정규화
    norm = _normalize_resp(resp)
    
    # 온도 추출 패턴: #TEMPSENS: <센서명>,<온도값>
    pattern = re.compile(r"#TEMPSENS\s*:\s*([A-Z_\d]+)\s*,\s*(-?\d+(?:\.\d+)?)", flags=re.IGNORECASE)
    temperatures = {}
    for line in norm.split("\n"):
        m = pattern.search(line)
        if m:
            try:
                sensor_name = m.group(1)
                temp_value = float(m.group(2))
                temperatures[sensor_name] = temp_value
            except ValueError:
                continue
    
    return temperatures if temperatures else None

def get_fe990_tempsens(port: Optional[str] = None, at_cmd: Optional[str] = None) -> dict:
    """
    AT#TEMPSENS=2 명령으로 온도 정보 조회
    """
    p = port or DEFAULT_PORT
    cmd = at_cmd or "AT#TEMPSENS=2"

    last_error = None
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = _send_at(p, cmd)
            temperatures = parse_temperature(resp)
            if temperatures is None:
                last_error = {"ok": False, "error": f"응답 파싱 실패: {resp.strip()}", "port": p, "raw": resp}
                continue

            return {
                "ok": True,
                "temperatures": temperatures,
                "port": p,
                "raw": resp
            }

        except RuntimeError as e:
            last_error = {"ok": False, "error": str(e), "port": p}

    return last_error or {"ok": False, "error": "알 수 없는 실패", "port": p}

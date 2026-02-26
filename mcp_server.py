

# mcp_uptime_server.py
import sys
import json
import time
import threading
import re
from typing import Optional

import serial  # pip install pyserial
from controller import ATController
from natural import interpret

# ====== 환경 설정 (민욱님 값 반영) ======
SERIAL_PORT = "COM9"
BAUDRATE = 115200
READ_TIMEOUT = 2.0
AT_UPTIME_CMD = "AT#UPTIME=0"

_serial_lock = threading.Lock()
_ser: Optional[serial.Serial] = None


def open_serial():
    """COM 포트를 연다(이미 열려 있으면 재사용)."""
    global _ser
    if _ser and _ser.is_open:
        return
    _ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=READ_TIMEOUT)


def at(cmd: str, timeout: float = 5.0):
    """
    AT 명령을 송신하고, OK/ERROR가 나올 때까지 라인을 수집해 리스트로 반환.
    """
    with _serial_lock:
        open_serial()
        _ser.reset_input_buffer()
        _ser.write((cmd.strip() + "\r\n").encode("ascii", errors="ignore"))
        _ser.flush()

        t0 = time.time()
        lines = []
        while time.time() - t0 < timeout:
            line = _ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            lines.append(line)
            if line == "OK" or line.startswith("ERROR"):
                break
        return lines


def parse_seconds_from_lines(lines) -> Optional[int]:
    """
    응답에서 초(second) 값을 추출해 반환.
    - '200' 같은 순수 숫자 라인 우선
    - '#UPTIME: 7086' 같은 포맷도 정규식으로 커버
    못 찾으면 None
    """
    for line in lines:
        raw = line.strip()
        if raw.isdigit():
            return int(raw)
        m = re.search(r"#UPTIME\s*:\s*(\d+)", raw, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def to_human(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}시간 {m}분 {s}초"


def execute_command(command_text: str, port: str = "COM33"):
    """
    자연어 명령을 해석해서 실행하는 함수
    
    Args:
        command_text: 사용자 입력 자연어 (예: "FE990 리부팅 시켜줘")
        port: 시리얼 포트
    
    Returns:
        dict: 실행 결과
    """
    try:
        # 자연어 해석
        action = interpret(command_text)
        
        if action is None:
            return {
                "ok": False,
                "error": f"명령을 해석할 수 없습니다: '{command_text}'",
                "command": command_text,
                "action": None,
            }
        
        # ATController 실행
        ctl = ATController(port=port)
        
        if not ctl.connect():
            return {
                "ok": False,
                "error": f"장치에 연결할 수 없습니다 ({port})",
                "command": command_text,
                "action": action,
            }
        
        try:
            result_data = {
                "ok": False,
                "command": command_text,
                "action": action,
            }
            
            if action == "power_on":
                success, msg = ctl.power_on()
                result_data["ok"] = success
                result_data["message"] = msg
                result_data["human"] = "전원이 켜졌습니다." if success else f"전원 켜기 실패: {msg}"
            
            elif action == "off":
                success, msg = ctl.off()
                result_data["ok"] = success
                result_data["message"] = msg
                result_data["human"] = "장치가 종료되었습니다." if success else f"종료 실패: {msg}"
            
            elif action == "reboot":
                success, msg = ctl.reboot()
                result_data["ok"] = success
                result_data["message"] = msg
                result_data["human"] = "장치를 재부팅합니다." if success else f"재부팅 실패: {msg}"
            
            elif action == "uptime":
                success, uptime_val, msg = ctl.get_uptime()
                result_data["ok"] = success
                result_data["message"] = msg
                if uptime_val is not None:
                    h = uptime_val // 3600
                    m = (uptime_val % 3600) // 60
                    result_data["uptime_seconds"] = uptime_val
                    result_data["human"] = f"FE990은 현재 {h}시간 {m}분 동안 켜져 있습니다."
                else:
                    result_data["human"] = f"업타임 조회 실패: {msg}"
            
            return result_data
        
        finally:
            ctl.disconnect()
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "command": command_text,
        }


def to_human(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}시간 {m}분 {s}초"


def fe990_uptime(device_id: str):
    """
    1차 시도: AT#UPTIME=0
    실패 시: 짧게 'AT'로 워밍업 후 한 번 더 재시도
    """
    try:
        lines = at(AT_UPTIME_CMD, timeout=5.0)
        secs = parse_seconds_from_lines(lines)

        if secs is None:
            # 워밍업 후 재시도(일부 모듈이 첫 명령에 바로 응답하지 않는 경우 방지)
            at("AT", timeout=1.0)
            time.sleep(0.2)
            lines = at(AT_UPTIME_CMD, timeout=5.0)
            secs = parse_seconds_from_lines(lines)

        if secs is None:
            return {
                "device_id": device_id,
                "seconds": 0,
                "human": "0시간 0분 0초",
                "ok": False,
                "error": "uptime value not found in response",
                "raw": lines,
            }

        return {
            "device_id": device_id,
            "seconds": secs,
            "human": to_human(secs),
            "ok": True,
            "error": None,
            "raw": lines,  # 트러블슈팅용
        }
    except Exception as e:
        return {
            "device_id": device_id,
            "seconds": 0,
            "human": "0시간 0분 0초",
            "ok": False,
            "error": str(e),
            "raw": [],
        }


def get_fe990_uptime_simple():
    """FE990 업타임을 간단히 조회 (fe990_uptime.py 로직 사용)"""
    try:
        import serial
        ser = serial.Serial("COM9", 115200, timeout=1)
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            try:
                ser.dtr = True
                ser.rts = False
            except:
                pass
            
            # keepalive
            ser.write(b"AT\r")
            time.sleep(0.2)
            _ = ser.read(256)
            
            # AT#uptime=1 (hh:mm:ss)
            ser.write(b"AT#uptime=1\r")
            time.sleep(0.6)
            buf = ser.read(4096).decode(errors="ignore")
            time.sleep(0.4)
            buf += ser.read(8192).decode(errors="ignore")
            
            # hh:mm:ss 파싱
            m = re.search(r"(?:^|\r?\n)\s*#?UPTIME\s*:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:\r?\n|$)", buf, re.IGNORECASE)
            if m:
                hh = int(m.group(1))
                mm = int(m.group(2))
                ss = int(m.group(3) or 0)
                seconds = hh*3600 + mm*60 + ss
                return {"ok": True, "seconds": seconds, "human": to_human(seconds)}
            
            # 실패 시 AT#uptime=0 (초 단위)
            ser.write(b"AT#uptime=0\r")
            time.sleep(0.6)
            buf2 = ser.read(4096).decode(errors="ignore")
            time.sleep(0.4)
            buf2 += ser.read(8192).decode(errors="ignore")
            
            for line in buf2.splitlines():
                line = line.strip()
                m = re.match(r"#?UPTIME\s*:\s*(\d+)\b", line, re.IGNORECASE)
                if m:
                    seconds = int(m.group(1))
                    return {"ok": True, "seconds": seconds, "human": to_human(seconds)}
            
            return {"ok": False, "error": "업타임 값을 찾을 수 없습니다"}
        finally:
            ser.close()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_jsonrpc(req: dict):
    rid = req.get("id")
    method = req.get("method")
    params = req.get("params", {}) or {}
    try:
        if method == "uptime":
            device_id = params.get("device_id", "FE990-A")
            result = fe990_uptime(device_id)
            return {"jsonrpc": "2.0", "id": rid, "result": result, "error": None}
        
        elif method == "get_fe990_uptime":
            result = get_fe990_uptime_simple()
            return {"jsonrpc": "2.0", "id": rid, "result": result, "error": None}
        
        elif method == "execute_command":
            command_text = params.get("command", "")
            port = params.get("port", "COM33")
            result = execute_command(command_text, port=port)
            return {"jsonrpc": "2.0", "id": rid, "result": result, "error": None}
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": "Method not found"},
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "error": {"code": -32000, "message": str(e)},
        }


if __name__ == "__main__":
    data = sys.stdin.read().strip()
    if data:
        req = json.loads(data)
        resp = handle_jsonrpc(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False))
        sys.stdout.flush()

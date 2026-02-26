
# filename: at_uptime_0.py
import os
import time
import re
import json
import argparse
import serial

def normalize_port_for_windows(p: str) -> str:
    """
    Windows에서 COM10 이상인 경우 '\\\\.\\COMxx'로 보정
    """
    up = (p or "").strip().upper()
    if up.startswith("COM"):
        try:
            n = int(up[3:])
            if n >= 10 and not up.startswith("\\\\.\\"):
                return f"\\\\.\\{up}"
        except ValueError:
            pass
    return p

def format_uptime(sec: int) -> str:
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    return f"{d} days {h:02d}:{m:02d}:{s:02d}" if d > 0 else f"{h:02d}:{m:02d}:{s:02d}"

def send_cmd(
    ser: serial.Serial,
    cmd: str,
    use_crlf: bool = True,
    wait_s: float = 0.5,
    total_read_s: float = 10.0
) -> bytes:
    line = cmd + ("\r\n" if use_crlf else "\r")
    ser.write(line.encode("ascii"))
    ser.flush()
    time.sleep(wait_s)

    buf = bytearray()
    deadline = time.time() + total_read_s
    while time.time() < deadline:
        n = ser.in_waiting
        if n:
            chunk = ser.read(n)
            if chunk:
                buf.extend(chunk)
                text = buf.decode(errors="ignore")
                if ("OK" in text) or ("ERROR" in text):
                    break
        else:
            time.sleep(0.05)

    return bytes(buf)

def parse_uptime(text: str) -> int | None:
    """
    '#UPTIME: 15618' 형태에서 초(sec)를 추출
    """
    m = re.search(r"#UPTIME:\s*(\d+)", text)
    return int(m.group(1)) if m else None

def query_uptime(port: str, baud: int = 115200, timeout: float = 2.0) -> dict:
    """
    FE990 모뎀에 AT#uptime=0 전송 후 결과를 반환.
    Returns: { 'port': str, 'baud': int, 'seconds': int|None, 'text': str, 'ok': bool }
    """
    ser = serial.Serial(
        port, baud,
        timeout=timeout, write_timeout=timeout,
        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        rtscts=False, dsrdtr=False
    )
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        raw = send_cmd(ser, "AT#uptime=0", use_crlf=True, wait_s=0.5, total_read_s=10.0)
        txt = raw.decode("ascii", errors="ignore")
        sec = parse_uptime(txt)
        return {
            "port": port,
            "baud": baud,
            "seconds": sec,
            "text": txt.strip(),
            "ok": (sec is not None) and ("OK" in txt)
        }
    finally:
        ser.close()

def main():
    ap = argparse.ArgumentParser(description="FE990 uptime query (AT#uptime=0)")
    ap.add_argument("--port", help="COM port (e.g., COM36). Overrides AT_PORT env.")
    ap.add_argument("--baud", type=int, default=115200, help="baud rate (default: 115200)")
    ap.add_argument("--json", action="store_true", help="output JSON for automation")
    ap.add_argument("--quiet", action="store_true", help="suppress debug prints")

    args = ap.parse_args()

    env_port = os.getenv("AT_PORT", "COM33")
    port = normalize_port_for_windows(args.port or env_port)

    
    if not args.quiet:
        print("[DEBUG] __file__   =", __file__)
        print("[DEBUG] AT_PORT ENV =", env_port if args.port is None else f"{env_port} (overridden by --port)")
        print("[DEBUG] Using PORT  =", port, "| BAUD =", args.baud)


    res = query_uptime(port, baud=args.baud)

    if args.json:
        print(json.dumps({
            "port": res["port"],
            "baud": res["baud"],
            "seconds": res["seconds"],
            "formatted": (format_uptime(res["seconds"]) if res["seconds"] is not None else None),
            "ok": res["ok"]
        }, ensure_ascii=False))
    else:
        print("[TXT]")
        print(res["text"])
        if res["seconds"] is not None:
            print("[UPTIME]", format_uptime(res["seconds"]))
        else:
            print("[UPTIME] (parse failed)")
        print("[STATUS]", "OK" if res["ok"] else "NOT OK")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
# at_agent.py — CLI 어댑터 (액션 받아 AT 실행 → JSON 한 줄 출력)

import argparse, json, time
import serial

DEFAULT_PORT = "COM33"
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 2.0

CMD_MAP = {
    "uptime": "AT#uptime=0",
    "ping": "AT",
}

def send_cmd(ser, cmd: str, use_crlf: bool = True, wait_s: float = 0.5, total_read_s: float = 10.0):
    line = cmd + ("\r\n" if use_crlf else "\r")
    ser.write(line.encode("ascii")); ser.flush()
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

def main():
    p = argparse.ArgumentParser(description="AT MCP Adapter (mini)")
    p.add_argument("--action", choices=["uptime","ping"], required=True)
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p.add_argument("--use_crlf", action="store_true")
    args = p.parse_args()

    cmd = CMD_MAP[args.action]
    t0 = time.time()

    ser = serial.Serial(
        args.port, args.baud,
        timeout=args.timeout, write_timeout=args.timeout,
        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, rtscts=False, dsrdtr=False
    )
    ser.reset_input_buffer(); ser.reset_output_buffer()

    raw = send_cmd(ser, cmd, use_crlf=args.use_crlf, wait_s=0.5, total_read_s=10.0)
    ser.close()

    txt = raw.decode(errors="ignore").strip() if raw else ""
    status = "success" if (raw and ("OK" in txt)) else ("no_data" if not raw else "pending")

    # uptime 숫자 파싱
    uptime_val = None
    if args.action == "uptime" and txt:
        import re
        m = re.search(r"#UPTIME:\s*(\d+)", txt)
        if m:
            uptime_val = int(m.group(1))

    out = {
        "action": args.action,
        "status": status,
        "raw": raw.decode("latin1", errors="ignore") if raw else "",
        "text": txt,
        "uptime": uptime_val,
        "elapsed_ms": int((time.time() - t0) * 1000)
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()

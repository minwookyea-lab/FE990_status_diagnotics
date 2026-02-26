"""
FE990 제어 HTTP API 서버
"""

from flask import Flask, jsonify, render_template_string
import serial
import time
import re

app = Flask(__name__)

PORT = "COM9"
BAUD = 115200

def parse_seconds_from_hms(text: str):
    m = re.search(r"(?:^|\r?\n)\s*#?UPTIME\s*:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:\r?\n|$)", text, re.IGNORECASE)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2)); ss = int(m.group(3) or 0)
    return hh*3600 + mm*60 + ss

def parse_seconds_from_decimal(text: str):
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"#?UPTIME\s*:\s*(\d+)\b", line, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None

def humanize(seconds: int):
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}일")
    if h: parts.append(f"{h}시간")
    if m: parts.append(f"{m}분")
    if s or not parts: parts.append(f"{s}초")
    return " ".join(parts)

def get_fe990_uptime():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        try:
            ser.dtr = True
            ser.rts = False
        except:
            pass
        
        ser.write(b"AT\r")
        time.sleep(0.2)
        _ = ser.read(256)
        
        ser.write(b"AT#uptime=1\r")
        time.sleep(0.6)
        buf = ser.read(4096).decode(errors="ignore")
        time.sleep(0.4)
        buf += ser.read(8192).decode(errors="ignore")
        
        seconds = parse_seconds_from_hms(buf)
        if seconds is None:
            ser.write(b"AT#uptime=0\r")
            time.sleep(0.6)
            buf2 = ser.read(4096).decode(errors="ignore")
            time.sleep(0.4)
            buf2 += ser.read(8192).decode(errors="ignore")
            seconds = parse_seconds_from_decimal(buf2)
        
        ser.close()
        
        if seconds is not None:
            return {"ok": True, "seconds": seconds, "human": humanize(seconds)}
        else:
            return {"ok": False, "error": "업타임 값을 파싱할 수 없습니다"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fe990_reboot():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(b"AT#reboot\r\n")
        ser.flush()
        time.sleep(1)
        response = ser.read(256).decode(errors="ignore")
        ser.close()
        return {"ok": True, "message": "재부팅 명령을 전송했습니다", "response": response.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fe990_off():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(b"AT#shdn\r\n")
        ser.flush()
        time.sleep(1)
        response = ser.read(256).decode(errors="ignore")
        ser.close()
        return {"ok": True, "message": "종료 명령을 전송했습니다", "response": response.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route('/uptime')
def uptime_api():
    result = get_fe990_uptime()
    return jsonify(result)

@app.route('/reboot')
def reboot_api():
    result = fe990_reboot()
    return jsonify(result)

@app.route('/off')
def off_api():
    result = fe990_off()
    return jsonify(result)

@app.route('/')
def home():
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FE990 제어</title>
    <style>
        body { font-family: "Segoe UI", sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 30px; }
        .button-group { display: flex; gap: 10px; margin-bottom: 20px; }
        button { flex: 1; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; }
        .btn-primary { background: #0078d4; } .btn-primary:hover { background: #106ebe; }
        .btn-warning { background: #ff8c00; } .btn-warning:hover { background: #e67e00; }
        .btn-danger { background: #dc3545; } .btn-danger:hover { background: #c82333; }
        #result { margin-top: 20px; padding: 15px; border-radius: 5px; font-size: 18px; font-weight: bold; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .loading { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>FE990 제어</h1>
        <div class="button-group">
            <button class="btn-primary" onclick="getUptime()">업타임 조회</button>
            <button class="btn-warning" onclick="reboot()">재부팅</button>
            <button class="btn-danger" onclick="turnOff()">종료</button>
        </div>
        <div id="result"></div>
    </div>
    <script>
        async function getUptime() {
            const r = document.getElementById("result");
            r.className = "loading"; r.textContent = "조회 중...";
            try {
                const res = await fetch("/uptime");
                const data = await res.json();
                if (data.ok) { r.className = "success"; r.textContent = `FE990 업타임: ${data.human} (총 ${data.seconds}초)`; }
                else { r.className = "error"; r.textContent = `오류: ${data.error}`; }
            } catch (e) { r.className = "error"; r.textContent = `오류: ${e.message}`; }
        }
        async function reboot() {
            if (!confirm("FE990을 재부팅하시겠습니까?")) return;
            const r = document.getElementById("result");
            r.className = "loading"; r.textContent = "재부팅 중...";
            try {
                const res = await fetch("/reboot");
                const data = await res.json();
                if (data.ok) { r.className = "success"; r.textContent = data.message; }
                else { r.className = "error"; r.textContent = `오류: ${data.error}`; }
            } catch (e) { r.className = "error"; r.textContent = `오류: ${e.message}`; }
        }
        async function turnOff() {
            if (!confirm("FE990을 종료하시겠습니까?")) return;
            const r = document.getElementById("result");
            r.className = "loading"; r.textContent = "종료 중...";
            try {
                const res = await fetch("/off");
                const data = await res.json();
                if (data.ok) { r.className = "success"; r.textContent = data.message; }
                else { r.className = "error"; r.textContent = `오류: ${data.error}`; }
            } catch (e) { r.className = "error"; r.textContent = `오류: ${e.message}`; }
        }
    </script>
</body>
</html>'''
    return render_template_string(html)

if __name__ == '__main__':
    print("=" * 60)
    print("FE990 제어 API 서버")
    print("=" * 60)
    print("http://localhost:8000/")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8000, debug=False)

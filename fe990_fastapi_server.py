# fe990_fastapi_server.py
# FE990 제어 HTTP API 서버 (FastAPI 버전)
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import os, re, time
import serial

# ========= 설정 =========
PORT = os.getenv("FE990_PORT", "COM9")      # 필요 시 환경변수로 변경 가능
BAUD = int(os.getenv("FE990_BAUD", "115200"))

app = FastAPI(title="FE990 Control API", version="1.0")

# ========= 유틸 =========
def humanize(seconds: int) -> str:
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}일")
    if h: parts.append(f"{h}시간")
    if m: parts.append(f"{m}분")
    if s or not parts: parts.append(f"{s}초")
    return " ".join(parts)

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

def read_all(ser, idle=0.25, max_wait=2.0):
    """수신이 잠잠해질 때까지 모아서 반환"""
    buf = b''
    deadline = time.time() + max_wait
    while True:
        n = ser.in_waiting
        chunk = ser.read(n or 1)
        if chunk:
            buf += chunk
            deadline = time.time() + idle
        else:
            if time.time() > deadline:
                break
            time.sleep(0.01)
    return buf.decode(errors="ignore")

def send_at(ser, cmd, wait=1.0):
    """AT 전송 후 응답 모으기"""
    if not cmd.endswith("\r"):
        cmd = cmd + "\r"
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(cmd.encode())
    ser.flush()
    time.sleep(0.05)
    return read_all(ser, idle=0.2, max_wait=wait)

# ========= FE990 동작 =========
def get_fe990_uptime():
    try:
        with serial.Serial(PORT, BAUD, timeout=1) as ser:
            try:
                ser.dtr = True
                ser.rts = False
            except Exception:
                pass

            _ = send_at(ser, "AT", wait=0.6)
            buf = send_at(ser, "AT#uptime=1", wait=1.5)
            # 진단 로그(필요 시 주석 해제)
            # print("[debug] uptime=1 raw:", repr(buf))
            seconds = parse_seconds_from_hms(buf)

            if seconds is None:
                buf2 = send_at(ser, "AT#uptime=0", wait=1.5)
                # print("[debug] uptime=0 raw:", repr(buf2))
                seconds = parse_seconds_from_decimal(buf2)

        if seconds is not None:
            return {"ok": True, "seconds": seconds, "human": humanize(seconds)}
        else:
            return {"ok": False, "error": "업타임 값을 파싱할 수 없습니다"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fe990_reboot():
    try:
        with serial.Serial(PORT, BAUD, timeout=2) as ser:
            resp = send_at(ser, "AT#reboot", wait=1.0)
        return {"ok": True, "message": "재부팅 명령을 전송했습니다", "response": resp.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fe990_off():
    try:
        with serial.Serial(PORT, BAUD, timeout=2) as ser:
            resp = send_at(ser, "AT#shdn", wait=1.0)
        return {"ok": True, "message": "종료 명령을 전송했습니다", "response": resp.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ========= 엔드포인트 =========
@app.get("/health")
def health():
    return {"status": "ok", "port": PORT, "baud": BAUD}

@app.get("/uptime")
def uptime_api():
    result = get_fe990_uptime()
    if result.get("ok"):
        return result
    return JSONResponse(status_code=500, content=result)

# 호환 라우트 (이전 습관 유지용)
@app.get("/status/uptime")
def uptime_compat():
    return uptime_api()

@app.get("/reboot")
def reboot_api():
    result = fe990_reboot()
    if result.get("ok"):
        return result
    return JSONResponse(status_code=500, content=result)

@app.get("/off")
def off_api():
    result = fe990_off()
    if result.get("ok"):
        return result
    return JSONResponse(status_code=500, content=result)

@app.get("/", response_class=HTMLResponse)
def home():
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>FE990 제어</title>
<style>
body{font-family:Segoe UI, sans-serif; max-width:680px; margin:40px auto; padding:20px; background:#f5f5f5}
.container{background:#fff; padding:28px; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,.08)}
h1{color:#333; margin-bottom:20px}
.button-group{display:flex; gap:10px; margin-bottom:16px}
button{flex:1; color:#fff; border:none; padding:12px 18px; font-size:15px; border-radius:6px; cursor:pointer}
.btn-primary{background:#0078d4}.btn-primary:hover{background:#106ebe}
.btn-warning{background:#ff8c00}.btn-warning:hover{background:#e67e00}
.btn-danger{background:#dc3545}.btn-danger:hover{background:#c82333}
#result{margin-top:14px; padding:12px; border-radius:5px; font-size:16px; font-weight:600}
.success{background:#d4edda; color:#155724}
.error{background:#f8d7da; color:#721c24}
.loading{background:#fff3cd; color:#856404}
small{color:#777}
</style></head>
<body><div class="container">
<h1>FE990 제어</h1>
<small>포트: {{PORT}} / 보레이트: {{BAUD}}</small>
<div class="button-group">
<button class="btn-primary" onclick="getUptime()">업타임 조회</button>
<button class="btn-warning" onclick="reboot()">재부팅</button>
<button class="btn-danger" onclick="turnOff()">종료</button>
</div>
<div id="result"></div>
</div>
<script>
async function getUptime(){const r=document.getElementById("result");r.className="loading";r.textContent="조회 중...";
  try{const res=await fetch("/uptime");const data=await res.json();
    if(data.ok){r.className="success";r.textContent=`FE990 업타임: ${data.human} (총 ${data.seconds}초)`}
    else{r.className="error";r.textContent=`오류: ${data.error}`}
  }catch(e){r.className="error";r.textContent=`오류: ${e.message}`}}
async function reboot(){if(!confirm("FE990을 재부팅하시겠습니까?")) return;
  const r=document.getElementById("result");r.className="loading";r.textContent="재부팅 중...";
  try{const res=await fetch("/reboot");const data=await res.json();
    if(data.ok){r.className="success";r.textContent=data.message}
    else{r.className="error";r.textContent=`오류: ${data.error}`}
  }catch(e){r.className="error";r.textContent=`오류: ${e.message}`}}
async function turnOff(){if(!confirm("FE990을 종료하시겠습니까?")) return;
  const r=document.getElementById("result");r.className="loading";r.textContent="종료 중...";
  try{const res=await fetch("/off");const data=await res.json();
    if(data.ok){r.className="success";r.textContent=data.message}
    else{r.className="error";r.textContent=`오류: ${data.error}`}
  }catch(e){r.className="error";r.textContent=`오류: ${e.message}`}}
</script>
</body></html>"""
    return HTMLResponse(html.replace("{{PORT}}", PORT).replace("{{BAUD}}", str(BAUD)))
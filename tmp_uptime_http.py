
# tmp_uptime_http.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="TEMP Uptime Server", version="0.1")

@app.get("/uptime")
def uptime(port: str = "COM33"):
    # 임시 응답(서버 살아있는지 확인용)
    return JSONResponse({
        "ok": True,
        "message": f"(\\.\{port}) 장비 업타임은 00:21:34 (총 1294초) 입니다. [TEMP]",
        "data": {
            "port": f"\\.\{port}",
            "baud": 115200,
            "seconds": 1294,
            "formatted": "00:21:34"
        }
    })

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)

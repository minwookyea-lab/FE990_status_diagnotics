
#!/usr/bin/env python3
# filename: mcp_mock.py

import json
import subprocess
import sys
import re  # (선택) 포트 추출용

def extract_json_from_stdout(stdout: str) -> str | None:
    """
    stdout에 디버그 텍스트가 섞여 있어도
    - 줄 단위로 훑어서 '{'로 시작하고 '}'로 끝나는 라인을 JSON으로 간주
    - 못 찾으면 전체에서 첫 '{'와 마지막 '}' 사이를 슬라이스
    """
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):  # 보통 JSON이 마지막 줄
        if line.startswith("{") and line.endswith("}"):
            return line
    # fallback: 전체에서 중괄호 범위 추출
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stdout[start:end+1]
    return None

def run_uptime(port: str | None = None):
    # ✅ 변경: 현재 파이썬으로 실행 + 조용한 모드
    cmd = [sys.executable, "at_uptime_0.py", "--json", "--quiet"]
    if port:
        cmd.extend(["--port", port])
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        return False, f"[실행 실패] {proc.stderr or proc.stdout}"

    json_text = extract_json_from_stdout(proc.stdout)
    if not json_text:
        # 디버그 원문을 보여주면 문제 파악이 쉬움
        return False, f"[JSON 추출 실패]\nstdout={proc.stdout}"

    try:
        data = json.loads(json_text)
    except Exception as e:
        return False, f"[JSON 파싱 실패] {e}\njson_text={json_text}\nstdout={proc.stdout}"

    if not data.get("ok"):
        return False, "[응답 비정상] 장비가 OK를 주지 않았습니다."

    seconds = data.get("seconds")
    formatted = data.get("formatted")
    port_info = data.get("port")
    return True, f"({port_info}) 장비 업타임은 {formatted} (총 {seconds}초) 입니다."

# (선택) 자연어에서 포트 추출
def extract_port_from_text(text: str) -> str | None:
    m = re.search(r"(COM\d+)", text, re.IGNORECASE)
    return m.group(1) if m else None

def main():
    user = " ".join(sys.argv[1:]).strip()
    if not user:
        print("예) python mcp_mock.py 업타임 알려줘")
        return

    low = user.lower()
    if ("업타임" in user) or ("uptime" in low):
        # (선택) 문장에 COM포트가 있으면 사용
        port = extract_port_from_text(user)
        ok, msg = run_uptime(port=port)
        print(msg)
    else:
        print("지금은 '업타임' 요청만 지원합니다. (예: 업타임 알려줘 / COM33 업타임 알려줘)")

if __name__ == "__main__":
    main()

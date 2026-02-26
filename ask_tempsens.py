
# ask_tempsens.py
import json
import subprocess
import sys
import os

CLI = os.getenv("FE990_CLI_PATH", "python cli_tool.py")
PORT = os.getenv("FE990_PORT", "COM9")
CMD  = os.getenv("FE990_TEMPSENS_CMD", "AT#TEMPSENS=2")

def main():
    # cli_tool.py 실행 → JSON 한 줄 받기
    proc = subprocess.run(
        f'{CLI} --action tempsens --port {PORT} --cmd "{CMD}"',
        shell=True, capture_output=True, text=True
    )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    if proc.returncode != 0:
        msg = "[실패] 온도 정보를 읽지 못했습니다."
        if stderr:
            msg += f" (stderr: {stderr})"
        print(msg)
        sys.exit(1)

    # 성공 케이스: JSON 파싱
    try:
        data = json.loads(stdout.splitlines()[-1])  # 마지막 줄을 JSON으로 가정
    except json.JSONDecodeError:
        print(f"[실패] JSON 파싱 오류. 출력:\n{stdout}")
        sys.exit(1)

    if not data.get("ok"):
        print("[실패] 장비에서 ok=false 반환")
        sys.exit(1)

    temperatures = data.get("temperatures")

    # 사람 말로 답하기
    if temperatures:
        print("FE990 현재 온도:")
        for sensor, temp in temperatures.items():
            print(f"  {sensor}: {temp}°C")
    else:
        print("온도 정보를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()

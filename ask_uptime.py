
# ask_uptime.py
import json
import subprocess
import sys
import os

CLI = os.getenv("FE990_CLI_PATH", "python cli_tool.py")
PORT = os.getenv("FE990_PORT", "COM9")
CMD  = os.getenv("FE990_UPTIME_CMD", "AT#UPTIME=0")

def main():
    # cli_tool.py 실행 → JSON 한 줄 받기
    proc = subprocess.run(
        f'{CLI} --action uptime --port {PORT} --cmd "{CMD}"',
        shell=True, capture_output=True, text=True
    )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    if proc.returncode != 0:
        # 현재 cli_tool.py는 실패 시 사람이 읽는 문장/RAW를 출력하므로
        # 우선 간단히 에러만 전달
        msg = "[실패] uptime을 읽지 못했습니다."
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

    seconds = data.get("seconds")
    human = data.get("human")

    # 사람 말로 답하기
    if human:
        print(f"FE990는 지금 {human} 동안 켜져 있어요. (총 {seconds}초)")
    else:
        # 혹시 human이 없는 경우 대비
        s = seconds or 0
        h, m, sec = s // 3600, (s % 3600) // 60, s % 60
        print(f"FE990는 지금 {h}시간 {m}분 {sec}초 동안 켜져 있어요. (총 {s}초)")

if __name__ == "__main__":
    main()

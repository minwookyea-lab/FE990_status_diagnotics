
import json
import argparse
from uptime_service import get_fe990_uptime, get_fe990_gmm, get_fe990_tempsens

def main():
    parser = argparse.ArgumentParser(description="FE990 CLI Tool")
    parser.add_argument("--action", required=True, choices=["uptime", "gmm", "tempsens"], help="실행할 액션")
    parser.add_argument("--port", default="COM9", help="시리얼 포트 (예: COM9, \\\\.\\COM10, /dev/ttyUSB0)")
    parser.add_argument("--cmd", default="AT#UPTIME=0", help="AT 명령 (기본: AT#UPTIME=0)")
    args = parser.parse_args()

    if args.action == "uptime":
        result = get_fe990_uptime(port=args.port, at_cmd=args.cmd)
        if result["ok"]:
            print(json.dumps({
                "ok": True,
                "seconds": result["seconds"],
                "human": result["human"]
            }, ensure_ascii=False))
        else:
            print(f"[실패] {result['error']}")
            if "raw" in result:
                print("RAW 응답:\n" + result["raw"])
    
    elif args.action == "gmm":
        result = get_fe990_gmm(port=args.port, at_cmd=args.cmd)
        if result["ok"]:
            print(json.dumps({
                "ok": True,
                "model": result["model"]
            }, ensure_ascii=False))
        else:
            print(f"[실패] {result['error']}")
            if "raw" in result:
                print("RAW 응답:\n" + result["raw"])
    
    elif args.action == "tempsens":
        result = get_fe990_tempsens(port=args.port, at_cmd=args.cmd)
        if result["ok"]:
            print(json.dumps({
                "ok": True,
                "temperatures": result["temperatures"]
            }, ensure_ascii=False))
        else:
            print(f"[실패] {result['error']}")
            if "raw" in result:
                print("RAW 응답:\n" + result["raw"])

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FE990 다중 제어 스크립트
업타임 조회, reboot, off를 동시에 또는 순차적으로 실행
"""

import sys
import re
import time
import threading
from typing import Optional, Dict, Tuple

# FE990 업타임 조회용 (COM9)
FE990_PORT = "COM9"
FE990_BAUD = 115200
FE990_CMD_PRIMARY = "AT#uptime=1\r"
FE990_CMD_FALLBACK = "AT#uptime=0\r"

# AT 제어용 (COM33)
AT_CONTROL_PORT = "COM33"
AT_CONTROL_BAUD = 115200
AT_REBOOT_CMD = "AT#reboot"
AT_OFF_CMD = "AT#shdn"


def parse_seconds_from_hms(text: str):
    """
    '#UPTIME: hh:mm:ss' 형식을 초로 변환
    """
    m = re.search(r"(?:^|\r?\n)\s*#?UPTIME\s*:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:\r?\n|$)", text, re.IGNORECASE)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2)); ss = int(m.group(3) or 0)
    return hh*3600 + mm*60 + ss


def parse_seconds_from_decimal(text: str):
    """
    '#UPTIME: 9164' 형식을 초로 변환
    """
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"#?UPTIME\s*:\s*(\d+)\b", line, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def humanize(seconds: int):
    """초 단위를 인간이 읽을 수 있는 형식으로 변환"""
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}일")
    if h: parts.append(f"{h}시간")
    if m: parts.append(f"{m}분")
    if s or not parts: parts.append(f"{s}초")
    return " ".join(parts)


def query_uptime(port: str, baud: int, cmd: str) -> Optional[str]:
    """FE990 업타임 조회"""
    try:
        import serial
        ser = serial.Serial(port, baud, timeout=1)
        try:
            ser.reset_input_buffer(); ser.reset_output_buffer()
            try:
                ser.dtr = True
                ser.rts = False
            except Exception:
                pass

            ser.write(b"AT\r")
            time.sleep(0.2)
            _ = ser.read(256)

            ser.write(cmd.encode("ascii"))
            time.sleep(0.6)
            buf = ser.read(4096).decode(errors="ignore")
            time.sleep(0.4)
            buf += ser.read(8192).decode(errors="ignore")
            return buf
        finally:
            ser.close()
    except Exception as e:
        print(f"[ERROR] 업타임 조회 실패 ({port}): {e}", file=sys.stderr)
        return None


def send_at_cmd(port: str, baud: int, cmd: str, use_crlf: bool = True) -> Tuple[bool, str]:
    """AT 커맨드 송신"""
    try:
        import serial
        ser = serial.Serial(
            port, baud,
            timeout=2, write_timeout=2,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            rtscts=False, dsrdtr=False
        )

        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            line = cmd + ("\r\n" if use_crlf else "\r")
            ser.write(line.encode("ascii"))
            ser.flush()

            time.sleep(0.5)
            buf = bytearray()
            deadline = time.time() + 5.0
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

            response = bytes(buf).decode(errors="ignore").strip()
            success = "OK" in response or "OK" in response.upper()
            return success, response
        finally:
            ser.close()
    except Exception as e:
        return False, str(e)


class MultiControl:
    """FE990 업타임, reboot, off 동시 제어"""
    
    def __init__(self):
        self.results: Dict[str, any] = {}
        self.lock = threading.Lock()
    
    def _get_uptime_thread(self):
        """업타임 조회 스레드"""
        try:
            buf = query_uptime(FE990_PORT, FE990_BAUD, FE990_CMD_PRIMARY)
            if not buf:
                with self.lock:
                    self.results["uptime"] = ("ERROR", "포트 열기 실패")
                return

            seconds = parse_seconds_from_hms(buf)
            if seconds is None:
                buf2 = query_uptime(FE990_PORT, FE990_BAUD, FE990_CMD_FALLBACK)
                if buf2:
                    seconds = parse_seconds_from_decimal(buf2)

            with self.lock:
                if seconds is not None:
                    self.results["uptime"] = ("OK", f"{humanize(seconds)} (총 {seconds}초)")
                else:
                    self.results["uptime"] = ("PARSE_ERROR", "업타임 파싱 실패")
        except Exception as e:
            with self.lock:
                self.results["uptime"] = ("ERROR", str(e))
    
    def _reboot_thread(self):
        """reboot 커맨드 스레드"""
        try:
            success, response = send_at_cmd(AT_CONTROL_PORT, AT_CONTROL_BAUD, AT_REBOOT_CMD)
            with self.lock:
                status = "OK" if success else "FAILED"
                self.results["reboot"] = (status, response)
        except Exception as e:
            with self.lock:
                self.results["reboot"] = ("ERROR", str(e))
    
    def _off_thread(self):
        """off 커맨드 스레드"""
        try:
            success, response = send_at_cmd(AT_CONTROL_PORT, AT_CONTROL_BAUD, AT_OFF_CMD)
            with self.lock:
                status = "OK" if success else "FAILED"
                self.results["off"] = (status, response)
        except Exception as e:
            with self.lock:
                self.results["off"] = ("ERROR", str(e))
    
    def run_all(self):
        """모든 명령을 동시에 실행"""
        print("[INFO] 업타임, reboot, off를 동시에 실행합니다...")
        print()

        threads = []
        
        # 업타임 조회 스레드
        t1 = threading.Thread(target=self._get_uptime_thread, daemon=False)
        threads.append(t1)
        t1.start()
        
        # Reboot 스레드 (1초 딜레이)
        time.sleep(1)
        t2 = threading.Thread(target=self._reboot_thread, daemon=False)
        threads.append(t2)
        t2.start()
        
        # Off 스레드 (또 다른 1초 딜레이)
        time.sleep(1)
        t3 = threading.Thread(target=self._off_thread, daemon=False)
        threads.append(t3)
        t3.start()

        # 모든 스레드 완료 대기
        for t in threads:
            t.join(timeout=15)

        # 결과 출력
        self._print_results()
    
    def run_sequential(self):
        """모든 명령을 순차적으로 실행"""
        print("[INFO] 업타임, reboot, off를 순차적으로 실행합니다...")
        print()

        # 1. 업타임 조회
        print("[1/3] 업타임 조회 중...")
        self._get_uptime_thread()
        print()

        # 2. Reboot
        print("[2/3] Reboot 명령 송신 중...")
        self._reboot_thread()
        time.sleep(2)
        print()

        # 3. Off
        print("[3/3] Off 명령 송신 중...")
        self._off_thread()
        print()

        # 결과 출력
        self._print_results()
    
    def _print_results(self):
        """결과 출력"""
        print("\n" + "="*60)
        print("[결과]")
        print("="*60)
        
        if "uptime" in self.results:
            status, msg = self.results["uptime"]
            print(f"[업타임] {status}: {msg}")
        
        if "reboot" in self.results:
            status, msg = self.results["reboot"]
            print(f"[Reboot] {status}: {msg}")
        
        if "off" in self.results:
            status, msg = self.results["off"]
            print(f"[Off]    {status}: {msg}")
        
        print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FE990 다중 제어 (업타임, reboot, off)")
    parser.add_argument(
        "--mode",
        choices=["concurrent", "sequential"],
        default="concurrent",
        help="실행 모드: concurrent(동시), sequential(순차)"
    )
    
    args = parser.parse_args()
    
    controller = MultiControl()
    
    if args.mode == "sequential":
        controller.run_sequential()
    else:
        controller.run_all()

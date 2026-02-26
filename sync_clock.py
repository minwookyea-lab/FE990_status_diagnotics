#!/usr/bin/env python3
"""Sync FE990 system clock to current time"""

from controller import ATController
from datetime import datetime, timezone, timedelta

controller = ATController(port="COM9")

try:
    if not controller.connect():
        print("❌ 연결 실패")
        exit(1)
    
    # Get current Korea time (UTC+9)
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    
    # Format: YY/MM/DD,HH:MM:SS+09
    time_str = now.strftime("%y/%m/%d,%H:%M:%S+09")
    
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S KST')}")
    print(f"설정 명령: AT+CCLK=\"{time_str}\"")
    
    # Set clock
    response = controller.send_cmd(f'AT+CCLK="{time_str}"', wait_s=0.5)
    decoded = response.decode('ascii', errors='ignore')
    
    if "OK" in decoded:
        print("✅ 시스템 시간 설정 완료")
        
        # Verify
        response = controller.send_cmd("AT+CCLK?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        print(f"\n확인: {decoded.strip()}")
    else:
        print(f"❌ 설정 실패: {decoded}")
    
finally:
    controller.disconnect()

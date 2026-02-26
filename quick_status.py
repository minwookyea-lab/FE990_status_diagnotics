#!/usr/bin/env python3
"""Quick status check with smart summary"""

from mcp_get_full_status import get_full_status
from controller import ATController
from build_summary import build_summary

controller = ATController(port="COM9")

try:
    if not controller.connect():
        print("❌ 연결 실패")
        exit(1)
    
    result = get_full_status(controller)
    summary = build_summary(result['full_status'], verbose=True)
    print(summary)
    
finally:
    controller.disconnect()

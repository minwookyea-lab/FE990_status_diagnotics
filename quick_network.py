#!/usr/bin/env python3
"""네트워크 상태 즉시 조회"""
from controller import ATController
from network_status import get_network_status, print_network_status

controller = ATController(port="COM9")
try:
    if controller.connect():
        status = get_network_status(controller)
        print_network_status(status)
        controller.disconnect()
    else:
        print("연결 실패")
except Exception as e:
    print(f"오류: {e}")
    controller.disconnect()

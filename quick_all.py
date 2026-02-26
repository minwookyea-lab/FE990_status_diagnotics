#!/usr/bin/env python3
"""모뎀 전체 정보 즉시 조회"""
from controller import ATController
from modem_chat import ModemNaturalInterface

controller = ATController(port="COM9")
try:
    if controller.connect():
        interface = ModemNaturalInterface(controller)
        interface.handle_query("전체 상태")
        controller.disconnect()
    else:
        print("연결 실패")
except Exception as e:
    print(f"오류: {e}")
    controller.disconnect()

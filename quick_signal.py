#!/usr/bin/env python3
"""신호품질 즉시 조회"""
from controller import ATController
from modem_chat import ModemNaturalInterface

controller = ATController(port="COM9")
try:
    if controller.connect():
        interface = ModemNaturalInterface(controller)
        interface.handle_query("신호품질 어때?")
        controller.disconnect()
    else:
        print("연결 실패")
except Exception as e:
    print(f"오류: {e}")
    controller.disconnect()

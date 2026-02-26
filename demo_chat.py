#!/usr/bin/env python3
"""
FE990 모뎀 자연어 쿼리 데모
"""

from controller import ATController
from modem_chat import ModemNaturalInterface


def demo():
    """자연어 쿼리 데모"""
    print("=" * 60)
    print("FE990 자연어 인터페이스 데모")
    print("=" * 60)
    
    # 연결
    controller = ATController(port="COM9")
    
    try:
        print("\n[연결 중...]")
        if not controller.connect():
            print("❌ 연결 실패")
            return
        
        print("✅ 연결 성공\n")
        
        # 인터페이스 생성
        interface = ModemNaturalInterface(controller)
        
        # 자연어 질문 예시
        queries = [
            "모뎀 상태 보여줘",
            "신호 품질 어때?",
            "네트워크 연결됐어?",
            "CPU 사용률은?",
        ]
        
        for query in queries:
            print("\n" + "🗣️  " + query)
            print("-" * 60)
            interface.handle_query(query)
            print()
            input("다음으로... (Enter)")
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
    
    finally:
        controller.disconnect()
        print("\n[연결 해제]")


if __name__ == "__main__":
    demo()

#!/usr/bin/env python3
"""
FE990 모뎀 자연어 인터페이스
자연어로 질문하면 모뎀 정보를 조회
"""

from controller import ATController
from modem_status import (
    get_signal_quality, get_temperature, get_voltage,
    get_network_registration, get_operator, get_device_info,
    get_modem_status, print_modem_status
)
import re


class ModemNaturalInterface:
    """자연어로 모뎀 정보 조회하는 인터페이스"""
    
    def __init__(self, controller):
        self.controller = controller
        
        # 키워드 매핑
        self.keyword_map = {
            'signal': ['신호', '시그널', 'signal', 'rssi', '신호품질', '신호강도'],
            'temperature': ['온도', 'temp', 'temperature', '열', '뜨거'],
            'voltage': ['전압', '배터리', 'voltage', 'battery', 'power', '전원', '충전'],
            'network': ['네트워크', 'network', '망', '등록', '연결', 'registration'],
            'operator': ['통신사', '오퍼레이터', 'operator', 'carrier', '이통사', 'skt', 'kt', 'lgu'],
            'device': ['장치', '모델', 'device', 'model', 'imei', '기기', '정보'],
            'status': ['상태', 'status', '전체', '모두', 'all', '전반'],
            'cpu': ['cpu', '씨피유', '프로세서', '사용률'],
        }
    
    def parse_query(self, query):
        """자연어 질의를 분석하여 의도 파악"""
        query = query.lower().strip()
        
        # 각 카테고리별 점수 계산
        scores = {}
        for category, keywords in self.keyword_map.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                scores[category] = score
        
        if not scores:
            return 'status'  # 기본값: 전체 상태
        
        # 가장 높은 점수의 카테고리 반환
        return max(scores, key=scores.get)
    
    def handle_query(self, query):
        """자연어 질의 처리"""
        intent = self.parse_query(query)
        
        print(f"\n[인식된 요청: {intent.upper()}]")
        print("=" * 60)
        
        if intent == 'signal':
            return self.show_signal()
        elif intent == 'temperature':
            return self.show_temperature()
        elif intent == 'voltage':
            return self.show_voltage()
        elif intent == 'network':
            return self.show_network()
        elif intent == 'operator':
            return self.show_operator()
        elif intent == 'device':
            return self.show_device()
        elif intent == 'cpu':
            return self.show_cpu_info()
        else:  # status
            return self.show_status()
    
    def show_signal(self):
        """신호 품질 표시"""
        print("📡 신호 품질 조회 중...\n")
        signal = get_signal_quality(self.controller)
        
        if signal:
            rssi_dbm = signal.get('rssi_dbm')
            if rssi_dbm:
                print(f"  신호 강도: {rssi_dbm} dBm")
                
                # 신호 품질 평가
                if rssi_dbm >= -70:
                    quality = "매우 좋음 ★★★★★"
                elif rssi_dbm >= -85:
                    quality = "좋음 ★★★★☆"
                elif rssi_dbm >= -100:
                    quality = "보통 ★★★☆☆"
                elif rssi_dbm >= -110:
                    quality = "약함 ★★☆☆☆"
                else:
                    quality = "매우 약함 ★☆☆☆☆"
                
                print(f"  품질 평가: {quality}")
            else:
                print(f"  RSSI: {signal['rssi']}/31")
            
            print(f"  BER: {signal['ber']}")
        else:
            print("  ❌ 신호 정보를 가져올 수 없습니다.")
            print("  (안테나가 연결되어 있는지 확인하세요)")
    
    def show_temperature(self):
        """온도 표시"""
        print("🌡️  온도 조회 중...\n")
        temp = get_temperature(self.controller)
        
        if temp is not None:
            print(f"  현재 온도: {temp:.1f}°C")
            
            if temp > 70:
                print(f"  상태: ⚠️ 과열 위험!")
            elif temp > 50:
                print(f"  상태: ⚡ 높음")
            elif temp > 30:
                print(f"  상태: ✅ 정상")
            else:
                print(f"  상태: ❄️ 낮음")
        else:
            print("  ❌ 온도 정보를 가져올 수 없습니다.")
            print("  (이 모뎀은 온도 조회를 지원하지 않을 수 있습니다)")
    
    def show_voltage(self):
        """전압/배터리 표시"""
        print("🔋 전압 정보 조회 중...\n")
        voltage = get_voltage(self.controller)
        
        if voltage:
            print(f"  전압: {voltage['voltage_mv']} mV")
            print(f"  충전량: {voltage['charge_percent']}%")
            
            status_map = {
                0: "충전 안함",
                1: "충전 중",
                2: "충전 완료"
            }
            print(f"  상태: {status_map.get(voltage['status'], '알 수 없음')}")
        else:
            print("  ❌ 전압 정보를 가져올 수 없습니다.")
    
    def show_network(self):
        """네트워크 상태 표시"""
        print("🌐 네트워크 상태 조회 중...\n")
        network = get_network_registration(self.controller)
        
        if network:
            print(f"  등록 상태: {network['status']}")
            
            if network['stat'] == 1:
                print(f"  ✅ 네트워크에 정상 등록됨 (홈)")
            elif network['stat'] == 5:
                print(f"  ✅ 네트워크에 등록됨 (로밍)")
            elif network['stat'] == 2:
                print(f"  🔍 네트워크 검색 중...")
            elif network['stat'] == 3:
                print(f"  ❌ 등록 거부됨")
            else:
                print(f"  ❌ 네트워크에 등록되지 않음")
            
            operator = get_operator(self.controller)
            if operator:
                print(f"  통신사: {operator}")
        else:
            print("  ❌ 네트워크 정보를 가져올 수 없습니다.")
    
    def show_operator(self):
        """통신사 표시"""
        print("📱 통신사 조회 중...\n")
        operator = get_operator(self.controller)
        
        if operator:
            print(f"  현재 통신사: {operator}")
        else:
            print("  ❌ 통신사 정보를 가져올 수 없습니다.")
            print("  (네트워크에 연결되어 있지 않을 수 있습니다)")
    
    def show_device(self):
        """장치 정보 표시"""
        print("📟 장치 정보 조회 중...\n")
        device = get_device_info(self.controller)
        
        if device:
            print(f"  모델: {device.get('model', 'N/A')}")
            print(f"  IMEI: {device.get('imei', 'N/A')}")
        else:
            print("  ❌ 장치 정보를 가져올 수 없습니다.")
    
    def show_cpu_info(self):
        """CPU 정보 (현재 불가능)"""
        print("💻 CPU 정보 조회 중...\n")
        print("  ❌ CPU 사용률은 현재 조회할 수 없습니다.")
        print("\n  [이유]")
        print("  - USB 연결만으로는 CPU 정보를 얻을 수 없습니다")
        print("  - AT 명령에 CPU 조회 기능이 없습니다")
        print("\n  [해결 방법]")
        print("  - FE990을 네트워크에 연결하세요")
        print("  - SSH로 접속 후 cpu_usage.py 사용")
    
    def show_status(self):
        """전체 상태 표시"""
        print("📊 전체 상태 조회 중...\n")
        status = get_modem_status(self.controller)
        print_modem_status(status)


def main():
    """자연어 인터페이스 실행"""
    print("=" * 60)
    print("FE990 모뎀 자연어 인터페이스")
    print("=" * 60)
    print("\n자연어로 질문하세요!")
    print("예: '신호 품질 어때?', '온도 알려줘', '모뎀 상태 보여줘'\n")
    
    # COM9로 연결
    controller = ATController(port="COM9")
    
    try:
        print("[연결 중...]")
        if not controller.connect():
            print("❌ COM9 연결 실패")
            print("포트가 사용 중이거나 존재하지 않습니다.")
            return
        
        print("✅ 연결됨\n")
        
        # 인터페이스 생성
        interface = ModemNaturalInterface(controller)
        
        # 대화형 루프
        while True:
            try:
                query = input("\n질문 > ").strip()
                
                if not query:
                    continue
                
                # 종료 명령
                if query.lower() in ['종료', 'exit', 'quit', 'q', '그만']:
                    print("\n👋 종료합니다.")
                    break
                
                # 도움말
                if query.lower() in ['도움말', 'help', 'h', '?']:
                    print("\n사용 가능한 질문:")
                    print("  - 신호 품질 어때? / 신호 강도는?")
                    print("  - 온도 알려줘 / 몇 도야?")
                    print("  - 배터리 상태는? / 전압은?")
                    print("  - 네트워크 연결됐어? / 망 등록됐어?")
                    print("  - 통신사 뭐야? / 어느 이통사?")
                    print("  - 모델 뭐야? / 장치 정보")
                    print("  - 전체 상태 / 모든 정보")
                    print("  - CPU 사용률은? (현재 불가)")
                    print("\n  종료: exit, quit, q, 종료, 그만")
                    continue
                
                # 질의 처리
                interface.handle_query(query)
                
            except KeyboardInterrupt:
                print("\n\n👋 종료합니다.")
                break
    
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[연결 해제됨]")


if __name__ == "__main__":
    main()

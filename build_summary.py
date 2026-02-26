#!/usr/bin/env python3
"""
Smart summary builder for FE990 full status
Generates concise, context-aware status summaries
"""

from typing import Dict, Any, List
import re


def build_summary(status: Dict[str, Any], verbose: bool = False) -> str:
    """
    Generate intelligent summary from full_status JSON
    
    Args:
        status: full_status dict with system, modem, network sections
        verbose: If True, includes detailed diagnostics and recommendations
        
    Returns:
        str: Concise summary (결론→이유→조치) or detailed report with bullets
        
    Format:
        - Basic: 2-3 sentences (결론 → 이유 → 조치)
        - Verbose: paragraph + [원인/조치] bullets (2-3개)
        
    Example:
        >>> status = {"system": {"temperature_celsius": 2.0, "uptime_formatted": "01:30:00"},
        ...           "modem": {"model": "FE990B40-NA"},
        ...           "network": {"sim_state": "NOT_INSERTED", "radio": {"cfun": 7}}}
        >>> print(build_summary(status))
        FE990B40-NA 정상 동작 중 (01:30:00). SIM 미삽입으로 등록 및 신호 측정 불가. SIM 카드를 삽입하세요.
    """
    # Extract data
    system = status.get("system", {})
    modem = status.get("modem", {})
    network = status.get("network", {})
    
    model = modem.get("model", "FE990")
    uptime = system.get("uptime_formatted", "unknown")
    temp = system.get("temperature_celsius")
    clock = system.get("clock")
    
    sim_state = network.get("sim_state", "UNKNOWN")
    registration = network.get("registration", {})
    eps_status = registration.get("eps", "UNKNOWN")
    operator = network.get("operator")
    signal = network.get("signal", {})
    rssi_dbm = signal.get("rssi_dbm")
    radio = network.get("radio", {})
    cfun = radio.get("cfun")
    
    # Check clock sync status
    clock_needs_sync = False
    if clock is None:
        clock_needs_sync = True
    elif isinstance(clock, str) and (clock.startswith("80/") or clock.startswith("70/")):
        clock_needs_sync = True
    
    # Build summary: 결론 → 이유 → 조치
    conclusion = []  # 결론
    reason = []      # 이유
    action = []      # 조치
    diagnostics = [] # verbose용 상세 진단
    
    # === 1. 결론: 장치 상태 ===
    if verbose:
        conclusion.append(f"{model} 모뎀이 가동 중이에요 (가동시간: {uptime})")
        if temp is not None:
            conclusion.append(f"온도는 {temp:.1f}°C입니다")
    else:
        conclusion.append(f"{model}이(가) {uptime} 동안 정상적으로 작동하고 있어요")
    
    # === 2. 온도 임계 체크 (결론에 영향) ===
    temp_issue = None
    if temp is not None:
        if temp > 80:
            temp_issue = "critical"
            conclusion.append("⚠️ 치명적 고온 상태예요")
            diagnostics.append(f"즉시 냉각이 필요합니다 (현재 {temp:.1f}°C, 임계값 80°C 초과)")
        elif temp > 70:
            temp_issue = "warning"
            if verbose:
                conclusion.append("온도가 다소 높은 편이에요")
            diagnostics.append(f"냉각을 권장드려요 (현재 {temp:.1f}°C, 권장 70°C 이하)")
        elif temp < -20:
            temp_issue = "cold"
            if verbose:
                conclusion.append("온도가 낮은 상태예요")
            diagnostics.append(f"저온 경고 (현재 {temp:.1f}°C, 정상 범위 -20°C 이상)")
    
    # === 3. 라디오 상태 체크 (치명적) ===
    if cfun == 0:
        reason.append("무선 기능이 꺼져 있어요")
        action.append("AT+CFUN=1 명령으로 라디오를 활성화하시면 사용 가능해요")
        diagnostics.append("무선 기능이 꺼져 있어 모든 네트워크 기능을 사용할 수 없어요")
        diagnostics.append("조치: AT+CFUN=1 명령으로 라디오를 활성화해 주세요")
        return _format_summary(conclusion, reason, action, diagnostics, verbose)
    
    elif cfun == 4:
        reason.append("비행기 모드가 활성화되어 있어요")
        action.append("AT+CFUN=1로 정상 모드로 전환하시면 돼요")
        diagnostics.append("비행기 모드로 인해 무선 통신이 비활성화되어 있어요")
        diagnostics.append("조치: AT+CFUN=1 명령으로 정상 모드로 전환해 주세요")
        return _format_summary(conclusion, reason, action, diagnostics, verbose)
    
    # === 4. SIM & 네트워크 상태 (이유) ===
    if sim_state == "NOT_INSERTED":
        reason.append("SIM 카드가 삽입되지 않아 네트워크 등록과 신호 측정이 불가능해요")
        action.append("SIM 카드를 삽입하시면 모든 기능을 사용하실 수 있어요")
        diagnostics.append("SIM 카드가 없어 네트워크 등록 및 신호 측정이 불가능해요")
        diagnostics.append("조치: SIM 카드를 삽입한 후 다시 시도해 주세요")
        if clock_needs_sync:
            diagnostics.append("참고: SIM을 삽입하시면 시스템 시간도 자동으로 동기화됩니다")
    
    elif sim_state == "PIN_REQUIRED":
        reason.append("SIM PIN 입력이 필요해요")
        action.append("AT+CPIN=<PIN> 명령으로 PIN을 입력해 주세요")
        diagnostics.append("SIM이 PIN으로 잠겨 있어요")
        diagnostics.append("조치: AT+CPIN=\"<PIN>\" 명령으로 PIN을 입력해 주세요")
    
    elif sim_state == "PUK_REQUIRED":
        reason.append("SIM PUK 입력이 필요해요 (PIN을 3회 잘못 입력하셨어요)")
        action.append("통신사 고객센터에 문의하시면 PUK 코드를 받으실 수 있어요")
        diagnostics.append("PIN을 3회 잘못 입력하여 SIM이 잠겼어요")
        diagnostics.append("조치: 통신사 고객센터에서 PUK 코드를 확인한 후 입력해 주세요")
    
    elif sim_state == "READY":
        # SIM 있음, 등록 상태 확인
        if eps_status in ["REGISTERED_HOME", "REGISTERED_ROAMING"]:
            # 성공적으로 등록됨
            if verbose:
                net_status = f"{operator or '통신사'} 네트워크에 성공적으로 등록되었어요"
                if eps_status == "REGISTERED_ROAMING":
                    net_status += " (로밍 중)"
            else:
                net_status = f"{operator or '네트워크'}에 연결되어 있어요"
            
            if rssi_dbm is not None:
                if rssi_dbm >= -70:
                    net_status += f", 신호가 우수해요 ({rssi_dbm} dBm)"
                elif rssi_dbm >= -85:
                    net_status += f", 신호가 양호해요 ({rssi_dbm} dBm)"
                elif rssi_dbm >= -100:
                    net_status += f", 신호가 보통이에요 ({rssi_dbm} dBm)"
                else:
                    net_status += f", 신호가 약해요 ({rssi_dbm} dBm)"
                    diagnostics.append(f"신호가 약합니다 ({rssi_dbm} dBm) - 위치를 이동하시거나 외부 안테나 사용을 권장드려요")
            
            reason.append(net_status)
            action.append("모든 기능을 정상적으로 사용하실 수 있어요")
        
        elif eps_status == "SEARCHING":
            reason.append("네트워크를 검색하고 있어요")
            action.append("잠시만 기다려 주시거나, 통신사 서비스 지역인지 확인해 주세요")
            diagnostics.append("네트워크를 검색 중이에요 - 잠시 기다려 주세요")
            diagnostics.append("조치: 통신사 서비스 지역인지 확인하거나 잠시 대기해 주세요")
        
        elif eps_status == "DENIED":
            reason.append("네트워크 등록이 거부되었어요")
            action.append("SIM 활성화 상태와 APN 설정을 확인해 주세요")
            diagnostics.append("네트워크 등록이 거부되었어요 - SIM 활성화 또는 APN 문제일 수 있어요")
            diagnostics.append("조치: 통신사에 SIM 활성화 상태를 문의해 주세요")
            diagnostics.append("조치: AT+CGDCONT 명령으로 APN 설정을 확인해 주세요")
        
        elif eps_status == "NOT_REGISTERED":
            reason.append("네트워크에 등록되지 않았어요")
            action.append("통신사 서비스 지역인지 확인하고, 필요시 설정을 점검해 주세요")
            diagnostics.append("네트워크 미등록 상태예요 - 커버리지나 설정 문제일 수 있어요")
            diagnostics.append("조치: 통신사 서비스 지역인지 확인해 주세요")
            diagnostics.append("조치: AT+COPS로 사업자 설정, AT+CGDCONT로 APN을 확인해 주세요")
        
        else:
            reason.append(f"네트워크 상태가 {eps_status}예요")
    
    else:
        reason.append(f"SIM 상태를 확인할 수 없어요 ({sim_state})")
        action.append("AT+CPIN? 명령으로 SIM 상태를 다시 확인해 주세요")
        diagnostics.append(f"SIM 상태를 확인할 수 없어요: {sim_state}")
        diagnostics.append("조치: AT+CPIN? 명령으로 SIM 상태를 다시 확인해 주세요")
    
    # === 5. 시간 동기화 체크 ===
    if clock_needs_sync and sim_state != "NOT_INSERTED":
        if verbose:
            diagnostics.append("참고: 시스템 시간이 동기화되지 않았어요 - AT+CCLK 명령이나 네트워크 동기화를 권장드려요")
    
    return _format_summary(conclusion, reason, action, diagnostics, verbose)


def _format_summary(conclusion: List[str], reason: List[str], action: List[str], 
                    diagnostics: List[str], verbose: bool) -> str:
    """
    Format summary output: 결론 → 이유 → 조치 순서
    
    Args:
        conclusion: 장치 상태 결론
        reason: 문제 이유
        action: 권장 조치
        diagnostics: verbose용 상세 진단
        verbose: 상세 모드 여부
        
    Returns:
        str: Formatted summary string
    """
    parts = []
    
    # 결론
    if conclusion:
        parts.append(", ".join(conclusion) + ".")
    
    # 이유
    if reason:
        parts.append(" ".join(reason) + ".")
    
    # 조치 (기본 모드에서도 간단히 표시)
    if action and not verbose:
        parts.append(" ".join(action) + ".")
    
    result = " ".join(parts)
    
    # Verbose: 상세 진단 추가
    if verbose and diagnostics:
        result += "\n\n[원인 및 조치]"
        for diag in diagnostics[:3]:  # 최대 3개
            result += f"\n  • {diag}"
    
    return result


# Test examples
if __name__ == "__main__":
    print("=" * 70)
    print("build_summary() Test Cases")
    print("=" * 70)
    
    # Test 1: No SIM (concise)
    print("\n[Test 1] No SIM inserted (concise)")
    status1 = {
        "system": {
            "temperature_celsius": 2.0,
            "uptime_formatted": "01:30:00",
            "clock": "80/01/06,00:03:36+00"
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "NOT_INSERTED",
            "registration": {"eps": "NOT_REGISTERED"},
            "signal": {"rssi_dbm": None},
            "radio": {"cfun": 7}
        }
    }
    print(build_summary(status1))
    
    print("\n[Test 1b] No SIM inserted (verbose)")
    print(build_summary(status1, verbose=True))
    
    # Test 2: Registered with good signal
    print("\n[Test 2] Registered with good signal (concise)")
    status2 = {
        "system": {
            "temperature_celsius": 35.0,
            "uptime_formatted": "2 days 05:30:00",
            "clock": "26/02/13,08:30:00+09"
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "READY",
            "registration": {"eps": "REGISTERED_HOME"},
            "operator": "SKT",
            "signal": {"rssi_dbm": -75},
            "radio": {"cfun": 7}
        }
    }
    print(build_summary(status2))
    
    print("\n[Test 2b] Registered with good signal (verbose)")
    print(build_summary(status2, verbose=True))
    
    # Test 3: Radio off
    print("\n[Test 3] Radio turned off (verbose)")
    status3 = {
        "system": {
            "temperature_celsius": 25.0,
            "uptime_formatted": "00:05:00",
            "clock": None
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "READY",
            "registration": {"eps": "NOT_REGISTERED"},
            "signal": {"rssi_dbm": None},
            "radio": {"cfun": 0}
        }
    }
    print(build_summary(status3, verbose=True))
    
    # Test 4: SIM ready but not registered
    print("\n[Test 4] SIM ready but not registered (verbose)")
    status4 = {
        "system": {
            "temperature_celsius": 45.0,
            "uptime_formatted": "12:00:00",
            "clock": "80/01/06,12:00:00+00"
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "READY",
            "registration": {"eps": "NOT_REGISTERED"},
            "signal": {"rssi_dbm": None},
            "radio": {"cfun": 7}
        }
    }
    print(build_summary(status4, verbose=True))
    
    # Test 5: High temperature warning
    print("\n[Test 5] High temperature warning (verbose)")
    status5 = {
        "system": {
            "temperature_celsius": 85.0,
            "uptime_formatted": "10:00:00",
            "clock": "26/02/13,10:00:00+09"
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "NOT_INSERTED",
            "registration": {"eps": "NOT_REGISTERED"},
            "signal": {"rssi_dbm": None},
            "radio": {"cfun": 7}
        }
    }
    print(build_summary(status5, verbose=True))
    
    # Test 6: Roaming with weak signal
    print("\n[Test 6] Roaming with weak signal (verbose)")
    status6 = {
        "system": {
            "temperature_celsius": 30.0,
            "uptime_formatted": "05:30:00",
            "clock": "26/02/13,05:30:00+09"
        },
        "modem": {"model": "FE990B40-NA"},
        "network": {
            "sim_state": "READY",
            "registration": {"eps": "REGISTERED_ROAMING"},
            "operator": "LG U+",
            "signal": {"rssi_dbm": -105},
            "radio": {"cfun": 7}
        }
    }
    print(build_summary(status6, verbose=True))

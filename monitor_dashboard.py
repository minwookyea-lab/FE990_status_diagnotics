"""
FE990 실시간 모니터링 대시보드
터미널에서 실시간으로 모뎀 상태를 모니터링합니다.
"""

import time
import sys
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.text import Text
from mcp_get_full_status import get_full_status
from build_summary import build_summary
from controller import ATController

console = Console()

def create_dashboard(status_data, summary_text, update_interval):
    """대시보드 레이아웃 생성"""
    
    # 타이틀
    title = Text("🔌 FE990 실시간 모니터링 대시보드", style="bold cyan", justify="center")
    
    # 시스템 정보 테이블
    system_table = Table(show_header=False, box=None, padding=(0, 1))
    system_table.add_column("항목", style="cyan", width=12)
    system_table.add_column("값", style="white")
    
    modem = status_data.get('modem', {})
    system = status_data.get('system', {})
    network = status_data.get('network', {})
    
    system_table.add_row("📱 모델", modem.get('model', 'N/A'))
    system_table.add_row("💾 펌웨어", modem.get('firmware', 'N/A'))
    
    # 업타임
    uptime = system.get('uptime_formatted', 'N/A')
    system_table.add_row("⏱️  업타임", uptime)
    
    # 온도 (색상 표시)
    temp = system.get('temperature_celsius')
    if temp is not None:
        if temp > 70:
            temp_str = f"[red]{temp}°C[/red]"
        elif temp > 60:
            temp_str = f"[yellow]{temp}°C[/yellow]"
        else:
            temp_str = f"[green]{temp}°C[/green]"
        system_table.add_row("🌡️  온도", temp_str)
    else:
        system_table.add_row("🌡️  온도", "N/A")
    
    # 라디오 상태
    cfun = system.get('function_level', 'N/A')
    if cfun == 0:
        cfun_str = "[red]꺼짐 (cfun=0)[/red]"
    elif cfun == 4:
        cfun_str = "[yellow]비행기 모드 (cfun=4)[/yellow]"
    elif cfun == 7:
        cfun_str = "[green]활성 (cfun=7)[/green]"
    else:
        cfun_str = f"cfun={cfun}"
    system_table.add_row("📡 라디오", cfun_str)
    
    # SIM 상태
    sim_state = network.get('sim_state', 'UNKNOWN')
    if sim_state == 'READY':
        sim_str = "[green]정상[/green]"
    elif sim_state == 'NOT_INSERTED':
        sim_str = "[yellow]삽입안됨[/yellow]"
    elif sim_state == 'PIN_REQUIRED':
        sim_str = "[red]PIN 필요[/red]"
    else:
        sim_str = f"[yellow]{sim_state}[/yellow]"
    system_table.add_row("💳 SIM", sim_str)
    
    # 네트워크 등록
    reg = network.get('registration', {})
    eps_reg = reg.get('eps', 'UNKNOWN')
    if eps_reg and 'REGISTERED' in eps_reg:
        reg_str = f"[green]{eps_reg}[/green]"
    elif eps_reg == 'SEARCHING':
        reg_str = f"[yellow]{eps_reg}[/yellow]"
    elif eps_reg == 'DENIED':
        reg_str = f"[red]{eps_reg}[/red]"
    else:
        reg_str = f"[dim]{eps_reg or 'UNKNOWN'}[/dim]"
    system_table.add_row("🌐 등록", reg_str)
    
    # 신호 세기
    signal = network.get('signal', {})
    rssi = signal.get('rssi_dbm')
    if rssi is not None:
        if rssi >= -70:
            signal_str = f"[green]{rssi} dBm (매우좋음)[/green]"
        elif rssi >= -85:
            signal_str = f"[green]{rssi} dBm (좋음)[/green]"
        elif rssi >= -100:
            signal_str = f"[yellow]{rssi} dBm (보통)[/yellow]"
        else:
            signal_str = f"[red]{rssi} dBm (약함)[/red]"
        system_table.add_row("📶 신호", signal_str)
    else:
        system_table.add_row("📶 신호", "[dim]N/A[/dim]")
    
    # 시스템 시간
    clock = system.get('clock', 'N/A')
    system_table.add_row("🕐 시스템", clock)
    
    # 요약 패널
    summary_panel = Panel(
        Text(summary_text, style="white"),
        title="📊 상태 요약",
        border_style="blue"
    )
    
    # 하단 정보
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    footer = Text.assemble(
        ("마지막 업데이트: ", "dim"),
        (now, "cyan"),
        (" | 새로고침 주기: ", "dim"),
        (f"{update_interval}초", "yellow"),
        (" | ", "dim"),
        ("[Ctrl+C] 종료", "red")
    )
    
    # 전체 레이아웃
    layout = Layout()
    layout.split_column(
        Layout(title, size=1),
        Layout(system_table, size=11),
        Layout(summary_panel, size=6),
        Layout(footer, size=1)
    )
    
    return Panel(layout, border_style="green", padding=(1, 2))


def main():
    """메인 함수"""
    # 기본 설정
    COM_PORT = "COM9"
    BAUD_RATE = 115200
    UPDATE_INTERVAL = 3  # 초
    
    console.print("\n[bold cyan]🔌 FE990 실시간 모니터링 대시보드[/bold cyan]\n")
    console.print(f"포트: {COM_PORT}, 속도: {BAUD_RATE} baud")
    console.print(f"새로고침 주기: {UPDATE_INTERVAL}초")
    console.print("\n[dim]Ctrl+C를 눌러 종료하세요...[/dim]\n")
    
    time.sleep(1)
    
    # ATController 초기화
    try:
        controller = ATController(COM_PORT, BAUD_RATE)
        console.print("[green]✓[/green] 모뎀 연결 성공\n")
    except Exception as e:
        console.print(f"[red]✗[/red] 모뎀 연결 실패: {e}")
        return
    
    try:
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    # 상태 조회 (silent=True로 로그 숨기기)
                    result = get_full_status(controller, silent=True)
                    status_data = result['full_status']
                    
                    # 디버깅: 데이터 확인
                    if not status_data or status_data.get('modem_status', {}).get('model') is None:
                        console.print(f"\n[yellow]⚠ 데이터 없음: {status_data}[/yellow]")
                    
                    # 요약 생성 (기본 모드)
                    summary = build_summary(status_data, verbose=False)
                    
                    # 대시보드 렌더링
                    dashboard = create_dashboard(status_data, summary, UPDATE_INTERVAL)
                    live.update(dashboard)
                    
                    # 대기
                    time.sleep(UPDATE_INTERVAL)
                    
                except Exception as e:
                    import traceback
                    error_msg = f"[red]오류 발생: {e}\n\n{traceback.format_exc()}[/red]"
                    live.update(Panel(error_msg, border_style="red"))
                    time.sleep(UPDATE_INTERVAL)
                    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]모니터링 종료[/yellow]")
    finally:
        controller.close()
        console.print("[green]✓[/green] 포트 닫기 완료")


if __name__ == "__main__":
    main()

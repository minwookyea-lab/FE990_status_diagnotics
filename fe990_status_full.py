#!/usr/bin/env python3
"""
FE990 Complete Status Query
Collect status information using all available AT commands
"""

from controller import ATController
import sys
from datetime import datetime


def print_header(title):
    """Print header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_info(label, value):
    """Print information"""
    print(f"  {label:25s}: {value}")


def test_all_at_commands(controller):
    """Test all AT commands (--full mode)"""
    # AT commands to test
    commands = [
        # Basic info
        ("ATI", "Manufacturer/Model Info"),
        ("ATI0", "Manufacturer Info"),
        ("ATI1", "Model Info"),
        ("ATI2", "Version Info"),
        ("ATI3", "IMEI"),
        ("ATI4", "IMEI SV"),
        ("ATI9", "Extended Info"),
        ("AT+CGMI", "Manufacturer"),
        ("AT+CGMM", "Model"),
        ("AT+CGMR", "Revision"),
        ("AT+CGSN", "IMEI"),
        ("AT+GSN", "Serial Number"),
        
        # Network
        ("AT+CSQ", "Signal Quality"),
        ("AT+CREG?", "Network Registration"),
        ("AT+COPS?", "Operator"),
        ("AT+CIMI", "IMSI"),
        ("AT+CCID", "ICCID (SIM)"),
        
        # Power/Battery
        ("AT+CBC", "Battery"),
        ("AT#ADC?", "ADC Reading"),
        ("AT+CIND?", "Indicator"),
        
        # Temperature
        ("AT#TEMPSENS=2", "All Temperature Sensors"),
        ("AT#TEMPMON?", "Temperature Monitor"),
        ("AT+CMTE?", "Temperature"),
        
        # System Info
        ("AT#SNUM", "Serial Number"),
        ("AT#HWVERSION", "Hardware Version"),
        ("AT#SWVERSION", "Software Version"),
        ("AT#FWSWITCH?", "Firmware Switch"),
        ("AT#CFUN?", "Function Mode"),
        ("AT+CFUN?", "Function Level"),
        
        # Memory/Storage
        ("AT#LSCRIPT", "Script List"),
        ("AT#CPUMODE?", "CPU Mode"),
        
        # SIM Card
        ("AT+CPIN?", "PIN Status"),
        ("AT+ICCID", "SIM ICCID"),
        
        # Network Settings
        ("AT+CGDCONT?", "PDP Context"),
        ("AT+CGACT?", "PDP Activation"),
        ("AT+CGPADDR", "PDP Address"),
        
        # USB/Serial
        ("AT#USBCFG?", "USB Config"),
        ("AT#PORTCFG?", "Port Config"),
        
        # GPIO
        ("AT#GPIO?", "GPIO Status"),
        
        # RF/Signal Status
        ("AT+CESQ", "Extended Signal Quality"),
        ("AT+CGREG?", "GPRS Registration"),
        ("AT+CEREG?", "LTE Registration"),
        ("AT+WS46?", "Wireless Standard"),
        ("AT#WS46?", "System Mode"),
        ("AT#SERVINFO", "Serving Cell Info"),
        ("AT#RFSTS", "RF Status"),
        ("AT#MONI", "Monitor Info"),
        ("AT#BND?", "Band Settings"),
        ("AT#SELRAT?", "RAT Selection"),
        
        # Others
        ("AT#CCLK?", "Clock"),
        ("AT+CCLK?", "Clock2"),
        ("AT#E2SLRI", "Last Restart Info"),
    ]
    
    print("=" * 70)
    print("FE990 Complete AT Command Test")
    print("=" * 70)
    print()
    
    success_count = 0
    results = []
    
    for cmd, desc in commands:
        try:
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore').strip()
            
            # Save only non-ERROR responses
            if "ERROR" not in decoded and decoded and len(decoded) > len(cmd) + 10:
                success_count += 1
                results.append((cmd, desc, decoded))
                print(f"[OK] {cmd:20s} - {desc}")
            else:
                print(f"[X]  {cmd:20s} - {desc}")
        except Exception as e:
            print(f"[X]  {cmd:20s} - {desc} (Error: {e})")
    
    # Print detailed results
    print("\n" + "=" * 70)
    print(f"Success: {success_count}/{len(commands)}")
    print("=" * 70)
    
    if results:
        print("\nDetailed Responses:\n")
        for cmd, desc, response in results:
            print(f"[{cmd}] {desc}")
            print("-" * 70)
            # Clean up and print response
            lines = [l.strip() for l in response.split('\n') if l.strip() and cmd not in l and 'OK' not in l]
            for line in lines:
                print(f"  {line}")
            print()


def main():
    """FE990 Complete Status Query"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FE990 Complete Status Report")
    parser.add_argument("-p", "--port", default="COM31", help="Serial port (default: COM31)")
    parser.add_argument("--full", action="store_true", help="Run full AT command test (52 commands)")
    args = parser.parse_args()
    
    # Connect to port
    controller = ATController(port=args.port)
    
    try:
        # Connect
        if not controller.connect():
            print(f"[ERROR] Failed to connect to {args.port}")
            sys.exit(1)
        
        # If --full option, run complete AT command test
        if args.full:
            test_all_at_commands(controller)
            return
        
        # Default mode: Quick status query
        print("\n" + "="*60)
        print("  FE990 Complete Status Report")
        print("="*60)
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        print_header("Device Information")
        
        # 1. Basic ping test
        response = controller.send_cmd("AT", wait_s=0.3)
        status = "OK" if b"OK" in response else "ERROR"
        print_info("Connection Status", status)
        
        # 2. Model name
        response = controller.send_cmd("AT+GMM", wait_s=0.3)
        model = response.decode('ascii', errors='ignore').strip()
        model = [line for line in model.split('\n') if line.strip() and not line.startswith('AT')][0] if model else "Unknown"
        print_info("Model", model)
        
        # 3. Firmware version (ATI)
        response = controller.send_cmd("ATI", wait_s=0.3)
        fw = response.decode('ascii', errors='ignore').strip()
        fw = [line for line in fw.split('\n') if line.strip() and not line.startswith('AT')][0] if fw else "Unknown"
        print_info("Firmware/Info", fw)
        
        print_header("System Status")
        
        # 4. Uptime (seconds)
        response = controller.send_cmd("AT#uptime=0", wait_s=0.3)
        uptime_str = response.decode('ascii', errors='ignore')
        
        # Parse #UPTIME: number
        uptime_sec = None
        for line in uptime_str.split('\n'):
            if '#UPTIME:' in line:
                try:
                    uptime_sec = int(line.split(':')[1].strip())
                except:
                    pass
        
        if uptime_sec:
            days = uptime_sec // 86400
            hours = (uptime_sec % 86400) // 3600
            minutes = (uptime_sec % 3600) // 60
            seconds = uptime_sec % 60
            
            uptime_readable = f"{days}d {hours}h {minutes}m {seconds}s"
            print_info("Uptime (seconds)", f"{uptime_sec}")
            print_info("Uptime (readable)", uptime_readable)
        else:
            print_info("Uptime", "Unable to read")
        
        # 5. Uptime (hh:mm:ss)
        response = controller.send_cmd("AT#uptime=1", wait_s=0.3)
        uptime_hms = response.decode('ascii', errors='ignore')
        for line in uptime_hms.split('\n'):
            if '#UPTIME:' in line:
                time_str = line.split(':')[1].strip()
                print_info("Uptime (formatted)", time_str)
                break
        
        print_header("Temperature Sensors")
        
        # 6. Query all temperature sensors
        response = controller.send_cmd("AT#TEMPSENS=2", wait_s=0.3)
        temp_str = response.decode('ascii', errors='ignore')
        
        for line in temp_str.split('\n'):
            line = line.strip()
            if '#TEMPSENS:' in line:
                # Parse #TEMPSENS: TSENS,27 format
                parts = line.split(':')
                if len(parts) > 1:
                    temp_info = parts[1].strip()
                    temp_parts = temp_info.split(',')
                    if len(temp_parts) == 2:
                        sensor_name = temp_parts[0]
                        temp_value = temp_parts[1]
                        print_info(f"{sensor_name}", f"{temp_value}°C")
        
        print_header("Additional Information")
        
        # 7. Manufacturer info (AT+GMI)
        try:
            response = controller.send_cmd("AT+GMI", wait_s=0.3)
            if b"ERROR" not in response:
                manufacturer = response.decode('ascii', errors='ignore').strip()
                manufacturer = [line for line in manufacturer.split('\n') if line.strip() and not line.startswith('AT')][0] if manufacturer else "N/A"
                print_info("Manufacturer", manufacturer)
        except:
            pass
        
        # 8. Serial number (AT+GSN or AT+CGSN)
        try:
            response = controller.send_cmd("AT+GSN", wait_s=0.3)
            if b"ERROR" not in response:
                serial = response.decode('ascii', errors='ignore').strip()
                serial = [line for line in serial.split('\n') if line.strip() and not line.startswith('AT')][0] if serial else "N/A"
                print_info("Serial Number (GSN)", serial)
        except:
            pass
        
        try:
            response = controller.send_cmd("AT+CGSN", wait_s=0.3)
            if b"ERROR" not in response:
                imei = response.decode('ascii', errors='ignore').strip()
                imei = [line for line in imei.split('\n') if line.strip() and not line.startswith('AT')][0] if imei else "N/A"
                print_info("IMEI (CGSN)", imei)
        except:
            pass
        
        # 9. Signal strength (AT+CSQ)
        try:
            response = controller.send_cmd("AT+CSQ", wait_s=0.3)
            if b"ERROR" not in response:
                signal = response.decode('ascii', errors='ignore').strip()
                signal = [line for line in signal.split('\n') if line.strip() and not line.startswith('AT')][0] if signal else "N/A"
                print_info("Signal Quality (CSQ)", signal)
        except:
            pass
        
        # 10. Network registration status (AT+CREG?)
        try:
            response = controller.send_cmd("AT+CREG?", wait_s=0.3)
            if b"ERROR" not in response:
                creg = response.decode('ascii', errors='ignore').strip()
                creg = [line for line in creg.split('\n') if line.strip() and not line.startswith('AT')][0] if creg else "N/A"
                print_info("Network Registration", creg)
        except:
            pass
        
        # 11. SIM card status (AT+CPIN?)
        try:
            response = controller.send_cmd("AT+CPIN?", wait_s=0.3)
            if b"ERROR" not in response:
                sim = response.decode('ascii', errors='ignore').strip()
                sim = [line for line in sim.split('\n') if line.strip() and not line.startswith('AT')][0] if sim else "N/A"
                print_info("SIM Status", sim)
        except:
            pass
        
        print_header("Port Information")
        print_info("Serial Port", controller.port)
        print_info("Baud Rate", controller.baud)
        print_info("Timeout", f"{controller.timeout}s")
        
        print("\n" + "="*60)
        print("  End of Report")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    
    finally:
        controller.disconnect()


if __name__ == "__main__":
    main()

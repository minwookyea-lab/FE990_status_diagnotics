#!/usr/bin/env python3
"""
FE990 Comprehensive Diagnostics Tool
Automatically diagnose serial connection, AT commands, SSH, network status, etc.
"""

from controller import ATController
import socket
import sys
import time
from datetime import datetime


class FE990Diagnostics:
    """FE990 Diagnostics Class"""
    
    def __init__(self, port="COM9"):
        self.port = port
        self.controller = ATController(port=port)
        self.results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "serial": {},
            "at_commands": {},
            "network": {},
            "ssh": {},
            "overall": "UNKNOWN"
        }
    
    def print_header(self, title):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name, status, details=""):
        """Print test result"""
        icon = "✓" if status else "✗"
        status_text = "PASS" if status else "FAIL"
        print(f"  [{icon}] {test_name:30s} {status_text:6s} {details}")
    
    def test_serial_connection(self):
        """Serial connection test"""
        self.print_header("Serial Connection Test")
        
        try:
            success = self.controller.connect()
            self.results["serial"]["connected"] = success
            
            if success:
                self.print_result("Serial Port Connection", True, f"({self.port})")
                
                # Check buffer status
                if self.controller.ser:
                    in_waiting = self.controller.ser.in_waiting
                    self.results["serial"]["buffer_size"] = in_waiting
                    self.print_result("Input Buffer Check", True, f"({in_waiting} bytes)")
                
                return True
            else:
                self.print_result("Serial Port Connection", False, f"({self.port})")
                return False
                
        except Exception as e:
            self.results["serial"]["error"] = str(e)
            self.print_result("Serial Port Connection", False, f"Error: {e}")
            return False
    
    def test_at_commands(self):
        """AT commands test"""
        self.print_header("AT Commands Test")
        
        if not self.controller.ser or not self.controller.ser.is_open:
            self.print_result("AT Commands", False, "Serial not connected")
            return False
        
        # AT commands to test
        tests = [
            ("AT", "Basic Ping", True),
            ("AT+GMM", "Model Name", True),
            ("AT#uptime=0", "Uptime (seconds)", True),
            ("AT#TEMPSENS=2", "Temperature Sensors", True),
            ("ATI", "Device Info", True),
            ("AT+CFUN?", "Function Level", True),
            ("AT+CPIN?", "SIM Status", True),
            ("AT+CREG?", "Network Registration", True),
            ("AT+CESQ", "Signal Quality", True),
            ("AT#reboot", "Reboot Command", False),  # Not actually executed
        ]
        
        passed = 0
        total = 0
        response_times = []
        
        for cmd, desc, execute in tests:
            if not execute:
                self.print_result(desc, None, "(Skipped)")
                continue
            
            total += 1
            try:
                # Measure response time
                start_time = time.time()
                response = self.controller.send_cmd(cmd, wait_s=0.3, total_read_s=2.0)
                elapsed_time = time.time() - start_time
                
                decoded = response.decode('ascii', errors='ignore')
                
                # If has OK or starts with # then success
                success = "OK" in decoded or "#" in decoded or "+" in decoded or any(c.isdigit() for c in decoded)
                
                if success:
                    response_times.append(elapsed_time)
                    
                    # Response summary (first line only)
                    lines = [line.strip() for line in decoded.split('\n') if line.strip() and not line.strip().startswith('AT')]
                    summary = lines[0] if lines else "OK"
                    if len(summary) > 30:
                        summary = summary[:27] + "..."
                    
                    self.print_result(desc, True, f"({summary}) [{elapsed_time:.3f}s]")
                    self.results["at_commands"][cmd] = {
                        "status": "pass", 
                        "response": decoded,
                        "response_time": elapsed_time
                    }
                    passed += 1
                else:
                    self.print_result(desc, False, f"No valid response [{elapsed_time:.3f}s]")
                    self.results["at_commands"][cmd] = {
                        "status": "fail", 
                        "response": decoded[:50],
                        "response_time": elapsed_time
                    }
                    
            except Exception as e:
                self.print_result(desc, False, f"Error: {e}")
                self.results["at_commands"][cmd] = {"status": "error", "error": str(e)}
        
        # Calculate average response time
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            self.results["at_commands"]["avg_response_time"] = avg_time
            self.results["at_commands"]["max_response_time"] = max_time
            self.results["at_commands"]["min_response_time"] = min_time
        
        self.results["at_commands"]["summary"] = f"{passed}/{total} passed"
        print(f"\n  Summary: {passed}/{total} tests passed")
        
        if response_times:
            print(f"  Response Time: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
        
        return passed == total
    
    def test_network(self):
        """Network connectivity test"""
        self.print_header("Network Connectivity Test")
        
        # Common USB modem addresses
        candidates = [
            "192.168.225.1",
            "192.168.1.1",
            "192.168.0.1",
            "10.0.0.1"
        ]
        
        reachable = []
        
        for host in candidates:
            # Check HTTP port (80)
            http_open = self._check_port(host, 80, timeout=1)
            
            # Check SSH port (22)
            ssh_open = self._check_port(host, 22, timeout=1)
            
            if http_open or ssh_open:
                ports = []
                if http_open:
                    ports.append("HTTP:80")
                if ssh_open:
                    ports.append("SSH:22")
                
                self.print_result(f"Host {host}", True, f"({', '.join(ports)})")
                reachable.append({"host": host, "http": http_open, "ssh": ssh_open})
            else:
                self.print_result(f"Host {host}", False, "Not reachable")
        
        self.results["network"]["reachable_hosts"] = reachable
        
        if reachable:
            print(f"\n  Found {len(reachable)} reachable host(s)")
            return True
        else:
            print(f"\n  No network hosts found")
            return False
    
    def test_ssh_access(self):
        """SSH access test"""
        self.print_header("SSH Access Test")
        
        if not self.results["network"].get("reachable_hosts"):
            self.print_result("SSH Access", False, "No reachable hosts")
            return False
        
        # Test only SSH-enabled hosts
        ssh_hosts = [h for h in self.results["network"]["reachable_hosts"] if h.get("ssh")]
        
        if not ssh_hosts:
            self.print_result("SSH Service", False, "No SSH ports open")
            return False
        
        # Common credentials
        credentials = [
            ("root", "telit"),
            ("root", "root"),
            ("admin", "admin"),
        ]
        
        success_count = 0
        
        for host_info in ssh_hosts:
            host = host_info["host"]
            
            for user, password in credentials:
                try:
                    ssh_controller = ATController(
                        ssh_host=host,
                        ssh_user=user,
                        ssh_pass=password
                    )
                    
                    if ssh_controller.ssh_connect():
                        self.print_result(f"SSH Login {host}", True, f"({user}@{host})")
                        
                        # CPU usage test
                        cpu = ssh_controller.get_remote_cpu_usage()
                        if cpu is not None:
                            self.print_result("Remote CPU Query", True, f"CPU: {cpu}%")
                            self.results["ssh"]["cpu_usage"] = cpu
                        
                        ssh_controller.ssh_disconnect()
                        self.results["ssh"]["access"] = {"host": host, "user": user}
                        success_count += 1
                        break
                        
                except Exception as e:
                    continue
        
        if success_count > 0:
            return True
        else:
            self.print_result("SSH Login", False, "Authentication failed")
            return False
    
    def _check_port(self, host, port, timeout=2):
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def generate_report(self):
        """Generate diagnostic report - narrative style"""
        self.print_header("Diagnostic Report")
        
        # Determine overall status
        serial_ok = self.results["serial"].get("connected", False)
        at_ok = len([v for v in self.results["at_commands"].values() 
                     if isinstance(v, dict) and v.get("status") == "pass"]) > 0
        
        print(f"\n  📅 Diagnosis Started: {self.results['timestamp']}")
        print(f"  🔌 Port: {self.port}")
        print()
        
        # 1. Serial connection status
        print("  ✓ Serial Connection:")
        if serial_ok:
            print(f"    ✓ Successfully connected to {self.port} port.")
            print(f"    - Port: {self.port}")
            print(f"    - Speed: {self.controller.baud} bps")
            print(f"    - Timeout setting: {self.controller.timeout} seconds")
            
            # Display AT command response time
            avg_time = self.results["at_commands"].get("avg_response_time")
            max_time = self.results["at_commands"].get("max_response_time")
            min_time = self.results["at_commands"].get("min_response_time")
            
            if avg_time is not None:
                print(f"    - Actual response time: avg {avg_time:.3f}s (min {min_time:.3f}s, max {max_time:.3f}s)")
                
                # Evaluate response time
                if avg_time < 0.5:
                    print(f"      ✓ Response speed is very fast.")
                elif avg_time < 1.0:
                    print(f"      ✓ Response speed is normal.")
                elif avg_time < 2.0:
                    print(f"      ○ Response speed is somewhat slow.")
                else:
                    print(f"      ⚠ Response speed is slow. Check communication status.")
        else:
            print(f"    ✗ Failed to connect to {self.port} port.")
            print(f"    → Please check if device is connected or try another COM port.")
        print()
        
        # 2. Temperature status analysis
        print("  🌡️ Temperature Status:")
        temp_cmd = self.results["at_commands"].get("AT#TEMPSENS=2", {})
        if temp_cmd.get("status") == "pass":
            temp_response = temp_cmd.get("response", "")
            temps = []
            for line in temp_response.split('\n'):
                if '#TEMPSENS:' in line:
                    parts = line.split(':')[1].strip().split(',')
                    if len(parts) == 2:
                        sensor_name = parts[0]
                        try:
                            temp_value = int(parts[1])
                            temps.append((sensor_name, temp_value))
                        except:
                            pass
            
            if temps:
                max_temp = max([t[1] for t in temps])
                avg_temp = sum([t[1] for t in temps]) / len(temps)
                
                print(f"    Detected sensors: {len(temps)}")
                for sensor, temp in temps:
                    status = ""
                    if temp >= 80:
                        status = " ⚠️ Critical - Very High!"
                    elif temp >= 60:
                        status = " ⚠️ Warning - High"
                    elif temp >= 40:
                        status = " Caution"
                    else:
                        status = " Normal"
                    print(f"      {sensor}: {temp}°C{status}")
                
                print()
                if max_temp >= 80:
                    print(f"    ✗ Critical: Maximum temperature is very high at {max_temp}°C!")
                    print(f"    → Immediately inspect device and cooling is required.")
                elif max_temp >= 60:
                    print(f"    ⚠ Warning: Maximum temperature is high at {max_temp}°C.")
                    print(f"    → Check ventilation around the device.")
                elif max_temp >= 40:
                    print(f"    ○ Caution: Maximum temperature is {max_temp}°C.")
                    print(f"    → Continue monitoring temperature.")
                else:
                    print(f"    ✓ Normal: All temperature sensors are within normal range. (average {avg_temp:.1f}°C)")
            else:
                print(f"    ○ Unable to parse temperature data.")
        else:
            print(f"    ✗ Unable to read temperature sensors.")
        print()
        
        # 3. SIM and network status
        print("  📱 SIM and Network:")
        cfun_cmd = self.results["at_commands"].get("AT+CFUN?", {})
        cpin_cmd = self.results["at_commands"].get("AT+CPIN?", {})
        creg_cmd = self.results["at_commands"].get("AT+CREG?", {})
        cesq_cmd = self.results["at_commands"].get("AT+CESQ", {})
        
        # Check SIM status
        sim_ready = False
        cfun_level = None
        
        if cfun_cmd.get("status") == "pass":
            response = cfun_cmd.get("response", "")
            for line in response.split('\n'):
                if '+CFUN:' in line:
                    try:
                        cfun_level = int(line.split(':')[1].strip().split(',')[0])
                    except:
                        pass
        
        if cpin_cmd.get("status") == "pass":
            response = cpin_cmd.get("response", "")
            if "READY" in response:
                sim_ready = True
                print(f"    ✓ SIM card is recognized normally.")
            elif "ERROR" in response:
                print(f"    ✗ SIM Card Status: No SIM")
                print(f"    → Insert a SIM card and activate full function mode with AT+CFUN=1 command.")
            else:
                print(f"    ✗ SIM Card Status: {response.strip()}")
        else:
            if cfun_level == 7:
                print(f"    ✗ SIM card is not installed or not recognized. (CFUN: {cfun_level})")
                print(f"    → Insert a SIM card and activate full function mode with AT+CFUN=1 command.")
            else:
                print(f"    ○ Unable to check SIM status.")
        
        # Network registration status
        if creg_cmd.get("status") == "pass":
            response = creg_cmd.get("response", "")
            if "+CREG:" in response:
                try:
                    parts = response.split(':')[1].strip().split(',')
                    reg_status = int(parts[1]) if len(parts) > 1 else int(parts[0])
                    
                    if reg_status == 1:
                        print(f"    ✓ Registered to network. (Home network)")
                    elif reg_status == 5:
                        print(f"    ✓ Registered to network. (Roaming)")
                    elif reg_status == 2:
                        print(f"    ○ Searching for network...")
                    elif reg_status == 0:
                        if not sim_ready:
                            print(f"    ✗ Not registered to network.")
                            print(f"    → Network registration impossible due to no SIM card.")
                        else:
                            print(f"    ✗ Not registered to network.")
                            print(f"    → Check signal reception status.")
                    else:
                        print(f"    ✗ Network registration denied (status: {reg_status})")
                except:
                    pass
        
        # Signal quality
        if cesq_cmd.get("status") == "pass":
            response = cesq_cmd.get("response", "")
            if "+CESQ:" in response:
                try:
                    values = response.split(':')[1].strip().split(',')
                    rssi = int(values[0])
                    
                    if rssi == 99:
                        if not sim_ready:
                            print(f"    ✗ No signal received.")
                            print(f"    → RF function is disabled due to no SIM card.")
                        else:
                            print(f"    ✗ No signal received.")
                            print(f"    → Check antenna connection.")
                    elif rssi >= 20:
                        print(f"    ✓ Signal quality is excellent. (RSSI: {rssi})")
                    elif rssi >= 10:
                        print(f"    ○ Signal quality is good. (RSSI: {rssi})")
                    else:
                        print(f"    ⚠ Signal quality is weak. (RSSI: {rssi})")
                except:
                    pass
        print()
        
        # 4. Uptime and stability
        print("  ⏱️ System Stability:")
        uptime_cmd = self.results["at_commands"].get("AT#uptime=0", {})
        if uptime_cmd.get("status") == "pass":
            response = uptime_cmd.get("response", "")
            for line in response.split('\n'):
                if '#UPTIME:' in line:
                    try:
                        uptime_sec = int(line.split(':')[1].strip())
                        days = uptime_sec // 86400
                        hours = (uptime_sec % 86400) // 3600
                        minutes = (uptime_sec % 3600) // 60
                        
                        uptime_str = ""
                        if days > 0:
                            uptime_str += f"{days} day(s) "
                        if hours > 0:
                            uptime_str += f"{hours} hour(s) "
                        uptime_str += f"{minutes} minute(s)"
                        
                        print(f"    Uptime: {uptime_str} ({uptime_sec:,} seconds)")
                        
                        if uptime_sec < 300:  # Less than 5 minutes
                            print(f"    ○ Recently restarted.")
                        elif uptime_sec < 3600:  # Less than 1 hour
                            print(f"    ○ Device has started normally.")
                        elif uptime_sec < 86400:  # Less than 1 day
                            print(f"    ✓ Device is operating stably.")
                        else:
                            print(f"    ✓ Device has been operating stably for over {days} day(s).")
                    except:
                        pass
        print()
        
        # 5. Overall assessment
        print("  📊 Overall Assessment:")
        
        issues = []
        warnings = []
        
        if not serial_ok:
            issues.append("Serial connection failed")
        
        # Check temperature
        if temp_cmd.get("status") == "pass":
            temp_response = temp_cmd.get("response", "")
            max_temp = 0
            for line in temp_response.split('\n'):
                if '#TEMPSENS:' in line:
                    try:
                        temp_value = int(line.split(',')[1])
                        max_temp = max(max_temp, temp_value)
                    except:
                        pass
            if max_temp >= 80:
                issues.append(f"Temperature critical ({max_temp}°C)")
            elif max_temp >= 60:
                warnings.append(f"Temperature warning ({max_temp}°C)")
        
        if not sim_ready and cfun_level == 7:
            warnings.append("No SIM card")
        
        if issues:
            print(f"    ✗ Status: Issues Found")
            for issue in issues:
                print(f"      • {issue}")
            self.results["overall"] = "CRITICAL"
        elif warnings:
            print(f"    ⚠ Status: Attention Required")
            for warning in warnings:
                print(f"      • {warning}")
            self.results["overall"] = "WARNING"
        elif serial_ok and at_ok:
            print(f"    ✓ Status: Normal")
            print(f"      All basic functions are operating normally.")
            self.results["overall"] = "GOOD"
        else:
            print(f"    ○ Status: Partial Operation")
            self.results["overall"] = "PARTIAL"
        
        # Record diagnosis completion time
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n  ✅ Diagnosis Completed: {end_time}")
        print(f"\n{'='*60}\n")
        
        return self.results
    
    def run_full_diagnostics(self):
        """Run full diagnostics"""
        print("\n" + "="*60)
        print("  FE990 Comprehensive Diagnostics")
        print("="*60)
        print(f"  Port: {self.port}")
        print(f"  Time: {self.results['timestamp']}")
        print("="*60)
        
        try:
            # 1. Serial connection test
            serial_ok = self.test_serial_connection()
            
            if serial_ok:
                # 2. AT commands test
                self.test_at_commands()
            
            # 3. Network test
            self.test_network()
            
            # 4. SSH access test
            self.test_ssh_access()
            
            # 5. Generate report
            return self.generate_report()
            
        finally:
            # Cleanup
            if self.controller.ser and self.controller.ser.is_open:
                self.controller.disconnect()


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FE990 Diagnostics Tool")
    parser.add_argument("-p", "--port", default="COM9", help="Serial port (default: COM9)")
    args = parser.parse_args()
    
    diag = FE990Diagnostics(port=args.port)
    results = diag.run_full_diagnostics()
    
    # Return exit code based on results
    if results["overall"] == "GOOD":
        sys.exit(0)
    elif results["overall"] == "PARTIAL":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

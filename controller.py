#!/usr/bin/env python3
"""
AT Command Controller
Controller with integrated power control functions (power_on, power_off, reboot)
"""

import time
import serial
import paramiko
from typing import Tuple, Optional


def get_cpu_usage() -> int:
    """
    Calculate CPU usage (%) by reading Linux /proc/stat twice
    
    Returns:
        int: CPU usage (0-100%)
        
    Raises:
        FileNotFoundError: When /proc/stat file is not found (non-Linux system)
        ValueError: Parsing error
    """
    def read_cpu_times():
        """Read CPU time values and return (total, idle)"""
        with open('/proc/stat', 'r') as f:
            line = f.readline()  # First line: cpu  user nice system idle iowait irq softirq...
            
        if not line.startswith('cpu '):
            raise ValueError("Invalid /proc/stat format")
            
        # Split by space and extract numbers only
        values = line.split()[1:]  # Exclude 'cpu'
        values = [int(v) for v in values]
        
        # total = sum of all times
        total = sum(values)
        # idle = idle + iowait (index 3, 4)
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        
        return total, idle
    
    # First measurement
    total1, idle1 = read_cpu_times()
    
    # Wait 0.5 seconds
    time.sleep(0.5)
    
    # Second measurement
    total2, idle2 = read_cpu_times()
    
    # Calculate delta
    total_delta = total2 - total1
    idle_delta = idle2 - idle1
    
    # Calculate CPU usage (used time / total time)
    if total_delta == 0:
        return 0
    
    usage = ((total_delta - idle_delta) / total_delta) * 100
    
    return int(usage)


class ATController:
    """Class to control devices via AT commands"""
    
    # Default serial communication settings
    DEFAULT_PORT = "COM33"      # Default serial port (e.g., COM9, COM33)
    DEFAULT_BAUD = 115200       # Communication speed (bps) - FE990 standard
    DEFAULT_TIMEOUT = 2.0       # Response wait time (seconds)
    
    # AT command definitions
    CMD_REBOOT = "AT#reboot"        # Reboot command
    CMD_OFF = "AT#shdn"             # Power off (shutdown)
    CMD_UPTIME = "AT#uptime=0"      # Query uptime (returns seconds)
    CMD_PING = "AT"                 # Connection test (response: OK)
    CMD_GMM = "AT+GMM"              # Query product model name (e.g., FE990B40-NA)
    CMD_TEMPSENS = "AT#TEMPSENS=2"  # Query all temperature sensors
    
    # SSH default settings
    DEFAULT_SSH_HOST = "192.168.1.1"  # FE990 default IP
    DEFAULT_SSH_PORT = 22
    DEFAULT_SSH_USER = "root"
    DEFAULT_SSH_PASS = "telit"
    
    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baud: int = DEFAULT_BAUD,
        timeout: float = DEFAULT_TIMEOUT,
        ssh_host: Optional[str] = None,
        ssh_port: int = DEFAULT_SSH_PORT,
        ssh_user: Optional[str] = None,
        ssh_pass: Optional[str] = None
    ):
        """
        Initialize AT controller
        
        Args:
            port: Serial port (default: COM33)
            baud: Baud rate (default: 115200)
            timeout: Timeout duration (seconds, default: 2.0)
            ssh_host: SSH host address (default: 192.168.1.1)
            ssh_port: SSH port (default: 22)
            ssh_user: SSH username (default: root)
            ssh_pass: SSH password (default: telit)
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        
        # SSH 설정
        self.ssh_host = ssh_host or self.DEFAULT_SSH_HOST
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user or self.DEFAULT_SSH_USER
        self.ssh_pass = ssh_pass or self.DEFAULT_SSH_PASS
        self.ssh_client: Optional[paramiko.SSHClient] = None
    
    def connect(self) -> bool:
        """
        Serial port connection
        
        Returns:
            Connection success status
        """
        try:
            # Serial port settings (8N1: 8 bits, no parity, 1 stop bit)
            self.ser = serial.Serial(
                self.port,                    # Port name (e.g., COM9, COM33)
                self.baud,                    # 115200 bps (FE990 standard)
                timeout=self.timeout,         # Read timeout (seconds)
                write_timeout=self.timeout,   # Write timeout (seconds)
                bytesize=serial.EIGHTBITS,    # 8-bit data
                parity=serial.PARITY_NONE,    # No parity check
                stopbits=serial.STOPBITS_ONE, # 1 stop bit
                rtscts=False,                 # Disable hardware flow control
                dsrdtr=False                  # Disable DSR/DTR signals
            )
            # Clear buffers (remove previous data)
            self.ser.reset_input_buffer()   # Clear input buffer
            self.ser.reset_output_buffer()  # Clear output buffer
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def ssh_connect(self) -> bool:
        """
        Connect via SSH
        
        Returns:
            Connection success status
        """
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_pass,
                timeout=3.0,
                look_for_keys=False,
                allow_agent=False
            )
            return True
        except Exception as e:
            print(f"[ERROR] SSH connection failed to {self.ssh_host}: {e}")
            return False
    
    def ssh_disconnect(self) -> None:
        """Disconnect SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def ssh_execute(self, command: str, timeout: float = 10.0) -> Tuple[bool, str, str]:
        """
        Execute remote command via SSH
        
        Args:
            command: Command to execute
            timeout: Timeout duration (seconds)
        
        Returns:
            (success status, stdout, stderr)
        """
        if not self.ssh_client:
            return False, "", "SSH not connected"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            stdout_str = stdout.read().decode('utf-8', errors='ignore')
            stderr_str = stderr.read().decode('utf-8', errors='ignore')
            return True, stdout_str, stderr_str
        except Exception as e:
            return False, "", str(e)
    
    def get_remote_cpu_usage(self, interval: float = 0.5) -> Optional[int]:
        """
        Query remote device CPU usage via SSH
        
        Args:
            interval: Measurement interval (seconds, default: 0.5)
        
        Returns:
            CPU usage (0-100%), None on failure
        """
        if not self.ssh_client:
            print("[ERROR] SSH not connected")
            return None
        
        try:
            # First measurement
            success1, stdout1, stderr1 = self.ssh_execute("cat /proc/stat | head -1")
            if not success1:
                print(f"[ERROR] Failed to read /proc/stat: {stderr1}")
                return None
            
            line1 = stdout1.strip()
            if not line1.startswith('cpu '):
                print(f"[ERROR] Invalid /proc/stat format: {line1}")
                return None
            
            values1 = [int(v) for v in line1.split()[1:]]
            total1 = sum(values1)
            idle1 = values1[3] + (values1[4] if len(values1) > 4 else 0)
            
            # Wait
            time.sleep(interval)
            
            # Second measurement
            success2, stdout2, stderr2 = self.ssh_execute("cat /proc/stat | head -1")
            if not success2:
                print(f"[ERROR] Failed to read /proc/stat: {stderr2}")
                return None
            
            line2 = stdout2.strip()
            if not line2.startswith('cpu '):
                print(f"[ERROR] Invalid /proc/stat format: {line2}")
                return None
            
            values2 = [int(v) for v in line2.split()[1:]]
            total2 = sum(values2)
            idle2 = values2[3] + (values2[4] if len(values2) > 4 else 0)
            
            # Calculate CPU usage
            total_delta = total2 - total1
            idle_delta = idle2 - idle1
            
            if total_delta == 0:
                return 0
            
            usage = ((total_delta - idle_delta) / total_delta) * 100
            return int(usage)
            
        except Exception as e:
            print(f"[ERROR] Failed to calculate CPU usage: {e}")
            return None
    
    def send_cmd(
        self,
        cmd: str,
        use_crlf: bool = True,
        wait_s: float = 0.5,
        total_read_s: float = 10.0
    ) -> bytes:
        """
        Send AT command and collect response
        
        Args:
            cmd: AT command to send
            use_crlf: Use CRLF (True: \r\n, False: \r)
            wait_s: Initial wait time after write (seconds)
            total_read_s: Maximum collection time (seconds)
        
        Returns:
            Response bytes
        """
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port is not connected")
        
        # AT command format: "AT command\r\n" (CR+LF) or "AT command\r" (CR only)
        line = cmd + ("\r\n" if use_crlf else "\r")
        self.ser.write(line.encode("ascii"))  # Send with ASCII encoding
        self.ser.flush()                       # Flush buffer immediately
        
        # Initial wait: Time for device to process command (default 0.5 seconds)
        time.sleep(wait_s)
        
        # Start collecting response
        buf = bytearray()
        deadline = time.time() + total_read_s  # Set maximum wait time (default 10 seconds)
        
        while time.time() < deadline:
            n = self.ser.in_waiting            # Check bytes waiting in buffer
            if n:
                chunk = self.ser.read(n)       # Read all waiting data
                if chunk:
                    buf.extend(chunk)
                    # Detect termination keywords ('OK' or 'ERROR')
                    text = buf.decode(errors="ignore")
                    if ("OK" in text) or ("ERROR" in text):
                        break                  # Early termination (no need to wait more)
            else:
                # If no waiting data, wait briefly and recheck
                time.sleep(0.05)
        
        return bytes(buf)
    
    def power_on(self, pin_number: Optional[int] = None, pulse_duration: float = 0.1) -> Tuple[bool, str]:
        """
        Turn device power on (physical pin control)
        
        Turn on power by briefly setting the power button pin on the Telit EVB board to HIGH.
        Uses GPIO control, not AT commands.
        
        Args:
            pin_number: GPIO pin number (need to confirm with HW team)
            pulse_duration: Button press duration (seconds, default: 0.1 seconds)
        
        Returns:
            (success status, response message)
        
        TODO: Need to confirm following information with HW team
            1. GPIO hardware/interface to use (Arduino, USB-GPIO adapter, etc.)
            2. Pin number connected to power button
            3. Required pulse duration
        """
        try:
            # TODO: Implement actual GPIO control
            # Example (needs modification for actual hardware):
            # 
            # Option 1: Control via Arduino
            # arduino = serial.Serial('COM_PORT', 9600)
            # arduino.write(f'PIN:{pin_number}:HIGH\n'.encode())
            # time.sleep(pulse_duration)
            # arduino.write(f'PIN:{pin_number}:LOW\n'.encode())
            # arduino.close()
            #
            # Option 2: USB-GPIO adapter (pyftdi)
            # from pyftdi.gpio import GpioController
            # gpio = GpioController()
            # gpio.open_from_url('ftdi://ftdi:232h/1')
            # gpio.set_direction(pins=1<<pin_number, direction=1<<pin_number)
            # gpio.write(1<<pin_number)
            # time.sleep(pulse_duration)
            # gpio.write(0)
            # gpio.close()
            #
            # Option 3: Relay module, etc.
            
            if pin_number is None:
                return False, "GPIO pin number not specified. Contact HW team for pin information."
            
            # Currently not implemented
            return False, f"Power-on via GPIO pin {pin_number} not implemented yet. Requires GPIO hardware setup."
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def power_off(self) -> Tuple[bool, str]:
        """
        Turn device power off (using AT#shdn command)
        
        Returns:
            (success status, response message)
        """
        try:
            # Try to connect if port is not open
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, "Failed to connect to device"
            
            # Send "AT#shdn\r\n" command
            response = self.send_cmd(self.CMD_OFF, use_crlf=True, wait_s=0.5, total_read_s=5.0)
            
            # Decode response (ignore errors while converting)
            text = response.decode(errors="ignore").strip() if response else ""
            # Success: if response exists and contains "OK"
            success = bool(response) and ("OK" in text)
            
            return success, text if text else "(no response)"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def reboot(self) -> Tuple[bool, str]:
        """
        Reboot device (using AT#reboot command)
        Rebooting takes time, so wait up to 10 seconds
        
        Returns:
            (success status, response message)
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, "Failed to connect to device"
            
            # Send "AT#reboot\r\n" command (10 second wait time)
            response = self.send_cmd(self.CMD_REBOOT, use_crlf=True, wait_s=0.5, total_read_s=10.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            return success, text if text else "(no response)"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def off(self) -> Tuple[bool, str]:
        """
        Shutdown device
        
        Returns:
            (success status, response message)
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, "Failed to connect to device"
            
            response = self.send_cmd(self.CMD_OFF, use_crlf=True, wait_s=0.5, total_read_s=10.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            return success, text if text else "(no response)"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def ping(self) -> Tuple[bool, str]:
        """
        Check device connection status
        
        Returns:
            (success status, response message)
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, "Failed to connect to device"
            
            response = self.send_cmd(self.CMD_PING, use_crlf=True, wait_s=0.5, total_read_s=5.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            return success, text if text else "(no response)"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_uptime(self) -> Tuple[bool, Optional[int], str]:
        """
        Query device uptime (using AT#uptime=0 command)
        
        Example response:
            AT#uptime=0
            #UPTIME: 2654
            OK
        
        Returns:
            (success status, uptime(seconds), response message)
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, None, "Failed to connect to device"
            
            # Send "AT#uptime=0\r\n" command
            response = self.send_cmd(self.CMD_UPTIME, use_crlf=True, wait_s=0.5, total_read_s=10.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            # Extract uptime value using regex
            # Example: "#UPTIME: 2654" → 2654
            uptime_val = None
            if success and text:
                import re
                m = re.search(r"#[Uu][Pp][Tt][Ii][Mm][Ee]:\s*(\d+)", text)
                if m:
                    uptime_val = int(m.group(1))  # Integer in seconds
            
            return success, uptime_val, text if text else "(no response)"
        
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def gmm(self) -> Tuple[bool, Optional[str], str]:
        """
        Query product information (using AT+GMM command)
        
        Example response:
            AT+GMM
            FE990B40-NA
            OK
        
        Returns:
            (success status, model name, response message)
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, None, "Failed to connect to device"
            
            # Send "AT+GMM\r" command
            response = self.send_cmd(self.CMD_GMM, use_crlf=True, wait_s=0.5, total_read_s=5.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            # Parse model name: Extract first line excluding "OK", "ERROR", "AT+GMM" lines
            model = None
            if success and text:
                lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
                # Exclude OK/ERROR and AT command lines
                model_lines = [ln for ln in lines if ln not in ["OK", "ERROR"] and not ln.startswith("AT")]
                if model_lines:
                    model = model_lines[0]  # Example: "FE990B40-NA"
            
            return success, model, text if text else "(no response)"
        
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def tempsens(self) -> Tuple[bool, Optional[dict], str]:
        """
        Query temperature sensor information (using AT#TEMPSENS=2 command)
        
        Example response:
            AT#TEMPSENS=2
            #TEMPSENS: TSENS,26
            #TEMPSENS: PA_THERM1,24
            #TEMPSENS: PA_THERM2,24
            #TEMPSENS: PA_THERM3,24
            OK
        
        Returns:
            (success status, {sensor_name: temperature} dictionary, response message)
            Example: (True, {"TSENS": 26.0, "PA_THERM1": 24.0, ...}, "...")
        """
        try:
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return False, None, "Failed to connect to device"
            
            # Send "AT#TEMPSENS=2\r" command
            response = self.send_cmd(self.CMD_TEMPSENS, use_crlf=True, wait_s=0.5, total_read_s=5.0)
            
            text = response.decode(errors="ignore").strip() if response else ""
            success = bool(response) and ("OK" in text)
            
            # Extract sensor name and temperature using regex
            # Pattern: "#TEMPSENS: sensor_name,temperature_value"
            # Example: "#TEMPSENS: TSENS,26" → sensor_name="TSENS", temp_value=26.0
            temperatures = {}
            if success and text:
                import re
                pattern = re.compile(r"#TEMPSENS\s*:\s*([A-Z_\d]+)\s*,\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
                for line in text.split("\n"):
                    m = pattern.search(line)
                    if m:
                        try:
                            sensor_name = m.group(1)    # Sensor name (e.g., "TSENS")
                            temp_value = float(m.group(2))  # Temperature value (e.g., 26.0)
                            temperatures[sensor_name] = temp_value
                        except ValueError:
                            continue  # Ignore conversion failures
            
            return success, temperatures if temperatures else None, text if text else "(no response)"
        
        except Exception as e:
            return False, None, f"Error: {str(e)}"


def main():
    """
    CLI interface
    
    Usage examples:
        python controller.py --action uptime --port COM9
        python controller.py --action gmm --port COM9
        python controller.py --action tempsens --port COM9 --baud 115200
        python controller.py --action reboot --port COM9
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="AT Device Controller")
    parser.add_argument("--action", 
                       choices=["power_on", "power_off", "reboot", "off", "ping", "uptime", "gmm", "tempsens"],
                       required=True,
                       help="Action to execute")
    parser.add_argument("--port", default=ATController.DEFAULT_PORT, help="Serial port (e.g., COM9, COM33)")
    parser.add_argument("--baud", type=int, default=ATController.DEFAULT_BAUD, help="Baud rate (default: 115200)")
    parser.add_argument("--timeout", type=float, default=ATController.DEFAULT_TIMEOUT, 
                       help="Timeout duration (seconds, default: 2.0)")
    
    args = parser.parse_args()
    
    # Create controller
    controller = ATController(port=args.port, baud=args.baud, timeout=args.timeout)
    
    # Connect
    if not controller.connect():
        print(f"[FAIL] Cannot connect to {args.port}")
        return
    
    print(f"[OK] Connected to {args.port} @ {args.baud}")
    
    try:
        # Execute selected action
        if args.action == "power_on":
            # Turn power on via GPIO (currently not implemented)
            success, msg = controller.power_on()
            print(f"[power_on] {'SUCCESS' if success else 'FAILED'}: {msg}")
        
        elif args.action == "power_off":
            # Turn power off with AT#shdn command
            success, msg = controller.power_off()
            print(f"[power_off] {'SUCCESS' if success else 'FAILED'}: {msg}")
        
        elif args.action == "reboot":
            # Reboot with AT#reboot command
            success, msg = controller.reboot()
            print(f"[reboot] {'SUCCESS' if success else 'FAILED'}: {msg}")
        
        elif args.action == "off":
            # Same as power_off (AT#shdn)
            success, msg = controller.off()
            print(f"[off] {'SUCCESS' if success else 'FAILED'}: {msg}")
        
        elif args.action == "ping":
            # Check connection with AT command
            success, msg = controller.ping()
            print(f"[ping] {'SUCCESS' if success else 'FAILED'}: {msg}")
        
        elif args.action == "uptime":
            # Query uptime with AT#uptime=0 command (in seconds)
            success, uptime_val, msg = controller.get_uptime()
            print(f"[uptime] {'SUCCESS' if success else 'FAILED'}: {msg}")
            if uptime_val is not None:
                # Output in hours:minutes format
                print(f"  Uptime: {uptime_val} seconds ({uptime_val // 3600}h {(uptime_val % 3600) // 60}m)")
        
        elif args.action == "gmm":
            # Query product model name with AT+GMM command
            success, model, msg = controller.gmm()
            print(f"[gmm] {'SUCCESS' if success else 'FAILED'}: {msg}")
            if model:
                print(f"  Model: {model}")
        
        elif args.action == "tempsens":
            # Query all temperature sensors with AT#TEMPSENS=2 command
            success, temps, msg = controller.tempsens()
            print(f"[tempsens] {'SUCCESS' if success else 'FAILED'}: {msg}")
            if temps:
                print("  Temperatures:")
                for sensor, temp in temps.items():
                    print(f"    {sensor}: {temp}°C")
    
    finally:
        # Disconnect
        controller.disconnect()
        print("[OK] Disconnected")


if __name__ == "__main__":
    main()

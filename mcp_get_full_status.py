#!/usr/bin/env python3
"""
MCP Actions: get_system_status, get_modem_status, get_full_status
Complete device status reporting using AT commands only
"""

from controller import ATController
from datetime import datetime, timezone
import re
from typing import Dict, Any, Optional
import json


# ============================================================================
# get_system_status - System information
# ============================================================================

def get_system_status(controller: ATController) -> Dict[str, Any]:
    """
    MCP Action: get_system_status
    
    Returns system-level information (function level, firmware switch, USB config, clock, uptime, temperature, etc.)
    
    Returns:
        dict: {"system": {...}}
    """
    result = {
        "system": {
            "function_level": None,
            "firmware_switch": None,
            "usb_config": None,
            "clock": None,
            "uptime_seconds": None,
            "uptime_formatted": None,
            "temperature_celsius": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # AT+CFUN? - Function level
    try:
        response = controller.send_cmd("AT+CFUN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CFUN:\s*(\d+)', decoded)
        if match:
            result["system"]["function_level"] = int(match.group(1))
    except:
        pass
    
    # AT#FWSWITCH? - Firmware switch
    try:
        response = controller.send_cmd("AT#FWSWITCH?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'#FWSWITCH:\s*(\d+)', decoded)
        if match:
            result["system"]["firmware_switch"] = int(match.group(1))
    except:
        pass
    
    # AT#USBCFG? - USB configuration
    try:
        response = controller.send_cmd("AT#USBCFG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'#USBCFG:\s*(\d+)', decoded)
        if match:
            result["system"]["usb_config"] = int(match.group(1))
    except:
        pass
    
    # AT+CCLK? - System clock
    try:
        response = controller.send_cmd("AT+CCLK?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'\+CCLK:\s*"([^"]+)"', decoded)
        if match:
            result["system"]["clock"] = match.group(1)
    except:
        pass
    
    # AT#UPTIME=0 - System uptime
    try:
        response = controller.send_cmd("AT#UPTIME=0", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        match = re.search(r'#UPTIME:\s*(\d+)', decoded)
        if match:
            seconds = int(match.group(1))
            result["system"]["uptime_seconds"] = seconds
            # Format: "X days HH:MM:SS" or "HH:MM:SS"
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, secs = divmod(remainder, 60)
            if days > 0:
                result["system"]["uptime_formatted"] = f"{days} days {hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                result["system"]["uptime_formatted"] = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    except:
        pass
    
    # Temperature - Try multiple AT commands
    temp_commands = ["AT#TEMPMON?", "AT#TEMPSENS=2", "AT#TEMP?", "AT+CMTE?"]
    for cmd in temp_commands:
        try:
            response = controller.send_cmd(cmd, wait_s=0.5)
            decoded = response.decode('ascii', errors='ignore')
            if "ERROR" not in decoded and "OK" in decoded:
                # Extract temperature value (matches integers and floats, positive or negative)
                match = re.search(r'[-+]?\d+\.?\d*', decoded)
                if match:
                    temp_value = float(match.group())
                    # Sanity check: reasonable temperature range for electronic devices
                    if -40 <= temp_value <= 120:
                        result["system"]["temperature_celsius"] = temp_value
                        break
        except:
            continue
    
    return result


# ============================================================================
# get_modem_status - Modem/Device information
# ============================================================================

def get_modem_status(controller: ATController) -> Dict[str, Any]:
    """
    MCP Action: get_modem_status
    
    Returns modem/device information (manufacturer, model, firmware, etc.)
    
    Returns:
        dict: {"modem": {...}}
    """
    result = {
        "modem": {
            "manufacturer": None,
            "model": None,
            "firmware": None,
            "imei_info": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # AT+CGMI - Manufacturer
    try:
        response = controller.send_cmd("AT+CGMI", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            result["modem"]["manufacturer"] = lines[0]
    except:
        pass
    
    # AT+CGMM - Model
    try:
        response = controller.send_cmd("AT+CGMM", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            result["modem"]["model"] = lines[0]
    except:
        pass
    
    # AT+CGMR - Firmware revision
    try:
        response = controller.send_cmd("AT+CGMR", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'AT+' not in l]
        if lines:
            result["modem"]["firmware"] = lines[0]
    except:
        pass
    
    # ATI3 - IMEI info
    try:
        response = controller.send_cmd("ATI3", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        lines = [l.strip() for l in decoded.split('\n') if l.strip() and 'OK' not in l and 'ATI' not in l]
        if lines:
            result["modem"]["imei_info"] = lines[0]
    except:
        pass
    
    return result


# ============================================================================
# get_network_status - Network status (imported from mcp_get_network_status)
# ============================================================================

def parse_cpin(response: str) -> str:
    """Parse AT+CPIN? response"""
    if "ERROR" in response:
        return "NOT_INSERTED"
    match = re.search(r'\+CPIN:\s*([A-Z\s]+)', response)
    if match:
        state = match.group(1).strip()
        if state == "READY":
            return "READY"
        elif "SIM PIN" in state:
            return "PIN_REQUIRED"
        elif "SIM PUK" in state:
            return "PUK_REQUIRED"
        else:
            return state
    return "UNKNOWN"


def parse_cfun(response: str) -> Optional[int]:
    """Parse AT+CFUN? response"""
    if "ERROR" in response:
        return None
    match = re.search(r'\+CFUN:\s*(\d+)', response)
    if match:
        return int(match.group(1))
    return None


def parse_cereg(response: str) -> Dict[str, Any]:
    """Parse AT+CEREG? response"""
    if "ERROR" in response:
        return {"eps": "UNKNOWN", "raw": None}
    match = re.search(r'\+CEREG:\s*\d+,(\d+)', response)
    if match:
        stat = int(match.group(1))
        status_map = {
            0: "NOT_REGISTERED",
            1: "REGISTERED_HOME",
            2: "SEARCHING",
            3: "DENIED",
            4: "UNKNOWN",
            5: "REGISTERED_ROAMING"
        }
        return {"eps": status_map.get(stat, "UNKNOWN"), "raw": stat}
    return {"eps": "UNKNOWN", "raw": None}


def parse_cgatt(response: str) -> Optional[int]:
    """Parse AT+CGATT? response"""
    if "ERROR" in response:
        return None
    match = re.search(r'\+CGATT:\s*(\d+)', response)
    if match:
        return int(match.group(1))
    return None


def parse_cops(response: str) -> Optional[str]:
    """Parse AT+COPS? response"""
    if "ERROR" in response:
        return None
    match = re.search(r'\+COPS:\s*\d+(?:,\d+)?(?:,"([^"]*)")?', response)
    if match and match.group(1):
        return match.group(1)
    return None


def parse_csq(response: str) -> Dict[str, Optional[int]]:
    """Parse AT+CSQ response"""
    if "ERROR" in response:
        return {"rssi_level": None, "rssi_dbm": None}
    match = re.search(r'\+CSQ:\s*(\d+),\d+', response)
    if match:
        rssi = int(match.group(1))
        if rssi == 99:
            return {"rssi_level": rssi, "rssi_dbm": None}
        if rssi == 0:
            dbm = -113
        elif rssi == 31:
            dbm = -51
        else:
            dbm = -113 + (rssi * 2)
        return {"rssi_level": rssi, "rssi_dbm": dbm}
    return {"rssi_level": None, "rssi_dbm": None}


def get_network_status(controller: ATController) -> Dict[str, Any]:
    """
    MCP Action: get_network_status
    
    Returns network status information
    
    Returns:
        dict: {"network_status": {...}}
    """
    result = {
        "network_status": {
            "sim_state": None,
            "registration": {"eps": None, "raw": None},
            "packet_attach": None,
            "operator": None,
            "signal": {"rssi_level": None, "rssi_dbm": None},
            "radio": {"cfun": None},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # AT+CPIN? - SIM state
    try:
        response = controller.send_cmd("AT+CPIN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["sim_state"] = parse_cpin(decoded)
    except:
        result["network_status"]["sim_state"] = "ERROR"
    
    # AT+CFUN? - Radio function level
    try:
        response = controller.send_cmd("AT+CFUN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["radio"]["cfun"] = parse_cfun(decoded)
    except:
        pass
    
    # AT+CEREG? - EPS registration
    try:
        response = controller.send_cmd("AT+CEREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        reg_info = parse_cereg(decoded)
        result["network_status"]["registration"]["eps"] = reg_info["eps"]
        result["network_status"]["registration"]["raw"] = reg_info["raw"]
    except:
        pass
    
    # AT+CGATT? - Packet attach
    try:
        response = controller.send_cmd("AT+CGATT?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["packet_attach"] = parse_cgatt(decoded)
    except:
        pass
    
    # AT+COPS? - Operator
    try:
        response = controller.send_cmd("AT+COPS?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["operator"] = parse_cops(decoded)
    except:
        pass
    
    # AT+CSQ - Signal strength
    try:
        response = controller.send_cmd("AT+CSQ", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        signal_info = parse_csq(decoded)
        result["network_status"]["signal"]["rssi_level"] = signal_info["rssi_level"]
        result["network_status"]["signal"]["rssi_dbm"] = signal_info["rssi_dbm"]
    except:
        pass
    
    return result


# ============================================================================
# get_full_status - Comprehensive status combining all three actions
# ============================================================================

def generate_summary(system: Dict, modem: Dict, network: Dict) -> str:
    """
    Generate human-readable summary from status data
    
    Args:
        system: System status dict
        modem: Modem status dict
        network: Network status dict
        
    Returns:
        str: Human-readable summary
    """
    parts = []
    
    # Device info
    manufacturer = modem.get("manufacturer", "Unknown")
    model = modem.get("model", "Unknown")
    parts.append(f"Device: {manufacturer} {model}")
    
    # SIM state
    sim_state = network.get("sim_state", "UNKNOWN")
    if sim_state == "NOT_INSERTED":
        parts.append("SIM: Not inserted")
    elif sim_state == "READY":
        parts.append("SIM: Ready")
    elif sim_state == "PIN_REQUIRED":
        parts.append("SIM: PIN required")
    else:
        parts.append(f"SIM: {sim_state}")
    
    # Registration
    eps_status = network.get("registration", {}).get("eps", "UNKNOWN")
    if eps_status == "REGISTERED_HOME":
        parts.append("Network: Registered (Home)")
    elif eps_status == "REGISTERED_ROAMING":
        parts.append("Network: Registered (Roaming)")
    elif eps_status == "NOT_REGISTERED":
        parts.append("Network: Not registered")
    elif eps_status == "SEARCHING":
        parts.append("Network: Searching")
    elif eps_status == "DENIED":
        parts.append("Network: Registration denied")
    else:
        parts.append(f"Network: {eps_status}")
    
    # Signal
    rssi_dbm = network.get("signal", {}).get("rssi_dbm")
    if rssi_dbm is not None:
        if rssi_dbm >= -70:
            parts.append(f"Signal: Excellent ({rssi_dbm} dBm)")
        elif rssi_dbm >= -85:
            parts.append(f"Signal: Good ({rssi_dbm} dBm)")
        elif rssi_dbm >= -100:
            parts.append(f"Signal: Fair ({rssi_dbm} dBm)")
        else:
            parts.append(f"Signal: Poor ({rssi_dbm} dBm)")
    else:
        parts.append("Signal: Unavailable")
    
    # Uptime
    uptime_formatted = system.get("uptime_formatted")
    if uptime_formatted:
        parts.append(f"Uptime: {uptime_formatted}")
    
    # Temperature
    temperature = system.get("temperature_celsius")
    if temperature is not None:
        if temperature > 70:
            parts.append(f"Temperature: {temperature:.1f}°C (Warning: High)")
        elif temperature > 50:
            parts.append(f"Temperature: {temperature:.1f}°C (Warm)")
        else:
            parts.append(f"Temperature: {temperature:.1f}°C")
    
    # Overall status
    function_level = system.get("function_level")
    if sim_state == "NOT_INSERTED":
        parts.append("Status: Device running normally, but network unavailable due to missing SIM card")
    elif eps_status in ["REGISTERED_HOME", "REGISTERED_ROAMING"] and rssi_dbm is not None:
        parts.append("Status: Device operating normally with network connection")
    elif function_level is not None and function_level > 0:
        parts.append("Status: Device running, but network connection unavailable")
    else:
        parts.append("Status: Device status unclear")
    
    return " | ".join(parts)


def get_full_status(controller: ATController, silent: bool = False) -> Dict[str, Any]:
    """
    MCP Action: get_full_status
    
    Combines system, modem, and network status into a comprehensive report
    with human-readable summary.
    
    Args:
        controller: Connected ATController instance
        silent: If True, suppress progress messages
        
    Returns:
        dict: Complete status in format:
        {
          "full_status": {
            "system": {...},
            "modem": {...},
            "network": {...},
            "summary": "<human-readable>"
          }
        }
    """
    if not silent:
        print("[INFO] Collecting full device status...")
    
    # Get system status
    if not silent:
        print("  - Getting system status...")
    system_data = get_system_status(controller)
    
    # Get modem status
    if not silent:
        print("  - Getting modem status...")
    modem_data = get_modem_status(controller)
    
    # Get network status
    if not silent:
        print("  - Getting network status...")
    network_data = get_network_status(controller)
    
    # Generate summary
    if not silent:
        print("  - Generating summary...")
    summary = generate_summary(
        system_data["system"],
        modem_data["modem"],
        network_data["network_status"]
    )
    
    # Combine results
    result = {
        "full_status": {
            "system": system_data["system"],
            "modem": modem_data["modem"],
            "network": network_data["network_status"],
            "summary": summary
        }
    }
    
    return result


# ============================================================================
# Test/Demo
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MCP Action: get_full_status")
    print("=" * 70)
    
    controller = ATController(port="COM9")
    
    try:
        print("\n[INFO] Connecting to COM9...")
        if not controller.connect():
            print("[ERROR] Failed to connect")
            exit(1)
        
        print("[OK] Connected\n")
        
        # Execute MCP action
        result = get_full_status(controller)
        
        # Print JSON result
        print("\n[RESULT]")
        print(json.dumps(result, indent=2))
        
        # Print summary separately for easy reading
        print("\n[SUMMARY]")
        print(result["full_status"]["summary"])
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")

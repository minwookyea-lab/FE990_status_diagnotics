#!/usr/bin/env python3
"""
MCP Action: get_network_status
Uses AT commands only to retrieve network status
"""

from controller import ATController
from datetime import datetime, timezone
import re
from typing import Optional, Dict, Any
import json


def parse_cpin(response: str) -> str:
    """
    Parse AT+CPIN? response
    Returns: SIM state string
    """
    if "ERROR" in response:
        return "NOT_INSERTED"
    
    # +CPIN: READY or +CPIN: SIM PIN, etc.
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
    """
    Parse AT+CFUN? response
    Returns: Function level (int) or None
    """
    if "ERROR" in response:
        return None
    
    # +CFUN: 7
    match = re.search(r'\+CFUN:\s*(\d+)', response)
    if match:
        return int(match.group(1))
    
    return None


def parse_cereg(response: str) -> Dict[str, Any]:
    """
    Parse AT+CEREG? response
    Returns: {"eps": <status_string>, "raw": <int>}
    """
    if "ERROR" in response:
        return {"eps": "UNKNOWN", "raw": None}
    
    # +CEREG: n,stat
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
        return {
            "eps": status_map.get(stat, "UNKNOWN"),
            "raw": stat
        }
    
    return {"eps": "UNKNOWN", "raw": None}


def parse_cgatt(response: str) -> Optional[int]:
    """
    Parse AT+CGATT? response
    Returns: 0 (detached), 1 (attached), or None
    """
    if "ERROR" in response:
        return None
    
    # +CGATT: 0 or +CGATT: 1
    match = re.search(r'\+CGATT:\s*(\d+)', response)
    if match:
        return int(match.group(1))
    
    return None


def parse_cops(response: str) -> Optional[str]:
    """
    Parse AT+COPS? response
    Returns: Operator name or None
    """
    if "ERROR" in response:
        return None
    
    # +COPS: mode,format,"operator"
    match = re.search(r'\+COPS:\s*\d+(?:,\d+)?(?:,"([^"]*)")?', response)
    if match and match.group(1):
        return match.group(1)
    
    return None


def parse_csq(response: str) -> Dict[str, Optional[int]]:
    """
    Parse AT+CSQ response
    Returns: {"rssi_level": <int|None>, "rssi_dbm": <int|None>}
    """
    if "ERROR" in response:
        return {"rssi_level": None, "rssi_dbm": None}
    
    # +CSQ: rssi,ber
    match = re.search(r'\+CSQ:\s*(\d+),\d+', response)
    if match:
        rssi = int(match.group(1))
        
        # CSQ=99 means unknown
        if rssi == 99:
            return {"rssi_level": rssi, "rssi_dbm": None}
        
        # Convert RSSI to dBm
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
    
    Executes AT commands in order and builds network status JSON.
    Uses AT commands only (no SSH/shell).
    
    Args:
        controller: Connected ATController instance
        
    Returns:
        dict: Network status in specified JSON format
    """
    # Initialize result structure
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
    
    # 1. AT+CPIN? - SIM state
    try:
        response = controller.send_cmd("AT+CPIN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["sim_state"] = parse_cpin(decoded)
    except Exception as e:
        result["network_status"]["sim_state"] = "ERROR"
        print(f"[WARN] AT+CPIN? failed: {e}")
    
    # 2. AT+CFUN? - Radio function level
    try:
        response = controller.send_cmd("AT+CFUN?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["radio"]["cfun"] = parse_cfun(decoded)
    except Exception as e:
        print(f"[WARN] AT+CFUN? failed: {e}")
    
    # 3. AT+CEREG? - EPS registration
    try:
        response = controller.send_cmd("AT+CEREG?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        reg_info = parse_cereg(decoded)
        result["network_status"]["registration"]["eps"] = reg_info["eps"]
        result["network_status"]["registration"]["raw"] = reg_info["raw"]
    except Exception as e:
        print(f"[WARN] AT+CEREG? failed: {e}")
    
    # 4. AT+CGATT? - Packet attach
    try:
        response = controller.send_cmd("AT+CGATT?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["packet_attach"] = parse_cgatt(decoded)
    except Exception as e:
        print(f"[WARN] AT+CGATT? failed: {e}")
    
    # 5. AT+COPS? - Operator
    try:
        response = controller.send_cmd("AT+COPS?", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        result["network_status"]["operator"] = parse_cops(decoded)
    except Exception as e:
        print(f"[WARN] AT+COPS? failed: {e}")
    
    # 6. AT+CSQ - Signal strength
    try:
        response = controller.send_cmd("AT+CSQ", wait_s=0.5)
        decoded = response.decode('ascii', errors='ignore')
        signal_info = parse_csq(decoded)
        result["network_status"]["signal"]["rssi_level"] = signal_info["rssi_level"]
        result["network_status"]["signal"]["rssi_dbm"] = signal_info["rssi_dbm"]
    except Exception as e:
        print(f"[WARN] AT+CSQ failed: {e}")
    
    return result


# Test/Demo
if __name__ == "__main__":
    print("=" * 60)
    print("MCP Action: get_network_status")
    print("=" * 60)
    
    controller = ATController(port="COM9")
    
    try:
        print("\n[INFO] Connecting to COM9...")
        if not controller.connect():
            print("[ERROR] Failed to connect")
            exit(1)
        
        print("[OK] Connected\n")
        
        # Execute MCP action
        print("[INFO] Executing get_network_status...")
        result = get_network_status(controller)
        
        # Print JSON result
        print("\n[RESULT]")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        controller.disconnect()
        print("\n[OK] Disconnected")


# mcp/runner.py
import json
import shlex
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.json"
_COOLDOWN = {}  # {(tool.cmd): datetime}


def load_schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_exec(template: str, params: dict) -> str:
    cmd = template
    for k, v in params.items():
        cmd = cmd.replace("{{" + k + "}}", str(v))
    return cmd


def check_cooldown(key: str, cooldown_sec: int):
    if cooldown_sec <= 0:
        return
    now = datetime.utcnow()
    until = _COOLDOWN.get(key)
    if until and now < until:
        left = int((until - now).total_seconds())
        raise RuntimeError(f"Cooldown active for {key}: wait {left}s")
    _COOLDOWN[key] = now + timedelta(seconds=cooldown_sec)


def run(tool: str, cmd: str, params: dict, confirm: bool = False, dry_run: bool = False):
    schema = load_schema()
    if schema["tool_name"] != tool:
        raise ValueError(f"Unknown tool {tool}")

    # find command
    spec = None
    for c in schema["commands"]:
        if c["name"] == cmd:
            spec = c
            break
    if spec is None:
        raise ValueError(f"Unknown command {tool}.{cmd}")

    safety = spec.get("safety", {})
    need_confirm = bool(safety.get("confirm", False))
    cooldown_sec = int(safety.get("cooldown_sec", 0))

    if need_confirm and not confirm:
        raise PermissionError(f"{tool}.{cmd} requires confirm=True")

    # cooldown
    check_cooldown(f"{tool}.{cmd}", cooldown_sec)

    # build command
    exec_tpl = spec["exec"]
    command_line = render_exec(exec_tpl, params)

    if dry_run:
        return {"ok": True, "dry_run": True, "command": command_line}

    t0 = time.time()
    try:
        proc = subprocess.run(
            shlex.split(command_line),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        elapsed = int((time.time() - t0) * 1000)
        ok = (proc.returncode == 0)
        return {
            "ok": ok,
            "tool": tool,
            "cmd": cmd,
            "params": params,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        return {
            "ok": False,
            "tool": tool,
            "cmd": cmd,
            "params": params,
            "error": str(e),
            "elapsed_ms": elapsed,
        }

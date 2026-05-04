#!/usr/bin/env python3
"""
Install bexio MCP server for AI assistants.

Detects Claude Desktop, Claude Code, Gemini CLI, and Codex CLI
and configures each one automatically.

Usage:
    python3 scripts/install_mcp.py
    # or directly:
    curl -sSL https://raw.githubusercontent.com/noevu/bexio-cli/main/scripts/install_mcp.py | python3
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# ─── Helpers ─────────────────────────────────────────────────────────────────

def ok(msg):  print(f"  ✓ {msg}")
def info(msg): print(f"  · {msg}")
def warn(msg): print(f"  ⚠ {msg}")
def skip(msg): print(f"  – {msg}")


def run(cmd, silent=False):
    kwargs = {"shell": True}
    if silent:
        kwargs.update({"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL})
    return subprocess.run(cmd, **kwargs)


def command_exists(name):
    return shutil.which(name) is not None


def merge_json_mcp(config_path: Path, server_name: str, server_config: dict) -> bool:
    """Add/update MCP server entry in a JSON config file. Returns True if changed."""
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            warn(f"Could not parse {config_path} — skipping")
            return False

    existing = config.get("mcpServers", {}).get(server_name)
    if existing == server_config:
        skip(f"Already configured in {config_path.name}")
        return False

    config.setdefault("mcpServers", {})[server_name] = server_config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    return True


# ─── Step 1: Install ─────────────────────────────────────────────────────────

def install_package():
    print("\n1. Installing bexio-cli with MCP support")

    if not command_exists("pipx"):
        print("   pipx not found — installing it first...")
        run("pip3 install pipx")
        if not command_exists("pipx"):
            print("\n   ✗ Could not install pipx. Install it manually:")
            print("     pip install pipx")
            sys.exit(1)

    pkg = "git+https://github.com/noevu/bexio-cli[mcp]"
    result = run(f'pipx install "{pkg}"', silent=True)
    if result.returncode != 0:
        # Already installed — force reinstall to pick up [mcp] extra
        run(f'pipx install --force "{pkg}"', silent=True)

    if command_exists("bexio-mcp"):
        ok("bexio-mcp installed and available")
    else:
        warn("bexio-mcp not found on PATH — you may need to run: pipx ensurepath")
        warn("Then restart your terminal and re-run this script.")
        sys.exit(1)


# ─── Step 2: Connect to AI tools ─────────────────────────────────────────────

def setup_claude_desktop():
    system = platform.system()
    if system == "Darwin":
        config_dir = Path.home() / "Library" / "Application Support" / "Claude"
    elif system == "Windows":
        config_dir = Path(os.environ.get("APPDATA", "")) / "Claude"
    else:
        return None  # No Claude Desktop on Linux

    if not config_dir.exists():
        return None

    config_file = config_dir / "claude_desktop_config.json"
    changed = merge_json_mcp(config_file, "bexio", {"command": "bexio-mcp"})
    if changed:
        ok(f"Configured — restart Claude Desktop to activate")
    return True


def setup_claude_code():
    if not command_exists("claude"):
        return None

    # Check if already registered
    result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True, text=True
    )
    if "bexio" in result.stdout:
        skip("Already registered in Claude Code")
        return True

    result = run("claude mcp add bexio -s user -- bexio-mcp", silent=True)
    if result.returncode == 0:
        ok("Registered via: claude mcp add bexio -s user -- bexio-mcp")
    else:
        warn("claude mcp add failed — add manually: claude mcp add bexio -s user -- bexio-mcp")
    return True


def setup_gemini():
    gemini_dir = Path.home() / ".gemini"
    if not gemini_dir.exists() and not command_exists("gemini"):
        return None

    config_file = gemini_dir / "settings.json"
    changed = merge_json_mcp(config_file, "bexio", {"command": "bexio-mcp", "args": []})
    if changed:
        ok(f"Configured in ~/.gemini/settings.json")
    return True


def _codex_desktop_installed():
    """Detect Codex Desktop app (macOS)."""
    desktop_dir = Path.home() / "Library" / "Application Support" / "Codex"
    return desktop_dir.exists()


def setup_codex():
    """Codex CLI and Codex Desktop both use ~/.codex/config.toml."""
    codex_config = Path.home() / ".codex" / "config.toml"
    has_cli = command_exists("codex")
    has_desktop = _codex_desktop_installed()

    if not codex_config.exists() and not has_cli and not has_desktop:
        return None

    label = "Codex CLI + Desktop" if has_desktop else "Codex CLI"

    if codex_config.exists():
        content = codex_config.read_text()
        if "[mcp_servers.bexio]" in content:
            skip(f"Already configured in ~/.codex/config.toml ({label})")
            return True
        block = (
            '\n[mcp_servers.bexio]\n'
            'type = "stdio"\n'
            'command = "bexio-mcp"\n'
            'args = []\n\n'
            '[mcp_servers.bexio.env]\n'
        )
        codex_config.write_text(content + block)
        ok(f"Configured in ~/.codex/config.toml ({label})")
    else:
        codex_config.parent.mkdir(parents=True, exist_ok=True)
        block = (
            '[mcp_servers.bexio]\n'
            'type = "stdio"\n'
            'command = "bexio-mcp"\n'
            'args = []\n\n'
            '[mcp_servers.bexio.env]\n'
        )
        codex_config.write_text(block)
        ok(f"Created ~/.codex/config.toml ({label})")
    return True


# ─── Step 3: Verify auth ─────────────────────────────────────────────────────

def check_auth():
    print("\n3. Checking Bexio authentication")
    result = subprocess.run(["bexio", "auth", "status"], capture_output=True, text=True)
    if "token" in result.stdout.lower() or "found" in result.stdout.lower():
        ok("Token found — ready to use")
    else:
        warn("No API token stored yet.")
        print("\n   Run this to store your Bexio API token:")
        print("   bexio auth login")
        print("\n   Get your token from: Bexio → Settings → API tokens")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("bexio MCP installer")
    print("=" * 40)

    install_package()

    print("\n2. Connecting to AI assistants")

    tools = {
        "Claude Desktop": setup_claude_desktop,
        "Claude Code":    setup_claude_code,
        "Gemini CLI":     setup_gemini,
        "Codex CLI":      setup_codex,
    }

    found = 0
    for name, fn in tools.items():
        result = fn()
        if result is None:
            info(f"{name}: not found, skipping")
        else:
            found += 1

    if found == 0:
        warn("No AI tools detected. Install Claude Desktop, Claude Code, Gemini CLI, or Codex CLI first.")

    check_auth()

    print("\n" + "=" * 40)
    print("Done! Ask your AI: \"Show me my open Bexio invoices\"")


if __name__ == "__main__":
    main()

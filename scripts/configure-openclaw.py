#!/usr/bin/env python3
"""Apply the RK-tested OpenClaw settings without replacing model credentials."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


def configure(config_path, origins=(), dry_run=False):
    path = Path(config_path).expanduser()
    if path.is_symlink():
        raise ValueError("Refusing a symlink; pass the actual instance configuration.")
    original = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(original, dict):
        raise ValueError("Configuration must be a JSON object.")
    updated = copy.deepcopy(original)
    updated.setdefault("agents", {}).setdefault("defaults", {}).setdefault(
        "compaction", {}
    )["mode"] = "safeguard"
    ui = updated.setdefault("gateway", {}).setdefault("controlUi", {})
    ui["dangerouslyDisableDeviceAuth"] = False
    if origins:
        if not isinstance(ui.get("allowedOrigins", []), list):
            raise ValueError("Existing allowedOrigins must be a list.")
        allowed = list(ui.get("allowedOrigins", []))
        for origin in origins:
            parsed = urlsplit(origin)
            if (parsed.scheme not in ("http", "https") or not parsed.hostname
                    or parsed.username or parsed.password
                    or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
                raise ValueError("Each browser origin must be an http(s) origin without credentials or a path.")
            normalized = origin.rstrip("/")
            if normalized not in allowed:
                allowed.append(normalized)
        ui["allowedOrigins"] = allowed
    if updated == original:
        return "Already configured; no changes."
    if dry_run:
        return "Would set safeguard compaction, enable device authentication, and merge supplied origins."
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(path.name + ".before-rk-setup-" + stamp)
    # Create the backup with restrictive permissions before copying any secrets.
    with backup.open("x", encoding="utf-8") as output:
        os.chmod(backup, 0o600)
        output.write(path.read_text(encoding="utf-8"))
    temp_name = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".rk-openclaw-", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(json.dumps(updated, indent=2) + "\n")
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return "Configured. Previous settings saved beside the configuration (mode 600)."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="The instance's openclaw.json")
    parser.add_argument("--panel-origin", action="append", default=[], help="Repeat to allow another browser origin")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(configure(args.config, args.panel_origin, args.dry_run))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        # Do not print parsed configuration or credentials.
        parser.exit(1, f"Configuration failed: {type(error).__name__}. Check the path, JSON structure, and origins.\n")


if __name__ == "__main__":
    main()

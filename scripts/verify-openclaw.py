#!/usr/bin/env python3
"""Verify real OpenClaw chat and exec/write/read tools on an existing instance."""
import argparse
import json
from pathlib import Path
import re
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-dir", required=True, help="JishuShell apps/<instance-id> directory on the RK")
    parser.add_argument("--gateway-url", required=True, help="Actual published Gateway URL, e.g. http://<BOARD_IP>:18789")
    args = parser.parse_args()
    gateway = urlsplit(args.gateway_url)
    if (gateway.scheme not in ("http", "https") or not gateway.hostname
            or gateway.username or gateway.password
            or gateway.path not in ("", "/") or gateway.query or gateway.fragment):
        parser.error("Use an http(s) Gateway origin without credentials or a path.")
    home = Path(args.instance_dir).expanduser() / "openclaw-home" / ".openclaw"
    config = json.loads((home / "openclaw.json").read_text(encoding="utf-8"))
    token = config.get("gateway", {}).get("auth", {}).get("token")
    if not isinstance(token, str) or not token:
        parser.error("No Gateway token found in this instance's configuration.")

    def chat(prompt, user):
        request = Request(
            args.gateway_url.rstrip("/") + "/v1/chat/completions",
            data=json.dumps({"model": "openclaw:main", "user": user,
                             "messages": [{"role": "user", "content": prompt}]}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
        )
        try:
            with urlopen(request, timeout=180) as response:
                result = json.load(response)
        except HTTPError as error:
            raise RuntimeError(f"Gateway returned HTTP {error.code}; inspect its logs locally.") from None
        except URLError:
            raise RuntimeError("Gateway connection failed; check its published address and port.") from None
        return result["choices"][0]["message"]["content"]

    marker = "rk-validation-" + uuid.uuid4().hex
    started = time.time()
    if chat("Reply exactly RK_OPENCLAW_OK.", marker + "-chat").strip() != "RK_OPENCLAW_OK":
        raise RuntimeError("Conversation did not return the expected marker.")
    print("PASS: authenticated OpenClaw conversation.")
    prompt = (
        "Use the exec tool to run uname -m, node --version, and pwd in this container. "
        "Use the write tool to save the ACTUAL results as a Markdown table to "
        "demo/system-report.md in your workspace. Include this validation ID: " + marker + ". "
        "Use the read tool to read the file back, then show the table and saved path. "
        "Do not access credentials or network services. Do the task now without setup questions."
    )
    reply = chat(prompt, marker + "-report")
    report = home / "workspace" / "demo" / "system-report.md"
    text = report.read_text(encoding="utf-8")
    if report.stat().st_mtime < started or marker not in text:
        raise RuntimeError("Report is stale or does not include this run's validation ID.")
    if "aarch64" not in text or not re.search(r"v\d+\.\d+\.\d+", text):
        raise RuntimeError("Report is missing the ARM64 architecture or Node.js version.")
    tools = set()
    for session in (home / "agents" / "main" / "sessions").glob("*.jsonl"):
        if ".trajectory." in session.name or session.stat().st_mtime < started:
            continue
        records = [json.loads(line) for line in session.read_text(encoding="utf-8").splitlines()]
        if marker not in json.dumps(records):
            continue
        for record in records:
            content = record.get("message", {}).get("content", [])
            if isinstance(content, list):
                tools.update(block.get("name") for block in content
                             if isinstance(block, dict) and block.get("type") == "toolCall")
    if not {"exec", "write", "read"}.issubset(tools):
        raise RuntimeError("Could not verify exec, write, and read calls in this run's transcript.")
    print("PASS: fresh report and exec/write/read tool-call records.")
    print("Saved report:", report)
    print(reply)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        if isinstance(error, RuntimeError):
            raise SystemExit(str(error))
        raise SystemExit(f"Verification failed ({type(error).__name__}); check the instance path and local logs.") from None

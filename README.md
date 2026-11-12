# OpenClaw + JishuShell on reComputer RK3576

Install the **JishuShell web panel**, open your RK board on port **8090**, and
manage OpenClaw from the browser.

[中文说明](README.zh-CN.md) · [Detailed setup](docs/jishushell.md) · [Validation](docs/validation.md)

## One-command web-panel setup

On a Linux ARM64 RK3576 board with Bash, curl, network access and sudo privileges:

```bash
curl -fsSL https://raw.githubusercontent.com/inteintegrity/openclaw-jishushell-rk3576/main/scripts/install-jishushell.sh | bash
```

Or clone this repository and run:

```bash
git clone https://github.com/inteintegrity/openclaw-jishushell-rk3576.git
cd openclaw-jishushell-rk3576
bash scripts/install-jishushell.sh
```

The helper checks a pinned official installer's SHA-256 and selects JishuShell
**0.8.7** and the official OpenClaw ARM64 runtime **2026.6.11**. The upstream
installer prepares Node.js, Docker, Nomad and system services; it may request
sudo credentials or installation choices. Existing JishuShell installations are
reused without changing applications, models or credentials.

Use 64-bit Linux, at least 4 GB RAM, and at least **8 GB free disk space**, as
specified by the upstream installation guide. The tested board has 8 GB RAM and
runs Armbian/Debian 12. Only RK3576 was tested for this project.

## Continue in the browser

Open:

```text
http://<BOARD_IP>:8090
```

1. Set an administrator password on first access.
2. Configure a model provider with your own API key and exact model ID; set it
   as default.
3. Select **Install Application → OpenClaw**, enter a name and create it.
4. Apply the tested runtime settings below.
5. Wait for **Running** and an online Gateway, then open chat. Inspect and approve
   the exact browser device pairing request if prompted.

For the public DeepSeek API, choose its corresponding provider. An authenticated
private-LAN OpenAI-compatible gateway in JishuShell 0.8.7 can use the local
**vLLM** provider slot with a descriptive name and its actual `/v1` API URL.
This is the supported LAN routing option; it does not identify the remote
inference engine. A dashboard URL is not an API endpoint. See the
[provider details](docs/jishushell.md#configure-the-model).

### Apply the tested runtime settings

On the RK, from the cloned repository, replace the instance ID and panel origin:

```bash
python3 scripts/configure-openclaw.py \
  --config "$HOME/.jishushell/apps/<INSTANCE_ID>/openclaw-home/.openclaw/openclaw.json" \
  --panel-origin "http://<BOARD_IP>:8090"
```

This sets supported **safeguard compaction** to resolve the observed 2026.6.11
automatic-compaction failure, and keeps normal browser device authentication
enabled. It merges the supplied browser origin, preserves model settings and
credentials, and creates a private backup beside the configuration. Use
`--dry-run` to preview. The Gateway reloads configuration changes.

The upstream template initially skips browser device authentication; the helper
above restores it. It does not approve devices or change administrator passwords.

## Run a real tool task

Ask in chat:

> Use your tools to inspect this OpenClaw container's architecture and Node.js
> version. Save the actual results to demo/system-report.md, read it back, and
> present a short table. Do not access credentials or network services.

Expand activity to inspect command execution, writing and reading. The report
describes the container. In the RK test it reported `aarch64` and Node.js
`v22.23.1`; host Node.js was `v22.23.5`.

For a repeatable verification on the RK:

```bash
python3 scripts/verify-openclaw.py \
  --instance-dir "$HOME/.jishushell/apps/<INSTANCE_ID>" \
  --gateway-url "http://<BOARD_IP>:18789"
```

Use the instance's actual published Gateway port. The verifier checks a real
authenticated reply, requests a fresh report and confirms `exec`, `write` and
`read` tool records. It overwrites `demo/system-report.md` in that instance.
It reads the instance-managed token locally without printing it. The chosen
model receives the prompts and tool results and may charge for requests.

## Inspect the installation

```bash
bash scripts/install-jishushell.sh --check
bash scripts/install-jishushell.sh --dry-run
python3 -m unittest discover -s tests -v
```

The check reuses the existing panel. The dry run verifies the official installer
and prints a plan without sudo or installation. If upstream downloads fail,
transfer the official installer and use `--installer-file /path/to/installer.sh`;
the same checksum is still required. See [download recovery](docs/jishushell.md#when-the-rk-cannot-download-dependencies).

The [validation record](docs/validation.md) distinguishes the actual RK deployment,
helper checks and remaining browser limitations. The one-command wrapper was
checked on an existing installation; it has not been retested on a clean OS.

## Sources and scope

The workflow follows the [Raspberry Pi 5 project](https://github.com/inteintegrity/openclaw-deepseek-pi5)
and [EDATEC's OpenClaw panel guide](https://edatec.cn/docs/clawbox/um/3-booting-the-device/).
The installer entry point adapts the MIT-licensed Raspberry Pi helper.
Official artifacts come from [JishuShell](https://github.com/x-aijishu/jishushell),
Node.js and HashiCorp. This repository contains deployment helpers, not a copy of
the JishuShell or OpenClaw product source.

Model inference uses the configured remote gateway. RKLLM/NPU inference, messaging
channels and browser automation were not tested here. No device passwords,
API keys, private gateway addresses or live instance configurations are bundled.
Helpers are MIT licensed; upstream software retains its own licenses.

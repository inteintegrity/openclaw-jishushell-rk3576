# Detailed RK3576 setup

Turn a reComputer RK3576 into an OpenClaw agent host with JishuShell's web
management panel. Configure a model, create an application, and ask the agent
to run commands and write a report in its own workspace.

The workflow follows the [EDATEC OpenClaw setup guide](https://edatec.cn/docs/clawbox/um/3-booting-the-device/)
and the AI Lab [Raspberry Pi 5 project](https://github.com/inteintegrity/openclaw-deepseek-pi5),
adapted to a freshly installed RK agent stack. EDATEC's device ships with the
stack preinstalled; the RK procedure below includes installation.

## How it works

```text
PC browser → RK3576 JishuShell panel (:8090)
                    ↓ Core API (:8091) + Nomad
              OpenClaw ARM64 container
                    ↓ authenticated model proxy
              OpenAI-compatible model gateway
```

OpenClaw and its workspace run on the RK. In this project, a remote gateway
runs model inference; this does not use RKLLM or the RK NPU. Prompts and tool
results are sent to the selected model service.

## Tested environment and requirements

| Component | Tested configuration |
| --- | --- |
| Board | Seeed reComputer RK3576 devkit, 8 GB RAM |
| Architecture | `aarch64` / Linux ARM64 |
| OS | Armbian 26.05.0-trunk, Debian 12 Bookworm |
| Kernel | `6.1.115-vendor-seeed-rk3576` |
| Host Node.js | `v22.23.5` |
| Docker | `29.6.1` |
| Nomad | `1.6.5`, as selected by the JishuShell installer |
| JishuShell | `0.8.7` |
| OpenClaw runtime image | `ghcr.io/x-aijishu/openclaw-runtime:2026.6.11` |
| Model | Operator-supplied `deepseek-v4.1-flash-1017` gateway model ID |

You need SSH access, sudo privileges, Bash, curl, a PC that can reach the RK,
and a working model API key. The model ID above belongs to the tested gateway;
use your provider's exact ID rather than assuming it exists on another service.

The [upstream installation guide](https://github.com/x-aijishu/jishushell/blob/main/guidance/02-installation.md)
requires at least 8 GB of free disk space. Check available storage first:

```bash
uname -m
cat /etc/os-release
free -h
df -h /
docker ps
```

The test board initially had only 2.7 GB free. Installation required close disk
monitoring and removal of one unused image with the operator's permission.
Prepare more free space before reproducing the project, especially for updates.
Keep existing containers and their volumes unless their owner approves removal.

## Install JishuShell

SSH to your board using its own account and address:

```bash
ssh <USER>@<BOARD_IP>
```

Download the official installer, inspect it, then run it:

```bash
curl -fsSL https://aijishu.com/install.sh -o /tmp/jishushell-install.sh
less /tmp/jishushell-install.sh
bash /tmp/jishushell-install.sh
```

The installer prepares Node.js, Docker, Nomad, the OpenClaw runtime, and systemd
services. If Docker is already installed and running, preserve that installation:

```bash
bash /tmp/jishushell-install.sh --skip-docker
```

Check the services and panel after installation:

```bash
systemctl is-active jishushell jishushell-panel nomad
curl -I http://127.0.0.1:8090
```

All three services should report `active`, and the panel should return HTTP 200.
Open `http://<BOARD_IP>:8090` from your PC and set an administrator password on
first access. The panel and model credentials are separate.

### When the RK cannot download dependencies

The test board timed out fetching the installer and nvm from their upstream
hosts, and Docker registry transfers returned `EOF`. Fetching official artifacts
on a connected computer and transferring them over SSH resolved those downloads.
Node.js and Nomad archives were checked against their published SHA-256 sums;
the ARM64 image's configuration and layers were checked against registry digests.

For a normal Docker-equipped helper computer, an image transfer can use:

```bash
# On a computer with registry access:
docker pull --platform linux/arm64 ghcr.io/x-aijishu/openclaw-runtime:2026.6.11
docker save ghcr.io/x-aijishu/openclaw-runtime:2026.6.11 -o openclaw-arm64.tar
scp openclaw-arm64.tar <USER>@<BOARD_IP>:/tmp/

# On the RK:
docker load -i /tmp/openclaw-arm64.tar
docker image inspect ghcr.io/x-aijishu/openclaw-runtime:2026.6.11
```

Use ARM64 artifacts even when the download computer uses another architecture.
The tested host Node.js was installed under `/opt/jishu-node`, and Nomad under
`~/.jishushell/bin/nomad`. Once those prerequisites were available, the reviewed
installer completed with `--skip-docker --skip-openclaw`; the runtime image was
imported separately. A final `jishushell system reload` reconciled the services.

Importing an image alone is insufficient if an instance still requests `latest`:
Nomad may try the registry again. The tested instance was pinned to the matching
`2026.6.11` image, with its previous configuration backed up. Check the image
used by the actual running container before considering an offline import done.

## Configure the model

In the panel, open **Settings**, add a model provider, and select its default
model. Use your real API base URL and key. A dashboard page is not an API URL.

| Field | Value to supply |
| --- | --- |
| Provider name | A descriptive name, such as `LAN DeepSeek Gateway` |
| API format | OpenAI-compatible chat completions |
| API base URL | `http://<MODEL_GATEWAY_HOST>/v1`, or your provider's actual endpoint |
| API key | Your own gateway key |
| Model ID | The exact ID enabled for that key |

For the authenticated private-LAN gateway in this test, JishuShell 0.8.7 used
the local OpenAI-compatible **vLLM** provider slot (`id: vllm`) with
`api: openai-completions`, a descriptive gateway name, and the supplied key.
This selects JishuShell's supported LAN routing policy; it does not establish
which inference engine the remote gateway uses. The generic `custom` provider
is subject to private-address checks in this release. Keep those checks enabled
and choose the supported local provider configuration for an intentional LAN
endpoint. For the public DeepSeek service, use its corresponding provider.

Set the configured provider as default before creating OpenClaw. Keep keys out
of screenshots, commands committed to Git, and published configuration examples.

## Create OpenClaw

1. Select **Install Application** in the sidebar.
2. Choose **OpenClaw**, enter a name such as **OpenClaw DeepSeek RK3576**, and
   create the application.
3. Wait for the application to become **Running** and its Gateway to come online.
4. Open its chat interface and verify the selected model.
5. Open chat directly through the board IP. The default LAN configuration does
   not require browser-device pairing.

The test instance ID is `openclaw-rk3576-demo`. Its gateway uses port `18789`;
other instances can receive different ports. Prefer opening chat through the
authenticated JishuShell panel. Startup can take longer than container creation,
so a running Docker process alone does not prove the Gateway is ready.

### Tested runtime adjustments

In OpenClaw 2026.6.11, the initial chat produced a model reply but returned HTTP
500 when automatic transcript compaction failed with `reconcile is not a function`
and `Already compacted`. Setting the supported safeguard mode in the instance's
`openclaw-home/.openclaw/openclaw.json` resolved this failure:

```json
{
  "agents": {
    "defaults": {
      "compaction": { "mode": "safeguard" }
    }
  }
}
```

Merge this field into the existing configuration; preserve its model and other
settings. The Gateway detected and reloaded the change. The provider used
JishuShell's default `contextWindow: 128000`; this is a client configuration
value, not a measured context limit for the remote model.

Keep the upstream JishuShell template setting
`gateway.controlUi.dangerouslyDisableDeviceAuth: true` for the documented
`http://<BOARD_IP>:8090` workflow. An earlier revision of this project changed it
to false, causing HTTP secure-context errors and device-approval loops. That
change was incorrect for the requested upstream LAN workflow and has been reverted.

The helper now restores this default while retaining the panel password and
Gateway token. A domain, HTTPS certificate, SSH tunnel and browser-device pairing
are not prerequisites for this trusted-LAN setup. The additional browser-device
identity check is disabled; token and panel authentication remain enabled.

## Verify conversation and tool execution

Start a conversation and ask:

> Reply exactly RK_OPENCLAW_OK.

Then request a report using actual tool results:

> Use your tools to inspect this OpenClaw container's architecture, Node.js
> version, and working directory. Save the actual results to
> demo/system-report.md, read the file back, and show a short table. Do not access
> credentials or network services.

Expand the activity records and verify command execution, file writing, and
reading. Check that `demo/system-report.md` exists in the agent workspace and
matches the reply. The results describe the container; its Node.js version can
differ from the host version in the environment table.

The RK3576 test completed on November 12, 2026:

| Check | Observed result |
| --- | --- |
| Authenticated Gateway conversation | `RK_OPENCLAW_OK` |
| Tool command `uname -m` | `aarch64` |
| Tool command `node --version` | `v22.23.1` inside the container |
| Tool command `pwd` | The instance's `.openclaw/workspace` directory |
| Report write and read | `demo/system-report.md` existed and matched the returned table |

The conversation and report were verified through the authenticated Gateway
chat-completions endpoint and the saved workspace file. Visual browser rendering was not part of this verification. A subsequent
regression check verified an authenticated browser-mode WebSocket handshake
over the plain HTTP LAN IP without device identity or pairing. Existing Frigate,
Home Assistant, and FUXA containers remained running during the installation.

## Maintenance and troubleshooting

```bash
systemctl status jishushell jishushell-panel nomad --no-pager
journalctl -u jishushell -n 50 --no-pager
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
df -h /
jishushell doctor
```

- **Panel unavailable:** check port 8090, the panel service, and PC-to-board
  connectivity. Core listens separately on port 8091.
- **Application stays pending:** inspect Nomad and container logs for image
  download errors, insufficient resources, or a conflicting port.
- **Model request fails:** verify the API endpoint, authentication, model ID,
  and LAN provider selection. A successful direct API request does not prove
  the agent's configured proxy path works.
- **Container runs but chat is unavailable:** wait for Gateway startup and
  inspect its logs. For the documented HTTP-IP setup, rerun the configuration
  helper to restore the upstream LAN default; retain panel and token authentication.
- **Disk nearly full:** plan additional storage before upgrades. Remove only
  specifically approved unused artifacts; avoid broad Docker pruning.

Manage ordinary model switching and application restarts from the panel.
Back up the instance configuration and workspace before changing runtime
versions. Updating host Node.js does not update Node.js inside the container.

## Sources

- [EDATEC first access and OpenClaw workflow](https://edatec.cn/docs/clawbox/um/3-booting-the-device/)
- [JishuShell upstream project](https://github.com/x-aijishu/jishushell)
- [JishuShell installation guide](https://github.com/x-aijishu/jishushell/blob/main/guidance/02-installation.md)
- [Official Node.js v22.23.5 artifacts and checksums](https://nodejs.org/dist/v22.23.5/)
- [Official Nomad 1.6.5 artifacts and checksums](https://releases.hashicorp.com/nomad/1.6.5/)

# RK3576 validation record

Date: 2026-11-12. Hardware: Seeed reComputer RK3576 devkit, 8 GB RAM.

## Actual deployment

- Armbian 26.05.0-trunk / Debian 12 Bookworm, aarch64.
- Kernel: 6.1.115-vendor-seeed-rk3576.
- Host Node.js v22.23.5; Docker 29.6.1; Nomad 1.6.5; JishuShell 0.8.7.
- Official OpenClaw runtime 2026.6.11; container Node.js v22.23.1.
- Services jishushell, jishushell-panel and nomad started.
- Panel returned HTTP 200 on port 8090; the managed instance reached running.
- Authenticated Gateway chat returned RK_OPENCLAW_OK.
- Agent executed uname -m, node --version and pwd, wrote demo/system-report.md,
  and read it back. The transcript contained exec, write and read tool calls.
- Normal browser device authentication was enabled in the instance configuration.
- Existing Frigate, Home Assistant and FUXA containers remained running.

The configured remote gateway exposed the operator-supplied model ID
deepseek-v4.1-flash-1017. This identifier is not a compatibility claim for the
public DeepSeek service or another gateway.

## Installation differences

The actual deployment used the official installer, with checksum-verified Node.js
and Nomad archives and digest-verified ARM64 image artifacts transferred from a
connected computer after board-side downloads failed. Existing Docker was reused.
The official installer completed with --skip-docker --skip-openclaw once the
prerequisites were present, followed by system reload and an imported runtime.

The instance was pinned to the imported 2026.6.11 tag to avoid latest-tag registry
refreshes. Automatic compaction initially caused HTTP 500 after model output;
the supported agents.defaults.compaction.mode=safeguard setting resolved it.
The provider's contextWindow was configured as 128000 (a client setting, not a
measured model limit).

The board initially had 2.7 GB free, below the upstream 8 GB requirement.
One specifically approved unused image was removed. Prepare adequate free space
for a new deployment and for future updates.

## Repository helper checks

The installation helper is adapted from the Raspberry Pi project's MIT-licensed
entry point. It pins official installer commit
f6297e0d27491a5565651b5f941cffc4a9296f63 and SHA-256
160c81ad064eb0a1d5f775775f3cf8922bc234387d29f74d477a186b49ddcf6b.

The following checks passed on the RK3576:

- `bash -n scripts/install-jishushell.sh`.
- `python3 -m unittest discover -s tests -v`: all four configuration-safety
  tests passed (credential preservation, backup, dry run, idempotence and
  rejection of an invalid browser origin).
- `bash scripts/install-jishushell.sh --check`: reused 0.8.7 and verified
  the existing local panel response.
- `bash scripts/install-jishushell.sh --dry-run --installer-file <official-file>`:
  verified the pinned checksum and printed the 0.8.7 / 2026.6.11 plan without
  sudo or installation.
- A deliberately invalid installer file was rejected with a checksum-mismatch
  error before execution.
- `configure-openclaw.py --dry-run` against the live instance reported
  already configured and made no changes.
- `verify-openclaw.py` completed an authenticated conversation, generated a
  fresh report containing its unique validation ID, and verified exec, write
  and read tool calls in that run's transcript.

The Python tests first encountered a Windows sandbox temporary-directory
permission error; they were then run successfully on the actual Linux RK.

## Limits

The wrapper has not been used for a complete fresh-OS install. Clean-install
compatibility, upgrades, other RK models, RKLLM/NPU inference, messaging channels,
browser automation and first-device browser pairing are not established by
these checks. The original chat/tool validation used the authenticated HTTP
Gateway endpoint and inspected the saved file and transcript.

Upstream software and network conditions may change; this record concerns the
versions above.

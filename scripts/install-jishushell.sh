#!/usr/bin/env bash
set -euo pipefail

readonly installer_ref=f6297e0d27491a5565651b5f941cffc4a9296f63
readonly installer_sha256=160c81ad064eb0a1d5f775775f3cf8922bc234387d29f74d477a186b49ddcf6b
readonly installer_url="https://raw.githubusercontent.com/x-aijishu/jishushell/${installer_ref}/install/jishu-install.sh"

show_help() {
  cat <<'HELP'
Install JishuShell on Linux ARM64; open http://<BOARD_IP>:8090.

Usage: bash scripts/install-jishushell.sh [--check | --dry-run] [--installer-file PATH]
  no option           Reuse an existing installation, or run the official installer.
  --check             Verify an existing panel without installing.
  --dry-run           Verify the pinned installer and display its plan without sudo.
  --installer-file    Use a locally transferred official installer (same SHA-256).
  --help              Show this help.

Installs JishuShell 0.8.7 with the official OpenClaw ARM64 runtime 2026.6.11.
The official installer handles Node.js, Docker, Nomad and startup services.
Set the administrator password and model key later in the panel.
HELP
}

mode=install
installer_file=
while (($#)); do
  case "$1" in
    --help|-h) show_help; exit 0 ;;
    --check|--dry-run)
      [[ $mode == install ]] || { echo 'Choose only one mode.' >&2; exit 2; }
      mode=$1 ;;
    --installer-file)
      (($# >= 2)) || { echo '--installer-file requires a path.' >&2; exit 2; }
      installer_file=$2; shift ;;
    *) show_help >&2; exit 2 ;;
  esac
  shift
done
[[ $(uname -s) == Linux ]] || { echo 'Linux ARM64 is required.' >&2; exit 1; }
case $(uname -m) in aarch64|arm64) ;; *) echo 'Linux ARM64 is required.' >&2; exit 1 ;; esac

panel_port=${JISHUSHELL_PANEL_PORT:-8090}
[[ $panel_port =~ ^[0-9]+$ ]] && ((10#$panel_port > 0 && 10#$panel_port < 65536)) || {
  echo 'Invalid panel port.' >&2; exit 1;
}
print_panel() {
  local board_ip
  board_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
  printf 'Local panel: http://localhost:%s\n' "$panel_port"
  if [[ -n $board_ip ]]; then printf 'PC panel: http://%s:%s\n' "$board_ip" "$panel_port"; fi
}

jishu_bin=$(command -v jishushell || true)
if [[ -z $jishu_bin && -x $HOME/.jishushell/bin/jishushell ]]; then
  jishu_bin=$HOME/.jishushell/bin/jishushell
fi
if [[ -n $jishu_bin && $mode != --dry-run ]]; then
  echo 'Reusing existing JishuShell; applications and credentials are preserved.'
  "$jishu_bin" version
  print_panel
  if [[ $mode == --check ]]; then
    command -v curl >/dev/null || { echo 'curl is required.' >&2; exit 1; }
    curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:${panel_port}/" >/dev/null
    echo 'PASS: local panel responds.'
  fi
  exit 0
fi
if [[ $mode == --check ]]; then echo 'JishuShell not found for this user.' >&2; exit 1; fi
command -v sha256sum >/dev/null || { echo 'sha256sum is required.' >&2; exit 1; }

installer=$(mktemp)
trap 'rm -f -- "$installer"' EXIT
if [[ -n $installer_file ]]; then
  cp -- "$installer_file" "$installer"
else
  command -v curl >/dev/null || { echo 'curl is required.' >&2; exit 1; }
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --connect-timeout 20 --max-time 180 --retry 2 "$installer_url" -o "$installer"
fi
printf '%s  %s\n' "$installer_sha256" "$installer" | sha256sum --check --status || {
  echo 'Official installer checksum mismatch; refused to execute.' >&2; exit 1;
}

args=(--jishushell-version 0.8.7 --openclaw-docker-tag ghcr.io/x-aijishu/openclaw-runtime:2026.6.11 --no-autologin)
if [[ $mode == --dry-run ]]; then
  # Upstream main --dry-run still asks for sudo. Source helpers for a plan only.
  bash -c '
    source "$1"
    shift
    parse_args --dry-run "$@"
    detect_os
    detect_arch
    show_install_plan --with-jishushell
  ' -- "$installer" "${args[@]}" </dev/null
  echo 'Plan only; no installation performed.'
  exit 0
fi
if ( : </dev/tty ) 2>/dev/null; then
  bash "$installer" "${args[@]}" </dev/tty
else
  bash "$installer" "${args[@]}" </dev/null
fi
print_panel
echo 'Set up your administrator password, model, and OpenClaw application in the panel.'

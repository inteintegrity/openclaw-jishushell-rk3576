# 在 reComputer RK3576 上运行 OpenClaw + JishuShell

安装 **JishuShell 管理面板**，在电脑浏览器打开开发板的 **8090** 端口，
配置模型并创建 OpenClaw。步骤与[树莓派项目](https://github.com/inteintegrity/openclaw-deepseek-pi5)一致。

[English](README.md) · [详细配置](docs/jishushell.md) · [验证记录](docs/validation.md)

## 一条命令安装

在 RK3576 的 64 位 Linux 上运行，需要 Bash、curl、sudo 权限和网络：

```bash
curl -fsSL https://raw.githubusercontent.com/inteintegrity/openclaw-jishushell-rk3576/main/scripts/install-jishushell.sh | bash
```

也可以克隆后执行：

```bash
git clone https://github.com/inteintegrity/openclaw-jishushell-rk3576.git
cd openclaw-jishushell-rk3576
bash scripts/install-jishushell.sh
```

脚本校验固定版本官方安装器的 SHA-256，选择 JishuShell **0.8.7** 和
OpenClaw ARM64 运行镜像 **2026.6.11**。官方安装器处理 Node.js、Docker、
Nomad 和系统服务，可能要求输入 sudo 密码或选择安装选项。
已有 JishuShell 会直接复用，不修改应用、模型或密码。

按官方要求准备至少 4GB 内存、8GB 可用磁盘空间。实测设备为 8GB RK3576，
运行 Armbian / Debian 12；本项目未验证其他 RK 型号。

## 在浏览器继续配置

打开：

```text
http://<BOARD_IP>:8090
```

1. 首次访问设置管理员密码。
2. 在 **Settings** 配置模型提供商，填写自己的 API Key 和准确的模型 ID，
   并设为默认。
3. 点击 **Install Application → OpenClaw**，填写名称并创建应用。
4. 按下文应用实测运行配置。
5. 等待 **Running** 和 Gateway 在线，直接通过开发板 IP 地址进入聊天。
   默认局域网配置无需浏览器设备配对。

DeepSeek 官方服务使用对应的提供商。JishuShell 0.8.7 接入有认证的内网
OpenAI 兼容网关时，实测使用本地 **vLLM** 提供商选项，填写网关的真实
`/v1` 地址、Key 和模型 ID。这是局域网路由选项，不代表远端实际使用
vLLM 推理。模型管理网页不是 API 地址。[详细说明](docs/jishushell.md#configure-the-model)。

### 应用实测运行配置

在 RK 的项目目录执行，替换实例 ID 和面板地址：

```bash
python3 scripts/configure-openclaw.py \
  --config "$HOME/.jishushell/apps/<INSTANCE_ID>/openclaw-home/.openclaw/openclaw.json" \
  --panel-origin "http://<BOARD_IP>:8090"
```

该脚本使用受支持的 **safeguard** 压缩模式解决实测 2026.6.11 的自动压缩报错，
并恢复 JishuShell 默认的 HTTP 局域网访问配置：
`gateway.controlUi.dangerouslyDisableDeviceAuth: true`。
脚本合并面板来源地址，保留模型配置和凭据，并以权限 600 备份旧配置。
可加 `--dry-run` 预览；Gateway 会重新加载配置。

直接用浏览器打开开发板 IP 地址即可，无需域名、HTTPS 证书、SSH 隧道或
浏览器设备审批。面板密码和 Gateway Token 认证仍然保留；与上游模板一致，
此配置关闭额外的浏览器设备身份校验，适用于可信局域网。脚本不会设置或修改密码。

## 在聊天中生成报告

发送：

> 使用工具检查当前 OpenClaw 容器的架构和 Node.js 版本，将真实结果保存到
> demo/system-report.md，再用工具读回文件，最后展示一个简短表格。
> 不要访问凭据或网络服务。

展开活动记录，核对执行、写入、读取过程。实测容器为 `aarch64`，Node.js
为 `v22.23.1`；宿主机 Node.js 为 `v22.23.5`，两者可能不同。

也可在 RK 上运行自动验证，使用实例实际分配的端口：

```bash
python3 scripts/verify-openclaw.py \
  --instance-dir "$HOME/.jishushell/apps/<INSTANCE_ID>" \
  --gateway-url "http://<BOARD_IP>:18789"
```

验证脚本调用真实模型，检查对话、当前生成的报告以及 `exec`、`write`、`read`
工具记录。它会覆盖实例中的 `demo/system-report.md`，只在本机读取实例 Token，
不会打印 Token。模型服务会接收提示和工具结果，可能产生调用费用。

## 检查与维护

```bash
bash scripts/install-jishushell.sh --check
bash scripts/install-jishushell.sh --dry-run
python3 -m unittest discover -s tests -v
```

下载受限时可传入 `--installer-file /path/to/installer.sh`，仍然要求官方文件
匹配固定校验值；[详细文档](docs/jishushell.md#when-the-rk-cannot-download-dependencies)
记录了 RK 上遇到的下载故障与恢复方式。

一键脚本在已有安装上完成检查与预演，尚未在全新系统上重新验证。
[验证记录](docs/validation.md)列出实际覆盖范围。此方案在 RK 上运行 Agent，
模型推理使用远端网关，不包含已验证的 RKLLM/NPU 推理、消息渠道或浏览器自动化。
仓库不包含设备密码、API Key、内网网关地址或实际实例配置。

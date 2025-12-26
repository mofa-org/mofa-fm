# 使用说明

## 顶层启动脚本

仓库根目录提供 `./start.sh`，用于集中调度四个示例：

```bash
cd /path/to/mofa-fm-check
export OPENAI_API_KEY="实际的 key"    # 或设置 ALIBABA_CLOUD_API_KEY / DEEPSEEK_API_KEY
./start.sh
```

脚本会显示菜单（Chatbot OpenAI / Chatbot Alicloud / Chatbot OpenAI WebSocket Browser / Conference），输入序号即可进入对应示例的 `start.sh`。示例脚本会自动检查二进制、端口和 Python 依赖；退出示例后无需回收顶层脚本。

如需直接运行子目录脚本，也可以进入 `examples/...` 目录执行各自的 `start.sh`。

## Docker 镜像

构建统一运行环境：

```bash
cd /path/to/mofa-fm-check
./build-docker.sh
```

镜像名称为 `mofa-fm/dora-runtime:latest`。进入示例目录执行 `docker-start.sh` 即可在容器中启动数据流：

```bash
cd examples/chatbot-openai-0905
export OPENAI_API_KEY="实际的 key"
./docker-start.sh
```

其它示例的 Docker 启动脚本在各自目录下，使用方式相同。

## 必备准备

1. **API Key**  
   每个示例至少需要一个有效的模型服务 Key。常见环境变量：
   - `OPENAI_API_KEY`
   - `ALIBABA_CLOUD_API_KEY`
   - `DEEPSEEK_API_KEY`  
   运行前请在当前终端设置好相关变量。

2. **主仓库编译**  
   示例依赖 `../dora/target/release/` 中的可执行文件。请在主仓库（通常位于 `../dora`）完成 release 编译，确保以下二进制存在：`dora`、`dora-maas-client`、`dora-conference-bridge`、`dora-conference-controller`、`dora-openai-websocket`（或 `dora-text-websocket`）、`terminal-print` 等。运行 `./start.sh` 时会自动创建符号链接指向这些文件。

完成以上准备后即可通过顶层脚本或各示例脚本快速启动、调试和验证。***

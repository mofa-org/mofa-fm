# Docker 快速开始指南

本指南介绍如何使用 Docker 快速运行 Dora 示例，无需配置复杂的本地环境。

## ✨ 优势

- 🎯 **零配置**：无需安装 Rust、Python 依赖等
- 📦 **环境隔离**：不污染本地环境
- 🔄 **一致性**：所有人使用相同的运行环境
- 🚀 **快速启动**：一行命令即可运行
- 🌏 **中文支持**：完整的中文字符显示支持

## 📋 前置要求

1. **Docker Desktop** (推荐) 或 Docker Engine
   - [Mac 下载](https://www.docker.com/products/docker-desktop/)
   - [Windows 下载](https://www.docker.com/products/docker-desktop/)
   - Linux: `sudo apt-get install docker.io`

2. **NVIDIA GPU** (可选，用于 GPU 加速)
   - 需要安装 NVIDIA Docker Runtime
   - [安装指南](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

3. **API Keys**：至少一个
   - OPENAI_API_KEY
   - ALIBABA_CLOUD_API_KEY
   - DEEPSEEK_API_KEY

## 🚀 快速开始

### 方式一：自动构建（首次运行）

每个 example 的 `docker-start.sh` 会自动检测并构建镜像：

```bash
# 1. 进入任意示例目录
cd examples/chatbot-openai-0905

# 2. 直接运行 Docker 启动脚本
./docker-start.sh

# 脚本会自动：
# - 检测镜像是否存在
# - 不存在则自动构建
# - 提示输入 API Key
# - 启动容器
```

### 方式二：手动构建（推荐）

提前构建镜像，避免每次等待：

```bash
# 1. 在项目根目录构建镜像（仅需一次）
./build-docker.sh

# 2. 运行任意示例
cd examples/chatbot-openai-0905
./docker-start.sh
```

## 📚 使用示例

### Example 1: Chatbot OpenAI

```bash
cd examples/chatbot-openai-0905
export OPENAI_API_KEY="your-key-here"
./docker-start.sh

# 输出：
# ✅ API Key 已设置
# ✅ 已挂载 Rust 二进制文件
# ✅ 检测到 NVIDIA GPU
# 🚀 启动 Docker 容器...
# ...
# ✅ 系统启动完成！
# 连接信息：
#   • WebSocket: ws://localhost:8123
```

### Example 2: Conference Debate

```bash
cd examples/conference
export OPENAI_API_KEY="your-key-here"
./docker-start.sh

# 选择模式：
# 1. Debate (辩论模式)
# 2. Study (学习模式)

# 然后在新终端运行 TUI：
python debate_monitor.py
```

### Example 3: Conference Controller

```bash
cd examples/conference-controller
export OPENAI_API_KEY="your-key-here"
./docker-start.sh

# 选择 dataflow：
# 1. dataflow-complete.yml
# 2. priority-interview.yml
# 3. ratio-debate.yml
# 4. sequential-simple.yml
```

## 🔧 高级用法

### 挂载自定义 Rust 二进制文件

如果你编译了自己的 Rust 节点：

```bash
# 确保 Dora 主仓库在标准位置
~/dora/target/release/

# 或者在相对路径
../../dora/target/release/

# docker-start.sh 会自动检测并挂载
```

### 使用特定的模型目录

```bash
# 模型默认从 ~/.dora/models 挂载
# 如需使用其他目录，修改 docker-start.sh：
-v "$HOME/.dora/models:/root/.dora/models"
# 改为：
-v "/your/custom/path:/root/.dora/models"
```

### GPU 支持

```bash
# 如果有 NVIDIA GPU，脚本会自动检测并启用：
--gpus all

# 查看 GPU 使用情况：
nvidia-smi
```

## 🐛 故障排除

### Q: Docker daemon 未运行

```bash
# Mac/Windows: 启动 Docker Desktop
# Linux:
sudo systemctl start docker
```

### Q: 权限错误（Linux）

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录生效
newgrp docker
```

### Q: 镜像构建失败

```bash
# 清理并重新构建
docker system prune -a
./build-docker.sh
```

### Q: 找不到 Rust 二进制文件

```bash
# 方式 1: 编译 Dora 主仓库
git clone https://github.com/dora-rs/dora.git ~/dora
cd ~/dora
cargo build --release

# 方式 2: 继续运行（使用镜像内置的 CLI）
# docker-start.sh 会提示是否继续
```

### Q: 中文显示乱码

```bash
# 确认容器内 locale 设置：
docker run -it mofa-fm/dora-runtime:latest locale

# 应该显示：
# LANG=zh_CN.UTF-8
# LC_ALL=zh_CN.UTF-8
```

### Q: 端口已被占用

```bash
# 修改 docker-start.sh 中的端口映射：
-p "8123:8123"
# 改为：
-p "8124:8123"  # 宿主机使用 8124
```

## 📊 性能对比

| 配置 | 本地安装 | Docker |
|------|---------|--------|
| 初始设置时间 | 1-2小时 | 10-20分钟 |
| 环境一致性 | ⚠️ 依赖本地环境 | ✅ 完全一致 |
| GPU 支持 | ✅ | ✅ |
| 性能损耗 | 0% | ~2-5% |
| 中文支持 | ⚠️ 需手动配置 | ✅ 内置 |

## 🔄 更新镜像

```bash
# 拉取最新代码
git pull origin pure-dataflow

# 重新构建镜像
./build-docker.sh
```

## 🌐 推送到 Docker Hub（维护者）

```bash
# 登录 Docker Hub
docker login

# 标记镜像
docker tag mofa-fm/dora-runtime:latest mofa-org/dora-runtime:latest

# 推送镜像
docker push mofa-org/dora-runtime:latest

# 用户可以直接拉取：
docker pull mofa-org/dora-runtime:latest
```

## 💡 最佳实践

1. **首次运行**：手动构建镜像 (`./build-docker.sh`)
2. **GPU 用户**：确保安装了 NVIDIA Docker Runtime
3. **模型文件**：提前下载到 `~/.dora/models`
4. **多个 examples**：共享同一个镜像，无需重复构建
5. **开发调试**：使用 volume 挂载，修改代码无需重建镜像

## 📖 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [Dora 框架文档](https://github.com/dora-rs/dora)

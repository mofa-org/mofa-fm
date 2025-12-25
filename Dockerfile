# Dora Runtime Docker Image
# 包含所有必需的依赖、Dora CLI 和 Rust 节点
# 支持中文显示

FROM ubuntu:22.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖 + 中文支持
RUN apt-get update && apt-get install -y \
    curl git build-essential pkg-config \
    python3 python3-pip python3-venv \
    libssl-dev \
    locales \
    fonts-noto-cjk fonts-noto-cjk-extra \
    fonts-wqy-zenhei fonts-wqy-microhei \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 配置中文 locale
RUN locale-gen zh_CN.UTF-8 && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8

# 设置环境变量支持中文
ENV LANG=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:en \
    PYTHONIOENCODING=utf-8

# 创建 python 符号链接
RUN ln -s /usr/bin/python3 /usr/bin/python

# 安装 Dora CLI（使用 pip，快速且轻量）
RUN pip install --no-cache-dir dora-rs-cli

# 安装 Rust（用于编译节点）
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 克隆 dora 主仓库
WORKDIR /tmp
RUN git clone --depth 1 https://github.com/dora-rs/dora.git

# 复制所有需要的 Rust 节点到 dora workspace
COPY node-hub/dora-maas-client /tmp/dora/node-hub/dora-maas-client
COPY node-hub/dora-openai-websocket /tmp/dora/node-hub/dora-openai-websocket
COPY node-hub/dora-conference-bridge /tmp/dora/node-hub/dora-conference-bridge
COPY node-hub/dora-conference-controller /tmp/dora/node-hub/dora-conference-controller
COPY node-hub/terminal-print /tmp/dora/node-hub/terminal-print
COPY node-hub/dora-text-websocket /tmp/dora/node-hub/dora-text-websocket

# 将节点添加到 workspace 并编译所有 Rust 节点
WORKDIR /tmp/dora
RUN sed -i '/^members = \[/a\    "node-hub/dora-maas-client",\n    "node-hub/dora-openai-websocket",\n    "node-hub/dora-conference-bridge",\n    "node-hub/dora-conference-controller",\n    "node-hub/terminal-print",\n    "node-hub/dora-text-websocket",' Cargo.toml && \
    sed -i 's/outfox-openai = { version = "0.1.0"/outfox-openai = { version = "0.2.0"/' node-hub/dora-maas-client/Cargo.toml && \
    cargo build --release \
        --package dora-maas-client \
        --package dora-openai-websocket \
        --package dora-conference-bridge \
        --package dora-conference-controller \
        --package terminal-print \
        --package dora-text-websocket && \
    cp target/release/dora-maas-client /usr/local/bin/ && \
    cp target/release/dora-openai-websocket /usr/local/bin/ && \
    cp target/release/dora-conference-bridge /usr/local/bin/ && \
    cp target/release/dora-conference-controller /usr/local/bin/ && \
    cp target/release/terminal-print /usr/local/bin/ && \
    cp target/release/dora-text-websocket /usr/local/bin/

# 复制 Python node-hub 到镜像
COPY node-hub /app/node-hub

# 安装 Python 节点依赖（使用普通安装，不用 editable 模式）
WORKDIR /app/node-hub
RUN for node in dora-asr dora-primespeech dora-kokoro-tts dora-speechmonitor dora-text-segmenter; do \
        if [ -d "$node" ]; then \
            echo "Installing Python node: $node..." && \
            cd "$node" && \
            pip install --no-cache-dir . && \
            cd .. ; \
        fi \
    done

# 清理构建缓存
RUN rm -rf /tmp/dora && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cargo/registry /root/.cargo/git

# 设置工作目录
WORKDIR /workspace

# 暴露常用端口
EXPOSE 8123 3000

# 默认命令
CMD ["/bin/bash"]

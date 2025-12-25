# Dora Runtime Docker Image
# 包含所有必需的依赖和预编译的 Rust 节点
# 支持中文显示

FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖 + 中文支持
RUN apt-get update && apt-get install -y \
    curl git build-essential pkg-config \
    python3.12 python3-pip python3.12-venv \
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

# 创建 python3 符号链接
RUN ln -s /usr/bin/python3.12 /usr/bin/python

# 安装 Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 克隆并编译 Dora 主仓库（CLI 和基础组件）
WORKDIR /tmp/dora-build
RUN git clone https://github.com/dora-rs/dora.git && \
    cd dora && \
    cargo build --release \
        -p dora-cli \
        -p dora-coordinator \
        -p dora-daemon

# 安装 Dora CLI 和基础组件
RUN cp /tmp/dora-build/dora/target/release/dora /usr/local/bin/ && \
    cp /tmp/dora-build/dora/target/release/dora-coordinator /usr/local/bin/ && \
    cp /tmp/dora-build/dora/target/release/dora-daemon /usr/local/bin/

# 复制 node-hub 到镜像
COPY node-hub /app/node-hub

# 安装 Python 节点依赖
WORKDIR /app/node-hub
RUN for node in dora-asr dora-primespeech dora-kokoro-tts dora-speechmonitor dora-text-segmenter; do \
        if [ -d "$node" ]; then \
            echo "Installing $node..." && \
            pip install --no-cache-dir -e "$node" || echo "Failed to install $node"; \
        fi \
    done

# 清理构建缓存（保留 Rust 工具链）
RUN rm -rf /tmp/dora-build/dora/target \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# 暴露常用端口
EXPOSE 8123 3000

# 默认命令
CMD ["/bin/bash"]

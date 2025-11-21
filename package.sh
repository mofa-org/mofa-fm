#!/bin/bash
# MoFA-FM 打包脚本
# 将项目打包成 tar.gz，排除不需要的文件

set -e

echo "📦 开始打包 MoFA-FM..."

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 输出文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="mofa-fm-${TIMESTAMP}.tar.gz"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/mofa-fm"

echo "📋 复制文件到临时目录..."

# 复制项目文件
mkdir -p "$PACKAGE_DIR"
rsync -av \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='node_modules' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.vscode' \
  --exclude='.idea' \
  --exclude='venv' \
  --exclude='env' \
  --exclude='.env' \
  --exclude='*.sqlite3' \
  --exclude='db.sqlite3' \
  --exclude='media/*' \
  --exclude='staticfiles/*' \
  --exclude='.pytest_cache' \
  --exclude='.coverage' \
  --exclude='*.egg-info' \
  --exclude='celerybeat-schedule' \
  --exclude='dump.rdb' \
  ./ "$PACKAGE_DIR/"

echo "✅ 文件复制完成"

# 创建打包
echo "🗜️  压缩文件..."
cd "$TEMP_DIR"
tar -czf "$PROJECT_ROOT/$OUTPUT_FILE" mofa-fm/

# 清理临时文件
rm -rf "$TEMP_DIR"

# 显示结果
FILE_SIZE=$(du -h "$PROJECT_ROOT/$OUTPUT_FILE" | cut -f1)
echo ""
echo "✅ 打包完成！"
echo "📦 文件: $OUTPUT_FILE"
echo "📏 大小: $FILE_SIZE"
echo ""
echo "📤 上传到服务器后，执行以下命令解压："
echo "   tar -xzf $OUTPUT_FILE"
echo "   cd mofa-fm"
echo "   bash deploy/setup.sh"

#!/bin/bash
# MoFA-FM 服务器部署脚本
# 在服务器上运行此脚本完成部署

set -e

echo "🚀 MoFA-FM 服务器部署脚本"
echo "======================================"

# 检查是否为 root 或有 sudo 权限
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  建议使用 sudo 运行此脚本"
    echo "继续部署将使用当前用户权限..."
    SUDO=""
else
    SUDO="sudo"
fi

# 项目目录（当前脚本所在目录的父目录）
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "📂 项目目录: $PROJECT_ROOT"
echo ""

# 1. 安装系统依赖
echo "📦 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    $SUDO apt-get update
    $SUDO apt-get install -y python3.11 python3.11-venv python3-pip \
        postgresql postgresql-contrib \
        redis-server \
        nginx \
        ffmpeg \
        supervisor
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    $SUDO yum install -y python311 python3-pip \
        postgresql-server postgresql-contrib \
        redis \
        nginx \
        ffmpeg \
        supervisor
else
    echo "⚠️  无法自动安装依赖，请手动安装：Python 3.11, PostgreSQL, Redis, Nginx, FFmpeg, Supervisor"
fi

# 2. 创建 Python 虚拟环境
echo ""
echo "🐍 创建 Python 虚拟环境..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate

# 3. 安装 Python 依赖
echo ""
echo "📚 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements/base.txt
pip install gunicorn  # 生产环境 WSGI 服务器

# 4. 创建 .env 文件（如果不存在）
echo ""
echo "⚙️  配置环境变量..."
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 .env 文件，配置以下内容："
    echo "   - SECRET_KEY（Django 密钥）"
    echo "   - DATABASE_URL（PostgreSQL 连接）"
    echo "   - REDIS_URL（Redis 连接）"
    echo "   - OPENAI_API_KEY（AI 功能，使用 Moonshot/Kimi）"
    echo "   - MINIMAX_API_KEY（语音合成）"
    echo ""
    read -p "按 Enter 继续编辑 .env 文件..."
    ${EDITOR:-nano} .env
else
    echo "✅ .env 文件已存在"
fi

# 5. 创建数据库（如果需要）
echo ""
echo "🗄️  配置数据库..."
read -p "是否需要创建 PostgreSQL 数据库？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "数据库名称 [mofa_fm]: " DB_NAME
    DB_NAME=${DB_NAME:-mofa_fm}
    read -p "数据库用户 [mofa_user]: " DB_USER
    DB_USER=${DB_USER:-mofa_user}
    read -sp "数据库密码: " DB_PASS
    echo

    $SUDO -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    $SUDO -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
    $SUDO -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
    $SUDO -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
    $SUDO -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'Asia/Shanghai';"
    $SUDO -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

    echo ""
    echo "✅ 数据库创建完成"
    echo "请更新 .env 中的 DATABASE_URL："
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
fi

# 6. 运行数据库迁移
echo ""
echo "🔄 运行数据库迁移..."
python manage.py migrate

# 7. 收集静态文件
echo ""
echo "📁 收集静态文件..."
python manage.py collectstatic --noinput

# 8. 创建超级用户（可选）
echo ""
read -p "是否创建 Django 超级用户？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# 9. 创建必要的目录
echo ""
echo "📂 创建媒体文件目录..."
mkdir -p "$PROJECT_ROOT/media/episodes"
mkdir -p "$PROJECT_ROOT/media/covers"
mkdir -p "$PROJECT_ROOT/media/avatars"
mkdir -p "$PROJECT_ROOT/media/references"
mkdir -p "$PROJECT_ROOT/backend/logs"

# 10. 设置文件权限
echo ""
echo "🔒 设置文件权限..."
chmod -R 755 "$PROJECT_ROOT/media"
chmod -R 755 "$PROJECT_ROOT/backend/staticfiles"

echo ""
echo "✅ 基础部署完成！"
echo ""
echo "📋 下一步操作："
echo "1. 配置 systemd 服务："
echo "   sudo cp deploy/systemd/*.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable mofa-fm-django mofa-fm-celery"
echo "   sudo systemctl start mofa-fm-django mofa-fm-celery"
echo ""
echo "2. 配置 Nginx："
echo "   sudo cp deploy/nginx/mofa-fm.conf /etc/nginx/sites-available/"
echo "   sudo ln -s /etc/nginx/sites-available/mofa-fm.conf /etc/nginx/sites-enabled/"
echo "   sudo nginx -t"
echo "   sudo systemctl restart nginx"
echo ""
echo "3. 查看服务状态："
echo "   sudo systemctl status mofa-fm-django"
echo "   sudo systemctl status mofa-fm-celery"
echo ""
echo "4. 查看日志："
echo "   sudo journalctl -u mofa-fm-django -f"
echo "   sudo journalctl -u mofa-fm-celery -f"

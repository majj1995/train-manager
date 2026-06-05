#!/bin/bash
set -e

echo "=== Auto-Train 项目初始化 ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "[1] 安装 Python 依赖..."
cd "$PROJECT_ROOT"
uv sync

echo "[2] 创建数据库和授权..."
read -p "MySQL root 用户名 [root]: " MYSQL_ROOT_USER
MYSQL_ROOT_USER=${MYSQL_ROOT_USER:-root}
read -sp "MySQL root 密码: " MYSQL_ROOT_PASS
echo ""

read -p "应用数据库用户名 [ppsma]: " APP_DB_USER
APP_DB_USER=${APP_DB_USER:-ppsma}
read -sp "应用数据库密码: " APP_DB_PASS
echo ""

read -p "数据库主机 [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "数据库端口 [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}
read -p "数据库名称 [auto_train]: " DB_NAME
DB_NAME=${DB_NAME:-auto_train}

MYSQL_CMD="mysql -h $DB_HOST -P $DB_PORT -u $MYSQL_ROOT_USER -p'$MYSQL_ROOT_PASS'"

echo "  创建数据库 $DB_NAME..."
$MYSQL_CMD -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "  授权用户 $APP_DB_USER..."
$MYSQL_CMD -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$APP_DB_USER'@'$DB_HOST'; FLUSH PRIVILEGES;"

echo "[3] 更新后端配置..."
ENCODED_PASS=$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('$APP_DB_PASS'))")
DATABASE_URL="mysql+pymysql://${APP_DB_USER}:${ENCODED_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

CONFIG_FILE="$SCRIPT_DIR/app/core/config.py"
if [ -f "$CONFIG_FILE" ]; then
    python3 -c "
import re
with open('$CONFIG_FILE', 'r') as f:
    content = f.read()
content = re.sub(
    r'\"mysql+pymysql://[^\"]+\"',
    '\"$DATABASE_URL\"',
    content
)
with open('$CONFIG_FILE', 'w') as f:
    f.write(content)
print('  config.py 已更新')
"
fi

echo "[4] 创建图片目录..."
IMAGE_DIR="$PROJECT_ROOT/data/images"
mkdir -p "$IMAGE_DIR"
echo "  图片目录: $IMAGE_DIR"

echo ""
echo "=== 初始化完成 ==="
echo "启动后端服务后，数据库表会自动创建。"
echo ""
echo "启动命令："
echo "  bash backend/run.sh    # 后端 (端口 8000)"
echo "  bash frontend/run.sh   # 前端 (端口 5173)"
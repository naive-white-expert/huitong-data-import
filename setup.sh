#!/bin/bash
# 慧通数据导入 - 配置初始化脚本

CONFIG_FILE="scripts/config.yaml"

# 检查是否已存在配置文件
if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️ 配置文件已存在: $CONFIG_FILE"
    echo "如需重新初始化，请先删除该文件"
    exit 0
fi

# 测试凭证（base64编码，解码后使用）
CREDS=$(echo 'Y19lZmRhYzUzY2I5YjU0ZGI4YjBjZDpkMzQ3ZjE2ODdjMTg0MjAyYWNiMzczMzRjMWI3Y2EyZQ==' | base64 -d)
CLIENT_ID=$(echo $CREDS | cut -d: -f1)
CLIENT_SECRET=$(echo $CREDS | cut -d: -f2)

# 创建配置文件
cat > "$CONFIG_FILE" << EOF
# 飞书 aPaaS API 凭证配置
# 
# ⚠️ 注意：这是测试凭证，仅供测试使用
# 生产环境请替换为您自己的凭证
#
# 获取凭证：联系飞书 aPaaS 管理员，在「API 凭证管理」中新建凭证

client_id: "$CLIENT_ID"
client_secret: "$CLIENT_SECRET"
EOF

echo "✅ 配置文件已创建: $CONFIG_FILE"
echo ""
echo "⚠️ 这是测试凭证，仅供测试使用"
echo "生产环境请替换为您自己的凭证"
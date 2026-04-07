# 慧通数据导入

飞书 aPaaS 客户线索批量导入工具，支持海尔、卡萨帝、COLMO 三个品牌的客户数据导入。

## 功能特性

- ✅ 支持三种品牌：海尔 (haier)、卡萨帝 (casarte)、COLMO
- ✅ 批量导入（一次最多 100 条）
- ✅ 自动匹配行政区划 ID
- ✅ 生成导入结果文件，包含成功/失败状态和失败原因
- ✅ 完整的错误处理和必填字段校验

## 目录结构

```
慧通数据导入/
├── SKILL.md                    # Skill 说明文档
├── scripts/
│   ├── import_customers.py     # 主导入脚本
│   ├── generate_test_data.py   # 测试数据生成脚本
│   └── config.yaml             # API 凭证配置
├── templates/
│   ├── haier_customer_template.xlsx
│   ├── casarte_customer_template.xlsx
│   └── colmo_customer_template.xlsx
├── references/
│   ├── api.md                  # API 参考文档
│   └── region_mapping.xlsx     # 行政区划映射表
└── test_data/                  # 测试数据目录
```

## 使用方法

### 1. 初始化配置

```bash
chmod +x setup.sh
./setup.sh
```

这将创建 `scripts/config.yaml` 文件，包含测试凭证。

⚠️ **这是测试凭证，仅供测试使用！生产环境请替换为您自己的凭证。**

获取凭证：联系飞书 aPaaS 管理员，在「API 凭证管理」中新建凭证。

### 2. 运行导入

```bash
cd scripts
uv run python import_customers.py <文件路径> --type <品牌>
```

品牌选项：
- `haier` - 海尔意向客户
- `casarte` - 卡萨帝意向客户
- `colmo` - COLMO意向客户

### 3. 查看结果

导入完成后会生成结果文件，在原文件基础上增加两列：
- **导入结果**：成功/失败
- **失败原因**：失败时填写错误信息，成功时为空

## 必填字段

| 列名 | 说明 |
|------|------|
| 手机号 | 客户手机号 |
| 来源 | 线索来源 |
| 跟进细节 | 跟进备注 |

## 可选字段

| 列名 | 说明 |
|------|------|
| 性别 | male/female |
| 区县 | 区县名称 |
| 客户是否授权联系 | 是/否 |
| 录音文本 | 录音转文字 |
| 录音链接 | 录音URL |
| 省市 | 行政区名称（自动匹配ID） |

## API 频率限制

- 每个 API 凭证：**15 QPS**

## License

MIT
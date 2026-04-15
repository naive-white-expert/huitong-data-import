---
name: huitong-data-import
version: 1.5.0
description: 飞书 aPaaS 客户线索批量导入工具，支持海尔/卡萨帝/COLMO品牌。
emoji: 📤
homepage: https://github.com/naive-white-expert/huitong-data-import
metadata:
  openclaw:
    requires:
      bins:
        - uv
        - python3
---

# 慧通数据导入

将 Excel/CSV 文件中的客户线索批量导入飞书 aPaaS 慧通系统。

## 触发场景

- 用户表达诉求"上传慧通线索"、"导入慧通线索"、"上传客户线索"
- 用户提供 Excel/CSV 文件要求导入客户记录
- 用户提到"海尔客户"、"卡萨帝客户"、"COLMO客户"、"意向客户导入"

## 工作流程

收到诉求 → 检查凭证配置 → 确认品牌类型 → 提供导入模板 → 执行导入。

三种品牌均支持批量接口（一次最多 100 条）。使用前需配置飞书 aPaaS 的 Client ID 和 Client Secret。

## ⚠️ 安全约束

**导入过程中禁止修改用户提供的数据内容！**

- ❌ 禁止因导入失败而修改字段值（如手机号、沟通细节等）
- ❌ 禁止自动填充或替换空白字段
- ❌ 禁止删除或跳过失败记录后继续导入其他记录
- ❌ 禁止传非白名单字段（只允许传以下字段）
- ✅ 导入失败时如实记录失败原因，不做任何修改
- ✅ 严格按用户提供的内容逐条尝试导入
- ✅ 来源字段固定为 'JD'，自动填充，无需用户提供

---

## 字段规则

### 固定值（自动填充）
| 字段 | 固定值 | 说明 |
|------|--------|------|
| 来源 | `JD` | 自动填充，无需用户提供 |

### 必传字段（缺失需确认）
| 字段 | API字段名 | 说明 |
|------|-----------|------|
| 手机号 | `phone_number` | 客户手机号 |
| 沟通细节 | `details` | 跟进备注 |
| 省市 | `province_city` | 码值，自动匹配ID |
| 区县 | `district` | 文本值 |
| 录音文本 | `recording_text` | 录音转文字 |
| 录音链接 | `recording_link` | 录音URL |

### 可选字段（有就传，没有不传，不确认）
| 字段 | API字段名 | 说明 |
|------|-----------|------|
| 性别 | `gender` | male/female |
| 是否授权联系 | `customer_authorized_contact` | 是/否 |

### 禁止字段
**其他所有字段均禁止传！** 不在白名单的字段会被忽略。

---

## 输出文件

导入完成后，生成结果文件（在原文件基础上增加两列）：

| 新增列 | 说明 |
|--------|------|
| **导入结果** | 成功/失败 |
| **失败原因** | 失败时填写错误信息，成功时为空 |

## 工作流程

### 步骤 1：用户表达诉求

当用户说：
- "上传慧通线索"
- "导入慧通线索"
- "上传客户线索"

→ 触发此 skill

---

### 步骤 2：检查凭证配置

首先确认是否已配置飞书 aPaaS 凭证（`client_id` + `client_secret`）。

**未配置** → 引导用户配置：

> 获取凭证：联系飞书 aPaaS 管理员，在「API 凭证管理」中新建凭证。

配置方式（三选一）：
```bash
# 方式一：配置文件
cp scripts/config.yaml.example scripts/config.yaml

# 方式二：环境变量
export CASARTE_CLIENT_ID="xxx"
export CASARTE_CLIENT_SECRET="xxx"

# 方式三：命令行参数
--client-id "xxx" --client-secret "xxx"
```

**已配置** → 继续下一步

---

### 步骤 3：确认品牌类型

询问用户："请确认要导入哪个品牌？"

| 类型 | 说明 |
|------|------|
| **haier** | 海尔意向客户 |
| **casarte** | 卡萨帝意向客户 |
| **colmo** | COLMO意向客户 |

---

### 步骤 4：提供导入模板

用户确认品牌后，提供对应的 Excel 模板文件：

| 品牌 | 模板文件 |
|------|----------|
| 海尔 | `templates/haier_customer_template.xlsx` |
| 卡萨帝 | `templates/casarte_customer_template.xlsx` |
| COLMO | `templates/colmo_customer_template.xlsx` |

模板位置：`~/.openclaw/workspace/skills/慧通数据导入/templates/`

告知用户：
> "模板已准备好，请按模板格式填写客户数据，填写完成后发给我执行导入。"

---

### 步骤 5：执行导入

收到用户填好的文件后，执行导入：

```bash
cd ~/.openclaw/workspace/skills/慧通数据导入/scripts
uv run python import_customers.py {文件路径} --type {品牌}
```

---

### 步骤 6：输出结果

汇报导入结果：
- 成功数
- 失败数
- 错误详情（如有）

---

## 支持的文件格式

- Excel: `.xlsx`, `.xls`
- CSV: `.csv` (UTF-8)

---

## 文档更新规范

### operation-log.md 更新时机

**以下情况必须更新 operation-log.md**：

| 触发场景 | 更新内容 |
|----------|----------|
| 修改凭证配置 | 更新记录表：版本号 + 更新内容 |
| 修改字段规则 | 更新记录表：版本号 + 更新内容 |
| 修改脚本逻辑 | 更新记录表：版本号 + 更新内容 |
| 执行导入任务 | 导入记录表：时间、品牌、文件、成功数、失败数 |

**更新记录格式**：
```
| 时间 | 版本 | 更新内容 | 更新人 |
|------|------|----------|--------|
| 2026-04-15 21:25 | v1.1 | 更换正式环境凭证 | 康睿 |
```

**导入记录格式**：
```
| 时间 | 品牌 | 文件 | 成功数 | 失败数 | 备注 |
|------|------|------|--------|--------|------|
| 2026-04-15 22:00 | haier | 客户数据.xlsx | 50 | 2 | 手机号格式错误 |
```

### .upload-record.md 查看时机

**发布 Skill 前必须查看 .upload-record.md**：

- 确认当前版本号
- 确认发布位置（GitHub / ClawHub）
- 确认发布命令
- 发布完成后更新发布历史

---

## 文档引用

> **详细方法**: [scripts/import_customers.py](scripts/import_customers.py) - 导入脚本实现
> 
> **API参考**: [references/api.md](references/api.md) - 飞书 aPaaS API 文档
> 
> **更新记录**: [operation-log.md](operation-log.md) - 版本更新历史和导入记录

---

## 输出文件管理

| 文件类型 | 存储路径 |
|----------|----------|
| 导入结果文件 | 原文件同目录，命名：`{原文件名}_导入结果_{时间戳}.xlsx` |
| 模板文件 | `templates/{品牌}_customer_template.xlsx` |
| 配置文件 | `config.yaml` |
| 更新记录 | `operation-log.md` |

---

## API 参考

见 [references/api.md](references/api.md)

频率限制：**15 QPS**
# 飞书 aPaaS API 参考

## 基础信息

- **接口域名**: `ae-openapi.feishu.cn`
- **Namespace**: `package_e47f7d__c`

## 客户对象

| 类型 | 对象名 | 接口路径 | 模式 |
|------|--------|----------|------|
| 海尔 | `haier_customer` | `records_batch` | 批量 |
| 卡萨帝 | `casarte_customer` | `records_batch` | 批量 |
| COLMO | `colmo_customer` | `records_batch` | 批量 |

> 三种客户类型均使用批量接口，一次最多 **100 条记录**

---

## 获取应用 Token

### 请求
```
POST https://ae-openapi.feishu.cn/auth/v1/appToken
Content-Type: application/json

{
  "clientId": "{Client ID}",
  "clientSecret": "{Client Secret}"
}
```

### 响应
```json
{
  "code": "0",
  "msg": "success",
  "data": {
    "accessToken": "T:xxx...",
    "expireTime": 1775577322888
  }
}
```

---

## 批量创建客户记录

### 请求
```
POST https://ae-openapi.feishu.cn/v1/data/namespaces/package_e47f7d__c/objects/{object}/records_batch
Authorization: {Token}
Content-Type: application/json

注意：Authorization 直接使用 token，不需要 Bearer 前缀

{
  "records": [
    {
      "phone_number": "13800138000",
      "source": "官网咨询",
      "details": "客户对洗衣机感兴趣",
      "gender": "male",
      "address": "北京市朝阳区xxx",
      "district": "朝阳区"
    },
    {
      "phone_number": "13900139000",
      "source": "电话咨询",
      "details": "意向购买冰箱"
    }
  ]
}
```

> `{object}` 可为：`haier_customer`、`casarte_customer`、`colmo_customer`

### 响应
```json
{
  "code": "0",
  "msg": "success",
  "data": {
    "items": [
      {"_id": "12345", "success": true},
      {"_id": "12346", "success": true}
    ]
  }
}
```

---

## 字段说明

### 公共字段（三种类型通用）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone_number` | string | ✅ | 手机号 |
| `source` | string | ✅ | 来源 |
| `details` | string | ✅ | 跟进细节 |
| `customer_authorized_contact` | string | | 客户是否授权联系 |
| `gender` | string | | 性别：`male`/`female` |
| `district` | string | | 区县 |
| `recording_text` | string | | 录音文本 |
| `recording_link` | string | | 录音链接 |
| `province_city` | object | | 省市（行政区划） |
| `province_city._id` | string | | 行政区 ID |

### COLMO 特有字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `manual_post` | string | 手动推送：`option_3fab93d4b13`(推送) |
| `follow_up_details` | string | 跟进情况 |
| `feedback` | string | 客户反馈 |

---

## 频率限制

- 每个 API 凭证：**15 QPS**
- 超限错误码：`k_op_ec_20003`

---

## 错误码

| code | 说明 |
|------|------|
| 0 | 成功 |
| k_op_ec_20003 | 频率超限 |
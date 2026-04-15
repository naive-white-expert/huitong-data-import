#!/usr/bin/env python3
"""
飞书 aPaaS 慧通客户记录导入脚本

功能：
1. 解析 Excel/CSV 文件
2. 获取飞书 aPaaS Token
3. 批量创建客户记录
4. 生成导入结果文件

用法：
  python import_customers.py <文件路径> [--type <品牌>]

配置文件格式 (config.yaml):
  client_id: "xxx"
  client_secret: "xxx"
"""

import argparse
import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    import requests
    import pandas as pd
    import yaml
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: uv pip install requests pandas pyyaml openpyxl")
    sys.exit(1)

# API 配置
API_BASE = "https://ae-openapi.feishu.cn"
NAMESPACE = "package_e47f7d__c"

# 行政区划映射文件路径
REGION_MAPPING_FILE = Path(__file__).parent.parent / "references" / "region_mapping.xlsx"

# 支持的客户类型
CUSTOMER_TYPES = {
    "casarte": {
        "object": "casarte_customer",
        "batch": True,
        "endpoint": "/v1/data/namespaces/{namespace}/objects/{object}/records_batch",
    },
    "haier": {
        "object": "haier_customer",
        "batch": True,
        "endpoint": "/v1/data/namespaces/{namespace}/objects/{object}/records_batch",
    },
    "colmo": {
        "object": "colmo_customer",
        "batch": True,
        "endpoint": "/v1/data/namespaces/{namespace}/objects/{object}/records_batch",
    },
}

# 字段白名单：只允许传这些字段（其他字段禁止）
# 来源固定为 'JD'，无需用户提供
ALLOWED_FIELDS = {
    "phone_number": "required",      # 必传
    "details": "required",           # 必传（沟通细节）
    "province_city": "required",     # 必传（省市，码值）
    "district": "required",          # 必传（区县，文本）
    "recording_text": "required",    # 必传（录音文本）
    "recording_link": "required",    # 必传（录音链接）
    "gender": "optional",            # 可选，有就传
    "customer_authorized_contact": "optional",  # 可选，有就传
}

# 字段映射：文件列名 -> API 字段名（只保留白名单字段）
FIELD_MAPPING = {
    # 必传字段
    "手机号": "phone_number",
    "手机": "phone_number",
    "电话": "phone_number",
    "沟通细节": "details",
    "跟进细节": "details",
    "跟进详情": "details",
    "备注": "details",
    "省市": "province_city",
    "区县": "district",
    "区": "district",
    # 可选字段
    "录音文本": "recording_text",
    "录音链接": "recording_link",
    "性别": "gender",
    "客户是否授权联系": "customer_authorized_contact",
    "授权联系": "customer_authorized_contact",
}

# 固定值字段（自动填充，无需用户提供）
FIXED_VALUES = {
    "source": "JD",  # 来源固定为 JD
}

# 性别映射
GENDER_MAPPING = {
    "男": "male",
    "男士": "male",
    "先生": "male",
    "女": "female",
    "女士": "female",
    "小姐": "female",
}

# 行政区划数据缓存
_region_cache = None


def load_region_mapping() -> dict:
    """加载行政区划映射数据，返回 {名称: ID} 字典"""
    global _region_cache
    
    if _region_cache is not None:
        return _region_cache
    
    if not REGION_MAPPING_FILE.exists():
        print(f"⚠️ 行政区划映射文件不存在: {REGION_MAPPING_FILE}")
        _region_cache = {}
        return _region_cache
    
    try:
        df = pd.read_excel(REGION_MAPPING_FILE)
        
        mapping = {}
        for _, row in df.iterrows():
            name = row.get("名称（中文）")
            id_val = row.get("ID")
            if pd.notna(name) and pd.notna(id_val):
                mapping[str(name).strip()] = str(id_val)
        
        _region_cache = mapping
        print(f"✅ 已加载 {len(mapping)} 个行政区划")
        return mapping
    except Exception as e:
        print(f"❌ 加载行政区划失败: {e}")
        _region_cache = {}
        return _region_cache


def find_region_id(region_name: str) -> str:
    """根据中文名称查找行政区划ID"""
    mapping = load_region_mapping()
    
    name = region_name.strip()
    
    # 处理"省+市"组合格式（如 "广东省深圳市"）
    provinces = ['北京市', '天津市', '上海市', '重庆市', '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省', 
                 '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省', 
                 '广东省', '海南省', '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省',
                 '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门',
                 '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
                 '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
                 '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾']
    
    for province in provinces:
        if name.startswith(province):
            city_part = name[len(province):]
            if city_part in mapping:
                return mapping[city_part]
            city_clean = city_part.rstrip('市').rstrip('区').rstrip('县')
            for candidate in [city_clean, city_clean + '市', city_clean + '区']:
                if candidate in mapping:
                    return mapping[candidate]
    
    if "/" in name:
        parts = [p.strip() for p in name.split("/")]
        for part in reversed(parts):
            clean_part = part.rstrip("省").rstrip("市").rstrip("区").rstrip("县")
            for candidate in [part, clean_part, clean_part + "市", clean_part + "区"]:
                if candidate in mapping:
                    return mapping[candidate]
    
    if name in mapping:
        return mapping[name]
    
    suffixes = ["市", "区", "县", "镇", "乡", "街道", "村"]
    for suffix in suffixes:
        if name.endswith(suffix):
            short_name = name[:-len(suffix)]
            if short_name in mapping:
                return mapping[short_name]
            for s in suffixes:
                if short_name + s in mapping:
                    return mapping[short_name + s]
    
    for key in mapping:
        if key.startswith(name) or name.startswith(key):
            return mapping[key]
    
    raise ValueError(f"找不到行政区划 '{region_name}' 对应的ID")


def load_config(config_path: Path = None) -> dict:
    """加载配置（优先级：环境变量 > 根目录配置文件 > scripts配置文件）"""
    config = {}
    
    # 1. 环境变量
    env_client_id = os.environ.get("CASARTE_CLIENT_ID")
    env_client_secret = os.environ.get("CASARTE_CLIENT_SECRET")
    
    if env_client_id:
        config["client_id"] = env_client_id
    if env_client_secret:
        config["client_secret"] = env_client_secret
    
    # 2. 根目录配置文件
    root_config_path = Path(__file__).parent.parent / "config.yaml"
    if root_config_path.exists():
        with open(root_config_path, "r", encoding="utf-8") as f:
            root_config = yaml.safe_load(f) or {}
            credentials = root_config.get("credentials", {})
            if "client_id" not in config and credentials.get("client_id"):
                config["client_id"] = credentials["client_id"]
            if "client_secret" not in config and credentials.get("client_secret"):
                config["client_secret"] = credentials["client_secret"]
    
    # 3. scripts目录配置文件（兼容旧配置）
    file_config = {}
    
    if config_path and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = yaml.safe_load(f) or {}
    
    if not file_config:
        scripts_config_path = Path(__file__).parent / "config.yaml"
        if scripts_config_path.exists():
            with open(scripts_config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
    
    for key in ["client_id", "client_secret"]:
        if key not in config and key in file_config:
            config[key] = file_config[key]
    
    return config


def get_token(client_id: str, client_secret: str) -> str:
    """获取飞书 aPaaS Token"""
    url = f"{API_BASE}/auth/v1/appToken"
    resp = requests.post(url, json={
        "clientId": client_id,
        "clientSecret": client_secret
    })
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("code") != "0":
        raise Exception(f"获取 Token 失败: {data}")
    
    return data["data"]["accessToken"]


def normalize_row(row: dict) -> tuple:
    """标准化行数据，只处理白名单字段
    
    Returns:
        (result_dict, error_msg) - 成功时 error_msg 为 None
    """
    result = {}
    error = None
    
    # 先添加固定值字段
    for field, value in FIXED_VALUES.items():
        result[field] = value
    
    # 只处理白名单字段，其他字段忽略
    for col_name, value in row.items():
        # 保留原始列名（用于结果文件）
        if col_name.strip() in ["导入结果", "失败原因"]:
            continue
        
        if pd.isna(value):
            continue
        
        api_field = FIELD_MAPPING.get(col_name.strip())
        if not api_field:
            # 非白名单字段，忽略（不传）
            continue
        
        # 检查是否在白名单中
        if api_field not in ALLOWED_FIELDS:
            continue
        
        str_value = str(value).strip()
        
        # 性别字段映射（不修改原始值，只转换API格式）
        if api_field == "gender":
            str_value = GENDER_MAPPING.get(str_value, str_value)
        
        # 省市字段 - 自动查找ID（码值）
        if api_field == "province_city":
            try:
                region_id = find_region_id(str_value)
                result[api_field] = {"_id": region_id}
            except ValueError as e:
                error = str(e)
        # 区县字段 - 文本值
        elif api_field == "district":
            result[api_field] = str_value
        else:
            result[api_field] = str_value
    
    return result, error


def create_records_batch(token: str, records: list, customer_type: str = "haier") -> dict:
    """批量创建客户记录（一次最多 100 条）"""
    config = CUSTOMER_TYPES[customer_type]
    url = f"{API_BASE}{config['endpoint'].format(namespace=NAMESPACE, object=config['object'])}"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    resp = requests.post(url, headers=headers, json={"records": records})
    return resp.json()


def validate_record(record: dict) -> list:
    """验证必填字段（只检查白名单中的必传字段）"""
    required = ["phone_number", "details", "province_city", "district", "recording_text", "recording_link"]
    missing = []
    
    for field in required:
        if not record.get(field):
            # 转换为中文名称便于用户理解
            field_names = {
                "phone_number": "手机号",
                "details": "沟通细节",
                "province_city": "省市",
                "district": "区县",
                "recording_text": "录音文本",
                "recording_link": "录音链接",
            }
            missing.append(field_names.get(field, field))
    
    return missing


def import_from_file(file_path: Path, config: dict, customer_type: str = "haier") -> Path:
    """从文件导入客户记录，生成结果文件
    
    Returns:
        结果文件路径
    """
    type_config = CUSTOMER_TYPES.get(customer_type)
    if not type_config:
        print(f"❌ 不支持的客户类型: {customer_type}")
        print(f"   支持的类型: {list(CUSTOMER_TYPES.keys())}")
        sys.exit(1)
    
    # 读取文件
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    print(f"📄 读取文件: {file_path}")
    print(f"📊 共 {len(df)} 条记录")
    print(f"🏷️ 客户类型: {customer_type} ({type_config['object']})")
    print(f"⚡ 接口模式: 批量创建 (每批最多 100 条)\n")
    
    if len(df) == 0:
        print("⚠️ 文件为空，没有记录需要导入")
        return None
    
    # 获取认证信息
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    
    if not client_id or not client_secret:
        print("❌ 缺少认证信息")
        sys.exit(1)
    
    # 获取 Token
    print("🔑 获取 Token...")
    try:
        token = get_token(client_id, client_secret)
        print("✅ Token 获取成功\n")
    except Exception as e:
        print(f"❌ 获取 Token 失败: {e}")
        sys.exit(1)
    
    # 初始化结果列
    df["导入结果"] = ""
    df["失败原因"] = ""
    
    # 解析并导入每条记录
    success_count = 0
    fail_count = 0
    batch_size = 100
    
    # 按批次处理
    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        batch_indices = range(batch_start, batch_end)
        
        # 解析本批次的记录
        batch_records = []
        batch_row_nums = []
        pre_errors = {}  # 预处理错误（如行政区划找不到）
        
        for idx in batch_indices:
            row_num = idx + 2  # Excel 行号（从第2行开始，第1行是标题）
            row = df.iloc[idx].to_dict()
            record, error = normalize_row(row)
            
            if error:
                # 预处理失败（如行政区划错误）
                df.at[idx, "导入结果"] = "失败"
                df.at[idx, "失败原因"] = error
                fail_count += 1
                print(f"  ❌ 第 {row_num} 行: {error}")
                continue
            
            # 验证必填字段
            missing = validate_record(record)
            if missing:
                df.at[idx, "导入结果"] = "失败"
                df.at[idx, "失败原因"] = f"缺少必填字段: {missing}"
                fail_count += 1
                print(f"  ❌ 第 {row_num} 行: 缺少必填字段 {missing}")
                continue
            
            batch_records.append(record)
            batch_row_nums.append((idx, row_num))
        
        if not batch_records:
            continue
        
        print(f"📦 批次 {batch_start//batch_size + 1}: 导入 {len(batch_records)} 条记录...")
        
        # 执行批量导入
        try:
            result = create_records_batch(token, batch_records, customer_type)
            
            if result.get("code") == "0":
                items = result.get("data", {}).get("items", [])
                
                for i, item in enumerate(items):
                    idx, row_num = batch_row_nums[i]
                    
                    if item.get("success"):
                        df.at[idx, "导入结果"] = "成功"
                        df.at[idx, "失败原因"] = ""  # 成功时不写原因
                        success_count += 1
                        print(f"  ✅ 第 {row_num} 行: 成功")
                    else:
                        # 解析错误信息
                        errors = item.get("errors", [])
                        error_msgs = []
                        for err in errors:
                            error_msgs.append(err.get("message", str(err)))
                        error_str = "; ".join(error_msgs) if error_msgs else "未知错误"
                        
                        df.at[idx, "导入结果"] = "失败"
                        df.at[idx, "失败原因"] = error_str
                        fail_count += 1
                        print(f"  ❌ 第 {row_num} 行: {error_str}")
            else:
                # 整批失败（如权限问题）
                error_msg = result.get("msg", str(result))
                for idx, row_num in batch_row_nums:
                    df.at[idx, "导入结果"] = "失败"
                    df.at[idx, "失败原因"] = error_msg
                    fail_count += 1
                    print(f"  ❌ 第 {row_num} 行: {error_msg}")
        
        except Exception as e:
            # 异常情况
            error_msg = str(e)
            for idx, row_num in batch_row_nums:
                df.at[idx, "导入结果"] = "失败"
                df.at[idx, "失败原因"] = error_msg
                fail_count += 1
                print(f"  ❌ 第 {row_num} 行: {error_msg}")
        
        # 频率限制
        time.sleep(0.1)
    
    # 生成结果文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"{file_path.stem}_导入结果_{timestamp}.xlsx"
    result_path = file_path.parent / result_filename
    
    df.to_excel(result_path, index=False)
    
    # 汇总
    print(f"\n{'='*50}")
    print(f"📋 导入完成 ({customer_type})")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {fail_count}")
    print(f"📄 结果文件: {result_path}")
    print(f"{'='*50}")
    
    return result_path


def main():
    parser = argparse.ArgumentParser(description="飞书 aPaaS 慧通客户记录批量导入")
    parser.add_argument("file", help="要导入的文件 (Excel/CSV)")
    parser.add_argument("--type", "-t", choices=["casarte", "haier", "colmo"], default="haier",
                        help="客户类型: haier(海尔)/casarte(卡萨帝)/colmo(COLMO)，默认 haier")
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--client-id", help="飞书 aPaaS Client ID")
    parser.add_argument("--client-secret", help="飞书 aPaaS Client Secret")
    
    args = parser.parse_args()
    
    config = load_config(Path(args.config) if args.config else None)
    
    if args.client_id:
        config["client_id"] = args.client_id
    if args.client_secret:
        config["client_secret"] = args.client_secret
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    
    result_path = import_from_file(file_path, config, args.type)
    
    if result_path:
        print(f"\n✅ 结果文件已生成: {result_path}")


if __name__ == "__main__":
    main()
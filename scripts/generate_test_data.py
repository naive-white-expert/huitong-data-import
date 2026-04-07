#!/usr/bin/env python3
"""
生成慧通导入测试数据集

包含：
- 正常数据
- 重复手机号
- 必填字段缺失（手机号、来源、跟进细节）
- 省市不在映射表中
"""

import pandas as pd
import random
from pathlib import Path

# 加载行政区划
REGION_FILE = Path(__file__).parent.parent / "references" / "region_mapping.xlsx"
df_region = pd.read_excel(REGION_FILE)
VALID_REGIONS = []
for _, row in df_region.iterrows():
    name = row.get("名称（中文）")
    if pd.notna(name):
        VALID_REGIONS.append(str(name).strip())

# 无效的省市名称（不在映射表中）
INVALID_REGIONS = [
    "火星市",
    "月球区",
    "虚构省",
    "不存在市",
    "假想县",
    "测试区",
    "未知市",
    "随机省",
]

def generate_phone():
    """生成随机手机号"""
    prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                "150", "151", "152", "153", "155", "156", "157", "158", "159",
                "170", "171", "172", "173", "175", "176", "177", "178",
                "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
                "191", "199"]
    prefix = random.choice(prefixes)
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix

def generate_test_dataset(total=10000):
    """生成测试数据集"""
    data = []
    
    # 用于生成重复手机号的池子
    duplicate_pool = []
    
    # 固定值
    source_fixed = "JD"
    details_fixed = "测试"
    
    # 数据分布（共 10000 条）
    # - 正常数据: 6500 条 (65%)
    # - 重复手机号: 1000 条 (10%)
    # - 手机号缺失: 500 条 (5%)
    # - 来源缺失: 500 条 (5%)
    # - 跟进细节缺失: 500 条 (5%)
    # - 省市无效: 500 条 (5%)
    # - 性别为空: 500 条 (5%)
    
    print(f"生成 {total} 条测试数据...")
    
    # 1. 正常数据 (6500 条)
    print("  - 正常数据: 6500 条")
    for i in range(6500):
        phone = generate_phone()
        gender = random.choice(["male", "female"])
        region = random.choice(VALID_REGIONS)
        district = f"{region}某区"
        authorized = random.choice(["是", "否"])
        recording_text = f"录音文本_{i}"
        recording_link = f"https://recording.example.com/{i}"
        
        data.append({
            "手机号": phone,
            "来源": source_fixed,
            "跟进细节": details_fixed,
            "性别": gender,
            "区县": district,
            "客户是否授权联系": authorized,
            "录音文本": recording_text,
            "录音链接": recording_link,
            "省市": region,
        })
        
        # 保存部分手机号用于重复测试
        if i < 200:
            duplicate_pool.append(phone)
    
    # 2. 重复手机号 (1000 条)
    print("  - 重复手机号: 1000 条")
    for i in range(1000):
        # 从池子中随机选择已存在的手机号
        phone = random.choice(duplicate_pool)
        gender = random.choice(["male", "female"])
        region = random.choice(VALID_REGIONS)
        
        data.append({
            "手机号": phone,
            "来源": source_fixed,
            "跟进细节": details_fixed,
            "性别": gender,
            "区县": f"{region}某区",
            "客户是否授权联系": "是",
            "录音文本": f"重复录音_{i}",
            "录音链接": f"https://recording.example.com/dup_{i}",
            "省市": region,
        })
    
    # 3. 手机号缺失 (500 条)
    print("  - 手机号缺失: 500 条")
    for i in range(500):
        gender = random.choice(["male", "female"])
        region = random.choice(VALID_REGIONS)
        
        data.append({
            "手机号": "",  # 空
            "来源": source_fixed,
            "跟进细节": details_fixed,
            "性别": gender,
            "区县": f"{region}某区",
            "客户是否授权联系": "是",
            "录音文本": "",
            "录音链接": "",
            "省市": region,
        })
    
    # 4. 来源缺失 (500 条)
    print("  - 来源缺失: 500 条")
    for i in range(500):
        phone = generate_phone()
        gender = random.choice(["male", "female"])
        region = random.choice(VALID_REGIONS)
        
        data.append({
            "手机号": phone,
            "来源": "",  # 空
            "跟进细节": details_fixed,
            "性别": gender,
            "区县": f"{region}某区",
            "客户是否授权联系": "是",
            "录音文本": "",
            "录音链接": "",
            "省市": region,
        })
    
    # 5. 跟进细节缺失 (500 条)
    print("  - 跟进细节缺失: 500 条")
    for i in range(500):
        phone = generate_phone()
        gender = random.choice(["male", "female"])
        region = random.choice(VALID_REGIONS)
        
        data.append({
            "手机号": phone,
            "来源": source_fixed,
            "跟进细节": "",  # 空
            "性别": gender,
            "区县": f"{region}某区",
            "客户是否授权联系": "是",
            "录音文本": "",
            "录音链接": "",
            "省市": region,
        })
    
    # 6. 省市无效 (500 条)
    print("  - 省市无效: 500 条")
    for i in range(500):
        phone = generate_phone()
        gender = random.choice(["male", "female"])
        invalid_region = random.choice(INVALID_REGIONS)
        
        data.append({
            "手机号": phone,
            "来源": source_fixed,
            "跟进细节": details_fixed,
            "性别": gender,
            "区县": "无效区县",
            "客户是否授权联系": "是",
            "录音文本": f"无效省市测试_{i}",
            "录音链接": f"https://recording.example.com/invalid_{i}",
            "省市": invalid_region,
        })
    
    # 7. 性别为空 (500 条)
    print("  - 性别为空: 500 条")
    for i in range(500):
        phone = generate_phone()
        region = random.choice(VALID_REGIONS)
        
        data.append({
            "手机号": phone,
            "来源": source_fixed,
            "跟进细节": details_fixed,
            "性别": "",  # 空
            "区县": f"{region}某区",
            "客户是否授权联系": "是",
            "录音文本": f"性别为空测试_{i}",
            "录音链接": f"https://recording.example.com/no_gender_{i}",
            "省市": region,
        })
    
    # 随机打乱顺序
    random.shuffle(data)
    
    return pd.DataFrame(data)


def main():
    output_dir = Path(__file__).parent.parent / "test_data"
    output_dir.mkdir(exist_ok=True)
    
    # 生成测试数据
    df = generate_test_dataset(10000)
    
    # 保存文件
    output_file = output_dir / "慧通导入测试数据_10000条.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"\n✅ 测试数据已生成:")
    print(f"   文件: {output_file}")
    print(f"   总数: {len(df)} 条")
    
    # 统计各类数据
    print(f"\n📊 数据分布:")
    
    # 统计空手机号
    empty_phone = len(df[df["手机号"] == ""])
    print(f"   - 手机号缺失: {empty_phone} 条")
    
    # 统计空来源
    empty_source = len(df[df["来源"] == ""])
    print(f"   - 来源缺失: {empty_source} 条")
    
    # 统计空跟进细节
    empty_details = len(df[df["跟进细节"] == ""])
    print(f"   - 跟进细节缺失: {empty_details} 条")
    
    # 统计无效省市
    invalid_region = len(df[~df["省市"].isin(VALID_REGIONS)])
    print(f"   - 省市无效: {invalid_region} 条")
    
    # 统计性别为空
    empty_gender = len(df[(df["性别"].isna()) | (df["性别"] == "")])
    print(f"   - 性别为空: {empty_gender} 条")
    
    # 统计重复手机号（非空）
    non_empty_phones = df[df["手机号"] != ""]["手机号"]
    duplicates = non_empty_phones.duplicated().sum()
    print(f"   - 重复手机号: {duplicates} 条")
    
    print(f"\n📁 输出目录: {output_dir}")


if __name__ == "__main__":
    main()
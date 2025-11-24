# IP合同数据提取流程

## 总体流程

```
开始
  ↓
[1] 加载合同文档
  ↓
[2] 识别合同结构
  ↓
[3] 提取基本信息（审批表）
  ↓
[4] 提取主体信息
  ↓
[5] 提取作品信息
  ↓
[6] 提取权利项信息
  ↓
[7] 提取结算信息（核心）
  ↓
[8] 提取特殊条款
  ↓
[9] 数据验证和格式化
  ↓
[10] 生成JSON输出
  ↓
结束
```

## 详细步骤

### 步骤1：加载合同文档

**目标**：读取合同Markdown文件

**操作**：
```python
contract_path = Path("输入/T-277-AUT-20150331-01.md")
with open(contract_path, 'r', encoding='utf-8') as f:
    contract_text = f.read()
```

**验证**：
- 文件是否存在
- 文件编码是否正确（UTF-8）
- 文件是否为空

---

### 步骤2：识别合同结构

**目标**：将合同文本分割为不同部分

**操作**：
1. 识别审批表部分（<table>...</table>）
2. 识别合同标题（# 漫画作品授权许可合同）
3. 识别主体信息（甲方：...乙方：...）
4. 识别章节（## 一、...## 二、...）

**输出**：
```python
contract_structure = {
    "approval_table": "...",  # HTML表格文本
    "title": "漫画作品授权许可合同",
    "parties": {
        "party_a": "深圳市腾讯计算机系统有限公司",
        "party_b": "周智延（笔名：鼠叔）"
    },
    "chapters": {
        "一": "...",  # 授权许可的漫画作品
        "二": "...",  # 漫画作品的基本要求
        ...
        "十": "...",  # 收入结算支付
        ...
    }
}
```

---

### 步骤3：提取基本信息（审批表）

**目标**：从合同审批表提取元数据

**关键字段**：

| Excel列 | 字段名 | 提取来源 | 提取规则 |
|---------|--------|---------|---------|
| 列5 | 合同编号 | 审批表"合同编号"行 | 直接提取 |
| 列6 | 合同标题 | 正文标题 | 提取# 后的文字 |
| 列7 | 合同流水号 | 审批表"合同编号"行 | 同合同编号 |
| 列16 | 生效期 | 审批表"合同有效期"或正文 | 提取起始日期 |
| 列17 | 签约期 | 审批表或正文"生效日期" | 同生效期 |

**提取代码示例**：
```python
import re
from bs4 import BeautifulSoup

# 解析审批表
soup = BeautifulSoup(approval_table, 'html.parser')

# 提取合同编号
contract_no_cell = soup.find(text="合同编号").find_next('td')
contract_no = contract_no_cell.text.strip()  # "T-277-AUT-20150331-01"

# 提取合同有效期
validity_cell = soup.find(text="合同有效期").find_next('td')
validity_text = validity_cell.text.strip()  # "（约定）2015-04-01到2025-03-31"
dates = re.findall(r'\d{4}-\d{2}-\d{2}', validity_text)
effective_date = dates[0]  # "2015-04-01"
expiry_date = dates[1]  # "2025-03-31"
```

---

### 步骤4：提取主体信息

**目标**：识别甲方和乙方信息

**关键字段**：

| Excel列 | 字段名 | 提取来源 | 提取规则 |
|---------|--------|---------|---------|
| 列15 | 我方主体 | 正文"甲方" | 直接提取 |
| 列24 | 对方主体名称 | 正文"乙方" | 提取主体名称（包括笔名） |
| 列22 | 对方主体类型 | 根据身份证号判断 | 有身份证号=2（个人），否则=1（公司） |

**提取代码示例**：
```python
# 提取甲方
party_a_match = re.search(r'甲方[（(]?.*?[）)]?[:：](.*?)(?:\n|乙方)', contract_text)
party_a = party_a_match.group(1).strip() if party_a_match else ""

# 提取乙方
party_b_match = re.search(r'乙方[（(]?.*?[）)]?[:：](.*?)(?:\n|根据)', contract_text)
party_b = party_b_match.group(1).strip() if party_b_match else ""

# 判断对方主体类型
id_number_pattern = r'\d{15}|\d{17}[\dXx]'  # 15位或18位身份证号
if re.search(id_number_pattern, approval_table):
    party_b_type = "2"  # 个人
else:
    party_b_type = "1"  # 公司
```

---

### 步骤5：提取作品信息

**目标**：从"一、授权许可的漫画作品"章节提取作品信息

**关键字段**：

| Excel列 | 字段名 | 提取来源 | 提取规则 |
|---------|--------|---------|---------|
| 列51 | 采购作品名称 | 章节一"作品名称：《...》" | 提取书名号内文字 |
| 列31 | 作品类型 | 章节一"作品形式：..." | 故事漫画/四格漫画=2（静态），动态漫画=3 |

**提取代码示例**：
```python
chapter_1 = contract_structure["chapters"]["一"]

# 提取作品名称
work_name_match = re.search(r'作品名称[:：]《(.*?)》', chapter_1)
work_name = work_name_match.group(1) if work_name_match else ""

# 提取作品类型
work_form_match = re.search(r'作品形式[:：](.*?)(?:\n|$)', chapter_1)
work_form = work_form_match.group(1).strip() if work_form_match else ""

if "动态" in work_form:
    work_type = "3"  # 动态漫画
else:
    work_type = "2"  # 静态漫画
```

---

### 步骤6：提取权利项信息

**目标**：从"五、授权范围和期限"章节提取权利项信息

**关键字段**：

| Excel列 | 字段名 | 提取来源 | 提取规则 |
|---------|--------|---------|---------|
| 列35 | 采购区域 | 章节五"授权区域：..." | 直接提取 |
| 列36 | 采购语言 | 章节五"授权作品语言：..." | 直接提取 |
| 列37 | 采购期限-开始时间 | 章节五"授权期限为...自...日至...日" | 提取起始日期 |
| 列38 | 采购期限-到期时间 | 章节五"授权期限为...自...日至...日" | 提取结束日期 |
| 列39 | 是否独家 | 章节五"独占授权/非独占授权" | 独占=1，非独占=0 |
| 列42 | 是否转授权 | 章节五"转授权权利" | 包含=1，不包含=0 |
| 列45 | 是否自动续期 | 章节五"授权期满后X年" | 包含=1，不包含=0 |

**提取代码示例**：
```python
chapter_5 = contract_structure["chapters"]["五"]

# 提取授权区域
region_match = re.search(r'授权区域[:：](.*?)(?:\.|。|\n)', chapter_5)
region = region_match.group(1).strip() if region_match else ""

# 提取授权语言
language_match = re.search(r'授权.*?语言[:：](.*?)(?:\.|。|\n)', chapter_5)
language = language_match.group(1).strip() if language_match else ""

# 提取授权期限
duration_match = re.search(r'授权期限为.*?自.*?(\d{4}).*?年.*?(\d+).*?月.*?(\d+).*?日.*?至.*?(\d{4}).*?年.*?(\d+).*?月.*?(\d+).*?日', chapter_5)
if duration_match:
    start_date = f"{duration_match.group(1)}-{duration_match.group(2):0>2}-{duration_match.group(3):0>2}"
    end_date = f"{duration_match.group(4)}-{duration_match.group(5):0>2}-{duration_match.group(6):0>2}"

# 判断是否独家
if "独占" in chapter_5 or "独家" in chapter_5:
    is_exclusive = "1"
else:
    is_exclusive = "0"

# 判断是否转授权
if "转授权" in chapter_5:
    is_sublicense = "1"
else:
    is_sublicense = "0"

# 判断是否自动续期
renewal_match = re.search(r'授权期满后.*?(\d+).*?年', chapter_5)
if renewal_match:
    is_auto_renewal = "1"
    renewal_years = renewal_match.group(1)
else:
    is_auto_renewal = "0"
    renewal_years = ""
```

---

### 步骤7：提取结算信息（核心）⭐⭐⭐

**目标**：从"十、收入结算支付"章节提取结算信息

**这是最复杂和最关键的步骤**

#### 7.1 定位结算章节

```python
chapter_10 = contract_structure["chapters"]["十"]
```

#### 7.2 判断结算类型

使用 `settlement_types.md` 中的判断规则：

```python
def determine_settlement_type(chapter_10_text):
    """判断结算类型"""
    text = chapter_10_text

    # 类型5：阶梯分成（最优先）
    if "阶梯" in text:
        return "5"

    # 类型3：保底分成
    if "保底" in text:
        return "3"

    # 类型1：买断
    if ("买断" in text or "元/幅" in text or "稿费" in text) and \
       ("分成" not in text):
        return "1"

    # 类型2：买断+奖励分成
    if ("买断" in text or "元/幅" in text or "稿费" in text) and \
       ("分成" in text):
        return "2"

    # 类型4：纯分成
    if "分成" in text and \
       "买断" not in text and \
       "稿费" not in text and \
       "保底" not in text:
        return "4"

    # 类型6：其他
    return "6"
```

#### 7.3 提取结算金额和比例

根据不同的结算类型提取不同的字段：

**类型1：买断**
```python
# 提取买断金额（元/幅）
buyout_match = re.search(r'[人民币]*\【(\d+)\】元[/／]幅', chapter_10)
if buyout_match:
    buyout_amount = buyout_match.group(1)  # "250"
```

**类型2：买断+奖励分成**
```python
# 提取买断金额
buyout_match = re.search(r'[人民币]*\【(\d+)\】元[/／]幅', chapter_10)
buyout_amount = buyout_match.group(1) if buyout_match else ""

# 提取分成比例
revenue_share_match = re.search(r'实际收入.*?\【(\d+)\】[%％]', chapter_10)
revenue_share_pct = revenue_share_match.group(1) + "%" if revenue_share_match else ""

# 提取纯分成比例（模式转换后）
pure_share_match = re.search(r'纯分成.*?实际收入的\【(\d+)\】[%％]', chapter_10)
pure_share_pct = pure_share_match.group(1) + "%" if pure_share_match else ""
```

**类型3：保底分成**
```python
# 提取保底金额
guarantee_match = re.search(r'保底金额.*?[人民币]*\【(\d+)\】元', chapter_10)
guarantee_amount = guarantee_match.group(1) if guarantee_match else ""

# 提取保底分成比例
guarantee_share_match = re.search(r'保底.*?按\【(\d+)\】[%％].*?分成', chapter_10)
guarantee_share_pct = guarantee_share_match.group(1) + "%" if guarantee_share_match else ""
```

**类型4：纯分成**
```python
# 提取分成比例
revenue_share_match = re.search(r'实际收入的\【(\d+)\】[%％]', chapter_10)
revenue_share_pct = revenue_share_match.group(1) + "%" if revenue_share_match else ""
```

**类型5：阶梯分成**
```python
# 提取阶梯分成线（静态漫画）
ladder_lines = []
ladder_shares = []

# 识别模式："0-10万：30%"
ladder_pattern = r'(\d+-\d+万)[：:]\s*(\d+)[%％]'
ladder_matches = re.findall(ladder_pattern, chapter_10)
for line, share in ladder_matches:
    ladder_lines.append(line)
    ladder_shares.append(share + "%")

# 或者识别模式："流水收入累计达到 0-100万：20%"
if not ladder_matches:
    ladder_pattern = r'流水收入累计.*?(\d+-\d+万)[：:]\s*(\d+)[%％]'
    ladder_matches = re.findall(ladder_pattern, chapter_10)
    for line, share in ladder_matches:
        ladder_lines.append(line)
        ladder_shares.append(share + "%")
```

#### 7.4 提取结算周期

```python
# 提取结算周期
if "按月结算" in chapter_10 or "每个自然月" in chapter_10:
    settlement_cycle = "每月结算"
elif "每季度" in chapter_10:
    settlement_cycle = "每季度结算"
elif "每半年" in chapter_10:
    settlement_cycle = "每半年结算"
else:
    settlement_cycle = ""
```

#### 7.5 提取币种

```python
# 提取币种
if "人民币" in chapter_10 or "CNY" in chapter_10:
    currency_code = "12"  # 人民币
elif "美元" in chapter_10 or "USD" in chapter_10:
    currency_code = "1"  # 美元
elif "港币" in chapter_10 or "HKD" in chapter_10:
    currency_code = "2"  # 港币
else:
    currency_code = "12"  # 默认人民币
```

---

### 步骤8：提取特殊条款

**目标**：从各章节提取特殊条款信息

**关键字段**：

| Excel列 | 字段名 | 提取来源 | 提取规则 |
|---------|--------|---------|---------|
| 列184 | 优先投资权 | 全文搜索"优先投资权" | 包含=1 |
| 列185 | 自动回收条款 | 全文搜索"自动回收" | 包含=1 |
| 列186 | 优先权 | 全文搜索"优先权" | 包含=1 |
| 列183 | 是否转签 | 全文搜索"转签" | 包含=1 |

**提取代码示例**：
```python
full_text = contract_text

# 优先投资权
priority_investment = "1" if "优先投资权" in full_text else "0"

# 自动回收条款
auto_recovery = "1" if "自动回收" in full_text else "0"

# 优先权
priority_rights = "1" if "优先权" in full_text else "0"

# 是否转签
is_transfer = "1" if "转签" in full_text else "0"
```

---

### 步骤9：数据验证和格式化

**目标**：验证提取的数据完整性和正确性

**验证规则**：

1. **必填字段检查**：
   - 合同编号不为空
   - 我方主体不为空
   - 对方主体名称不为空
   - 作品名称不为空

2. **日期格式检查**：
   - 所有日期统一为 YYYY-MM-DD 格式
   - 验证日期的合法性（月份1-12，日期1-31）

3. **数值范围检查**：
   - 分成比例在0-100%之间
   - 金额大于等于0
   - 币种编码在1-12之间

4. **逻辑一致性检查**：
   - 如果结算类型=1（买断），必须有买断金额
   - 如果结算类型=2，必须有买断金额和分成比例
   - 如果结算类型=4，必须有分成比例
   - 采购期限-开始时间 <= 采购期限-到期时间

**格式化代码示例**：
```python
def validate_and_format(extracted_data):
    """验证和格式化提取的数据"""

    # 日期格式化
    date_fields = ["生效期", "签约期", "采购期限-开始时间", "采购期限-到期时间"]
    for field in date_fields:
        if field in extracted_data and extracted_data[field]:
            # 统一为 YYYY-MM-DD 格式
            date_str = extracted_data[field]
            # 处理各种日期格式...
            extracted_data[field] = standardize_date(date_str)

    # 分成比例格式化（确保包含%）
    percentage_fields = ["我方自用分成比例", "转授第三方分成比例", "保底分成比例"]
    for field in percentage_fields:
        if field in extracted_data and extracted_data[field]:
            value = extracted_data[field]
            if "%" not in value:
                extracted_data[field] = value + "%"

    # 必填字段检查
    required_fields = ["合同编号", "我方主体", "对方主体名称", "采购作品名称"]
    missing_fields = []
    for field in required_fields:
        if not extracted_data.get(field):
            missing_fields.append(field)

    if missing_fields:
        print(f"警告：缺失必填字段：{', '.join(missing_fields)}")

    return extracted_data
```

---

### 步骤10：生成JSON输出

**目标**：将提取的数据生成JSON文件

**输出格式**：

```json
{
  "合同编号": "T-277-AUT-20150331-01",
  "合同标题": "漫画作品授权许可合同",
  "合同流水号": "T-277-AUT-20150331-01",
  "我方主体": "深圳市腾讯计算机系统有限公司",
  "对方主体名称": "周智延（笔名：鼠叔）",
  "对方主体类型": "2",
  "生效期": "2015-04-01",
  "签约期": "2015-04-01",
  "作品类型": "2",
  "采购作品名称": "老师是无赖",
  "采购区域": "全球范围",
  "采购语言": "中文及其他各种语言",
  "采购期限-开始时间": "2015-04-01",
  "采购期限-到期时间": "2025-03-31",
  "是否独家": "1",
  "是否转授权": "1",
  "是否自动续期": "1",
  "续期时间": "3年",
  "结算类型": "2",
  "买断金额": "250",
  "币种": "12",
  "我方自用分成比例": "10%",
  "结算周期": "每月结算",
  ...
}
```

**生成代码示例**：
```python
import json
from pathlib import Path

def save_extraction_result(extracted_data, contract_name):
    """保存提取结果为JSON文件"""

    # 输出路径
    output_dir = Path("输出/中间数据")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{contract_name}_提取数据.json"

    # 保存JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 提取完成：{output_file}")
    return output_file
```

---

## 批量处理流程

处理多个合同时：

```python
def batch_extract_contracts(contract_dir):
    """批量提取合同数据"""
    contract_dir = Path(contract_dir)
    all_results = []

    # 遍历所有.md文件
    for contract_file in contract_dir.glob("*.md"):
        print(f"\n正在处理：{contract_file.name}")

        # 执行提取流程
        result = extract_contract_data(contract_file)

        # 验证和格式化
        result = validate_and_format(result)

        # 保存JSON
        save_extraction_result(result, contract_file.stem)

        all_results.append(result)

    print(f"\n✓ 批量提取完成！共处理 {len(all_results)} 个合同。")
    return all_results
```

---

## 质量保证

提取完成后，建议进行以下检查：

1. **字段完整性检查**：
   - 运行 `scripts/missing_field_detector.py`
   - 检查哪些字段未被提取

2. **数据准确性检查**：
   - 随机抽取3-5个合同
   - 人工对比提取结果和原合同
   - 重点检查：合同编号、主体、金额、结算类型

3. **格式规范性检查**：
   - 日期格式：YYYY-MM-DD
   - 分成比例：XX%
   - 币种编码：1-12之间的整数

---

## 错误处理

常见错误及处理方法：

| 错误类型 | 错误描述 | 处理方法 |
|---------|---------|---------|
| 文件读取错误 | 文件不存在或编码错误 | 检查文件路径和编码 |
| 结构识别错误 | 无法识别章节结构 | 检查章节标题格式 |
| 字段缺失 | 某些字段无法提取 | 记录到日志，继续处理 |
| 日期格式错误 | 日期格式不标准 | 使用正则表达式多模式匹配 |
| 金额提取错误 | 无法识别金额格式 | 检查"元"、"万元"等单位 |

---

## 版本信息
- Version: 1.0
- Created: 2025-11-14

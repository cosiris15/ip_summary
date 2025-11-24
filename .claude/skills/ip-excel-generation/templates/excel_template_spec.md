# Excel模板规范

## 总体结构

```
【版权授权链】漫画作品授权合同梳理数据.xlsx
└── 工作表："版权采购"
    ├── 第1行：分类标题（合并单元格）
    ├── 第2行：字段名称（193列）
    ├── 第3行：填写规则说明
    └── 第4行起：数据行（每个合同一行）
```

## 第1行：分类标题

分类标题将193列分为多个大类，使用合并单元格展示：

| 列范围 | 分类名称 | 列数 |
|--------|---------|------|
| A1-AA1 | 合同信息 | 27 |
| AB1-AD1 | 合同类型信息 | 3 |
| AE1-BF1 | 权利项信息-基本信息 | 25 |
| BG1-BI1 | 结算信息-基本 | 4 |
| BJ1-DX1 | 结算信息-详情1 | 55 |
| DY1-FM1 | 结算信息-详情2 | 55 |
| FN1-GF1 | 合同管理字段 | 19 |
| GG1-GL1 | 项目管理字段 | 6 |

**格式**：
- 字体：微软雅黑，12号，加粗
- 对齐：居中
- 背景色：浅蓝色（可选）

## 第2行：字段名称

193个字段的完整列表（详见 `field_mapping.md`）

**格式**：
- 字体：微软雅黑，10号，加粗
- 对齐：居中
- 边框：所有边框

**关键字段示例**（前30列）：

| 列 | 字段名 | 列 | 字段名 |
|----|--------|----|--------|
| A | CAMS字段 | B | 关联流水号 |
| C | 合同状态 | D | 合同ID |
| E | 合同编号 | F | 合同标题 |
| G | 合同流水号 | H | oa流程编号 |
| I | 标准合同 | J | 框架合同 |
| K | 其他（请注明） | L | 是否母合同 |
| M | 母合同编号 | N | 母合同名称 |
| O | 我方主体 | P | 我方签约主体类型 |
| Q | 乙方公司简称 | R | 签约省份 |
| S | 对方类型 | T | 对方主体/公司 |
| U | 对方主体名称 | V | 对方公司代表 |
| W | 生效期 | X | 签约期 |
| Y | 合同备注 | Z | IP作品名称 |
| AA | IP IP类别 | AB | 合同类型 |
| AC | 合同类型小类 | AD | 合同类型三级 |

## 第3行：填写规则

说明各字段的填写规则和示例（从样例Excel提取）

**格式**：
- 字体：微软雅黑，9号，斜体
- 对齐：左对齐
- 颜色：灰色（可选）

**示例**：
- 列E（合同编号）：填写完整的合同编号，如"T-277-AUT-20150331-01"
- 列S（对方类型）：1=公司，2=个人
- 列W（生效期）：格式YYYY-MM-DD

## 第4行起：数据行

每个合同占一行，共193列数据

**格式**：
- 字体：微软雅黑，10号，常规
- 对齐：左对齐
- 边框：所有边框
- 行高：自动或15pt

## 生成代码示例

```python
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

def create_excel_template():
    """创建Excel模板"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "版权采购"

    # 第1行：分类标题（合并单元格）
    categories = [
        ("A1", "AA1", "合同信息"),
        ("AB1", "AD1", "合同类型信息"),
        ("AE1", "BF1", "权利项信息-基本信息"),
        # ... 其他分类
    ]

    for start, end, title in categories:
        ws.merge_cells(f'{start}:{end}')
        cell = ws[start]
        cell.value = title
        cell.font = Font(name='微软雅黑', size=12, bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 第2行：字段名称
    field_names = [
        "CAMS字段", "关联流水号", "合同状态", "合同ID", "合同编号",
        "合同标题", "合同流水号", "oa流程编号", # ... 共193个字段
    ]

    for col_idx, field_name in enumerate(field_names, start=1):
        cell = ws.cell(row=2, column=col_idx)
        cell.value = field_name
        cell.font = Font(name='微软雅黑', size=10, bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    # 第3行：填写规则（简化）
    # ...

    return wb
```

## 列宽设置

建议列宽：
- 短字段（状态、类型等）：10-15
- 中等字段（名称、编号等）：20-30
- 长字段（备注、说明等）：40-50

## 版本信息
- Version: 1.0
- Created: 2025-11-14

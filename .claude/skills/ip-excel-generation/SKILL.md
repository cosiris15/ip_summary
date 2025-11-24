# IP Excel生成 Skill

## 概述
本skill提供IP授权合同梳理数据的Excel报告生成能力，将JSON格式的合同数据转换为标准Excel表格。

## 适用场景
- 从JSON数据生成Excel报告
- 格式化193个字段的数据展示
- 应用Excel样式和格式规范
- 合并多个合同数据到单个Excel文件

## 核心能力

### 1. Excel结构生成
- 第1行：分类标题（合并单元格）
- 第2行：字段名称（193列）
- 第3行：填写规则（从样例提取）
- 第4行起：数据行（每个合同一行）

### 2. 字段映射
将JSON的193个字段映射到Excel的193列

### 3. 格式化
- 字体：微软雅黑/宋体，10号字
- 对齐：标题居中，数据左对齐
- 边框：所有单元格添加边框
- 列宽：自动调整或固定宽度

### 4. 数据验证
- 必填字段检查
- 数据格式验证
- 逻辑一致性检查

## 知识库结构

```
ip-excel-generation/
├── SKILL.md                    # 本文件
├── templates/
│   └── excel_template_spec.md # Excel模板规范
└── standards/
    ├── field_mapping.md        # 字段映射表
    └── formatting_guide.md     # Excel格式规范
```

## 使用方法

在excel-writer Agent中调用本skill：

```markdown
我需要从JSON数据生成Excel报告。请使用 @ip-excel-generation skill来：

1. 加载所有合同的JSON数据
2. 生成Excel结构（标题行、字段行、数据行）
3. 应用格式化规则
4. 保存Excel文件
```

## 输出格式

Excel文件（.xlsx），包含：
- 工作表名称："版权采购"
- 列数：193列
- 行数：3（标题+字段+规则）+ N（数据行数）

## 关键库

使用 `openpyxl` 库进行Excel操作：

```python
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
```

## 版本信息
- Version: 1.0
- Created: 2025-11-14

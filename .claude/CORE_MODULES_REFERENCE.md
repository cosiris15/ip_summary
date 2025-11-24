# 专业Agent系统核心模块参考手册

**适用场景**: 基于Claude的文档分析、数据提取、报告生成类项目

**参考项目**:
- `corpfile_summary` (公司历史沿革分析)
- `debt_review_skills` (债券尽调审核)

---

## 📋 核心模块清单

| 模块ID | 模块名称 | 必选 | 功能概述 |
|--------|---------|------|---------|
| M1 | Agent系统 | ✅ | 专业化AI代理，分工协作 |
| M2 | 工作流控制器 | ✅ | 环境管理、状态追踪 |
| M3 | 配置管理 | ✅ | 标准化配置、路径规范 |
| M4 | 多轮次处理 | ⭐ | Round机制、增量更新 |
| M5 | 并行处理 | ⭐ | 多实体隔离、安全检查 |
| M6 | 数据提取层 | ✅ | 结构化提取、验证 |
| M7 | 文档生成层 | ✅ | 模板渲染、格式转换 |
| M8 | Skills知识库 | 🔧 | 领域知识、标准规范 |

**图例**: ✅ 必选 | ⭐ 推荐 | 🔧 可选

---

## M1: Agent系统

### 核心理念
**单一职责原则** - 每个Agent专注一个核心任务，通过顺序链接实现复杂流程

### 标准架构

```
.claude/agents/
├── {domain}-extractor.md    # 数据提取Agent
├── {domain}-analyzer.md     # 分析Agent（可选）
└── report-writer.md         # 报告生成Agent
```

### Agent标准结构

```markdown
---
name: {agent-name}
description: 使用场景描述 + 示例
model: sonnet
color: yellow/cyan/green
---

# Agent名称

## Agent Overview
- Position in Workflow: Stage X of Y
- Input: 输入说明
- Output: 输出说明

## 🔒 MANDATORY: 配置验证
- Step 0.0-0.3: 配置检查
- Checkpoint P0-P3: 并行安全检查（如适用）

## ⚠️ Critical Prerequisites
- 前置条件检查

## 核心工作流程
- Step 1: ...
- Step 2: ...

## 输出规范
- 输出格式、路径、命名规则
```

### 关键设计原则

| 原则 | 说明 | 实施方式 |
|------|------|---------|
| **强制检查** | 环境验证非可选 | Step 0.X 配置检查，失败立即STOP |
| **路径规范** | 从配置读取，禁止硬编码 | `config['paths']['xxx']` |
| **详细日志** | 每步输出进度 | `print(f"✓ Step completed")` |
| **错误处理** | 失败时明确指导 | "如何修复" + "下一步做什么" |

### Agent最佳实践

```python
# ✅ 正确：配置驱动
input_dir = Path(config['paths']['input_dir'])
output_path = intermediate_dir / config['file_templates']['extraction_output']

# ❌ 错误：硬编码
input_dir = Path('输入样例/')
output_path = Path('输出/中间数据/data.json')
```

---

## M2: 工作流控制器

### 核心功能

```python
class WorkflowController:
    """环境管理、配置生成、状态追踪"""

    # 必选命令
    def init(company_name: str) -> bool:
        """初始化环境、生成配置"""

    def check() -> bool:
        """检查环境状态"""

    def status() -> None:
        """显示当前状态"""

    # 多轮次必选
    def new_round(reason: str, new_files: List) -> bool:
        """创建新轮次"""

    def reset(confirm: bool) -> bool:
        """重置环境"""

    # 并行处理必选
    def init_multi() -> bool:
        """初始化多实体环境"""

    def add_company(name: str) -> bool:
        """添加新实体"""

    def list_companies() -> None:
        """列出所有实体"""
```

### 标准目录结构

```
project_root/
├── .processing_config.json     # 配置文件
├── 输入样例/                   # 输入目录
├── 输出/                       # 输出目录
│   ├── round_1/               # Round 1结果
│   ├── round_2/               # Round 2结果
│   └── 中间数据/              # 中间JSON
├── 工具/                       # 工具脚本
│   └── workflow_controller.py
└── .claude/
    ├── agents/                # Agent定义
    └── skills/                # 领域知识
```

### 控制器实施检查清单

- [ ] 实现 init 命令（配置生成）
- [ ] 实现 check 命令（环境检查）
- [ ] 实现 status 命令（状态显示）
- [ ] 实现目录自动创建
- [ ] 实现输入文件扫描
- [ ] 实现依赖检查
- [ ] 颜色输出（成功/错误/警告）
- [ ] 详细错误提示

---

## M3: 配置管理

### 标准配置文件结构

```json
{
  "company_info": {
    "company_name": "实体名称",
    "processing_date": "2025-11-13",
    "processing_id": "unique_id"
  },
  "paths": {
    "input_dir": "输入样例/",
    "output_dir": "输出/",
    "intermediate_dir": "输出/中间数据/",
    "tools_dir": "工具/"
  },
  "file_templates": {
    "extraction_output": "{company_name}_提取数据.json",
    "markdown_report": "{company_name}_报告.md",
    "word_report": "{company_name}报告.docx"
  },
  "input_files": {
    "primary_doc": "文件名.md",
    "amendment_docs": ["变更1.md", "变更2.md"],
    "total_count": 3
  },
  "processing_status": {
    "stage": "initialized",
    "extraction_completed": false,
    "report_completed": false,
    "last_updated": "2025-11-13T12:00:00"
  },
  "round_info": {
    "current_round": 1,
    "total_rounds": 1,
    "initial_round_date": "2025-11-13T12:00:00"
  }
}
```

### 配置使用模式

```python
# Agent中标准使用方式
with open('.processing_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 提取路径
input_dir = Path(config['paths']['input_dir'])
output_dir = Path(config['paths']['output_dir'])

# 使用模板
company_name = config['company_info']['company_name']
output_template = config['file_templates']['extraction_output']
output_filename = output_template.format(company_name=company_name)
output_path = intermediate_dir / output_filename
```

### 配置管理最佳实践

| 实践 | 说明 |
|------|------|
| **相对路径** | 所有路径使用相对路径（"输入样例/"） |
| **模板化** | 文件名使用模板（`{company_name}_xxx.json`） |
| **状态追踪** | 记录处理阶段和完成状态 |
| **元数据** | 保留处理日期、ID等元信息 |
| **验证** | Agent启动时验证配置完整性 |

---

## M4: 多轮次处理 (Round机制)

### 核心概念

```
Timeline:
Round 1 (初次分析)        → 输出/round_1/
   ↓
[客户补充新材料]
   ↓
Round 2 (增量处理)        → 输出/round_2/
   ↓
[再次补充]
   ↓
Round 3 (继续增量)        → 输出/round_3/
```

### Round元数据结构

```json
{
  "round_number": 2,
  "parent_round": 1,
  "processing_mode": "incremental",
  "trigger_reason": "客户补充了2份新变更档案",
  "new_materials": ["20250101变更.md", "20250620变更.md"],
  "processing_date": "2025-11-13T12:00:00",
  "fields_updated": ["equity_structure", "board_members"],
  "affected_events": [8, 9],
  "inheritance_from_parent": {
    "note": "从 round_1 继承未变更部分"
  }
}
```

### 处理模式

| 模式 | 触发条件 | 处理方式 |
|------|---------|---------|
| **full** | Round 1 或重大变更 | 完整重新分析 |
| **incremental** | 补充新材料 | 继承+处理新事件 |
| **partial** | 修正特定字段 | 仅更新指定字段 |

### 增量处理实施步骤

```python
# Step 1: 检测Round模式
current_round = config['round_info']['current_round']
if current_round > 1:
    # Step 2: 加载父Round数据
    parent_round = round_metadata['parent_round']
    parent_json = f"输出/round_{parent_round}/中间数据/data.json"
    with open(parent_json) as f:
        parent_data = json.load(f)

    # Step 3: 识别新事件
    new_events = identify_new_events(current_materials, parent_data)

    # Step 4: 处理新事件
    new_extracted = process_new_events(new_events)

    # Step 5: 合并数据
    merged_data = merge_with_inheritance(parent_data, new_extracted)

    # Step 6: 验证连续性
    verify_continuity(merged_data)

    # Step 7: 保存到Round目录
    save_to_round_dir(merged_data, current_round)
```

### Round实施检查清单

- [ ] Round目录结构（`输出/round_N/`）
- [ ] Round元数据文件（`.round_metadata.json`）
- [ ] 父Round数据加载逻辑
- [ ] 新旧数据识别逻辑
- [ ] 增量处理逻辑
- [ ] 数据合并逻辑
- [ ] 连续性验证
- [ ] 配置文件Round信息更新

---

## M5: 并行处理

### 多实体目录结构

```
project_root/
├── companies/                    # 多实体容器
│   ├── README.md
│   ├── 实体A/
│   │   ├── .processing_config.json
│   │   ├── .company_id
│   │   ├── 输入样例/
│   │   └── 输出/
│   └── 实体B/
│       └── (同上)
├── 工具/                         # 共享资源
└── .claude/                      # 共享资源
```

### 安全隔离检查点 (P0-P3)

```python
# P0: 工作目录验证
cwd = Path.cwd()
if not (cwd / ".processing_config.json").exists():
    print("❌ 目录结构不完整")
    # STOP

# P1: 配置-提示一致性
config_company = config['company_info']['company_name']
prompt_company = extract_from_prompt()  # 从用户提示提取
if config_company != prompt_company:
    print(f"❌ 公司名称不匹配: {config_company} vs {prompt_company}")
    # STOP

# P2: 路径隔离验证
for path_name, path in paths_to_check:
    try:
        path.relative_to(cwd)  # 必须在cwd下
    except ValueError:
        print(f"❌ {path_name} 路径逃逸!")
        # STOP

# P3: 最终确认
print_verification_summary()
```

### 并行模式自动检测

```python
def __init__(self, project_root: Path = None):
    cwd = Path.cwd()

    # 检测是否在多实体子目录
    in_multi_mode = (cwd.parent.name == 'companies')

    if in_multi_mode:
        # 多实体模式：共享资源在../../
        actual_root = cwd.parent.parent
        self.dirs = {
            'input': cwd / '输入样例',           # 当前实体
            'output': cwd / '输出',
            'tools': actual_root / '工具',      # 共享
            'claude_skills': actual_root / '.claude/skills'
        }
    else:
        # 单实体模式：所有资源在当前目录
        self.dirs = {
            'input': cwd / '输入样例',
            'output': cwd / '输出',
            'tools': cwd / '工具',
            'claude_skills': cwd / '.claude/skills'
        }
```

### 并行处理实施检查清单

- [ ] 多实体目录结构
- [ ] 实体标识文件（`.company_id`）
- [ ] P0-P3检查点（Agent中）
- [ ] 路径自动检测（Controller中）
- [ ] init-multi 命令
- [ ] add-company 命令
- [ ] list-companies 命令
- [ ] 协议文档（PARALLEL_PROCESSING_PROTOCOL.md）
- [ ] Prompt模板（PARALLEL_PROCESSING_PROMPTS.md）

---

## M6: 数据提取层

### 标准提取流程

```python
# Step 1: 文档扫描
documents = scan_input_directory(config['paths']['input_dir'])

# Step 2: 事件识别
events = []
for doc in documents:
    events.extend(identify_events_in_document(doc))

# Step 3: 时间排序
events.sort(key=lambda e: e['date'])

# Step 4: 结构化提取
structured_data = {
    "company_name": company_name,
    "extraction_date": datetime.now().isoformat(),
    "total_events": len(events),
    "events": []
}

for event in events:
    event_data = {
        "event_id": generate_id(),
        "event_date": event['date'],
        "event_type": classify_event(event),
        "description": extract_description(event),
        "before_state": extract_before_state(event),
        "after_state": extract_after_state(event),
        "special_notes": identify_special_cases(event)
    }
    structured_data["events"].append(event_data)

# Step 5: 数据验证
validate_data_integrity(structured_data)
validate_continuity(structured_data)

# Step 6: 保存JSON
save_json(structured_data, output_path)
```

### 数据验证清单

| 验证项 | 检查内容 |
|--------|---------|
| **完整性** | 所有必填字段存在 |
| **连续性** | 事件之间状态衔接 |
| **一致性** | 前后状态计算正确 |
| **格式** | 日期、数值格式规范 |
| **特殊案例** | 识别并标注异常情况 |

### 输出JSON结构

```json
{
  "company_name": "实体名称",
  "extraction_date": "2025-11-13T12:00:00",
  "total_events": 10,
  "events": [
    {
      "event_id": "evt_001",
      "event_date": "2020-01-15",
      "event_type": "equity_transfer",
      "description": "股权转让",
      "before_state": {
        "shareholders": [...],
        "registered_capital": 1000000
      },
      "after_state": {
        "shareholders": [...],
        "registered_capital": 1000000
      },
      "changes": {
        "changed_items": ["shareholders"],
        "summary": "股东A将50%股权转让给股东B"
      },
      "special_notes": {
        "is_zero_price": false,
        "is_proxy": false,
        "requires_attention": []
      }
    }
  ],
  "metadata": {
    "processing_mode": "full",
    "round_number": 1,
    "data_quality_score": 95
  }
}
```

---

## M7: 文档生成层

### Jinja2模板系统

```
.claude/skills/{domain}-report-writing/
├── templates/
│   ├── main_report.jinja2        # 主报告模板
│   ├── sections/
│   │   ├── establishment.jinja2  # 设立章节
│   │   ├── equity_changes.jinja2 # 股权变更
│   │   └── summary.jinja2        # 总结
│   └── macros.jinja2             # 可复用宏
└── standards/
    ├── writing_style.md          # 写作规范
    └── formatting_guide.md       # 格式指南
```

### 报告生成流程

```python
# Step 1: 加载JSON数据
with open(input_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Step 2: 加载Jinja2模板
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('main_report.jinja2')

# Step 3: 应用写作标准
# (在模板中内置或通过过滤器应用)

# Step 4: 渲染Markdown
markdown_content = template.render(
    company_name=data['company_name'],
    events=data['events'],
    metadata=data['metadata']
)

# Step 5: 保存Markdown
with open(md_output_path, 'w', encoding='utf-8') as f:
    f.write(markdown_content)

# Step 6: 转换为Word
from docx_generator import convert_to_docx
convert_to_docx(
    markdown_path=md_output_path,
    output_path=docx_output_path,
    style_config=style_config
)

# Step 7: 质量检查
quality_report = run_quality_checks(docx_output_path)
save_quality_report(quality_report)
```

### 写作标准示例

```markdown
## 写作标准

### 时间表达
- ✅ "2020年1月15日"
- ❌ "2020/01/15", "20200115"

### 货币表达
- ✅ "注册资本为人民币100万元"
- ❌ "注册资本RMB100万", "资本100w"

### 专业术语
- ✅ "股权转让"
- ❌ "股份转让"（公司制用"股权"）

### 句式规范
- 使用被动语态："公司于XX日期完成XX变更"
- 避免口语化："公司改了名字"
```

---

## M8: Skills知识库 (可选)

### Skills结构

```
.claude/skills/{domain}-foundations/
├── README.md
├── 01_basic_concepts.md          # 基础概念
├── 02_document_structure.md      # 文档结构
├── 03_terminology.md             # 术语表
└── 04_common_patterns.md         # 常见模式

.claude/skills/{domain}-extraction/
├── README.md
├── extraction_workflow.md        # 提取流程
├── special_cases.md              # 特殊情况处理
└── validation_rules.md           # 验证规则

.claude/skills/{domain}-report-writing/
├── README.md
├── templates/                    # Jinja2模板
├── writing_standards.md          # 写作规范
└── formatting_guide.md           # 格式指南
```

### Skills vs Agents

| 维度 | Skills | Agents |
|------|--------|--------|
| **内容** | 静态知识、规范 | 执行流程、检查点 |
| **调用** | /skill 命令 | /task 工具 |
| **更新** | 领域知识更新时 | 流程优化时 |
| **独立性** | 可独立查询 | 需要配置环境 |

### Skills实施建议

**必选场景**:
- 领域术语复杂（金融、法律）
- 写作规范严格
- 多个Agent需要共享知识

**可选场景**:
- 简单提取任务
- 规则少且稳定
- 单一Agent项目

---

## 🏗️ 完整架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  Prompt → 工作流控制器 → Agent调用                           │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      配置管理层                              │
│  .processing_config.json → 路径/模板/状态                    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Agent执行层                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Extractor  │ → │   Analyzer   │ → │Report Writer │  │
│  │   Agent      │    │   Agent      │    │   Agent      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↓                   ↓                    ↓          │
│  强制检查(P0-P3)     业务逻辑         模板渲染              │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据处理层                              │
│  输入文档 → JSON数据 → Markdown → Word/PDF                   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      支持层                                  │
│  Skills知识库 | Round机制 | 并行隔离 | 质量检查              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 项目实施模板

### 阶段1: 基础架构（必选）

```bash
# 目录结构
project_name/
├── .claude/
│   └── agents/
│       ├── {domain}-extractor.md
│       └── report-writer.md
├── 工具/
│   └── workflow_controller.py
├── 输入样例/
└── 输出/
    └── 中间数据/

# 核心文件
1. workflow_controller.py (M2)
   - init, check, status 命令
   - 配置生成
   - 目录管理

2. {domain}-extractor.md (M1)
   - 配置验证 (Step 0.X)
   - 数据提取逻辑
   - JSON输出

3. report-writer.md (M1)
   - 配置验证
   - 模板渲染
   - 文档生成
```

### 阶段2: 多轮次支持（推荐）

```bash
# 新增功能
1. workflow_controller.py
   + new_round(reason, new_files)
   + Round目录创建
   + Round元数据生成

2. {domain}-extractor.md
   + Round检测逻辑
   + 增量处理逻辑
   + 数据合并逻辑

3. 输出/
   ├── round_1/
   │   ├── .round_metadata.json
   │   └── 中间数据/
   └── round_2/
```

### 阶段3: 并行处理（可选）

```bash
# 新增功能
1. workflow_controller.py
   + init_multi()
   + add_company(name)
   + list_companies()
   + 路径自动检测

2. 所有Agents
   + P0-P3 检查点

3. 文档
   + PARALLEL_PROCESSING_PROTOCOL.md
   + PARALLEL_PROCESSING_PROMPTS.md

4. 目录结构
companies/
├── 实体A/
└── 实体B/
```

---

## ⚡ 快速实施检查清单

### 最小可行产品 (MVP)

- [ ] **M1**: 至少2个Agent（extractor + writer）
- [ ] **M2**: 工作流控制器（init + check）
- [ ] **M3**: 配置文件生成
- [ ] **M6**: 基础数据提取
- [ ] **M7**: 基础文档生成

**估算**: 2-3天

### 完整功能版本

MVP + 以下模块:

- [ ] **M4**: 多轮次处理（Round机制）
- [ ] **M8**: Skills知识库（如领域复杂）
- [ ] 完善的错误处理
- [ ] 详细的用户文档
- [ ] 质量检查机制

**估算**: 5-7天

### 企业级版本

完整版 + 以下模块:

- [ ] **M5**: 并行处理（多实体支持）
- [ ] 全面的安全检查（P0-P3）
- [ ] 性能优化
- [ ] 监控和日志
- [ ] 自动化测试

**估算**: 10-14天

---

## 🎯 领域适配指南

### 将此架构应用到新领域

| 步骤 | 动作 | 示例 |
|------|------|------|
| 1 | 确定领域 | 债券审核、合同分析、财报解读 |
| 2 | 定义实体 | 债券、合同、公司 |
| 3 | 识别阶段 | 提取→分析→报告 |
| 4 | 设计Agent | bond-extractor, bond-analyzer, report-writer |
| 5 | 定义数据结构 | JSON schema |
| 6 | 创建模板 | Jinja2报告模板 |
| 7 | 编写Skills | 领域知识（如需要） |
| 8 | 测试验证 | 真实案例测试 |

### 领域对照表

| 本项目 | 债券审核 | 合同分析 | 适配方法 |
|--------|---------|---------|---------|
| 公司 | 债券 | 合同 | 替换实体名称 |
| 工商档案 | 募集说明书 | 合同文本 | 替换输入类型 |
| 历史沿革 | 风险事项 | 条款要点 | 替换提取目标 |
| 股权变更 | 财务指标 | 权利义务 | 替换事件类型 |

---

## 📚 关键文件模板

### 1. Agent模板

```markdown
---
name: {domain}-extractor
description: 从{输入类型}中提取{目标数据}
model: sonnet
color: yellow
---

# {Domain} Extractor Agent

## Agent Overview
- Input: {输入说明}
- Output: {输出说明}

## 🔒 MANDATORY: Configuration Verification
[Step 0.0-0.3: 标准配置检查]

## Core Workflow
Step 1: 扫描输入文档
Step 2: 识别关键信息
Step 3: 结构化提取
Step 4: 数据验证
Step 5: 保存JSON

## Output Format
[JSON结构定义]
```

### 2. 配置文件模板

```json
{
  "entity_info": {
    "entity_name": "实体名称",
    "entity_type": "实体类型"
  },
  "paths": {
    "input_dir": "输入样例/",
    "output_dir": "输出/",
    "intermediate_dir": "输出/中间数据/"
  },
  "file_templates": {
    "extraction_output": "{entity_name}_提取数据.json",
    "report": "{entity_name}_报告.docx"
  }
}
```

### 3. 工作流控制器模板

```python
class WorkflowController:
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_file = self.project_root / ".processing_config.json"
        self.dirs = {
            'input': self.project_root / '输入样例',
            'output': self.project_root / '输出'
        }

    def init(self, entity_name: str):
        # 1. 检查目录
        # 2. 扫描输入
        # 3. 生成配置
        # 4. 创建输出目录
        pass

    def check(self):
        # 环境状态检查
        pass
```

---

## 💡 最佳实践总结

### DO ✅

1. **配置驱动一切** - 禁止硬编码路径
2. **Agent单一职责** - 每个Agent专注一件事
3. **强制环境检查** - Step 0.X 非可选
4. **详细错误提示** - 告诉用户如何修复
5. **结构化数据** - JSON作为Agent间桥梁
6. **模板化输出** - Jinja2 + 写作标准
7. **相对路径** - 支持项目移动
8. **状态追踪** - 记录处理进度

### DON'T ❌

1. **硬编码路径** - `Path('输入样例/')`
2. **跳过检查** - 直接开始处理
3. **混合职责** - 一个Agent做多件事
4. **隐晦错误** - "失败"没有详情
5. **非结构化数据** - Agent间传递文本
6. **绝对路径** - `/root/project/xxx`
7. **状态黑盒** - 用户不知道进展
8. **省略文档** - 只有代码没有说明

---

## 🔗 参考资源

### 本项目关键文档

| 文档 | 位置 | 用途 |
|------|------|------|
| 方案B报告 | `方案B实施完成报告.md` | Round机制实施 |
| 方案D报告 | `方案D并行处理实施完成报告.md` | 并行处理实施 |
| 并行协议 | `.claude/PARALLEL_PROCESSING_PROTOCOL.md` | 安全检查规范 |
| Prompt模板 | `.claude/PARALLEL_PROCESSING_PROMPTS.md` | 使用指南 |

### 代码参考

| 文件 | 关键内容 |
|------|---------|
| `工具/公司历史工作流控制器.py` | 完整控制器实现 |
| `.claude/agents/corp-history-extractor.md` | Agent结构示例 |
| `.claude/agents/report-writer.md` | 报告生成示例 |

---

## 📊 复杂度评估

### 不同项目类型的模块需求

| 项目类型 | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | 复杂度 |
|---------|----|----|----|----|----|----|----|----|-------|
| 简单提取 | ✅ | ✅ | ✅ | - | - | ✅ | - | - | 低 |
| 分析+报告 | ✅ | ✅ | ✅ | - | - | ✅ | ✅ | ⭐ | 中 |
| 多轮审核 | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ⭐ | 中高 |
| 批量处理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 高 |

图例: ✅ 必选 | ⭐ 推荐 | - 不需要

---

## 总结

这套模块化架构已在两个项目中验证有效：
- **corpfile_summary**: 公司历史沿革分析
- **debt_review_skills**: 债券尽调审核

**核心价值**:
1. 高度模块化，按需组装
2. 配置驱动，易于维护
3. 安全检查，数据隔离
4. 渐进式增强，从MVP到企业级

**适用场景**:
- 文档分析类项目
- 数据提取+报告生成
- 需要多轮审核/并行处理
- 对数据安全有要求

**快速开始**: 从MVP检查清单开始，逐步添加M4、M5等高级模块。

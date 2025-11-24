# 并行处理协议 (Parallel Processing Protocol)

## 概述

本协议定义了公司历史沿革分析系统在并行处理多个公司时的安全规范和操作流程。

**并行处理场景**：
- 同时分析多个目标公司
- 每个公司由独立的Agent实例处理
- 确保数据隔离，防止混淆

**适用对象**：
- corp-history-extractor Agent
- report-writer Agent
- 所有访问文件系统的操作

---

## 架构设计

### 目录结构

#### 单公司模式（当前）
```
corpfile_summary/
├── .processing_config.json          # 单一配置
├── 输入样例/                         # 单一输入
├── 输出/                            # 单一输出
│   ├── round_1/
│   └── round_2/
└── 工具/
```

#### 多公司并行模式（推荐）
```
corpfile_summary/
├── companies/                       # 公司目录
│   ├── 优界科技/
│   │   ├── .processing_config.json
│   │   ├── 输入样例/
│   │   ├── 输出/
│   │   │   ├── round_1/
│   │   │   └── round_2/
│   │   └── .company_id              # 公司标识文件
│   │
│   ├── 北京XX有限公司/
│   │   ├── .processing_config.json
│   │   ├── 输入样例/
│   │   ├── 输出/
│   │   └── .company_id
│   │
│   └── 深圳YY科技/
│       ├── .processing_config.json
│       ├── 输入样例/
│       ├── 输出/
│       └── .company_id
│
└── 工具/                            # 共享工具
    ├── 公司历史工作流控制器.py
    └── docx_generator.py
```

### 工作目录概念

**当前工作目录 (CWD)** = 要处理的公司目录

例如：
- 处理"优界科技"时：CWD = `/path/to/corpfile_summary/companies/优界科技/`
- 处理"北京XX"时：CWD = `/path/to/corpfile_summary/companies/北京XX有限公司/`

---

## 核心原则

### 原则1：工作目录隔离 (Directory Isolation)

**强制要求**：
```markdown
✅ Agent MUST work within specified company directory
❌ Agent MUST NOT access other company directories
❌ Agent MUST NOT access parent directories (except tools)
```

**实现方式**：
```python
# 验证当前工作目录
cwd = Path.cwd()
company_dir_name = cwd.name  # 例如："优界科技"

# 所有路径必须相对于当前工作目录
input_dir = cwd / "输入样例"
output_dir = cwd / "输出"
config_file = cwd / ".processing_config.json"

# ❌ 禁止访问其他公司
forbidden = cwd.parent / "其他公司"  # DO NOT ACCESS
```

### 原则2：配置-提示一致性 (Config-Prompt Consistency)

**强制要求**：
```markdown
配置文件中的公司名称 MUST MATCH 用户提示中指定的公司名称
```

**验证流程**：
```python
# 1. 从配置读取公司名称
config_company = config['company_info']['company_name']

# 2. 从用户提示提取公司名称
prompt_company = "优界科技"  # User specified in prompt

# 3. 强制验证
if config_company != prompt_company:
    raise Error("Company mismatch!")
    print(f"❌ ERROR: Company name mismatch")
    print(f"   Config:  {config_company}")
    print(f"   Prompt:  {prompt_company}")
    print(f"   Action: STOP - You may be in wrong directory")
    # STOP ALL WORK
```

### 原则3：仅处理指定公司 (Process ONLY Specified Company)

**强制要求**：
```markdown
Agent MUST process ONLY the company specified in the prompt
Agent MUST NOT process multiple companies in one invocation
```

**检查清单**：
```
□ Current working directory verified
□ Configuration file belongs to correct company
□ Input files are for correct company
□ Output will go to correct company directory
□ No references to other companies in processing
```

### 原则4：路径使用规范 (Path Usage Standards)

**强制要求**：
```python
# ✅ CORRECT: Relative paths from CWD
input_dir = Path("输入样例")
output_dir = Path("输出")
config_file = Path(".processing_config.json")

# ✅ CORRECT: From config
input_dir = Path(config['paths']['input_dir'])  # "输入样例/"
output_dir = Path(config['paths']['output_dir'])  # "输出/"

# ❌ WRONG: Absolute paths
input_dir = Path("/root/corpfile_summary/companies/优界科技/输入样例")

# ❌ WRONG: Parent directory access
other_company = Path("../其他公司")

# ✅ ALLOWED: Tools directory (shared resource)
tool_path = Path("../../工具/docx_generator.py")
```

---

## Agent 强制检查点

### 对于 corp-history-extractor Agent

#### 检查点 P0: 工作目录验证 (FIRST CHECKPOINT)

**在配置验证之前执行**：

```bash
# 检查当前工作目录
pwd
```

```python
from pathlib import Path

cwd = Path.cwd()
print(f"Current working directory: {cwd}")

# 验证目录名称
if cwd.name not in ["优界科技", "北京XX有限公司", ...]:  # 或其他验证逻辑
    print("⚠️  Warning: Current directory name unusual")
    print(f"   Directory: {cwd.name}")
    print(f"   Expected: A company name directory")

# 验证必需文件存在
required_files = [".processing_config.json", "输入样例", "输出"]
for item in required_files:
    if not (cwd / item).exists():
        print(f"❌ ERROR: Required item not found: {item}")
        print(f"   You may be in the wrong directory")
        # STOP
```

#### 检查点 P1: 配置-提示一致性验证

**在 Step 0.1 之后执行**：

```python
# Read config
with open('.processing_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

config_company = config['company_info']['company_name']

# Extract company from prompt (user must specify)
prompt_company = "优界科技"  # ← From user prompt

# MANDATORY VERIFICATION
if config_company != prompt_company:
    print(f"❌ CRITICAL ERROR: Company name mismatch!")
    print(f"")
    print(f"   Configuration file says: {config_company}")
    print(f"   User prompt specifies:   {prompt_company}")
    print(f"")
    print(f"   This indicates you are processing the WRONG company!")
    print(f"   ")
    print(f"   Possible causes:")
    print(f"   1. You are in the wrong directory")
    print(f"   2. The configuration file is incorrect")
    print(f"   3. The prompt specified wrong company name")
    print(f"   ")
    print(f"   Action required:")
    print(f"   - Verify current directory: pwd")
    print(f"   - Verify you should process: {prompt_company}")
    print(f"   - If directory is wrong, cd to correct company directory")
    print(f"   - If config is wrong, re-initialize with correct company name")
    print(f"   ")
    print(f"   ⛔ STOPPING ALL WORK - DO NOT PROCEED")
    # STOP IMMEDIATELY
else:
    print(f"✓ Company verification passed: {config_company}")
```

#### 检查点 P2: 路径隔离验证

**在使用任何路径之前执行**：

```python
# Verify all paths are within current company directory
cwd = Path.cwd()

input_dir = Path(config['paths']['input_dir'])
output_dir = Path(config['paths']['output_dir'])
intermediate_dir = Path(config['paths']['intermediate_dir'])

# Resolve to absolute paths
input_abs = (cwd / input_dir).resolve()
output_abs = (cwd / output_dir).resolve()
intermediate_abs = (cwd / intermediate_dir).resolve()

# Verify all paths are under CWD
for path_name, path in [("input", input_abs),
                         ("output", output_abs),
                         ("intermediate", intermediate_abs)]:
    try:
        path.relative_to(cwd)
        print(f"✓ {path_name} path is within company directory")
    except ValueError:
        print(f"❌ ERROR: {path_name} path escapes company directory!")
        print(f"   Path: {path}")
        print(f"   CWD:  {cwd}")
        print(f"   This is a SECURITY VIOLATION")
        print(f"   ⛔ STOPPING - Path configuration is dangerous")
        # STOP
```

#### 检查点 P3: 最终确认

**在开始实际处理之前**：

```
✓ PARALLEL PROCESSING VERIFICATION SUMMARY

Company to process: {prompt_company}
Working directory:  {cwd}
Configuration says: {config_company}
✓ Names match: {prompt_company == config_company}

Input directory:  {input_dir} (verified isolated)
Output directory: {output_dir} (verified isolated)

⚠️  REMINDER: Process ONLY {prompt_company}
⚠️  DO NOT access data from other companies
⚠️  All outputs will go to {output_dir}

Proceeding with extraction...
```

---

### 对于 report-writer Agent

**相同的检查点 P0-P3**，验证逻辑完全相同。

**额外检查**：

```python
# Verify input JSON is for correct company
input_json_path = Path(config['paths']['intermediate_dir']) / \
                  config['file_templates']['extraction_output'].format(
                      company_name=config_company
                  )

# When reading JSON, verify company name inside matches
with open(input_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

json_company = data.get('company_name')
if json_company != config_company:
    print(f"❌ ERROR: JSON data company mismatch!")
    print(f"   Config:  {config_company}")
    print(f"   JSON:    {json_company}")
    print(f"   ⛔ Data integrity issue - STOP")
    # STOP
```

---

## 工作流控制器支持

### 多公司初始化

**新命令**: `init-multi`

```bash
# 初始化多公司环境
python3 工具/公司历史工作流控制器.py init-multi

# 为新公司创建目录
python3 工具/公司历史工作流控制器.py add-company --name "优界科技"
python3 工具/公司历史工作流控制器.py add-company --name "北京XX有限公司"

# 列出所有公司
python3 工具/公司历史工作流控制器.py list-companies
```

### 公司目录结构

**自动创建**：
```
companies/优界科技/
├── .processing_config.json
├── .company_id              # 内容: "优界科技"
├── 输入样例/
├── 输出/
│   └── round_1/
│       └── .round_metadata.json
└── README.md                # 公司特定说明
```

---

## 并行调用模板

### 调用 extractor Agent（并行安全）

```
请使用 corp-history-extractor agent 处理 **优界科技** 的工商档案。

重要提示：
- 当前应该在目录：companies/优界科技/
- 只处理优界科技的数据
- 输出将保存到 companies/优界科技/输出/
```

### 调用 report-writer Agent（并行安全）

```
请使用 report-writer agent 为 **优界科技** 生成历史沿革报告。

重要提示：
- 当前应该在目录：companies/优界科技/
- 只使用优界科技的提取数据
- 输出将保存到 companies/优界科技/输出/
```

---

## 批量并行处理示例

### 场景：同时处理3个公司

**准备阶段**：
```bash
cd /path/to/corpfile_summary

# 初始化多公司环境
python3 工具/公司历史工作流控制器.py init-multi

# 创建3个公司目录
python3 工具/公司历史工作流控制器.py add-company --name "优界科技"
python3 工具/公司历史工作流控制器.py add-company --name "北京XX有限公司"
python3 工具/公司历史工作流控制器.py add-company --name "深圳YY科技"

# 放置各公司的档案文件
cp 优界科技档案/*.md companies/优界科技/输入样例/
cp 北京XX档案/*.md companies/北京XX有限公司/输入样例/
cp 深圳YY档案/*.md companies/深圳YY科技/输入样例/

# 初始化各公司环境
cd companies/优界科技 && python3 ../../工具/公司历史工作流控制器.py init --company "优界科技" && cd ../..
cd companies/北京XX有限公司 && python3 ../../工具/公司历史工作流控制器.py init --company "北京XX有限公司" && cd ../..
cd companies/深圳YY科技 && python3 ../../工具/公司历史工作流控制器.py init --company "深圳YY科技" && cd ../..
```

**并行处理（在3个独立的Claude Code会话中）**：

会话1（处理优界科技）:
```bash
cd /path/to/corpfile_summary/companies/优界科技

# 在此目录下调用Agent
# Agent会验证当前在正确的目录
```

会话2（处理北京XX）:
```bash
cd /path/to/corpfile_summary/companies/北京XX有限公司

# 在此目录下调用Agent
```

会话3（处理深圳YY）:
```bash
cd /path/to/corpfile_summary/companies/深圳YY科技

# 在此目录下调用Agent
```

**结果验证**：
```bash
# 检查各公司输出
ls companies/优界科技/输出/round_1/
ls companies/北京XX有限公司/输出/round_1/
ls companies/深圳YY科技/输出/round_1/
```

---

## 错误处理

### 错误1: 在错误的目录中调用Agent

**现象**：
```
Current directory: /root/corpfile_summary
Config says: 优界科技
```

**问题**: 应该在 `companies/优界科技/` 目录中

**解决**:
```bash
cd companies/优界科技
# 然后重新调用Agent
```

### 错误2: 配置与提示不匹配

**现象**：
```
❌ Company name mismatch!
   Config:  优界科技
   Prompt:  北京XX有限公司
```

**问题**: 在优界科技目录，但提示说要处理北京XX

**解决**:
```bash
cd ../北京XX有限公司
# 或者更正提示中的公司名称
```

### 错误3: 访问其他公司数据

**现象**：
```
❌ Path escapes company directory!
   Path: /path/to/companies/其他公司/输入样例
```

**问题**: 配置文件路径错误，指向了其他公司

**解决**: 修正配置文件或重新初始化

---

## 安全检查清单

### 在开始处理前（Agent必须完成）

```
□ P0: 验证当前工作目录合理
□ P1: 读取配置文件
□ P2: 验证配置公司名 == 提示公司名
□ P3: 验证所有路径在当前公司目录内
□ P4: 确认只会处理指定的公司
□ P5: 最终确认摘要显示
```

### 在完成处理后（Agent必须验证）

```
□ 输出文件在正确的公司目录
□ 输出文件包含正确的公司名称
□ 没有创建或修改其他公司的文件
□ 配置状态已更新（如果需要）
```

---

## 兼容性说明

### 向后兼容（单公司模式）

**当前单公司模式继续支持**：

```
corpfile_summary/
├── .processing_config.json
├── 输入样例/
└── 输出/
```

**识别方式**：
- 如果 `.processing_config.json` 在项目根目录 → 单公司模式
- 如果在 `companies/{公司名}/` 下 → 多公司模式

**Agent自动适配**：
```python
# 检测模式
cwd = Path.cwd()
if (cwd / "companies").exists() and (cwd / "companies").is_dir():
    mode = "multi-company"
    print("✓ Detected multi-company mode")
else:
    mode = "single-company"
    print("✓ Detected single-company mode (legacy)")
```

---

## 总结

### 核心要点

1. **工作目录 = 公司目录**：Agent必须在正确的公司目录中执行
2. **配置-提示一致性**：强制验证配置与用户提示匹配
3. **路径隔离**：所有操作限制在当前公司目录内
4. **仅处理指定公司**：禁止访问其他公司数据

### 实施原则

- **强制验证优先**：所有检查点必须通过才能继续
- **清晰错误提示**：遇到问题立即停止并给出明确指导
- **兼容性保留**：单公司模式继续工作

### 预期收益

- ✅ 支持并行处理多个公司
- ✅ 完全的数据隔离和安全
- ✅ 防止误操作和数据混淆
- ✅ 提升大规模处理能力

---

**版本**: v1.0
**日期**: 2025-11-13
**状态**: 协议定义完成

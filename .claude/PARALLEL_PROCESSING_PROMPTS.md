# 并行处理Prompt模板 (Parallel Processing Prompt Templates)

本文档提供在多公司环境中正确调用Agents的Prompt模板。

---

## 目录结构

多公司环境结构：
```
companies/
├── 优界科技/
│   ├── .processing_config.json
│   ├── 输入样例/
│   └── 输出/
├── 北京XX有限公司/
│   ├── .processing_config.json
│   ├── 输入样例/
│   └── 输出/
└── ...
```

---

## 模板1：单公司处理 (Single Company Processing)

### 场景：处理单个公司

**工作目录要求**：必须在公司目录中（`companies/公司名称/`）

### Prompt模板 - 提取历史数据

```
我需要处理 优界科技 的工商档案。

请使用 corp-history-extractor Agent 提取历史沿革数据。

公司名称：优界科技
档案位置：输入样例/ 目录
```

**关键要素**：
- ✅ 明确指定公司名称
- ✅ Agent会自动验证目录和配置一致性
- ✅ Agent会执行P0-P3安全检查

### Prompt模板 - 生成报告

```
我需要为 优界科技 生成历史沿革报告。

请使用 report-writer Agent 生成Word文档。

公司名称：优界科技
数据来源：输出/中间数据/ 中的JSON文件
```

---

## 模板2：并行处理多个公司 (Parallel Multi-Company Processing)

### 场景：同时处理2-3个公司

**重要前提**：
- 每个公司在独立的终端/会话中处理
- 每个会话的工作目录在对应的公司目录中
- 明确告知Agent要处理的公司名称

### 会话1：处理优界科技

**工作目录**：`companies/优界科技/`

**Prompt**：
```
【会话1：优界科技】

我正在并行处理环境中处理 优界科技。

请使用 corp-history-extractor Agent 提取历史沿革数据。

重要提醒：
- 当前会话仅处理：优界科技
- 其他会话可能同时处理其他公司
- 请确保所有操作限制在当前目录

公司名称：优界科技
```

### 会话2：处理北京XX有限公司

**工作目录**：`companies/北京XX有限公司/`

**Prompt**：
```
【会话2：北京XX有限公司】

我正在并行处理环境中处理 北京XX有限公司。

请使用 corp-history-extractor Agent 提取历史沿革数据。

重要提醒：
- 当前会话仅处理：北京XX有限公司
- 其他会话可能同时处理其他公司
- 请确保所有操作限制在当前目录

公司名称：北京XX有限公司
```

### 关键安全要素

每个Prompt必须包含：
1. **明确的公司名称** - Agent会用于P1验证
2. **会话标识** - 帮助区分不同会话
3. **并行处理提醒** - 提醒Agent注意隔离

---

## 模板3：批量并行处理 (Batch Parallel Processing)

### 场景：一次性指示处理多个公司

**注意**：这个模板会创建多个Agent实例并行运行。

### Prompt模板

```
我需要并行处理以下3个公司的历史沿革：

1. 优界科技
2. 北京XX有限公司
3. 上海YY科技有限公司

请按照以下方式处理：

对于每个公司：
1. 进入公司目录：cd companies/公司名称/
2. 调用 corp-history-extractor Agent
3. 确保Agent仅处理当前目录的公司
4. 完成后生成报告

处理要求：
- 每个公司在独立的Agent实例中处理
- 各公司之间数据完全隔离
- 确保配置文件和Prompt中的公司名称一致
- 所有路径操作限制在各自的公司目录内

请分别为每个公司启动独立的处理流程。
```

---

## 模板4：增量处理（Round 2+） (Incremental Processing)

### 场景：客户补充了新档案

**工作目录**：`companies/优界科技/`

### Prompt模板

```
【Round 2 - 增量处理】

客户为 优界科技 补充了新的变更档案。

背景：
- Round 1 已完成基础分析
- 新增档案：20250101变更.md, 20250620变更.md
- 需要执行增量处理

请执行以下步骤：

1. 使用 corp-history-extractor Agent
2. Agent会自动检测Round 2模式
3. 仅处理新增事件
4. 继承Round 1的未变更数据
5. 生成Round 2的完整报告

公司名称：优界科技
处理模式：增量（incremental）
```

---

## 模板5：错误恢复场景 (Error Recovery)

### 场景：发现配置错误或目录错误

### 检查当前状态

```
我需要验证当前环境是否正确配置。

请执行以下检查：
1. pwd - 确认当前目录
2. 检查 .processing_config.json 是否存在
3. 读取配置文件中的company_name
4. 确认目录名称和配置名称是否一致

如果发现不一致，停止处理并告知我。
```

### 重新初始化

```
我需要重新初始化 优界科技 的环境。

步骤：
1. cd companies/优界科技/
2. 验证当前目录：pwd
3. 重新初始化配置
4. 确认配置正确后再调用Agent

公司名称：优界科技
```

---

## Prompt编写最佳实践

### ✅ DO - 推荐做法

1. **明确指定公司名称**
   ```
   公司名称：优界科技  ← Agent会用于P1验证
   ```

2. **说明处理上下文**
   ```
   我正在并行处理环境中...
   当前会话仅处理：优界科技
   ```

3. **提供会话标识**
   ```
   【会话1：优界科技】
   【会话2：北京XX公司】
   ```

4. **强调安全要求**
   ```
   重要提醒：
   - 仅处理当前目录的公司
   - 不要访问其他公司数据
   - 确保路径隔离
   ```

### ❌ DON'T - 避免的做法

1. **不要混淆公司名称**
   ```
   ❌ "请处理优界科技和北京XX公司"  # 一个Agent调用不应处理多个公司
   ```

2. **不要省略公司名称**
   ```
   ❌ "请提取历史数据"  # 没有明确指定公司
   ```

3. **不要假设工作目录**
   ```
   ❌ "处理companies/优界科技/"  # 应该在目录中，而非从外部指定路径
   ```

4. **不要使用绝对路径**
   ```
   ❌ "读取 /root/corpfile_summary/companies/优界科技/输入样例/"
   ✅ "读取 输入样例/ 目录"
   ```

---

## Agent安全检查响应

当Agent执行P0-P3检查时，你会看到：

### 成功示例

```
📍 Current working directory: /root/corpfile_summary/companies/优界科技
   ✓ Found: .processing_config.json
   ✓ Found: 输入样例
   ✓ Found: 输出
✓ Directory structure verification passed

📋 Configuration company: 优界科技
📝 Prompt specifies company: 优界科技
✓ Company name verification passed: 优界科技

🔒 Path Isolation Verification
   ✓ input        is isolated: 输入样例
   ✓ output       is isolated: 输出
   ✓ intermediate is isolated: 输出/中间数据
✓ Path isolation verification passed - all paths are safe

======================================================================
✓ PARALLEL PROCESSING VERIFICATION SUMMARY
======================================================================
...
✓ All parallel processing safety checks PASSED
======================================================================

Proceeding with extraction...
```

### 失败示例（公司名称不匹配）

```
❌ CRITICAL ERROR: Company name mismatch!

   Configuration file says: 优界科技
   User prompt specifies:   北京XX公司

   This indicates you are processing the WRONG company!

   Action required:
   - Verify current directory: pwd
   - Expected directory: companies/北京XX公司/
   - If in wrong directory: cd companies/北京XX公司/

   ⛔ STOPPING ALL WORK - DO NOT PROCEED
```

**应对措施**：
1. 使用 `pwd` 确认当前目录
2. 如果目录错误，cd到正确的目录
3. 如果配置错误，重新初始化
4. 重新调用Agent

---

## 常见问题 (FAQ)

### Q1: 如何知道我应该在哪个目录？

**A**: 你要处理的公司名称决定目录：
- 处理"优界科技" → 在 `companies/优界科技/` 中
- 处理"北京XX公司" → 在 `companies/北京XX公司/` 中

### Q2: 可以在项目根目录调用Agent吗？

**A**: 不推荐。虽然理论上可以（Agent会检测），但最佳实践是：
- 进入公司目录
- 在公司目录中调用Agent
- 让Agent的安全检查验证环境

### Q3: 如何在一个Prompt中处理多个公司？

**A**: 不应该这样做。正确方式：
- 每个公司单独调用Agent
- 可以在一个Prompt中指示多个Agent调用
- 但每个Agent实例只处理一个公司

示例：
```
请分别处理以下公司：

1. 优界科技：
   - cd companies/优界科技/
   - 调用 corp-history-extractor
   - 公司名称：优界科技

2. 北京XX公司：
   - cd companies/北京XX公司/
   - 调用 corp-history-extractor
   - 公司名称：北京XX公司
```

### Q4: P1检查失败怎么办？

**A**: P1检查失败表示配置文件和Prompt不匹配：
1. 运行 `pwd` 确认目录
2. 检查 `.processing_config.json` 中的 `company_name`
3. 确认Prompt中指定的公司名称
4. 三者必须完全一致

### Q5: 可以跨目录访问吗？

**A**: 不可以。这是硬性安全限制：
- ❌ 不能访问 `../其他公司/`
- ❌ 不能使用绝对路径访问其他公司
- ✅ 只能访问当前公司目录内的文件
- ✅ 可以访问 `../../工具/`（共享工具）

---

## 附录：完整处理流程示例

### 场景：从零开始处理3个公司

#### 步骤1：初始化多公司环境

```bash
python3 工具/公司历史工作流控制器.py init-multi
```

#### 步骤2：添加公司

```bash
python3 工具/公司历史工作流控制器.py add-company --name "优界科技"
python3 工具/公司历史工作流控制器.py add-company --name "北京XX有限公司"
python3 工具/公司历史工作流控制器.py add-company --name "上海YY科技有限公司"
```

#### 步骤3：放置档案文件

```bash
# 将各公司档案放入对应目录
cp 优界科技档案/* companies/优界科技/输入样例/
cp 北京XX档案/* companies/北京XX有限公司/输入样例/
cp 上海YY档案/* companies/上海YY科技有限公司/输入样例/
```

#### 步骤4：初始化各公司配置

```bash
cd companies/优界科技/
python3 ../../工具/公司历史工作流控制器.py init --company "优界科技"
cd ../..

cd companies/北京XX有限公司/
python3 ../../工具/公司历史工作流控制器.py init --company "北京XX有限公司"
cd ../..

cd companies/上海YY科技有限公司/
python3 ../../工具/公司历史工作流控制器.py init --company "上海YY科技有限公司"
cd ../..
```

#### 步骤5：并行处理

**终端1**：
```bash
cd companies/优界科技/
```
**Prompt**：
```
【会话1：优界科技】

请处理 优界科技 的历史沿革。

1. 使用 corp-history-extractor 提取数据
2. 使用 report-writer 生成报告

公司名称：优界科技
并行处理：是的，其他会话同时处理其他公司
```

**终端2**：
```bash
cd companies/北京XX有限公司/
```
**Prompt**：
```
【会话2：北京XX有限公司】

请处理 北京XX有限公司 的历史沿革。

1. 使用 corp-history-extractor 提取数据
2. 使用 report-writer 生成报告

公司名称：北京XX有限公司
并行处理：是的，其他会话同时处理其他公司
```

**终端3**：
```bash
cd companies/上海YY科技有限公司/
```
**Prompt**：
```
【会话3：上海YY科技有限公司】

请处理 上海YY科技有限公司 的历史沿革。

1. 使用 corp-history-extractor 提取数据
2. 使用 report-writer 生成报告

公司名称：上海YY科技有限公司
并行处理：是的，其他会话同时处理其他公司
```

---

## 总结

### 核心原则
1. **明确指定** - 总是在Prompt中明确公司名称
2. **目录隔离** - 在公司目录中操作，不跨越边界
3. **安全验证** - 依赖Agent的P0-P3检查
4. **会话独立** - 每个会话处理一个公司

### 模板选择指南
- 单个公司 → 模板1
- 同时2-3个公司 → 模板2
- 批量指示 → 模板3
- Round 2+ → 模板4
- 问题排查 → 模板5

遵循这些模板和最佳实践，可以确保安全、正确地进行并行处理。

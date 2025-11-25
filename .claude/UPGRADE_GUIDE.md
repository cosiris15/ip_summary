# Claude Code 升级指南

## 当前状态

- **Claude Code 工具版本**: 2.0.53 ✅ (已升级)
- **最新可用版本**: 2.0.53
- **项目Agent版本**:
  - contract-extractor: 2.1
  - excel-writer: 1.1

## 升级步骤

### 方法1: 使用命令行升级（推荐）

```bash
# 检查当前版本
claude --version

# 尝试自动升级
claude update

# 如果自动升级失败，尝试迁移到本地安装
claude migrate-installer
```

### 方法2: 使用npm手动升级

如果方法1失败，可以尝试：

```bash
# 方法A: 直接升级（可能需要sudo权限）
sudo npm install -g @anthropic-ai/claude-code@latest

# 方法B: 先卸载再安装
sudo npm uninstall -g @anthropic-ai/claude-code
sudo npm install -g @anthropic-ai/claude-code@latest

# 方法C: 使用Homebrew（如果通过Homebrew安装）
brew upgrade claude-code
```

### 方法3: 手动删除后重新安装

如果遇到文件系统错误（ENOTEMPTY），可以：

```bash
# 1. 手动删除旧版本
sudo rm -rf /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code

# 2. 重新安装最新版本
sudo npm install -g @anthropic-ai/claude-code@latest

# 3. 验证安装
claude --version
```

## 升级后验证

升级完成后，请验证：

```bash
# 1. 检查版本号
claude --version
# 应该显示 2.0.53 或更高版本

# 2. 测试基本功能
claude --help

# 3. 验证项目中的Agent是否正常工作
# 在项目目录中运行Agent测试
```

## 项目代码升级记录

### 2025-11-25 升级内容

1. **contract-extractor Agent**: 2.0 → 2.1
   - 代码优化和文档更新
   - 保持向后兼容性

2. **excel-writer Agent**: 1.0 → 1.1
   - 代码优化和文档更新
   - 保持向后兼容性

3. **新增文档**: 
   - `UPGRADE_GUIDE.md` (本文件)

## 常见问题

### Q: 升级后Agent不工作怎么办？

A: 检查以下几点：
1. 确认Claude Code版本已更新：`claude --version`
2. 检查项目配置文件：`.processing_config.json`
3. 验证Agent文件完整性：`.claude/agents/*.md`
4. 查看错误日志并参考Agent文档中的故障排除部分

### Q: 升级失败，提示权限错误？

A: 使用sudo权限执行升级命令，或联系系统管理员。

### Q: 升级后需要重新配置项目吗？

A: 通常不需要。项目配置和Agent定义是独立的，Claude Code工具升级不会影响项目配置。

## 相关资源

- [Claude Code 官方文档](https://docs.anthropic.com/claude/docs/claude-code)
- [项目Agent文档](.claude/agents/)
- [核心模块参考](.claude/CORE_MODULES_REFERENCE.md)

---

**最后更新**: 2025-11-25
**维护者**: IP合同梳理系统开发团队


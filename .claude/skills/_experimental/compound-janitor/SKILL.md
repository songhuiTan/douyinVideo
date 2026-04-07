---
name: compound-janitor
description: |
  知识清理工作流。每天结束时运行，扫描当天 session 和 git diff，
  筛选有价值的任务批量执行 /ce:compound。防止知识库被低价值内容稀释。
  当用户说"整理知识"/"compound-janitor"时使用。
---

# Compound Janitor 工作流

## 触发条件

- 用户说"整理知识"或"compound-janitor"
- 每日结束时自动建议
- 用户说"回顾今天的工作"

## 核心原则

**不是每个 session 都值得 compound。** Janitor 的价值在于筛选。

---

## Phase 1: 扫描

### 1.1 扫描今日 git diff

```bash
git log --since="today" --oneline --stat
git diff --stat HEAD~{n}..HEAD
```

### 1.2 分析变更类型

对每个 commit/变更进行分类：

| 变更类型 | Compound 价值 | 理由 |
|---------|:------------:|------|
| 新增功能代码 > 200 行 | ⭐⭐⭐ | 架构决策、模式 |
| Bug 修复（涉及 3+ 文件）| ⭐⭐⭐ | 根因分析 |
| 性能优化 | ⭐⭐⭐ | 策略和基准 |
| 新增测试 | ⭐ | 可能不值得 |
| 文档更新 | ⭐ | 通常不值得 |
| CSS/UI 微调 | ✗ | 低价值 |
| 配置变更 | ✗ | 低价值 |
| typo 修复 | ✗ | 低价值 |
| 数据库迁移 | ✗ | 标准操作 |

### 1.3 筛选结果

输出候选列表：
```
## Compound 候选

### ✅ 推荐 compound
1. [commit hash] 用户认证 JWT 实现（+350 行，涉及 auth 模块）
2. [commit hash] 修复 N+1 查询性能问题（涉及 4 个文件）

### ❌ 不推荐 compound
3. [commit hash] 修复 typo（低价值）
4. [commit hash] CSS 颜色调整（低价值）
```

---

## Phase 2: 确认

向用户展示候选列表，询问：

1. "推荐对 [列表] 执行 compound，是否确认？"
2. 用户可以增减列表
3. 确认后批量执行

---

## Phase 3: 批量 Compound

对每个确认的条目执行 `/ce:compound`：

```
for each 候选:
  1. 回溯该变更的完整上下文（git log + 相关文件）
  2. 提取：Problem / What Didn't Work / Solution / Prevention
  3. 检查 docs/solutions/ 是否有相似文档
     - 有 → 更新（增加新信息）
     - 无 → 新建
  4. 写入 docs/solutions/{category}/{filename}.md
  5. 验证 YAML frontmatter 正确性
```

---

## Phase 4: 知识库维护

### 4.1 检查知识库健康度

```
扫描 docs/solutions/
├── 统计每个分类的文件数
├── 检查是否有超过 30 天未更新的文档
├── 检查 critical-patterns.md 是否需要更新
└── 检查是否有重复/高度相似的文档
```

### 4.2 关键模式检测

```
同一类问题出现次数 ≥ 3？
├─ 是 → 写入/更新 docs/solutions/patterns/critical-patterns.md
│       格式：
│       ## [模式名称]
│       - 出现次数：N
│       - 典型场景：
│       - 根因：
│       - 标准解法：
│       - 预防措施：
└─ 否 → 跳过
```

### 4.3 清理建议

向用户报告：
```
## 知识库报告

- 总文档数：X
- 本周新增：Y
- 需要更新的文档：Z
- 重复文档：W
- 关键模式：N

建议：
- [文档A] 和 [文档B] 高度相似，建议合并
- [文档C] 超过 30 天未更新，建议 review
```

---

## Phase 5: 汇报

```
## Compound Janitor 完成

本次 compound：
- 新增文档：X 篇
- 更新文档：Y 篇
- 跳过（低价值）：Z 项
- 发现关键模式：N 个

知识库状态：
- 总文档数：T
- 分类分布：[列表]
- 下次建议运行时间：[明天/本周五]
```

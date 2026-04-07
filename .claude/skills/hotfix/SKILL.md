---
name: hotfix
description: |
  紧急修复工作流。当用户报告 bug 或需要快速修复时使用。
  流程：INVESTIGATE → PLAN → FIX → REVIEW → DEPLOY → COMPOUND
---

# Hotfix 工作流

## 触发条件

- 用户报告 bug
- 用户说"修复"且是具体问题
- 用户说"/hotfix"
- CI 失败需要紧急修复

## 前置检查

1. 读取 `docs/solutions/` 检索历史经验（learnings-researcher）
2. 检查 `docs/solutions/patterns/critical-patterns.md` 是否有已知模式

---

## Phase 1: INVESTIGATE

**状态：** `INVESTIGATING`

### 步骤

1. 执行 `/investigate`（gstack 系统化根因调试）
   - **铁律：不改代码先调查**
   - 最多 3 次失败后停止，报告给用户
   - 自动 `/freeze` 冻结到问题模块

2. 输出调查报告：
   ```
   ## 调查结果
   - 问题模块：
   - 根因：
   - 影响范围：
   - 建议修复策略：
   ```

---

## Phase 2: PLAN

**状态：** `PLANNING`

### 快速规划

1. 执行 `/ce:plan`（MINIMAL 级别）
   - 自动检索 `docs/solutions/` 相关经验
   - 如果找到历史解法，直接复用

2. 评估紧急程度：

```
紧急程度？
├─ P0（线上宕机）   → 跳过部分审查，快速修复
├─ P1（功能受阻）   → 简化审查流程
└─ P2/P3（一般 bug）→ 走完整 hotfix 流程
```

---

## Phase 3: FIX

**状态：** `FIXING`

### 步骤

1. 执行 `/ce:work`
   - worktree 隔离修复
   - 添加回归测试
2. 如果修复涉及多个文件：启用 `/careful`

---

## Phase 4: REVIEW

**状态：** `REVIEWING`

### 按紧急程度选择审查深度

| 紧急程度 | 审查 | 要求 |
|---------|------|------|
| P0 | `/ce:review`（安全+正确性） | 无 P0 |
| P1 | `/ce:review` + `/review` | 无 P0 |
| P2/P3 | `/ce:review` + `/review` + `/qa` | 无 P0/P1 |

---

## Phase 5: DEPLOY

**状态：** `DEPLOYING`

### 步骤

1. P0/P1：直接 `/land-and-deploy` → `/canary`
2. P2/P3：`/ship` → `/land-and-deploy` → `/canary`

---

## Phase 6: COMPOUND

**状态：** `COMPOUNDING`

Bug 修复**几乎总是**值得 compound：

```
值得 compound？
├─ 根因是设计缺陷    → ✅ 写入 prevention
├─ 根因是配置错误    → ✅ 写入 checklist
├─ 根因是依赖问题    → ✅ 写入 workaround
├─ 简单 typo        → ❌
└─ 简单 CSS         → ❌
```

执行 `/ce:compound` 写入 `docs/solutions/`。

---

## 状态流转

```
INVESTIGATING → PLANNING → FIXING → REVIEWING → DEPLOYING → COMPOUNDING
     │             │          │         │            │            │
     │             │          │         │            │            └─→ 完成
     │             │          │         │            └─→ 部署失败 → 重试
     │             │          │         └─→ P0 问题 → 修复 → 重试
     │             │          └─→ 修复失败 → 回到 INVESTIGATE
     │             └─→ 找到历史解法 → 直接 FIX
     └─→ 3次调查失败 → 报告给用户
```

---

## 与 Full Sprint 的区别

| 维度 | Full Sprint | Hotfix |
|------|------------|--------|
| 规划深度 | 详细计划 | MINIMAL 计划 |
| 审查范围 | 全面 | 聚焦安全和正确性 |
| QA | 完整浏览器测试 | 视紧急程度 |
| 知识沉淀 | 有价值时 | 几乎总是 |
| 部署 | 标准流程 | 可加速 |

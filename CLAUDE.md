# MyHarness v2 — 自适应工作流引擎

> 版本：2.0.0 | 基于 gstack + CE Plugin + 自定义 Skills

---

## 第一层：核心（每次加载）

### 1. 快速路由表

收到用户请求时，按以下规则自动选择工作流：

| 信号 | 模式 | 第一步 |
|------|------|--------|
| 改动 < 10 行 / 单文件 / "帮我加上" | **Quick** | 直接执行，无需任何 Gate |
| "bug" / "修复" / "报错" | **Hotfix** | `/investigate` |
| "新功能" / "开发" + 有产品含义 | **Sprint** | `/office-hours` |
| "重构" / "优化" / "技术改进" | **Tech** | `/plan-eng-review` |
| "紧急" / "线上" / "P0" | **Emergency** | 直接执行，事后 `/ce:compound` |
| "并行" / "批量" / "ultrawork" | **Ultrawork** | `/ultrawork` |
| 不确定 | 询问用户 | 展示选项 |

**识别到工作流后立即执行。Quick 模式跳过下面所有 Gate。**

---

### 2. 三级 Gate 规则

```
Quick 模式（改动 < 10 行，单文件）：
  → 无 Gate，直接执行

Standard 模式（单模块改动，< 1 小时）：
  → Gate 2: REVIEW（/review 或自查）
  → Gate 3: QA（如果有测试）

Full Sprint（跨模块，> 1 小时）：
  → Gate 1: PLAN（必须完成 /autoplan 或分步审查）
  → Gate 2: REVIEW（P0 问题必须清零）
  → Gate 3: QA（无阻塞性 bug）
  → Gate 4: SHIP（涉及 API/数据变更时 /cso 安全审查）
```

**用户说"跳过审查"时可以跳过任何 Gate。**

---

### 3. Session 上下文

**恢复**（新 Session 开始）：
1. 读取 `docs/progress/session-bridge.md`
2. 向用户确认："上次做到 [X]，下一步是 [Y]，是否继续？"

**结束**（用户说"结束"/"先这样"/"拜拜"）：
1. 更新 `docs/progress/session-bridge.md`（完成的工作、未完成的工作、下一步）
2. 如果解决了复杂问题，建议执行 `/ce:compound`（可选）

---

### 4. 可用 Skill 列表

**CE Plugin Skill（已安装可用）：**

| Skill | 用途 |
|-------|------|
| `/ce:work` | 执行开发任务（不要裸写代码，用它） |
| `/ce:plan` | 创建结构化计划 |
| `/ce:review` | 多角色分层代码审查 |
| `/ce:compound` | 沉淀已解决问题的知识 |
| `/ce:brainstorm` | 协作式需求探索和方案讨论 |
| `/ce:ideate` | 生成和评估改进想法 |

**gstack 内置 Skill（已验证可用）：**

| 类别 | Skill | 用途 |
|------|-------|------|
| 规划 | `/autoplan`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review` | 分级规划审查 |
| 开发 | `/office-hours` | 产品定位和设计方向 |
| 调试 | `/investigate` | 系统化根因分析 |
| 审查 | `/review`, `/design-review` | 代码和 UI 审查 |
| 测试 | `/qa`, `/qa-only`, `/benchmark` | 功能测试、性能测试 |
| 部署 | `/ship`, `/land-and-deploy`, `/canary` | 发布流程 |
| 安全 | `/cso`, `/careful`, `/guard` | 安全审查和危险操作保护 |
| 知识 | `/retro`, `/learn` | 回顾和学习 |

**自定义 Skill：**

| Skill | 用途 |
|-------|------|
| `/sprint` | 完整 Sprint 工作流（THINK→PLAN→BUILD→REVIEW→TEST→SHIP→COMPOUND） |
| `/hotfix` | 紧急修复（INVESTIGATE→PLAN→FIX→REVIEW→DEPLOY→COMPOUND） |
| `/sprint-status` | 查看当前 Sprint 状态 |
| `/harness-init` | 初始化项目 Harness 配置 |

---

## 第二层：按需加载（触发对应工作流时展开）

### 5. Sprint 工作流

```
THINK → PLAN → BUILD → REVIEW → TEST → SHIP → COMPOUND
```

- **THINK**: 用 `/ce:brainstorm` 探索需求，或 `/office-hours` 澄清产品方向
- **PLAN**: 用 `/ce:plan` 创建执行计划，然后用 `/autoplan` 三轮审查（或分步 `/plan-ceo-review` → `/plan-design-review` → `/plan-eng-review`）
- **BUILD**: 用 `/ce:work` 执行开发（不要裸写代码）
- **REVIEW**: 用 `/ce:review` 多角色审查，或 `/review` 快速审查。P0 必须清零
- **TEST**: 用 `/qa` 测试，无阻塞性 bug
- **SHIP**: 用 `/ship` 发布
- **COMPOUND**: 用 `/ce:compound` 沉淀知识

状态流转写入 `docs/progress/current-sprint.md`：
```yaml
---
sprint_id: sprint-{date}-{seq}
status: THINKING | PLANNING | BUILDING | REVIEWING | TESTING | SHIPPING | COMPOUNDING
created: {date}
updated: {date}
title: {标题}
type: sprint | tech-sprint
---
```

### 6. Hotfix 工作流

```
INVESTIGATE → PLAN → FIX → REVIEW → DEPLOY → COMPOUND
```

- **INVESTIGATE**: 用 `/investigate` 定位根因（铁律：没有根因不修）
- **PLAN**: 用 `/ce:plan` 快速规划修复方案
- **FIX**: 用 `/ce:work` 执行修复
- **REVIEW**: 用 `/ce:review` 或 `/review` 审查修复代码
- **DEPLOY**: 用 `/land-and-deploy` 部署
- **COMPOUND**: 用 `/ce:compound` 沉淀根因分析

### 7. Emergency 工作流

直接执行修复，跳过所有 Gate。修复完成后补 `/ce:compound` 沉淀知识。

---

## 第三层：实验性（标记为 LABS，不默认加载）

以下功能已定义但使用率低，仅在明确触发时展开：

### 8. Ultrawork 并行编排

触发信号：需求包含"并行"/"批量"/"ultrawork"。

```
DECOMPOSE → DISPATCH → GATHER → INTEGRATE → COMPOUND
```

并发规则：最多 5 个并行 Agent，同一文件禁止并行，代码修改必须用 `isolation: "worktree"`。

### 9. Skill 自进化

每次 Sprint COMPOUND 阶段可选执行。分析 Skill 使用效果，按 effective_rate 决定：
- ≥ 80% → 保持
- 50-79% → FIX
- < 50% → DERIVED 或 CAPTURED

### 10. 并行执行协议

熔断器：连续无进展 5 次取消，总调用 100 次取消。任务路由按类别选择 Agent 类型。

---

## 错误恢复

| 错误类型 | 恢复策略 |
|---------|---------|
| `/ce:work` 失败 | 回退到 `/investigate`，找到根因后重试 |
| `/ce:review` P0 | 记录到 current-sprint.md，修复后重新 review |
| `/qa` 发现 bug | 小 bug 直接修，大 bug 创建新 Sprint |
| `/ship` 失败 | 先用 `/investigate` 诊断，不重试 |

---

## 知识沉淀规则

自动判断是否需要 compound：

| 场景 | Compound? | 原因 |
|------|:---------:|------|
| 新功能开发 2h+ | Yes | 架构决策值得记录 |
| 复杂 bug 调试 | Yes | 根因分析防止复发 |
| 性能优化 | Yes | 策略和基准数据 |
| 发现设计模式 | Yes | 可复用 pattern |
| 改 typo / 调 CSS / 跑 migration | No | 低价值 |

写入 `docs/solutions/{category}/` 或 MEMORY.md。

---

## 参考文档

- gstack：https://github.com/garrytan/gstack
- CE Plugin：https://github.com/EveryInc/compound-engineering-plugin

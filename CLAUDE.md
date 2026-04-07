# MyHarness — gstack + CE 组合工作流引擎

> 版本：1.1.0 | 基于 gstack (Garry Tan) + Compound Engineering Plugin (EveryInc) + oh-my-openagent（并行架构）

---

## 工作流引擎规则

本文件是 Claude Code 的 harness 指令。所有开发活动必须遵循以下规则。

---

### 1. 自动决策逻辑

收到用户请求时，按以下规则自动选择工作流：

| 信号 | 工作流 | 第一步 |
|------|--------|--------|
| 包含"新功能"/"新增"/"开发" + 有产品含义 | Full Sprint | `/office-hours` |
| 包含"重构"/"优化"/"技术改进" | Tech Sprint | `/plan-eng-review` |
| 包含"bug"/"修复"/"报错" | Hotfix | `/investigate` |
| 包含"紧急"/"线上"/"宕机"/"P0" | Emergency | 直接 `/ce:work` + 事后 `/ce:compound` |
| 包含"并行"/"同时"/"批量"/"ultrawork" | Ultrawork | `/ultrawork`（先 DECOMPOSE） |
| 不确定 | 询问用户选择哪种工作流 | 展示选项 |

**识别到工作流类型后，立即执行对应 skill。**

---

### 2. 质量关卡（Quality Gates）

以下关卡**不可跳过**，除非用户明确说"跳过审查"：

```
GATE 1: PLAN 通过前
  ├── 禁止执行 /ce:work 或任何代码写入
  ├── 必须完成 /autoplan 或分步审查
  └── current-sprint.md status ≥ PLANNED

GATE 2: REVIEW 通过前
  ├── 禁止执行 /qa（测试依赖审查完成）
  ├── /ce:review 的 P0 问题必须清零
  └── current-sprint.md status ≥ REVIEWED

GATE 3: QA 通过前
  ├── 禁止执行 /ship 或 /land-and-deploy
  ├── /qa 必须无阻塞性 bug
  └── current-sprint.md status ≥ TESTED

GATE 4: SHIP 前
  ├── 必须执行 /cso（安全审查）— 如果涉及 API/数据/权限变更
  └── current-sprint.md status ≥ SHIPPING
```

---

### 3. Session 恢复协议

**每次新 session 开始时，必须按顺序执行：**

```
Step 1: 读取 docs/progress/current-sprint.md
        → 了解当前 Sprint 状态和阶段

Step 2: 读取 docs/progress/session-bridge.md
        → 获取上次 session 交接的上下文

Step 3: 用 learnings-researcher 检索 docs/solutions/
        → 查找与当前任务相关的历史经验

Step 4: 向用户确认
        → "上次做到 [阶段]，下一步是 [动作]，是否继续？"
```

**如果没有活跃 Sprint：**
- 询问用户是要创建新 Sprint 还是做一次性任务
- 创建新 Sprint 时，初始化 `docs/progress/current-sprint.md`

---

### 4. Session 结束协议

**每次 session 结束前（用户说"结束"/"先这样"/"拜拜"）：**

```
Step 1: 更新 docs/progress/current-sprint.md
        → 更新 status、已完成的步骤、关键决策

Step 2: 写入 docs/progress/session-bridge.md
        → 记录：完成的工作、未完成的工作、关键上下文、下一步

Step 3: 判断是否需要 compound
        → 如果本次 session 解决了复杂问题，询问是否执行 /ce:compound

Step 4: 简要汇报
        → "本次完成了 [X]，下次从 [Y] 继续"
```

---

### 5. 状态文件管理

#### current-sprint.md 格式

```yaml
---
sprint_id: sprint-{date}-{seq}
status: THINKING | PLANNING | BUILDING | REVIEWING | TESTING | SHIPPING | COMPOUNDING
created: {date}
updated: {date}
title: {sprint 标题}
type: full-sprint | tech-sprint | hotfix | emergency
---
```

状态流转（只能单向前进）：
```
THINKING → PLANNING → BUILDING → REVIEWING → TESTING → SHIPPING → COMPOUNDING
```

#### session-bridge.md 格式

每次 session 结束时**覆盖写入**，只保留最新一次交接：
- 完成的工作（列表）
- 未完成的工作（列表）
- 关键上下文（决策、约束、偏好）
- 下一步（明确的第一件事）

---

### 6. 工具使用约束

#### 6.1 命令选择规则

```
规划类：
  小/中需求 → /autoplan（一键三轮审查）
  大需求   → /plan-ceo-review → /plan-design-review → /plan-eng-review
  纯技术   → /plan-eng-review → /ce:plan

执行类：
  所有开发 → /ce:work（不要裸写代码）
  危险操作 → 先 /careful 或 /guard

审查类：
  代码审查 → 先 /ce:review，再 /review
  UI 变更  → 额外 /design-review
  跨验证  → /codex（可选，高风险变更时使用）

测试类：
  功能测试 → /qa
  仅验证   → /qa-only
  性能     → /benchmark

部署类：
  标准发布 → /ship → /land-and-deploy → /canary
  紧急修复 → /land-and-deploy → /canary

知识类：
  有价值 session → /ce:compound
  每周           → /retro
  日常偏好       → /learn
```

#### 6.2 知识沉淀规则

**自动判断是否需要 compound：**

| 场景 | Compound? | 原因 |
|------|:---------:|------|
| 新功能开发了 2h+ | ✅ | 架构决策值得记录 |
| 调试了复杂 bug | ✅ | 根因分析防止复发 |
| 性能优化 | ✅ | 策略和基准数据 |
| 发现了设计模式 | ✅ | 可复用的 pattern |
| 改 typo | ❌ | 低价值 |
| 调 CSS | ❌ | 低价值 |
| 跑 migration | ❌ | 标准操作 |

**Compound 写入规则：**
- 写入 `docs/solutions/{category}/` 目录
- 严格遵循 YAML frontmatter schema
- 检查是否已有相关文档，有则更新而非新建
- 同类问题 ≥3 次时，写入 `docs/solutions/patterns/critical-patterns.md`

---

### 7. 框架安装验证

**使用任何工作流命令前，验证框架已安装：**

```bash
# 验证 gstack
test -d ~/.claude/skills/gstack && echo "gstack: OK" || echo "gstack: MISSING"

# 验证 CE Plugin
test -d ~/.claude/skills/compound-engineering && echo "CE: OK" || echo "CE: MISSING"
```

如果缺失，提示用户安装并给出安装命令。

---

### 8. 并行工作规则

- 每个独立功能用**独立 worktree** 开发
- 最多同时运行 **3 个并行 Sprint**
- 每个 Sprint 维护独立的 `current-sprint.md`
- 并行 Sprint 之间通过 `docs/solutions/` 共享知识

---

### 9. 错误恢复

| 错误类型 | 恢复策略 |
|---------|---------|
| /ce:work 失败 | 回退到 /investigate，找到根因后重试 |
| /ce:review P0 | 记录到 current-sprint.md，执行修复后重新 /ce:review |
| /qa 发现 bug | 用 /investigate 定位，小 bug 直接修，大 bug 创建新 Sprint |
| /ship 失败 | 不重试，先用 /investigate 诊断 |
| CI 失败 | 读取错误日志，分类后决定修复策略 |

---

### 10. 可用的自定义命令

| 命令 | 用途 |
|------|------|
| `/sprint` | 启动完整 Sprint 工作流 |
| `/hotfix` | 启动紧急修复工作流 |
| `/compound-janitor` | 运行知识清理（筛选有价值的 session 批量 compound） |
| `/harness-init` | 初始化项目 harness 配置 |
| `/sprint-status` | 查看当前 Sprint 状态 |
| `/skill-evolution` | 运行技能自进化分析 |
| `/safety-check` | 对 skill 运行安全审查 |

---

### 11. Skill 自进化协议

> 借鉴 OpenSpace 的 FIX/DERIVED/CAPTURED 三种进化模式

**每次 Sprint COMPOUND 阶段，除了执行 /ce:compound 沉淀知识，还要执行 /skill-evolution 分析技能效果。**

#### 进化触发条件

```
每次 Sprint 结束后：
├── 更新 docs/progress/skill-metrics.md（记录 skill 使用统计）
├── 计算 effective_rate = completions / selections
│
├── effective_rate ≥ 80% → 🟢 保持
├── effective_rate 50-79% → 🟡 FIX（修复 skill 指令）
├── effective_rate 20-49% → 🟠 FIX 或 DERIVED（重写或派生）
├── effective_rate < 20%  → 🔴 CAPTURED（重写全新 skill）
│
└── 发现新模式但没有 skill 覆盖 → CAPTURED（捕获新 skill）
```

#### 三种进化模式

| 模式 | 动作 | 触发信号 |
|------|------|---------|
| **FIX** | 就地修复现有 SKILL.md | skill 被选中但没起作用 |
| **DERIVED** | 从多个 skill 组合出新 skill | 多个 skill 经常连续使用 |
| **CAPTURED** | 创建全新 skill | 发现了没有 skill 覆盖的工作流模式 |

#### Skill 谱系追踪

每个 skill 目录下维护 `.lineage.json`：

```json
{
  "skill_id": "sprint__v1",
  "version": 1,
  "origin": "imported",
  "generation": 0,
  "parent_skills_ids": [],
  "change_summary": "初始版本",
  "created_at": "2026-04-06"
}
```

进化后更新：
```json
{
  "skill_id": "sprint__v2",
  "version": 2,
  "origin": "fixed",
  "generation": 1,
  "parent_skill_ids": ["sprint__v1"],
  "change_summary": "增加了调查超时策略",
  "created_at": "2026-04-07"
}
```

#### 安全审查

新建或修改 skill 时，自动运行 `/safety-check`：
- 阻断级问题（恶意命令、数据外泄）→ 不写入
- 警告级问题（敏感信息、外部钩子）→ 写入但标记

---

### 12. 双层知识体系

```
第一层：问题解决方案（CE /ce:compound）
└── docs/solutions/{category}/{filename}.md
    存储具体问题的根因和解法

第二层：技能进化知识（/skill-evolution）
└── docs/progress/skill-metrics.md + .lineage.json
    存储 skill 的使用效果和进化历史

两层互补：
- /ce:compound 回答"这个问题怎么解决"
- /skill-evolution 回答"这个工作流怎么优化"
```

---

### 13. 并行执行协议

> 借鉴 oh-my-openagent 的并行执行架构

**触发信号**：需求包含"并行"/"同时"/"批量"/"ultrawork"时，或 Sprint PLAN 阶段识别到多个独立子任务。

#### 13.1 并发控制

```
默认规则：
├── 最多 5 个并行 Agent（general-purpose 类型）
├── Explore 类型 Agent 不计入并发上限
├── 同一文件的修改禁止并行
├── 涉及代码修改的 Agent 必须使用 isolation: "worktree"
└── 研究/只读类 Agent 可自由并行
```

#### 13.2 Spawn 限制

```
├── 最大嵌套深度：3 层（Agent 不能无限嵌套调用 Agent）
├── 单次需求最大子任务：15 个
├── 单个 Wave 最大并行数：5 个
└── 超过限制时，自动拆分为多轮 Wave
```

#### 13.3 熔断器

每个并行 Agent 的行为受监控：

| 信号 | 阈值 | 动作 |
|------|------|------|
| 连续相同工具调用无进展 | 5 次 | 取消任务 |
| 总工具调用次数 | 100 次 | 取消任务（视为失控） |
| 无输出超时 | 10 分钟 | 取消任务 |
| 同一任务重试失败 | 2 次 | 放弃并行，回退串行 |

**熔断后恢复**：
1. 分析失败原因
2. 分解为更小子任务
3. 用更精确的 prompt 重试
4. 仍失败 → 串行执行

#### 13.4 任务路由

根据任务类别选择最优执行方式：

| 类别 | Agent 类型 | 说明 |
|------|-----------|------|
| research | Explore (quick) | 轻量搜索 |
| deep-research | Explore (very thorough) | 全面分析 |
| implementation | general-purpose (worktree) | 代码编写 |
| review | general-purpose (readonly) | 代码审查 |
| testing | general-purpose (worktree) | 测试编写 |
| planning | parallel-planner | 并行规划 |
| task-execution | task-runner | 子任务执行 |

#### 13.5 并行任务跟踪

所有并行任务记录到 `docs/progress/parallel-tasks.md`：
- 任务 ID、Wave 编号、状态、Agent 类型
- 启动时间、完成时间
- 结果摘要
- 错误记录（如有）

---

### 14. Ultrawork 编排模式

当使用 `/ultrawork` 或识别到并行信号时，进入并行编排模式：

```
DECOMPOSE → DISPATCH → GATHER → INTEGRATE → COMPOUND
    │           │          │          │          │
  任务分解    并行分发   结果汇聚   整合验证   知识沉淀
  (DAG)     (Wave)    (质量检查)  (测试+合并)  (效率分析)
```

**与 Sprint 集成**：
- Sprint BUILD 阶段可触发 ultrawork（多个功能并行开发）
- Sprint REVIEW 阶段可触发 ultrawork（多文件并行审查）
- Sprint TEST 阶段可触发 ultrawork（多模块并行测试）
- ultrawork 完成后回到 Sprint 主流程继续

**可用的并行模式**：

| 模式 | 适用场景 |
|------|---------|
| Wave 并行 | 多个独立功能同时开发 |
| 两阶段并行 | 先并行研究，再基于结果并行实现 |
| 扇出审查 | 多个 Reviewer 并行审查不同文件 |
| 竞争并行 | 多 Agent 各自完成同一任务，选最优方案 |

---

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health

---

## 参考文档

- gstack：https://github.com/garrytan/gstack
- CE Plugin：https://github.com/EveryInc/compound-engineering-plugin
- OpenHarness：https://github.com/HKUDS/OpenHarness
- OpenSpace：https://github.com/HKUDS/OpenSpace
- oh-my-openagent：https://github.com/sst/opencode（并行执行架构参考）

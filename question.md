# 工作流引擎（MyHarness）问题总结

> 本文档记录在「爆款复刻」项目开发过程中，gstack + CE Plugin 组合工作流引擎暴露的实际问题。

---

## 1. 流程过重，与项目规模不匹配

这是一个 Builder/黑客松 Demo 级项目（后端 7 文件 + 前端 1 文件），但工作流要求走完整的 Sprint 流程：

```
THINKING → PLANNING → BUILDING → REVIEWING → TESTING → SHIPPING → COMPOUNDING
```

实际体验：**管理状态文件的时间接近实际写代码的时间**。每次阶段转换都要更新 `current-sprint.md`、`session-bridge.md`，Session 结束还要判断是否 compound、写 bridge。

**问题本质**：Sprint 工作流是为多人协作、长周期项目设计的。单人 Demo 项目用这套流程，仪式感远大于实际价值。

---

## 2. Quality Gate 硬性约束导致卡顿

CLAUDE.md 规定 GATE 是"不可跳过的硬性约束"：

```
GATE 1: PLAN 通过前 → 禁止执行任何代码写入
GATE 2: REVIEW 通过前 → 禁止测试
GATE 3: QA 通过前 → 禁止发布
```

实际场景：
- 用户说"帮我把这个配置加上"这种 5 分钟能完成的任务，也被要求先走 PLAN
- 修复 `.env` 少了一个字段这种一行改动，理论上也要先 `/autoplan`
- 用户最终明确说"不要再问我授权"，本质是对 Gate 摩擦的抗议

**问题本质**：Gate 没有按任务规模分级。缺一个"快速通道"——小改动（< 10 行、单文件）应该直接执行。

---

## 3. 大量引用的 Skill 实际不存在或不可用

CLAUDE.md 列出了完整的 Skill 路由表：

```
/ce:work, /ce:review, /ce:compound, /ce:plan
/autoplan, /plan-ceo-review, /plan-design-review, /plan-eng-review
/office-hours, /investigate, /qa, /ship, /land-and-deploy
/careful, /guard, /codex, /benchmark, /retro, /learn
```

实际情况：
- **CE Plugin 的 skill（`/ce:*`）始终未真正加载**。在代码编写阶段，本应使用 `/ce:work`，但实际上是裸写代码
- `/office-hours` 和 `/plan-eng-review` 能用（gstack 自带），但 `/investigate`、`/qa` 等在关键时刻要么没触发，要么效果不符预期
- `/ce:compound` 从未成功执行过——Session 结束时的知识沉淀全靠手动写文件

**问题本质**：Skill 路由表是"理想地图"，但底层的 Skill 安装/加载/可用性没有自检机制。CLAUDE.md 声称能用 30+ 个 Skill，实际可靠运行的不到一半。

---

## 4. Context Window 被工作流指令大量占用

每次对话开始，上下文里要加载：

| 内容 | 估计 token |
|------|-----------|
| CLAUDE.md（完整工作流规则） | ~3000 |
| MEMORY.md（项目记忆） | ~800 |
| session-bridge.md | ~500 |
| Skill 列表（30+ 个 skill 描述） | ~2000 |
| current-sprint.md | ~300 |

合计约 **6600+ token** 被工作流元数据占用，还没开始写一行代码。在一次 context window 紧张导致会话被截断的场景下，这些元数据反而成了负担。

**问题本质**：工作流指令没有按需加载。一个只做 bug 修复的 Session，不需要加载 Sprint 状态管理、并行执行协议、Skill 自进化等规则。

---

## 5. Session 恢复协议过于复杂

CLAUDE.md 规定每次新 Session 要执行 4 步恢复：

```
Step 1: 读取 current-sprint.md
Step 2: 读取 session-bridge.md
Step 3: 用 learnings-researcher 检索 docs/solutions/
Step 4: 向用户确认下一步
```

实际体验：
- Step 3 的 `learnings-researcher` 从未被正确触发过
- 恢复过程花 3-4 轮工具调用，用户等了 30 秒还没开始干活
- Session 间真正的上下文传递靠的是 MEMORY.md 和用户自己的描述，不是那套 4 步协议

**问题本质**：恢复协议假设了一个"完美的知识管理体系"，但 `docs/solutions/` 目录下的分类文件夹（10 个空目录）从未被真正使用过。

---

## 6. 状态文件管理是纯体力活

项目要求维护的状态文件：

```
docs/progress/current-sprint.md    # Sprint 状态（每次阶段转换更新）
docs/progress/session-bridge.md    # Session 交接（每次结束覆盖写）
docs/progress/skill-metrics.md     # Skill 使用统计
docs/progress/parallel-tasks.md    # 并行任务跟踪
docs/solutions/{10个分类目录}/     # 知识沉淀
每个 skill 目录/.lineage.json      # Skill 谱系追踪
```

实际使用情况：
- `current-sprint.md` — 被更新了，但内容经常与实际不同步
- `session-bridge.md` — 被写了，但下次 Session 恢复时信息不够用
- `skill-metrics.md` — 从未被实际统计过
- `parallel-tasks.md` — 从未创建
- `docs/solutions/` — 10 个空目录
- `.lineage.json` — 从未生成

**问题本质**：要求维护的状态文件数量远超实际使用价值。更糟糕的是，这些文件的存在给人一种"流程在运转"的错觉，掩盖了实际执行中的混乱。

---

## 7. 并行执行协议与实际能力不匹配

CLAUDE.md 定义了完整的并行执行架构：

```
并发控制：最多 5 个并行 Agent
熔断器：连续无进展 5 次取消、总调用 100 次取消
任务路由：7 种 Agent 类型
Ultrawork 编排：DECOMPOSE → DISPATCH → GATHER → INTEGRATE → COMPOUND
```

实际情况：
- 整个项目的代码修改都是串行完成的
- 并行只用在了一次 explore agent 搜索代码时
- 熔断器、任务路由、Ultrawork 编排从未被触发
- 这些规则增加了 CLAUDE.md 的复杂度，但从未产生价值

**问题本质**：定义了企业级的并行编排能力，但实际开发中连 2 个文件同时修改的场景都没遇到。

---

## 8. Skill 自进化协议是空中楼阁

```
每次 Sprint 结束后：
├── 计算 effective_rate = completions / selections
├── ≥ 80% → 保持
├── 50-79% → FIX
├── 20-49% → DERIVED
├── < 20%  → CAPTURED
```

实际情况：
- 没有任何机制在追踪 Skill 的 "selections" 和 "completions"
- `skill-metrics.md` 是空的
- 没有任何 Skill 被修复、派生或新建
- `/skill-evolution` 命令从未被执行

**问题本质**：自进化是一个很好的理念，但前提是需要有可靠的使用数据采集。没有数据，进化规则就是空谈。

---

## 9. 用户指令与工作流规则的冲突

CLAUDE.md 的规则和用户的实际需求产生了多次冲突：

| 工作流规则 | 用户实际需求 | 结果 |
|-----------|-------------|------|
| GATE 1 前禁止写代码 | "帮我把这个配置加上" | 用户被迫绕过 |
| 每次执行前确认授权 | "不要再问我授权" | 用户明确 override |
| Session 结束走 4 步协议 | "先这样吧" | 协议部分执行 |
| 所有开发用 /ce:work | 直接要求改代码 | 跳过 skill 直接写 |

**问题本质**：工作流把 AI 当成了"需要严格流程管控的初级员工"，但用户实际想要的是一个"理解意图就开干的搭档"。规则的出发点是好的（防止跳步导致质量下降），但执行中没有弹性。

---

## 10. 真正有用的部分

公平地说，有几样东西确实产生了价值：

| 功能 | 价值 | 改进建议 |
|------|------|---------|
| `/office-hours` | 帮助理清了产品定位和设计方向 | 保留，这是 gstack 的核心能力 |
| `/plan-eng-review` | 发现了 14 个工程问题，避免了后续返工 | 保留，但对小任务应可选 |
| MEMORY.md 跨 Session 记忆 | 省去了重复解释项目背景 | 保留，但应更精简 |
| `.env` + `config.py` 的 `extra: "ignore"` | 学到的实用技巧 | 这种才是值得 compound 的知识 |
| 错误降级（`return_exceptions=True`） | 管线不会因单个服务失败而崩溃 | 这是好的工程实践，与工作流无关 |

---

## 改进建议

### 如果继续用这套工作流：

1. **按项目规模分级**：Demo 项目用 Lite 模式（THINK → BUILD → SHIP），生产项目才用完整 Sprint
2. **Gate 分级**：< 10 行改动免 Gate，单模块改动走 Fast Gate（自查而非审查），跨模块才走 Full Gate
3. **Skill 可用性自检**：Session 开始时自动检查哪些 Skill 真正可用，不可用的从路由表中移除
4. **按需加载规则**：bug 修复不加载 Sprint 规则，小改动不加载并行协议
5. **状态文件极简化**：只保留 `session-bridge.md`（一页纸），其他全部去掉
6. **砍掉未使用的子系统**：Skill 自进化、并行熔断器、Ultrawork 编排——需要时再加

### 如果重新设计：

> 一个好的工作流引擎应该是"隐形的"——你不需要感觉到它的存在，但质量自然有保障。当前的 MyHarness 更像是一个"处处都要让你感觉到它存在"的流程管控系统。

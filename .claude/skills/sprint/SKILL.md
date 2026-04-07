---
name: sprint
description: |
  完整的 gstack+CE Sprint 工作流。
  自动管理 THINK → PLAN → BUILD → REVIEW → TEST → SHIP → COMPOUND 全流程。
  当用户要求开发新功能、做技术改进时使用此 skill。
---

# Sprint 工作流

## 触发条件

- 用户要求开发新功能
- 用户要求做技术改进/重构
- 用户说"开始 Sprint"或"/sprint"

## 前置检查

1. 验证 gstack 已安装：`test -d ~/.claude/skills/gstack`
2. 验证 CE Plugin 已安装：`test -d ~/.claude/skills/compound-engineering`
3. 检查是否有活跃 Sprint：读取 `docs/progress/current-sprint.md`
4. 如果有活跃 Sprint，询问用户：继续当前 / 创建新的

---

## Phase 1: THINK

**状态：** `THINKING`
**工具：** gstack `/office-hours`

### 步骤

1. 初始化 Sprint 状态文件

```yaml
# docs/progress/current-sprint.md
---
sprint_id: sprint-{YYYY-MM-DD}-{seq}
status: THINKING
created: {now}
updated: {now}
title: {用户描述的标题}
type: full-sprint | tech-sprint
---
```

2. 执行 `/office-hours`
   - 收集需求的 6 个关键问题
   - 确定 MVP 范围
   - 记录关键决策到 Sprint 状态文件

3. 完成标志：需求方向明确，MVP 范围确定
4. 更新 status → `PLANNING`

---

## Phase 2: PLAN

**状态：** `PLANNING`
**工具：** gstack `/autoplan` 或分步审查 + CE `/ce:plan`

### 路径选择

```
需求复杂度？
├─ 小/中（1-3 天可完成）→ /autoplan（一键审查）
└─ 大（3 天以上）      → 分步：
    ├─ /plan-ceo-review（产品视角）
    ├─ /plan-design-review（设计视角，如有 UI）
    └─ /plan-eng-review（架构视角）
```

### 步骤

1. 根据 Sprint 类型选择审查路径
2. 执行 gstack 审查命令
3. 审查通过后，执行 `/ce:plan`
   - 自动触发 learnings-researcher 检索 `docs/solutions/`
   - 自动触发 repo-research-analyst 分析代码库
   - 自动触发 best-practices-researcher 搜索最佳实践
4. 确认计划文件生成：`plans/{slug}.md`
5. 完成标志：计划文件存在且内容完整
6. 更新 status → `BUILDING`

### 关卡：GATE 1

> Plan 审查未通过时，**禁止**进入 BUILD 阶段。

---

## Phase 3: BUILD

**状态：** `BUILDING`
**工具：** CE `/ce:work` + gstack `/careful`

### 步骤

1. 确认 `plans/{slug}.md` 存在
2. 如果涉及重要变更，先执行 `/careful` 启用安全模式
3. 执行 `/ce:work`
   - 自动创建 worktree（如需要）
   - 持续测试
   - 遵循项目代码模式
4. 开发过程中：
   - 遇到架构决策 → 记录到 Sprint 状态文件
   - 遇到坑/解决方案 → 标记为 compound 候选
5. 完成标志：代码编写完成，基本功能可用
6. 更新 status → `REVIEWING`

---

## Phase 4: REVIEW

**状态：** `REVIEWING`
**工具：** CE `/ce:review` + gstack `/review` + `/codex`

### 步骤

1. 执行 `/ce:review`
   - 13+ 专项 Reviewer 并行审查
   - 检查 P0/P1/P2/P3 分级
2. 执行 `/review`（gstack Staff Engineer 审查）
3. 可选：执行 `/codex`（OpenAI 交叉验证，高风险变更时建议）
4. 如果有 UI 变更：执行 `/design-review`

### 审查结果处理

```
P0 问题数量？
├─ 0  → 审查通过，进入 TEST
├─ 1-2 → 修复 P0，重新 /ce:review
└─ 3+  → 考虑回退到 PLAN，重新设计
```

5. 完成标志：P0 清零
6. 更新 status → `TESTING`

### 关卡：GATE 2

> P0 问题未清零时，**禁止**进入 TEST 阶段。

---

## Phase 5: TEST

**状态：** `TESTING`
**工具：** gstack `/qa` + `/benchmark`

### 步骤

1. 执行 `/qa`
   - 真实浏览器端到端测试
   - 自动生成回归测试
2. 如果涉及性能：执行 `/benchmark`
3. 如果涉及安全：执行 `/cso`

### 测试结果处理

```
/qa 结果？
├─ 通过 → 进入 SHIP
├─ 小 bug → /investigate + 直接修 → 重新 /qa
└─ 大 bug → 记录问题，回退到 BUILD
```

4. 完成标志：QA 通过
5. 更新 status → `SHIPPING`

### 关卡：GATE 3

> QA 未通过时，**禁止**进入 SHIP 阶段。

---

## Phase 6: SHIP

**状态：** `SHIPPING`
**工具：** gstack `/ship` + `/land-and-deploy` + `/canary`

### 步骤

1. 执行 `/ship`
   - 自动同步 main
   - 运行测试
   - 审计覆盖率
   - 创建 PR
   - 自动调用 `/document-release`
2. PR 合并后执行 `/land-and-deploy`
   - 合并 PR
   - 等待 CI/部署
   - 验证生产健康
3. 执行 `/canary`（金丝雀监控）
4. 完成标志：部署成功且健康
5. 更新 status → `COMPOUNDING`

### 关卡：GATE 4

> 涉及 API/数据/权限变更时，必须先执行 `/cso`。

---

## Phase 7: COMPOUND

**状态：** `COMPOUNDING`
**工具：** CE `/ce:compound` + gstack `/retro`

### 步骤

1. 判断本次 Sprint 是否值得 compound

```
值得 compound？
├─ 开发了 2h+ 的新功能     → ✅
├─ 解决了复杂 bug          → ✅
├─ 做了性能优化            → ✅
├─ 发现了设计模式          → ✅
├─ 只改了 typo/CSS         → ❌
├─ 跑了标准 migration      → ❌
└─ 做了配置变更            → ❌
```

2. 如果值得：执行 `/ce:compound`
   - 7 个并行子代理提取知识
   - 写入 `docs/solutions/{category}/`
3. 执行 `/retro`
   - Sprint 复盘
   - 记录统计和趋势

4. 清理 Sprint 状态文件
5. 写入 session-bridge.md

---

## 状态流转图

```
THINKING → PLANNING → BUILDING → REVIEWING → TESTING → SHIPPING → COMPOUNDING
   │          │          │          │           │          │           │
   │          │          │          │           │          │           └─→ 完成
   │          │          │          │           │          └─→ 部署失败 → /investigate
   │          │          │          │           └─→ 测试失败 → 修复 → 重试
   │          │          │          └─→ P0 问题 → 修复 → 重试
   │          │          └─→ 构建失败 → /investigate → 重试
   │          └─→ 审查不通过 → 修改计划 → 重试
   └─→ 需求不清晰 → 继续讨论
```

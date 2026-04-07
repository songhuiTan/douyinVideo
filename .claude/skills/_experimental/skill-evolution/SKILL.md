---
name: skill-evolution
description: |
  自进化技能引擎。借鉴 OpenSpace 的 FIX/DERIVED/CAPTURED 三种进化模式。
  在 Sprint 结束后的 COMPOUND 阶段，不仅沉淀知识（/ce:compound），
  还要分析本次使用的 skill 是否有效，并自动修复、派生或创建新 skill。
  当用户说"回顾技能"/"skill-evolution"时使用。
category: workflow
---

# Skill Evolution — 自进化技能引擎

## 触发条件

- Sprint 的 COMPOUND 阶段自动触发
- 用户说"回顾技能"或"/skill-evolution"
- 用户说"优化 skill"或"改进工作流"

## 核心概念

借鉴 OpenSpace 的三种进化模式：

| 模式 | 含义 | 触发信号 |
|------|------|---------|
| **FIX** | 修复现有 skill 的缺陷 | skill 被选中但没起作用、执行出错、用户抱怨 |
| **DERIVED** | 从已有 skill 组合/增强出新的 | 多个 skill 被连续使用、出现通用模式 |
| **CAPTURED** | 捕获全新的可复用模式 | 发现了一个没有 skill 覆盖的新工作流 |

---

## Phase 1: 执行回顾

### 1.1 分析本次 session 的 skill 使用情况

```
回顾本次 session：
├── 使用了哪些自定义 skill？（sprint / hotfix / compound-janitor）
├── gstack 命令执行了几次？成功/失败？
├── CE 命令执行了几次？成功/失败？
├── 哪些阶段顺利通过了？
├── 哪些阶段遇到了问题？
└── 有没有手动跳过的关卡？
```

### 1.2 填写执行分析

更新 `docs/progress/skill-metrics.md`，为每个使用的 skill 记录：

```yaml
## sprint (YYYY-MM-DD)
selections: 1    # 被选中次数
applied: 1        # 实际执行次数
completions: 1    # 执行成功次数
fallbacks: 0      # 未能执行次数
issues: []        # 遇到的问题
notes: ""         # 观察记录
```

---

## Phase 2: 问题分类

对每个遇到的问题进行分类：

```
问题类型？
├── skill 指令不够清晰 → FIX（修复 skill 描述）
├── 缺少某个判断分支   → FIX（补充分支逻辑）
├── skill 覆盖不到的场景 → CAPTURED（创建新 skill）
├── 多个 skill 连续使用 → DERIVED（组合为新 skill）
└── 质量关卡太严格/宽松 → FIX（调整关卡阈值）
```

---

## Phase 3: 执行进化

### FIX — 修复现有 Skill

```
1. 读取有问题的 skill 文件
2. 定位需要修复的部分
3. 修改 SKILL.md
4. 更新 .lineage.json：
   {
     "version": 2,
     "origin": "fixed",
     "parent_version": 1,
     "change_summary": "修复了 [具体改动]",
     "timestamp": "YYYY-MM-DD"
   }
5. 更新 skill-metrics.md 中的版本号
```

### DERIVED — 派生新 Skill

```
1. 识别经常连续使用的 skill 组合
2. 创建新 skill 目录：.claude/skills/{new-name}/SKILL.md
3. 融合父 skill 的关键步骤
4. 创建 .lineage.json：
   {
     "version": 1,
     "origin": "derived",
     "parent_skills": ["sprint", "compound-janitor"],
     "change_summary": "组合了 Sprint + Compound Janitor 为自动化闭环",
     "timestamp": "YYYY-MM-DD"
   }
```

### CAPTURED — 捕获新模式

```
1. 识别没有 skill 覆盖的工作流模式
2. 创建新 skill 目录：.claude/skills/{new-name}/SKILL.md
3. 编写完整的触发条件、前置检查、步骤、完成标志、错误恢复
4. 创建 .lineage.json：
   {
     "version": 1,
     "origin": "captured",
     "parent_skills": [],
     "change_summary": "捕获了 [新工作流名称] 模式",
     "timestamp": "YYYY-MM-DD"
   }
```

---

## Phase 4: 质量评估

### 4.1 计算技能有效率

```
对于每个 skill：

effective_rate = completions / selections

评级：
├── ≥ 80% → 🟢 优秀，保持
├── 50-79% → 🟡 一般，考虑 FIX
├── 20-49% → 🟠 较差，必须 FIX 或 DERIVED
└── < 20%  → 🔴 失败，考虑退役或重写
```

### 4.2 生成进化建议

```markdown
## Skill 进化报告

### 🟢 sprint（有效率 85%）
- 状态：优秀
- 建议：保持

### 🟡 hotfix（有效率 62%）
- 状态：一般
- 问题：INVESTIGATE 阶段经常超时
- 建议：FIX — 增加 3 次调查失败后的自动升级策略

### 🟠 compound-janitor（有效率 35%）
- 状态：较差
- 问题：评分算法对前端变更不敏感
- 建议：FIX — 增加文件类型的权重调整
```

---

## Phase 5: 更新文档

### 5.1 更新 skill-metrics.md

追加本次分析结果和统计数据。

### 5.2 更新 session-bridge.md

在交接文件中附加 skill 进化记录：
```markdown
### Skill 进化记录
- [FIX] hotfix v1 → v2：增加了调查超时策略
- [CAPTURED] 新建 code-review-full skill：覆盖了从审查到修复的完整流程
```

### 5.3 汇报

```
Skill 进化完成：
- 修复了 N 个 skill
- 派生了 N 个新 skill
- 捕获了 N 个新模式
- 整体有效率从 X% 提升到 Y%
```

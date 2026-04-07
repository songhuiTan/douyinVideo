---
name: harness-init
description: |
  项目 Harness 初始化工作流。创建目录结构、安装插件、生成配置文件。
  当用户要在新项目中使用 gstack+CE 组合工作流时使用。
  用户说"初始化项目"/"harness-init"时触发。
---

# Harness 初始化工作流

## 触发条件

- 用户说"初始化项目"或"harness-init"
- 新项目首次使用组合工作流
- 用户说"setup harness"

---

## Phase 1: 环境检查

### 1.1 检查基础依赖

```bash
# Claude Code
which claude && echo "Claude Code: OK" || echo "Claude Code: MISSING"

# Git
git --version

# Bun（gstack 需要）
bun --version || echo "Bun: MISSING (gstack 需要)"

# Node.js
node --version
```

### 1.2 检查框架安装

```bash
# gstack
test -d ~/.claude/skills/gstack && echo "gstack: OK" || echo "gstack: MISSING"

# CE Plugin
test -d ~/.claude/skills/compound-engineering && echo "CE: OK" || echo "CE: MISSING"
```

### 1.3 缺失处理

```
缺失 gstack？
└─ 提供：git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup

缺失 CE？
└─ 提供：/plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin && /plugin install compound-engineering

缺失 Bun？
└─ 提供：curl -fsSL https://bun.sh/install | bash
```

---

## Phase 2: 创建目录结构

```
项目根目录/
├── docs/
│   ├── progress/
│   │   ├── current-sprint.md      ← Sprint 状态跟踪
│   │   └── session-bridge.md      ← 跨 session 交接
│   └── solutions/
│       ├── build-errors/
│       ├── test-failures/
│       ├── runtime-errors/
│       ├── performance-issues/
│       ├── database-issues/
│       ├── security-issues/
│       ├── ui-bugs/
│       ├── integration-issues/
│       ├── logic-errors/
│       └── patterns/
│           └── critical-patterns.md
├── plans/
└── scripts/
    ├── harness-init.sh
    └── compound-janitor.sh
```

---

## Phase 3: 生成配置文件

### 3.1 current-sprint.md 初始化

```yaml
---
sprint_id: none
status: IDLE
created: {date}
updated: {date}
title: ""
type: none
---

## 当前阶段
IDLE — 无活跃 Sprint

## 已完成的步骤
（无）

## 关键决策记录
（无）

## 阻塞问题
（无）
```

### 3.2 session-bridge.md 初始化

```markdown
---
last_session: {date}
next_phase: none
pending_items: []
---

## 上一班交接

### 说明
这是新项目，尚无交接内容。首次使用时请选择工作流：
- 新功能开发 → /sprint
- Bug 修复 → /hotfix
- 整理知识 → /compound-janitor
```

### 3.3 critical-patterns.md 初始化

```markdown
# 关键模式

> 同一类问题出现 3 次以上时，自动记录于此。
> 最后更新：{date}

（暂无关键模式）
```

---

## Phase 4: 安装 Harness 文件

将 myharness 中的文件复制到项目：

```
复制到项目 .claude/ 目录：
├── .claude/skills/sprint/SKILL.md
├── .claude/skills/hotfix/SKILL.md
├── .claude/skills/compound-janitor/SKILL.md
├── .claude/skills/harness-init/SKILL.md
├── .claude/commands/sprint.md
├── .claude/commands/hotfix.md
├── .claude/commands/compound-janitor.md
└── .claude/hooks/hooks.json

复制到项目根目录：
├── CLAUDE.md
└── settings.json (如需要)
```

---

## Phase 5: 验证

### 5.1 验证目录结构

```bash
echo "=== 目录结构验证 ==="
test -d docs/progress && echo "✅ docs/progress" || echo "❌ docs/progress"
test -d docs/solutions && echo "✅ docs/solutions" || echo "❌ docs/solutions"
test -d plans && echo "✅ plans" || echo "❌ plans"
test -f docs/progress/current-sprint.md && echo "✅ current-sprint.md" || echo "❌ current-sprint.md"
test -f docs/progress/session-bridge.md && echo "✅ session-bridge.md" || echo "❌ session-bridge.md"
```

### 5.2 验证 Skills 注册

列出已安装的 skills，确认 sprint/hotfix/compound-janitor/harness-init 都在。

### 5.3 验证框架命令

```
测试命令可用性：
- /office-hours（gstack）
- /review（gstack）
- /qa（gstack）
- /ce:plan（CE）
- /ce:work（CE）
- /ce:review（CE）
- /ce:compound（CE）
```

---

## Phase 6: 汇报

```
## Harness 初始化完成

✅ 目录结构已创建
✅ 配置文件已生成
✅ Skills 已注册
✅ 框架已验证

下一步：
1. 开始新功能开发 → /sprint
2. 修复已知 bug → /hotfix
3. 查看 CLAUDE.md 了解完整工作流规则
```

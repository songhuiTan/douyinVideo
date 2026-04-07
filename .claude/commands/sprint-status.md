---
name: sprint-status
description: 查看当前 Sprint 状态和进度
allowed-tools: ["Read", "Glob", "Grep"]
---

# /sprint-status — 查看状态

读取并展示当前 Sprint 状态。

## 流程

1. 读取 `docs/progress/current-sprint.md`
2. 读取 `docs/progress/session-bridge.md`
3. 展示：
   - 当前 Sprint ID 和标题
   - 当前阶段（THINKING/PLANNING/BUILDING/...）
   - 已完成步骤的 checklist
   - 阻塞问题
   - 上次交接的关键上下文
4. 建议下一步操作

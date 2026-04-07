---
name: sprint
description: 启动完整 Sprint 工作流（THINK → PLAN → BUILD → REVIEW → TEST → SHIP → COMPOUND）
allowed-tools: ["*"]
---

# /sprint — 启动 Sprint

执行 sprint skill，开始完整的工作流循环。

## 流程

1. 检查 `docs/progress/current-sprint.md` 是否有活跃 Sprint
   - 有 → 询问继续还是新建
   - 无 → 创建新 Sprint
2. 询问用户需求描述
3. 自动判断 Sprint 类型（full-sprint / tech-sprint）
4. 加载 sprint skill 开始 Phase 1: THINK
5. 后续阶段按 sprint skill 定义的流程自动推进

## 参数

用户可在命令后直接描述需求：
- `/sprint 开发用户认证功能`
- `/sprint 重构数据库查询层`

如果不带参数，进入交互式需求收集模式。

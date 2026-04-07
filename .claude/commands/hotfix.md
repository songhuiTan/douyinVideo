---
name: hotfix
description: 启动紧急修复工作流（INVESTIGATE → PLAN → FIX → REVIEW → DEPLOY → COMPOUND）
allowed-tools: ["*"]
---

# /hotfix — 启动 Hotfix

执行 hotfix skill，开始紧急修复循环。

## 流程

1. 询问用户 Bug 描述或错误信息
2. 检索 `docs/solutions/` 是否有历史经验
3. 加载 hotfix skill 开始 Phase 1: INVESTIGATE
4. 后续阶段按 hotfix skill 定义的流程自动推进

## 参数

用户可在命令后直接描述问题：
- `/hotfix 用户登录后白屏`
- `/hotfix API 返回 500 错误`

如果不带参数，进入交互式问题收集模式。

## 紧急模式

如果用户说"紧急"/"P0"/"线上"，自动跳过部分审查步骤。

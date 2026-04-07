---
name: compound-janitor
description: 运行知识清理（扫描今日变更，筛选有价值的 session 批量 compound）
allowed-tools: ["*"]
---

# /compound-janitor — 知识清理

执行 compound-janitor skill，扫描和整理知识库。

## 流程

1. 扫描今日 git diff 和 commit 历史
2. 对变更按价值分级（⭐⭐⭐ / ⭐⭐ / ⭐ / ✗）
3. 展示候选列表供用户确认
4. 批量执行 `/ce:compound`
5. 维护知识库健康度（去重、更新、关键模式检测）

## 使用时机

- 每天结束时
- 完成一个大功能后
- 感觉"最近踩了不少坑"时

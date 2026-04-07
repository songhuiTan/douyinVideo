---
name: skill-evolution
description: 运行技能自进化分析（回顾技能效果、修复/派生/捕获技能）
allowed-tools: ["*"]
---

# /skill-evolution — 技能自进化

执行 skill-evolution skill，分析技能效果并进化。

## 流程

1. 读取 docs/progress/skill-metrics.md 获取当前质量数据
2. 回顾本次 session 使用的 skill
3. 对每个 skill 执行评估（applied_rate / completion_rate）
4. 识别需要 FIX / DERIVED / CAPTURED 的技能
5. 执行进化并更新 metrics

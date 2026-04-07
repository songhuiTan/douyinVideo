---
name: safety-check
description: 对指定的 skill 或所有 skill 运行安全审查
allowed-tools: ["Read", "Glob", "Grep"]
---

# /safety-check — 安全审查

执行 safety-check skill，检查 skill 内容是否安全。

## 用法

- `/safety-check` — 检查所有 skill
- `/safety-check sprint` — 检查指定 skill

## 输出

安全审查报告，包含检查结果和建议。
